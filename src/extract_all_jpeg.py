import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path("data/raw")
OUTPUT = Path("data/processed/images")
MANIFEST = Path("data/processed/visual_manifest_all_jpeg.jsonl")

if MANIFEST.exists():
    raise SystemExit("Manifest global deja present : aucune modification.")

records = []
erreurs = []
nouveaux = 0

for famille in ("pompes", "vannes"):
    dossier = ROOT / famille

    for pdf in sorted(dossier.glob("*.pdf")):
        reader = PdfReader(str(pdf))
        compteur = 0

        for numero_page, page in enumerate(reader.pages, 1):
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

                element_id = (
                    f"{pdf.stem}_p{numero_page}_{str(nom).strip('/')}"
                )

                destination = (
                    OUTPUT / famille / pdf.stem / f"{element_id}.jpg"
                )

                try:
                    donnees = objet._data

                    if destination.exists():
                        if destination.read_bytes() != donnees:
                            raise ValueError(
                                "Conflit avec fichier existant"
                            )
                    else:
                        destination.parent.mkdir(
                            parents=True, exist_ok=True
                        )
                        destination.write_bytes(donnees)
                        nouveaux += 1

                    records.append({
                        "document_id": f"{famille}/{pdf.stem}",
                        "nom_fichier": pdf.name,
                        "famille": famille,
                        "page": numero_page,
                        "element_id": element_id,
                        "type": "image_jpeg",
                        "chemin": destination.as_posix()
                    })

                    compteur += 1

                except Exception as e:
                    erreurs.append(
                        f"{pdf.name} page {numero_page}: {e}"
                    )

        print(pdf.name, ":", compteur, "images JPEG")

if erreurs:
    print("ERREURS :", erreurs)
    raise SystemExit("Extraction incomplete. Manifest non cree.")

with MANIFEST.open("x", encoding="utf-8") as f:
    for record in records:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

print("\n=== RESULTAT GLOBAL MAINTiDOC ===")
print("Documents :", len(list(ROOT.glob("*/*.pdf"))))
print("Images referencees :", len(records))
print("Nouveaux fichiers :", nouveaux)
print("Manifest :", MANIFEST)
print("EXTRACTION JPEG TERMINEE")
