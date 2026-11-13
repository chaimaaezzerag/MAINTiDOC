"""Provisionnement explicite, TLS vérifié et modèles sans code distant."""
import argparse
import json
import shutil
from pathlib import Path
import truststore
truststore.inject_into_ssl()
from huggingface_hub import snapshot_download, HfApi
from src.settings import STATE

MODELS = {
    "text": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "reranker": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    "clip-image": "sentence-transformers/clip-ViT-B-32",
    "clip-text": "sentence-transformers/clip-ViT-B-32-multilingual-v1",
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=list(MODELS), required=True)
    parser.add_argument("--cached-only", action="store_true")
    args = parser.parse_args()
    target = STATE / "models" / args.kind
    if target.exists():
        print("Modèle local existant conservé :", args.kind)
        return
    repo = MODELS[args.kind]
    revision = None
    info = None
    if not args.cached_only:
        info = HfApi().model_info(repo, timeout=15, files_metadata=True)
        revision = info.sha
    if args.cached_only:
        source = snapshot_download(repo_id=repo, local_files_only=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    else:
        from huggingface_hub import hf_hub_download
        staging = target.with_name(target.name + ".download")
        staging.mkdir(parents=True, exist_ok=True)
        cache = Path.home() / ".cache/huggingface/hub" / ("models--" + repo.replace("/", "--")) / "blobs"
        siblings = {entry.rfilename: entry for entry in info.siblings}
        names = []
        for name, entry in siblings.items():
            parts = Path(name).parts
            if any(part in {"onnx", "openvino"} for part in parts): continue
            if name.startswith(("tf_model", "flax_model")): continue
            if not name.endswith((".json", ".txt", ".model", ".safetensors", ".bin", ".md")) and "LICENSE" not in name: continue
            if name.endswith(".bin") and any(other.endswith(".safetensors") and Path(other).parent == Path(name).parent for other in siblings): continue
            names.append(name)
            lfs = getattr(entry, "lfs", None)
            digest = lfs.get("sha256") if isinstance(lfs, dict) else getattr(lfs, "sha256", None)
            blob = cache / (digest or entry.blob_id)
            destination = staging / name
            if blob.is_file() and not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(blob, destination)
        for name in names:
            destination = staging / name
            entry = siblings[name]
            if destination.is_file() and (entry.size is None or destination.stat().st_size == entry.size): continue
            # local_dir utilise des fichiers ordinaires, pas de symlinks Windows.
            hf_hub_download(repo, name, revision=revision, local_dir=staging)
        if not staging.resolve().is_relative_to((STATE / "models").resolve()):
            raise ValueError("Répertoire de modèle hors du projet")
        staging.rename(target)
        source = target
    record = dict(repo_id=repo, revision=revision or Path(source).name, license=getattr(info.card_data, "license", None) if info and info.card_data else "voir README du modèle", source="cache local" if args.cached_only else "Hugging Face, TLS vérifié")
    (target / "MAINTIDOC_MODEL_PROVENANCE.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print("Modèle provisionné :", args.kind, "révision :", record["revision"])

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit("Provisionnement non effectué : " + type(exc).__name__ + ". TLS reste activé ; consulter la configuration des certificats réseau.") from None
