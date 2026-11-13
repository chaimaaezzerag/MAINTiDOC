import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def rechercher_mmr(question, famille=None, top_k=3, lambda_mmr=0.7):
    with (DATA / "chunks_search.jsonl").open(encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    vecteurs = np.load(DATA / "embeddings_search.npy")

    if len(chunks) != len(vecteurs):
        raise ValueError("Chunks et embeddings non alignes")

    model = SentenceTransformer(MODEL_NAME, device="cpu")
    q = model.encode(question, normalize_embeddings=True)

    scores = vecteurs @ q

    candidats = [
        i for i, c in enumerate(chunks)
        if famille is None or c["famille"] == famille
    ]

    candidats = sorted(
        candidats,
        key=lambda i: float(scores[i]),
        reverse=True
    )[:30]

    selection = []

    while candidats and len(selection) < top_k:
        meilleur = None
        meilleur_score = float("-inf")

        for i in candidats:
            pertinence = float(scores[i])

            redondance = max(
                (float(vecteurs[i] @ vecteurs[j]) for j in selection),
                default=0.0
            )

            score_mmr = (
                lambda_mmr * pertinence
                - (1 - lambda_mmr) * redondance
            )

            if score_mmr > meilleur_score:
                meilleur_score = score_mmr
                meilleur = i

        selection.append(meilleur)
        candidats.remove(meilleur)

    print("\nQUESTION :", question)
    print("FAMILLE :", famille or "toutes")

    for rang, i in enumerate(selection, 1):
        c = chunks[i]
        print(f"\n--- RESULTAT {rang} ---")
        print("Similarite :", round(float(scores[i]), 4))
        print("Document :", c["nom_fichier"])
        print("Famille :", c["famille"])
        print("Page :", c["page"])
        print("Texte :", c["texte"][:500])

if __name__ == "__main__":
    rechercher_mmr(
        "What are the maintenance instructions for a valve?",
        famille="vannes"
    )