import json
import re
from pathlib import Path

ROOT = Path("data/processed")

with (ROOT / "evidence_mmr_vannes.json").open(
    "r", encoding="utf-8"
) as f:
    dossier = json.load(f)

preuve = next(
    p for p in dossier["preuves"]
    if p["citation"]["document_id"] == "vannes/2bax70en"
    and p["citation"]["page"] == 16
)

texte = preuve["texte"]

elements = ["457", "502", "419", "18"]

print("=== CONTROLE DOCUMENTAIRE MAINTiDOC ===")
print("Document :", preuve["citation"]["document_id"])
print("Page :", preuve["citation"]["page"])

for element in elements:
    motif = rf"(?<!\d){re.escape(element)}(?!\d)"
    trouve = re.search(motif, texte)

    print(f"\nElement {element} :",
          "PRESENT" if trouve else "ABSENT")

    if trouve:
        debut = max(0, trouve.start() - 90)
        fin = min(len(texte), trouve.end() + 90)
        print("Contexte :", texte[debut:fin])

print("\nCONTROLE TEXTUEL TERMINE")
