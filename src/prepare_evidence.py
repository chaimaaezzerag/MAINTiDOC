import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path("data/processed")
OUTPUT = ROOT / "evidence_test_vannes.json"

def charger(nom):
    with (ROOT / nom).open("r", encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]

chunks = charger("chunks_search.jsonl")
liens = charger("multimodal_links.jsonl")
vecteurs = np.load(ROOT / "embeddings_search.npy")

assert len(chunks) == len(vecteurs)
liens_index = {l["chunk_index"]: l for l in liens}

question = "Comment effectuer l'inspection et la maintenance d'une vanne ?"

modele = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

q = modele.encode(question, normalize_embeddings=True)
scores = (vecteurs @ q) / np.maximum(
    np.linalg.norm(vecteurs, axis=1), 1e-12
)

indices = [
    int(i) for i in np.argsort(scores)[::-1]
    if liens_index.get(int(i), {}).get(
        "document_id", ""
    ).startswith("vannes/")
][:3]

preuves = []

for i in indices:
    lien = liens_index[i]
    image = Path(lien["image_path"])

    if not image.is_file():
        raise FileNotFoundError(image)

    preuves.append({
        "texte": chunks[i].get(
            "text", chunks[i].get("texte", "")
        ),
        "image": str(image),
        "score_similarite": round(float(scores[i]), 4),
        "citation": {
            "document_id": lien["document_id"],
            "page": lien["page"],
            "element_id": lien["element_id"]
        }
    })

resultat = {
    "question": question,
    "preuves": preuves
}

if OUTPUT.exists():
    raise SystemExit("Fichier de preuves deja present.")

with OUTPUT.open("x", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)

print("=== PREUVES MAINTiDOC ===")
print("Question :", question)
print("Nombre de preuves :", len(preuves))
print("Fichier :", OUTPUT)

for p in preuves:
    print(
        p["citation"]["document_id"],
        "- page", p["citation"]["page"]
    )

print("PREUVES PRETES")
