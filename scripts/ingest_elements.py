"""Compléter l'inventaire des éléments sans remplacer les extractions existantes."""
import argparse
import json
from pathlib import Path
from src.settings import ROOT, DATA
from src.security import policies, safe_path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables", action="store_true", help="Extraction supplémentaire des tableaux, plus coûteuse")
    parser.add_argument("--ocr", action="store_true", help="OCR local des pages sans texte ; Tesseract requis")
    args = parser.parse_args()
    suffix = "_tables_ocr" if args.tables and args.ocr else "_tables" if args.tables else "_ocr" if args.ocr else ""
    output = DATA / ("elements_catalog" + suffix + ".jsonl")
    if output.exists(): raise FileExistsError("Catalogue existant conservé")
    policy = policies()
    pages = [json.loads(x) for x in (DATA / "pages.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    rows = []
    for page in pages:
        doc = page["famille"] + "/" + Path(page["nom_fichier"]).stem
        if doc not in policy: continue
        rows.append(dict(document_id=doc, version=policy[doc].get("version"), page=page["page"], element_id=f"{doc}:page:{page['page']}", type="page_text", family=page["famille"], groups=policy[doc]["groups"], text=page["texte"], provenance="pages.jsonl existant"))
    for name in ("visual_pages_manifest.jsonl", "visual_manifest_all_jpeg.jsonl"):
        for line in (DATA / name).read_text(encoding="utf-8-sig").splitlines():
            if not line.strip(): continue
            item = json.loads(line)
            doc = item["document_id"]
            if doc not in policy: continue
            safe_path(item["chemin"])
            rows.append(dict(document_id=doc, version=policy[doc].get("version"), page=item["page"], element_id=item["element_id"], type=item["type"], family=item["famille"], groups=policy[doc]["groups"], path=item["chemin"], provenance=name))
    if args.tables or args.ocr:
        import pymupdf
        for doc, entry in policy.items():
            with pymupdf.open(safe_path(entry["path"])) as pdf:
                if pdf.is_encrypted and not pdf.authenticate(""): continue
                for number, page in enumerate(pdf,1):
                    if args.tables:
                        for index, table in enumerate(page.find_tables().tables):
                            rows.append(dict(document_id=doc, version=entry.get("version"), page=number, element_id=f"{doc}:table:{number}:{index}", type="table", family=doc.split('/')[0], groups=entry["groups"], cells=table.extract(), bbox=list(table.bbox), page_text=page.get_text(), provenance="PyMuPDF find_tables, à vérifier visuellement"))
                    if args.ocr and not page.get_text().strip():
                        tp = page.get_textpage_ocr(language="eng+fra", dpi=150)
                        rows.append(dict(document_id=doc, version=entry.get("version"), page=number, element_id=f"{doc}:ocr:{number}", type="ocr", family=doc.split('/')[0], groups=entry["groups"], text=page.get_text(textpage=tp), provenance="OCR local non vérifié"))
    with output.open("x", encoding="utf-8") as out:
        for row in rows: out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("Éléments inventoriés :",len(rows))

if __name__ == "__main__": main()
