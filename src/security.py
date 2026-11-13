"""Authentification par jetons aléatoires hachés et filtrage fermé par défaut."""
import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from src.settings import ROOT, STATE

@dataclass(frozen=True)
class Principal:
    user: str
    groups: tuple[str, ...]
    equipment: tuple[str, ...]

def authenticate(token: str) -> Principal:
    if len(token) < 32:
        raise PermissionError("Authentification requise")
    path = STATE / "auth.json"
    if not path.is_file():
        raise PermissionError("Initialisation requise")
    digest = hashlib.sha256(token.encode()).hexdigest()
    for record in json.loads(path.read_text(encoding="utf-8")):
        if hmac.compare_digest(record["token_hash"], digest):
            return Principal(record["user"], tuple(record["groups"]), tuple(record["equipment"]))
    raise PermissionError("Authentification refusée")

def policies():
    return json.loads((ROOT / "config/document_access.json").read_text(encoding="utf-8"))

def require_document(principal: Principal, document_id: str):
    policy = policies().get(document_id)
    if not policy or not set(principal.groups).intersection(policy["groups"]):
        raise PermissionError("Document non autorisé")
    return policy

def require_equipment(principal: Principal, equipment_id: str):
    if equipment_id not in principal.equipment:
        raise PermissionError("Équipement non autorisé")

def safe_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to((ROOT / "data").resolve()) or not path.is_file():
        raise PermissionError("Chemin non autorisé")
    return path
