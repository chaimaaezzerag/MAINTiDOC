import json
from pathlib import Path
from pypdf import PdfReader

pdf = Path("data/raw/vannes/2bax70en.pdf")
sortie = Path("data/processed/images/vannes/2bax70en")
manifest = Path("data/processed/visual_manifest_jpeg.jsonl")

sortie.mkdir(parents=True, exist_ok=True)
reader = PdfReader(str(pdf))
records = []

for page_num, page in enumerate(reader.pages, 1):
    resources = page.get("/Resources")
    if not resources:
        continue

    xobjects = resources.get_object().get("/XObject")
    if not xobjects:
        continue

    for nom, reference in xobjects.get_object().items():
        objet = reference.get_object()

        if objet.get("/Subtype") != "/Image":
            continue

        if objet.get("/Filter") != "/DCTDecode":
            continue

        element_id = f"{pdf.stem}_p{page_num}_{str(nom).strip('/')}"
        destination = sortie / f"{element_id}.jpg"

        if not destination.exists():
            destination.write_bytes(objet._data)

        records.append({
            "document_id": pdf.stem,
            "nom_fichier": pdf.name,
            "famille": "vannes",
            "page": page_num,
            "element_id": element_id,
            "type": "image_jpeg",
            "chemin": destination.as_posix()
        })

if manifest.exists():
    raise FileExistsError(f"Manifest deja present : {manifest}")

with manifest.open("w", encoding="utf-8") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

print("=== MAINTiDOC : EXTRACTION JPEG ===")
print("Document :", pdf.name)
print("Images JPEG :", len(records))
print("Manifest :", manifest)
