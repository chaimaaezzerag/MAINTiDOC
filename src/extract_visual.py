import json
from pathlib import Path
from pypdf import PdfReader

PDF = Path("data/raw/vannes/2bax70en.pdf")
SORTIE = Path("data/processed/images/vannes/2bax70en")
MANIFEST = Path("data/processed/visual_manifest_test.jsonl")

SORTIE.mkdir(parents=True, exist_ok=True)

reader = PdfReader(str(PDF))
records = []
erreurs = []

for numero_page, page in enumerate(reader.pages, start=1):
    try:
        for numero_image, image in enumerate(page.images, start=1):
            extension = Path(image.name).suffix.lower()

            if extension not in {".png", ".jpg", ".jpeg", ".jp2", ".tif", ".tiff"}:
                continue

            nom = f"page_{numero_page:03d}_image_{numero_image:03d}{extension}"
            destination = SORTIE / nom

            if destination.exists():
                raise FileExistsError(f"Fichier deja present : {destination}")

            destination.write_bytes(image.data)

            records.append({
                "document_id": PDF.stem,
                "nom_fichier": PDF.name,
                "famille": "vannes",
                "page": numero_page,
                "element_id": f"{PDF.stem}_p{numero_page}_img{numero_image}",
                "type": "image_integree",
                "chemin": destination.as_posix()
            })

    except Exception as erreur:
        erreurs.append(f"Page {numero_page}: {erreur}")

if MANIFEST.exists():
    raise FileExistsError(f"Manifest deja present : {MANIFEST}")

with MANIFEST.open("w", encoding="utf-8") as fichier:
    for record in records:
        fichier.write(json.dumps(record, ensure_ascii=False) + "\n")

print("=== EXTRACTION VISUELLE ===")
print("Document :", PDF.name)
print("Pages :", len(reader.pages))
print("Images sauvegardees :", len(records))
print("Erreurs :", len(erreurs))
print("Dossier :", SORTIE)
print("Manifest :", MANIFEST)

for erreur in erreurs[:10]:
    print("ERREUR :", erreur)
