import json
from pathlib import Path
from src.retrieval_multimodal import rechercher_contexte

OUTPUT = Path("data/processed/evidence_mmr_vannes.json")

if OUTPUT.exists():
    raise SystemExit("Preuves MMR deja presentes. Aucune modification.")

question = "Comment effectuer l'inspection et la maintenance d'une vanne ?"

preuves = rechercher_contexte(
    question,
    famille="vannes",
    k=3
)

resultat = {
    "question": question,
    "famille": "vannes",
    "methode_recherche": "semantic_mmr",
    "preuves": preuves
}

with OUTPUT.open("x", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)

print("=== PREUVES MMR MAINTiDOC ===")
print("Nombre de preuves :", len(preuves))
print("Fichier :", OUTPUT)

for p in preuves:
    print(
        p["citation"]["document_id"],
        "- page",
        p["citation"]["page"]
    )

print("PREUVES MMR ENREGISTREES")
