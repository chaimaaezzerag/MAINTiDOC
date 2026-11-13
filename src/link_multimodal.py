import json
from pathlib import Path

ROOT = Path("data/processed")

CHUNKS = ROOT / "chunks_search.jsonl"
PAGES = ROOT / "visual_pages_manifest.jsonl"
OUTPUT = ROOT / "multimodal_links.jsonl"

if OUTPUT.exists():
    raise SystemExit("Index multimodal deja present. Aucune modification.")

def charger(chemin):
    with chemin.open("r", encoding="utf-8-sig") as f:
        return [json.loads(ligne) for ligne in f if ligne.strip()]

chunks = charger(CHUNKS)
pages = charger(PAGES)

index_pages = {
    (p["nom_fichier"], int(p["page"])): p
    for p in pages
}

liens = []
manquants = 0

for numero, chunk in enumerate(chunks):
    nom = (
        chunk.get("nom_fichier")
        or chunk.get("source")
        or chunk.get("filename")
    )
    page = chunk.get("page")

    if not nom or page is None:
        manquants += 1
        continue

    visuel = index_pages.get((Path(str(nom)).name, int(page)))

    if visuel is None:
        manquants += 1
        continue

    liens.append({
        "chunk_index": numero,
        "document_id": visuel["document_id"],
        "nom_fichier": visuel["nom_fichier"],
        "page": visuel["page"],
        "element_id": visuel["element_id"],
        "image_path": visuel["chemin"]
    })

if manquants:
    print("Correspondances manquantes :", manquants)
    print("Exemple de chunk :", chunks[0] if chunks else None)
    raise SystemExit("Index non cree : verifier les metadonnees.")

with OUTPUT.open("x", encoding="utf-8") as f:
    for lien in liens:
        f.write(json.dumps(lien, ensure_ascii=False) + "\n")

print("=== LIENS MULTIMODAUX MAINTiDOC ===")
print("Passages textuels :", len(chunks))
print("Pages visuelles :", len(pages))
print("Liens crees :", len(liens))
print("Fichier :", OUTPUT)
print("ETAPE TERMINEE")
