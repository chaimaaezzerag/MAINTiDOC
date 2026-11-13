import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

DATA = Path("data/processed")
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def preparer_contexte(question, famille=None, top_k=5):
    with (DATA / "chunks_search.jsonl").open(encoding="utf-8") as f:
        chunks = [json.loads(ligne) for ligne in f]

    vecteurs = np.load(DATA / "embeddings_search.npy")
    assert len(chunks) == len(vecteurs)

    modele = SentenceTransformer(MODEL, device="cpu")
    question_vecteur = modele.encode(
        question, normalize_embeddings=True
    )

    scores = vecteurs @ question_vecteur

    indices = [
        i for i, c in enumerate(chunks)
        if famille is None or c["famille"] == famille
    ]

    meilleurs = sorted(
        indices,
        key=lambda i: float(scores[i]),
        reverse=True
    )[:top_k]

    passages = []

    for i in meilleurs:
        c = chunks[i]
        passages.append(
            f"Document : {c['nom_fichier']}\n"
            f"Page : {c['page']}\n"
            f"Texte : {c['texte']}"
        )

    return "\n\n---\n\n".join(passages)

if __name__ == "__main__":
    question = "What are the maintenance instructions for a valve?"
    contexte = preparer_contexte(question, famille="vannes")

    print("QUESTION :", question)
    print("\nCONTEXTE POUR LE RAG :\n")
    print(contexte)
