import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path("data/processed")

def charger(nom):
    with (ROOT / nom).open("r", encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]

def rechercher_contexte(question, famille=None, k=3, diversite=0.7):
    chunks = charger("chunks_search.jsonl")
    liens = charger("multimodal_links.jsonl")
    vecteurs = np.load(ROOT / "embeddings_search.npy")

    if len(chunks) != len(vecteurs):
        raise ValueError("Index non synchronise")

    index_liens = {l["chunk_index"]: l for l in liens}

    modele = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    requete = modele.encode(question, normalize_embeddings=True)
    normes = np.maximum(np.linalg.norm(vecteurs, axis=1), 1e-12)
    vecteurs = vecteurs / normes[:, None]

    scores = vecteurs @ requete

    candidats = [
        int(i) for i in np.argsort(scores)[::-1]
        if int(i) in index_liens
        and (
            famille is None
            or index_liens[int(i)]["document_id"].startswith(famille + "/")
        )
    ][:40]

    selection = []

    while candidats and len(selection) < k:
        meilleur = None
        meilleur_score = float("-inf")

        for i in candidats:
            redondance = max(
                (float(vecteurs[i] @ vecteurs[j]) for j in selection),
                default=0.0
            )

            score_mmr = (
                diversite * float(scores[i])
                - (1 - diversite) * redondance
            )

            if score_mmr > meilleur_score:
                meilleur_score = score_mmr
                meilleur = i

        selection.append(meilleur)
        candidats.remove(meilleur)

    resultats = []

    for i in selection:
        lien = index_liens[i]
        image = Path(lien["image_path"])

        if not image.is_file():
            raise FileNotFoundError(image)

        resultats.append({
            "texte": chunks[i].get("text", chunks[i].get("texte", "")),
            "image": str(image),
            "citation": {
                "document_id": lien["document_id"],
                "page": lien["page"],
                "element_id": lien["element_id"]
            },
            "similarite": round(float(scores[i]), 4)
        })

    return resultats

if __name__ == "__main__":
    question = "Comment effectuer l'inspection et la maintenance d'une vanne ?"

    resultats = rechercher_contexte(question, famille="vannes")

    print("=== CONTEXTE RAG MULTIMODAL ===")

    for n, resultat in enumerate(resultats, 1):
        print(f"\n--- SOURCE {n} ---")
        print("Citation :", resultat["citation"])
        print("Similarite :", resultat["similarite"])
        print("Image :", resultat["image"])
        print("Texte :", resultat["texte"][:350])

    print("\nCONTEXTE RAG PRET")
