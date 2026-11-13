"""Workflow LangGraph explicite, borné et conservateur."""
import base64
import time
from typing import TypedDict
import yaml
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from src.settings import ROOT, MAX_CONTEXT
from src.runtime_models import Answer, StrictModel
from pydantic import Field
from src.evidence_check import check_answer
from src.ollama_client import validate_photo
from src.security import require_equipment, safe_path

class Visual(StrictModel):
    observations: list[str] = Field(max_length=6)
    readable: bool
    uncertainties: list[str] = Field(max_length=6)

class State(TypedDict, total=False):
    question: str
    evidence: list
    notes: list
    visual: dict
    answer: dict
    evidence_report: dict
    history: dict
    stage: str
    session_history: list

def abstention(reason):
    return Answer(status="abstention", answer="Les preuves disponibles ne permettent pas une réponse technique vérifiée.", citations=[], uncertainties=[reason], clarification_question="Pouvez-vous préciser le modèle et fournir la page pertinente ?", proposed_action=None).model_dump()

def build_graph(retriever, model, principal, budget, request, token, mcp_call):
    photo = validate_photo(request.photo_base64) if request.photo_base64 and request.mode == "multimodal" else None
    def authorize(state):
        budget.remaining()
        if request.equipment_id: require_equipment(principal, request.equipment_id)
        return {"stage": "authorized", "notes": []}
    def retrieve(state):
        evidence, notes = retriever.search(state["question"], principal, request.family, photo, budget, enable_visual=request.mode == "multimodal")
        return {"evidence": evidence, "notes": notes, "stage": "retrieved"}
    def rerank(state):
        evidence, notes = retriever.rerank(state["question"], state["evidence"], budget)
        return {"evidence": evidence, "notes": state["notes"] + notes, "stage": "reranked"}
    async def history(state):
        if not request.equipment_id: return {"history": {}}
        result = await mcp_call(token, "get_equipment_history", {"equipment_id": request.equipment_id}, budget)
        return {"history": result}
    def vision(state):
        if request.mode == "text_only":
            return {"visual": {}, "notes": state["notes"] + ["Mode texte seul explicitement demandé"]}
        images = []
        if photo: images.append(base64.b64encode(photo).decode())
        if state["evidence"]:
            # Une seule page limite la latence et les besoins mémoire.
            image = state["evidence"][0].image
            if image: images.append(base64.b64encode(safe_path(image).read_bytes()).decode())
        if not images: return {"visual": {}}
        prompt = yaml.safe_load((ROOT / "prompts/visual_analysis_v1.yaml").read_text(encoding="utf-8"))["system"]
        result = model.generate(prompt, {"question": state["question"]}, Visual, budget, images=images)
        return {"visual": result.model_dump(), "stage": "visualized"}
    def generate(state):
        if not state["evidence"]: return {"answer": abstention("Aucune source pertinente autorisée")}
        if photo and not state.get("visual", {}).get("readable", False):
            value = abstention("Photographie ambiguë ou illisible")
            value["status"] = "needs_clarification"
            return {"answer": value}
        prompt = yaml.safe_load((ROOT / "prompts/runtime_answer_v1.yaml").read_text(encoding="utf-8"))["system"]
        rendered = ChatPromptTemplate.from_messages([("system", "{rules}"), ("human", "{question}")]).format_messages(rules=prompt, question=state["question"])
        payload = {"question": state["question"], "session_history_untrusted": state.get("session_history", []), "evidence": [e.model_dump() for e in state["evidence"]], "visual_observations_unverified": state.get("visual", {}), "maintenance_history_untrusted": state.get("history", {})}
        import json
        if len(json.dumps(payload)) > MAX_CONTEXT: raise ValueError("Contexte trop volumineux")
        result = model.generate(rendered[0].content, payload, Answer, budget)
        return {"answer": result.model_dump(), "stage": "generated"}
    def check(state):
        answer = Answer.model_validate(state["answer"])
        if answer.status != "answered":
            # Une réponse non vérifiée ne peut cacher une procédure sous un statut prudent.
            safe = abstention("Les preuves ne permettent pas de valider les faits proposés")
            safe["status"] = answer.status
            return {"answer": safe, "stage": "abstained"}
        answer.proposed_action = None
        report, supported = check_answer(state["question"], answer, state["evidence"], model, budget)
        return {"evidence_report": report.model_dump(), "answer": answer.model_dump() if supported else abstention("Preuve insuffisante, contradictoire ou citation non vérifiée"), "stage": "checked"}
    graph = StateGraph(State)
    for name, node in [("authorize", authorize), ("retrieve", retrieve), ("rerank", rerank), ("history", history), ("vision", vision), ("generate", generate), ("evidence_check", check)]:
        graph.add_node(name, node)
    sequence = [START, "authorize", "retrieve", "rerank", "history", "vision", "generate", "evidence_check", END]
    for a,b in zip(sequence, sequence[1:]): graph.add_edge(a,b)
    return graph.compile()
