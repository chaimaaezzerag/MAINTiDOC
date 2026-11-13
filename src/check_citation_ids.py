import json
from pathlib import Path

ROOT = Path("data/processed")

with (ROOT / "evidence_mmr_vannes.json").open(
    "r", encoding="utf-8"
) as f:
    dossier = json.load(f)

print("=== IDENTIFIANTS OFFICIELS MAINTiDOC ===")

for numero, preuve in enumerate(dossier["preuves"], 1):
    citation = preuve["citation"]

    print(f"\nSOURCE {numero}")
    print("document_id :", citation["document_id"])
    print("page        :", citation["page"])
    print("element_id  :", citation["element_id"])

print("\nREFERENCES DOCUMENTAIRES VERIFIEES")
