"""API locale authentifiée ; pas d'accès aux données ni aux outils sans identité."""
import asyncio
import base64
import io
import json
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Literal
import anyio
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langgraph.types import Command
from src.runtime_models import Ask, Draft, Approval, CreateTicket
from src.security import authenticate, require_document, require_equipment, safe_path
from src.settings import ROOT
from src.ollama_client import Budget, Ollama
from src.retrieval import Retriever
from src.workflow import build_graph, abstention
from src.approval_flow import build_approval_graph
from src.mcp_client import call_tool
from src.provenance import runtime_provenance

@asynccontextmanager
async def lifespan(app):
    # Chargement hors du budget d'une question et avant toute acceptation réseau.
    # Aucun téléchargement de modèle au démarrage.
    from src.retrieval import encoder, reranker
    from src.settings import STATE
    app.state.rag_ready = False
    app.state.rag_error = None
    try:
        retriever()
        if (STATE / "models/text").is_dir():
            await anyio.to_thread.run_sync(lambda: encoder("text"))
        if (STATE / "models/reranker").is_dir():
            await anyio.to_thread.run_sync(reranker)
        if (ROOT / "data/processed/clip_pages_v1.npz").exists():
            for kind in ("clip-image", "clip-text"):
                if (STATE / "models" / kind).is_dir():
                    await anyio.to_thread.run_sync(lambda kind=kind: encoder(kind))
        app.state.rag_ready = True
    except (FileNotFoundError, ValueError, OSError) as exc:
        app.state.rag_error = type(exc).__name__
        log.warning("rag_startup_unavailable type=%s", type(exc).__name__)
    yield

app = FastAPI(lifespan=lifespan, title="MAINTiDOC", version="0.2.0", docs_url=None, redoc_url=None, openapi_url=None)
bearer = HTTPBearer(auto_error=False)
lock = threading.Lock()
rate = defaultdict(deque)
histories = {}
pending = {}
log = logging.getLogger("maintidoc.audit")

@app.middleware("http")
async def body_limit(request: Request, call_next):
    body = bytearray()
    async for part in request.stream():
        body.extend(part)
        if len(body) > 8 * 1024 * 1024:
            return JSONResponse({"detail": "Requête trop volumineuse"}, status_code=413)
    request._body = bytes(body)
    return await call_next(request)

def identity(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    try:
        token = credentials.credentials if credentials else ""
        actor = authenticate(token)
        return actor, token
    except PermissionError:
        raise HTTPException(401, "Authentification refusée") from None

@app.exception_handler(PermissionError)
async def permission_error(request, exc):
    return JSONResponse({"detail": "Accès ou approbation refusé"}, status_code=403)

@lru_cache(maxsize=1)
def retriever():
    return Retriever()

@app.get("/health")
def health():
    return {"status": "ok", "scope": "prototype local fictif"}

@app.post("/ask")
async def ask(body: Ask, auth=Depends(identity)):
    actor, token = auth
    now = time.monotonic()
    for key in list(histories):
        if not histories[key] or histories[key][-1]["time"] < time.time() - 1800:
            histories.pop(key)
    prior = [{"question": row["question"][:500], "answer": row["answer"]["answer"][:500]} for row in list(histories.get((actor.user, body.session_id), []))[-2:]]
    recent = rate[actor.user]
    while recent and recent[0] < now - 60: recent.popleft()
    if len(recent) >= 6: raise HTTPException(429, "Quota de six demandes par minute")
    recent.append(now)
    if not lock.acquire(blocking=False): raise HTTPException(429, "Une analyse est déjà en cours")
    budget = Budget()
    request_id = uuid.uuid4().hex
    try:
        graph = build_graph(retriever(), Ollama(), actor, budget, body, token, call_tool)
        with anyio.fail_after(budget.remaining()):
            result = await graph.ainvoke({"question": body.question, "session_history": prior}, config={"recursion_limit": 12})
        answer = result.get("answer", abstention("Réponse absente"))
        output = dict(response=answer, evidence_report=result.get("evidence_report"), notes=result.get("notes", []), visual=result.get("visual"), history=result.get("history"), provenance={**runtime_provenance(), "mode": body.mode})
    except PermissionError:
        raise
    except Exception as exc:
        # Ni texte utilisateur, ni document, ni jeton dans les journaux.
        reasons = {"TimeoutError": "Délai de traitement dépassé ; aucune réponse technique n'est validée", "FileNotFoundError": "Fichier du corpus ou modèle local absent", "URLError": "Service du modèle indisponible", "ConnectionError": "Service du modèle indisponible", "HTTPError": "Le service du modèle a refusé la demande", "ValidationError": "La sortie du modèle ne respecte pas le schéma", "ValueError": "Sortie ou données invalides"}
        reason = reasons.get(type(exc).__name__, f"Traitement indisponible : {type(exc).__name__}")
        output = dict(response=abstention(reason), error_code=type(exc).__name__, notes=["Aucune réponse technique non vérifiée n'est présentée"])
    finally:
        lock.release()
    output["usage"] = dict(model_calls=budget.model_calls, model_call_breakdown=budget.model_roles, mcp_calls=budget.mcp_calls, elapsed_seconds=round(time.monotonic() - budget.start, 3))
    output["request_id"] = request_id
    if len(histories) >= 50 and (actor.user, body.session_id) not in histories:
        histories.pop(next(iter(histories)))
    # Historique limité et en mémoire, sans photographie ni preuves brutes.
    history = histories.setdefault((actor.user, body.session_id), deque(maxlen=10))
    history.append({"request_id": request_id, "status": output["response"]["status"], "question": body.question, "answer": output["response"], "time": time.time()})
    log.info("request=%s status=%s models=%s mcp=%s", request_id, output["response"]["status"], budget.model_calls, budget.mcp_calls)
    return output

@app.get("/sessions/{session_id}")
def session_history(session_id: str, auth=Depends(identity)):
    key = (auth[0].user, session_id)
    rows = histories.get(key, [])
    if rows and rows[-1]["time"] < time.time() - 1800:
        histories.pop(key, None)
        return []
    return list(rows)

@app.get("/sources/{document_id:path}")
def source(document_id: str, page: int = 1, kind: Literal["image", "pdf"] = "image", auth=Depends(identity)):
    policy = require_document(auth[0], document_id)
    if kind == "pdf":
        return FileResponse(safe_path(policy["path"]), media_type="application/pdf")
    link = next((l for l in list(retriever().links.values()) + list(retriever().visual_links.values()) if l["document_id"] == document_id and l["page"] == page), None)
    if link is None: raise HTTPException(404, "Source absente")
    return FileResponse(safe_path(link["image_path"]), media_type="image/png")

@app.get("/equipment/{equipment_id}/history")
async def equipment_history(equipment_id: str, auth=Depends(identity)):
    actor, token = auth
    require_equipment(actor, equipment_id)
    return await call_tool(token, "get_equipment_history", {"equipment_id": equipment_id}, Budget())

@app.get("/equipment/{equipment_id}/tickets")
async def equipment_tickets(equipment_id: str, auth=Depends(identity)):
    actor, token = auth
    require_equipment(actor, equipment_id)
    return await call_tool(token, "get_open_tickets", {"equipment_id": equipment_id}, Budget())

@app.post("/tickets/prepare")
def prepare(body: Draft, auth=Depends(identity)):
    actor, _ = auth
    require_equipment(actor, body.equipment_id)
    # Nettoyer les brouillons expirés et borner la mémoire.
    for key in list(pending):
        if pending[key][3] < time.monotonic(): pending.pop(key)
    if len(pending) >= 100: raise HTTPException(429, "Trop de brouillons")
    draft_id = uuid.uuid4().hex
    graph = build_approval_graph(actor)
    config = {"configurable": {"thread_id": draft_id}}
    graph.invoke({"draft": body.model_dump()}, config)
    pending[draft_id] = (actor.user, graph, body.model_dump(), time.monotonic() + 300)
    return {"draft_id": draft_id, "draft": body.model_dump(), "status": "awaiting_human_approval"}

@app.post("/tickets/{draft_id}/approve")
def approve(draft_id: str, body: Approval, auth=Depends(identity)):
    actor, _ = auth
    item = pending.get(draft_id)
    if item is None or item[0] != actor.user or item[3] < time.monotonic():
        raise HTTPException(403, "Brouillon absent, expiré ou interdit")
    if not body.confirmed or body.model_dump(exclude={"confirmed"}) != item[2]:
        raise HTTPException(403, "Nouvelle préparation requise pour un contenu modifié")
    result = item[1].invoke(Command(resume={"confirmed": True}), {"configurable": {"thread_id": draft_id}})
    pending.pop(draft_id)
    return {"approval_token": result["approval_token"]}

@app.post("/tickets")
async def create_ticket(body: CreateTicket, auth=Depends(identity)):
    actor, token = auth
    require_equipment(actor, body.equipment_id)
    return await call_tool(token, "create_ticket", body.model_dump(), Budget())
