import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data/processed/pages.jsonl"
OUTPUT = ROOT / "data/processed/chunks.jsonl"

CHUNK_SIZE = 1000
OVERLAP = 150

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def build_chunks():
    count = 0

    with INPUT.open(encoding="utf-8") as source, \
         OUTPUT.open("w", encoding="utf-8") as target:

        for line in source:
            page = json.loads(line)
            text = clean_text(page["texte"])

            if not text:
                continue

            start = 0
            index = 1

            while start < len(text):
                end = min(start + CHUNK_SIZE, len(text))

                if end < len(text):
                    space = text.rfind(" ", start, end)
                    if space > start:
                        end = space

                chunk = {
                    "chunk_id": f"{page['nom_fichier']}_p{page['page']}_c{index}",
                    "nom_fichier": page["nom_fichier"],
                    "famille": page["famille"],
                    "page": page["page"],
                    "texte": text[start:end].strip()
                }

                target.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                count += 1

                if end == len(text):
                    break

                start = max(start + 1, end - OVERLAP)
                index += 1

    print("Chunks crees :", count)
    print("Fichier :", OUTPUT)

if __name__ == "__main__":
    build_chunks()
