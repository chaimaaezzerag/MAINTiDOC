"""Empreintes des index, prompts et révisions de modèles réellement présents."""
import hashlib
import json
from functools import lru_cache
from src.settings import ROOT, STATE, DATA, MODEL

@lru_cache(maxsize=1)
def runtime_provenance():
    prompts = {}
    for name in ("runtime_answer_v1.yaml", "visual_analysis_v1.yaml", "evidence_check_v1.yaml", "ticket_draft_v1.yaml"):
        prompts[name] = hashlib.sha256((ROOT / "prompts" / name).read_bytes()).hexdigest()
    indexes = {}
    for name in ("chunks_search.jsonl", "embeddings_search.npy", "clip_pages_v1.npz"):
        path = DATA / name
        indexes[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    models = {}
    for kind in ("text", "reranker", "clip-image", "clip-text"):
        path = STATE / "models" / kind / "MAINTIDOC_MODEL_PROVENANCE.json"
        models[kind] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return {"vlm": MODEL, "prompts_sha256": prompts, "indexes_sha256": indexes, "models": models, "reranking": "CrossEncoder si présent, sinon repli RRF explicitement signalé"}
