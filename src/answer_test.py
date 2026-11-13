import json
from pathlib import Path
from src.response_schema import ReponseMAINTiDOC, Citation

SOURCE = Path("data/processed/evidence_mmr_vannes.json")
OUTPUT = Path("data/processed/response_test_vannes.json")

with SOURCE.open("r", encoding="utf-8") as f:
    dossier = json.load(f)

preuves = dossier["preuves"]

citations = [
    Citation.model_validate(p["citation"])
    for p in preuves
]

reponse = ReponseMAINTiDOC(
    status="clarification",
    answer=(
        "Les documents retrouves mentionnent des precautions "
        "contre la contamination des composants, des controles "
        "de joints et des precautions avant demontage. "
        "Ces informations ne constituent pas une procedure "
        "complete applicable a toutes les vannes."
    ),
    citations=citations,
    uncertainties=[
        "Le modele exact de vanne n'est pas connu.",
        "Les conditions de fonctionnement ne sont pas precisees.",
        "Les passages recuperes ne suffisent pas pour definir une procedure complete."
    ],
    clarification_question=(
        "Quel est le modele exact de la vanne et quel type "
        "d'inspection souhaitez-vous effectuer ?"
    ),
    proposed_action=None
)

if OUTPUT.exists():
    raise SystemExit("Reponse de test deja presente. Aucune modification.")

with OUTPUT.open("x", encoding="utf-8") as f:
    f.write(reponse.model_dump_json(indent=2))

print("=== REPONSE SOURCEE MAINTiDOC ===")
print(reponse.model_dump_json(indent=2))
print("REPONSE STRUCTUREE PRETE")
