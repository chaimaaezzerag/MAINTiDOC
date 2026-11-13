import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data/processed/chunks_filtered.jsonl"
OUTPUT = ROOT / "data/processed/embeddings.npy"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def generate_embeddings():
    with INPUT.open(encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]

    textes = [chunk["texte"] for chunk in chunks]

    print("Chunks charges :", len(textes))
    print("Chargement du modele...")

    model = SentenceTransformer(MODEL_NAME, device="cpu")

    print("Generation des embeddings...")

    vecteurs = model.encode(
        textes,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    np.save(OUTPUT, vecteurs)

    print("Embeddings generes :", vecteurs.shape)
    print("Fichier sauvegarde :", OUTPUT)
    print("TERMINE")

if __name__ == "__main__":
    generate_embeddings()
