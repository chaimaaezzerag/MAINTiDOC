"""Fine-tuning explicite de paires dérivées de triplets humains vérifiés."""
import argparse
import json
from pathlib import Path
from src.evaluation import validate_triplets
from src.settings import STATE

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("triplets", type=Path)
    parser.add_argument("--output", type=Path, default=STATE / "models/reranker-adapted")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()
    rows = [json.loads(x) for x in args.triplets.read_text(encoding="utf-8").splitlines() if x.strip()]
    validate_triplets(rows)
    if not 800 <= len(rows) <= 1500:
        raise ValueError("800 à 1500 triplets vérifiés requis pour l'expérience académique")
    if args.output.exists(): raise FileExistsError("Ne pas écraser un entraînement existant")
    import mlflow
    import torch
    from torch.utils.data import DataLoader
    from sentence_transformers import CrossEncoder, InputExample
    torch.manual_seed(42)
    model = CrossEncoder(str(STATE / "models/reranker"), device="cpu", local_files_only=True)
    training = []
    for row in rows:
        if row["split"] == "train":
            training.extend([InputExample(texts=[row["question"], row["positive"]], label=1.0), InputExample(texts=[row["question"], row["negative"]], label=0.0)])
    mlflow.set_tracking_uri((STATE / "mlruns").as_uri())
    mlflow.set_experiment("maintidoc-reranker")
    with mlflow.start_run():
        mlflow.log_params(dict(seed=42, epochs=args.epochs, train_pairs=len(training), split="document-disjoint"))
        model.fit(train_dataloader=DataLoader(training, shuffle=True, batch_size=8), epochs=args.epochs, output_path=str(args.output), show_progress_bar=True)
        mlflow.log_artifact(str(args.triplets))
    print("Entraînement effectué ; évaluation séparée requise avant toute conclusion.")

if __name__ == "__main__": main()
