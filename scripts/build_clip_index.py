"""Indexer les 228 pages, en réutilisant les vecteurs CLIP déjà disponibles."""
import json
import numpy as np
from PIL import Image
from src.retrieval import encoder
from src.security import safe_path
from src.settings import DATA

def main():
    output = DATA / "clip_pages_v1.npz"
    if output.exists():
        print("Index CLIP complet existant conservé")
        return
    pages = [json.loads(x) for x in (DATA / "visual_pages_manifest.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    known = {}
    previous = DATA / "clip_vectors.npz"
    if previous.exists():
        links = {x["chunk_index"]: x for x in [json.loads(x) for x in (DATA / "multimodal_links.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]}
        with np.load(previous, allow_pickle=False) as archive:
            for index, vector in zip(archive["chunk_indexes"], archive["vectors"]):
                known[links[int(index)]["image_path"]] = vector
    missing = [x["chemin"] for x in pages if x["chemin"] not in known]
    if missing:
        model = encoder("clip-image")
        for start in range(0, len(missing), 4):
            images = []
            for name in missing[start:start+4]:
                with Image.open(safe_path(name)) as source: images.append(source.convert("RGB"))
            vectors = model.encode(images, normalize_embeddings=True)
            known.update(zip(missing[start:start+4], vectors))
    with output.open("xb") as target:
        np.savez_compressed(target, vectors=np.array([known[x["chemin"]] for x in pages]), chunk_indexes=np.array([-1-i for i in range(len(pages))]))
    print("Pages CLIP indexées :", len(pages), "; nouvellement encodées :",len(missing))

if __name__ == "__main__": main()
