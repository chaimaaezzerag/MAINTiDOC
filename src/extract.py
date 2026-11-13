import csv
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "processed" / "manifest.csv"
OUTPUT = ROOT / "data" / "processed" / "pages.jsonl"

def extract_pages():
    total = 0

    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
        documents = list(csv.DictReader(f))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as out:
        for doc in documents:
            pdf_path = ROOT / doc["chemin_relatif"]
            reader = PdfReader(str(pdf_path))

            if reader.is_encrypted:
                reader.decrypt("")

            for number, page in enumerate(reader.pages, start=1):
                text = " ".join((page.extract_text() or "").split())

                record = {
                    "nom_fichier": doc["nom_fichier"],
                    "famille": doc["famille"],
                    "page": number,
                    "texte": text
                }

                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                total += 1

    print(f"Pages extraites : {total}")
    print(f"Resultat : {OUTPUT}")

if __name__ == "__main__":
    extract_pages()
