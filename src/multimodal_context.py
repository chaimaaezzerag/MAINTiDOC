import json
from pathlib import Path

ROOT = Path("data/processed")

def charger(nom):
    with (ROOT / nom).open("r", encoding="utf-8-sig") as f:
        return [json.loads(l) for l in f if l.strip()]

def construire_contexte(index):
    chunks = charger("chunks_search.jsonl")
    liens = charger("multimodal_links.jsonl")

    if index < 0 or index >= len(chunks):
        raise IndexError("Index du passage invalide")

    lien = next(
        (l for l in liens if l["chunk_index"] == index),
        None
    )

    if lien is None:
        raise ValueError("Aucune page visuelle associee")

    image = Path(lien["image_path"])

    if not image.is_file():
        raise FileNotFoundError(image)

    chunk = chunks[index]

    return {
        "texte": chunk.get("text", chunk.get("texte", "")),
        "image": str(image),
        "citation": {
            "document_id": lien["document_id"],
            "page": lien["page"],
            "element_id": lien["element_id"]
        }
    }

if __name__ == "__main__":
    contexte = construire_contexte(0)

    print("=== CONTEXTE MULTIMODAL MAINTiDOC ===")
    print("Texte :", contexte["texte"][:300])
    print("Image :", contexte["image"])
    print("Citation :", contexte["citation"])
    print("CONTEXTE PRET")
