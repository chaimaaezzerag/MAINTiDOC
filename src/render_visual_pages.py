import json
from pathlib import Path
import pymupdf

ROOT = Path("data/raw")
OUTPUT = Path("data/processed/pages_visual")
MANIFEST = Path("data/processed/visual_pages_manifest.jsonl")

if MANIFEST.exists():
    raise SystemExit(
        "Manifest deja present. Extraction non relancee."
    )

records = []
nouvelles = 0

for famille in ("pompes", "vannes"):
    for pdf in sorted((ROOT / famille).glob("*.pdf")):
        document = pymupdf.open(str(pdf))
        dossier = OUTPUT / famille / pdf.stem
        dossier.mkdir(parents=True, exist_ok=True)

        for index, page in enumerate(document):
            numero = index + 1
            element_id = f"{pdf.stem}_page_{numero}"
            destination = dossier / f"{element_id}.png"

            if not destination.exists():
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(1.5, 1.5),
                    alpha=False
                )
                pixmap.save(str(destination))
                nouvelles += 1

            records.append({
                "document_id": f"{famille}/{pdf.stem}",
                "nom_fichier": pdf.name,
                "famille": famille,
                "page": numero,
                "element_id": element_id,
                "type": "page_pdf_rendue",
                "chemin": destination.as_posix()
            })

        print(pdf.name, ":", len(document), "pages")
        document.close()

with MANIFEST.open("x", encoding="utf-8") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

print("\n=== EXTRACTION VISUELLE MAINTiDOC ===")
print("Pages referencees :", len(records))
print("Nouvelles images :", nouvelles)
print("Manifest :", MANIFEST)
print("EXTRACTION TERMINEE")
