import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path("data/processed")

def charger(nom):
    with (ROOT / nom).open("r", encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]

chunks = charger("chunks_search.jsonl")
liens = charger("multimodal_links.jsonl")
vecteurs = np.load(ROOT / "embeddings_search.npy")

assert len(chunks) == len(vecteurs), "Index texte et vecteurs non synchronises"

liens_par_index = {l["chunk_index"]: l for l in liens}

question = "Comment effectuer l'inspection et la maintenance d'une vanne ?"

print("=== RECHERCHE MAINTiDOC ===")
print("Question :", question)

modele = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vecteur_question = modele.encode(
    question,
    normalize_embeddings=True
)

normes = np.linalg.norm(vecteurs, axis=1)
scores = (vecteurs @ vecteur_question) / np.maximum(normes, 1e-12)

indices = [
    i for i in np.argsort(scores)[::-1]
    if liens_par_index.get(int(i), {}).get("document_id", "").startswith("vannes/")
][:3]

for rang, i in enumerate(indices, 1):
    i = int(i)
    lien = liens_par_index[i]
    chunk = chunks[i]

    print(f"\n--- RESULTAT {rang} ---")
    print("Score :", round(float(scores[i]), 4))
    print("Document :", lien["nom_fichier"])
    print("Page :", lien["page"])
    print("Image :", lien["image_path"])
    print("Element :", lien["element_id"])
    print("Texte :", chunk.get("text", chunk.get("texte", ""))[:500])

print("\nRECHERCHE TERMINEE")
