"""Mesures de classement sur annotations réelles, sans résultats fictifs."""
import math

def ranking_metrics(ranking, relevance):
    dcg = sum((2 ** relevance.get(key, 0) - 1) / math.log2(rank + 1) for rank, key in enumerate(ranking[:5], 1))
    ideal = sum((2 ** grade - 1) / math.log2(rank + 1) for rank, grade in enumerate(sorted(relevance.values(), reverse=True)[:5], 1))
    reciprocal = next((1 / rank for rank, key in enumerate(ranking[:10], 1) if relevance.get(key, 0) > 0), 0)
    relevant = {key for key, grade in relevance.items() if grade > 0}
    recall = len(set(ranking[:5]) & relevant) / len(relevant) if relevant else 0
    return {"ndcg@5": dcg / ideal if ideal else 0, "mrr@10": reciprocal, "recall@5": recall}

def validate_triplets(rows):
    """Exiger des annotations humaines et interdire toute fuite documentaire."""
    documents = {}
    for row in rows:
        if row.get("verified") is not True or not row.get("reviewer"):
            raise ValueError("Triplet non vérifié par un annotateur")
        if row.get("split") not in {"train", "validation", "test"}:
            raise ValueError("Split absent")
        for key in ("question", "positive", "negative", "positive_document", "negative_document"):
            if not row.get(key): raise ValueError(f"Champ absent : {key}")
        for doc in (row["positive_document"], row["negative_document"]):
            if doc in documents and documents[doc] != row["split"]:
                raise ValueError("Fuite documentaire entre splits")
            documents[doc] = row["split"]
    for split in ("train", "validation", "test"):
        if not any(row["split"] == split for row in rows):
            raise ValueError(f"Split vide : {split}")
