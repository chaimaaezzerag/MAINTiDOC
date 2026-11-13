import json
import urllib.request
from pathlib import Path

from src.response_schema import ReponseMAINTiDOC
from src.citation_validator import normaliser_citations

ROOT = Path("data/processed")
OUTPUT = ROOT / "response_ollama_test.json"

with (ROOT / "prompt_rag_test.json").open(
    "r", encoding="utf-8"
) as f:
    messages = json.load(f)

with (ROOT / "evidence_mmr_vannes.json").open(
    "r", encoding="utf-8"
) as f:
    dossier = json.load(f)

instructions = """
Respecte exactement le schema JSON.
Reponds en francais, en 2 ou 3 phrases maximum.
Utilise seulement les preuves documentaires fournies.
Si le modele de vanne n'est pas connu, utilise
le statut clarification et demande le modele exact.
Ne donne pas une procedure complete sans contexte suffisant.
Ne propose pas d'action automatique sur une machine.
Ne cree aucune citation absente des preuves.
"""

payload = {
    "model": "qwen2.5vl:3b",
    "stream": False,
    "format": ReponseMAINTiDOC.model_json_schema(),
    "messages": [
        {
            "role": "system",
            "content": messages["system"] + "\n" + instructions
        },
        {
            "role": "user",
            "content": messages["user"]
        }
    ],
    "options": {
        "temperature": 0,
        "num_predict": 1536
    }
}

request = urllib.request.Request(
    "http://127.0.0.1:11434/api/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("=== GENERATION RAG VALIDEE MAINTiDOC ===", flush=True)

with urllib.request.urlopen(request, timeout=300) as response:
    resultat = json.load(response)

print("Raison de fin :", resultat.get("done_reason"))

if resultat.get("done_reason") != "stop":
    raise SystemExit("Generation incomplete : reponse refusee.")

texte = resultat.get("message", {}).get("content", "")

try:
    donnees = json.loads(texte)
    validation = ReponseMAINTiDOC.model_validate(donnees)

    citations = normaliser_citations(
        [c.model_dump() for c in validation.citations],
        dossier["preuves"]
    )

    validation.citations = [
        type(validation.citations[0])(**c)
        for c in citations
    ] if citations else []

except (json.JSONDecodeError, ValueError) as erreur:
    print("VALIDATION ECHOUEE :", erreur)
    print("Reponse brute :", texte[:1200])
    raise SystemExit(1)

if OUTPUT.exists():
    print("Fichier existant conserve :", OUTPUT)
else:
    with OUTPUT.open("x", encoding="utf-8") as f:
        f.write(validation.model_dump_json(indent=2))

print(validation.model_dump_json(indent=2))
print("GENERATION ET CITATIONS VALIDEES")
