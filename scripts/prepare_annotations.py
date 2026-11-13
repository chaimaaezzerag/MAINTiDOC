"""Préparer des candidats non vérifiés ; aucune annotation ni métrique inventée."""
import json
from src.settings import DATA, ROOT

def main():
    output = ROOT / "data/evaluation/triplets_candidates.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(x) for x in (DATA / "chunks_search.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    # Documents répartis avant sélection des négatifs afin d'éviter les fuites.
    docs = sorted({x["famille"] + "/" + x["nom_fichier"] for x in rows})
    split_docs = {doc: "test" if i == 0 else "validation" if i == 1 else "train" for i,doc in enumerate(docs)}
    with output.open("x", encoding="utf-8") as target:
        for index, positive in enumerate(rows):
            doc = positive["famille"] + "/" + positive["nom_fichier"]
            split = split_docs[doc]
            candidates = [x for x in rows if x["chunk_id"] != positive["chunk_id"] and split_docs[x["famille"] + "/" + x["nom_fichier"]] == split and x["famille"] == positive["famille"]]
            if not candidates: continue
            # Proposition lexicale uniquement ; l'annotateur doit juger sa difficulté.
            terms = set(positive["texte"].lower().split())
            negative = max(candidates, key=lambda x: len(terms & set(x["texte"].lower().split())))
            record = dict(question="", positive=positive["texte"], negative=negative["texte"], positive_document=doc, negative_document=negative["famille"] + "/" + negative["nom_fichier"], split=split, verified=False, reviewer=None)
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("Candidats enregistrés ; questions et pertinence à annoter humainement.")

if __name__ == "__main__": main()
