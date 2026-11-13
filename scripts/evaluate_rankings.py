"""Calculer les comparaisons uniquement à partir d'annotations vérifiées."""
import argparse
import json
from pathlib import Path
from statistics import mean
from src.evaluation import ranking_metrics

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(x) for x in args.annotations.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not rows: raise ValueError("Aucune annotation")
    variants = ("without_reranker", "initial_reranker", "adapted_reranker")
    results = {}
    for row in rows:
        if row.get("verified") is not True or not row.get("reviewer"):
            raise ValueError("Annotation indépendante requise")
        if not row.get("relevance"): raise ValueError("Jugements de pertinence absents")
        if set(row.get("rankings", {})) != set(variants):
            raise ValueError("Les trois classements réellement exécutés sont requis")
        for variant in variants:
            results.setdefault(variant, []).append(ranking_metrics(row["rankings"][variant], row["relevance"]))
    summary = {variant: {metric: mean(item[metric] for item in scores) for metric in scores[0]} for variant,scores in results.items()}
    with args.output.open("x", encoding="utf-8") as target:
        json.dump({"queries":len(rows), "metrics":summary}, target, indent=2)
    print("Résultats réels calculés pour",len(rows),"questions ; aucun classement manquant simulé.")

if __name__ == "__main__": main()
