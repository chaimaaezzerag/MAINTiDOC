import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def rechercher(question, top_k=5, famille=None):
    with (DATA / "chunks_search.jsonl").open(encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    vecteurs = np.load(DATA / "embeddings_search.npy")

    if len(chunks) != len(vecteurs):
        raise ValueError("Nombre de chunks different du nombre de vecteurs")

    model = SentenceTransformer(MODEL_NAME, device="cpu")
    question_vecteur = model.encode(
        question,
        normalize_embeddings=True
    )

    scores = vecteurs @ question_vecteur

    indices = [
        i for i, chunk in enumerate(chunks)
        if famille is None or chunk["famille"] == famille
    ]

    if not indices:
        print("Aucun document pour cette famille.")
        return

    meilleurs = sorted(
        indices,
        key=lambda i: float(scores[i]),
        reverse=True
    )[:top_k]

    print("\nQUESTION :", question)
    print("FAMILLE :", famille or "toutes")

    for rang, index in enumerate(meilleurs, start=1):
        chunk = chunks[index]
        print(f"\n--- RESULTAT {rang} ---")
        print("Score :", round(float(scores[index]), 4))
        print("Document :", chunk["nom_fichier"])
        print("Famille :", chunk["famille"])
        print("Page :", chunk["page"])
        print("Texte :", chunk["texte"][:500])

if __name__ == "__main__":
    rechercher(
        "What are the maintenance instructions for a valve?",
        top_k=3,
        famille="vannes"
    )