"""Recherche sur le corpus autorisé : lexical + vecteurs existants + CLIP optionnel."""
import json
import os
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
import numpy as np
from src.settings import DATA, STATE
from src.security import policies, safe_path, require_document
from src.runtime_models import Evidence, Reference

def tokens(text):
    return re.findall(r"[^\W_]+", text.casefold())

def rrf(rankings, constant=60):
    scores = Counter()
    for ranking in rankings:
        for rank, key in enumerate(ranking, 1):
            scores[key] += 1 / (constant + rank)
    return [key for key, _ in sorted(scores.items(), key=lambda p: (-p[1], p[0]))]

def fuse_pages(rankings, links):
    """Aligner texte et images sur la même page avant RRF, sans doublon de rang."""
    aligned = []
    members = {}
    for ranking in rankings:
        pages = []
        for index in ranking:
            link = links[index]
            key = (link["document_id"], link["page"], link["element_id"])
            members.setdefault(key, [])
            if index not in members[key]: members[key].append(index)
            if key not in pages: pages.append(key)
        aligned.append(pages)
    return rrf(aligned), members


@lru_cache(maxsize=3)
def encoder(kind):
    import torch
    torch.set_num_threads(2)
    from sentence_transformers import SentenceTransformer
    path = STATE / "models" / kind
    if not path.is_dir():
        raise FileNotFoundError(f"Modèle local absent : {kind}")
    return SentenceTransformer(str(path), device="cpu", local_files_only=True)

@lru_cache(maxsize=1)
def reranker():
    import torch
    torch.set_num_threads(2)
    from sentence_transformers import CrossEncoder
    path = STATE / "models/reranker"
    if not path.is_dir():
        raise FileNotFoundError("Reranker local absent")
    return CrossEncoder(str(path), device="cpu", local_files_only=True)

class Retriever:
    def __init__(self):
        def load(name):
            with (DATA / name).open(encoding="utf-8-sig") as f:
                return [json.loads(line) for line in f if line.strip()]
        self.chunks = load("chunks_search.jsonl")
        self.links = {x["chunk_index"]: x for x in load("multimodal_links.jsonl")}
        self.vectors = np.load(DATA / "embeddings_search.npy", allow_pickle=False, mmap_mode="r")
        if self.vectors.shape != (len(self.chunks), 384):
            raise ValueError("Index et passages désynchronisés")
        self.bags = [Counter(tokens(c.get("texte", ""))) for c in self.chunks]
        page_text = {(p["famille"] + "/" + Path(p["nom_fichier"]).stem, p["page"]): p["texte"] for p in load("pages.jsonl")}
        self.visual_links = {}
        self.visual_text = {}
        for index, page in enumerate(load("visual_pages_manifest.jsonl")):
            self.visual_links[-1-index] = {"document_id": page["document_id"], "page": page["page"], "element_id": page["element_id"], "image_path": page["chemin"]}
            self.visual_text[-1-index] = page_text.get((page["document_id"], page["page"]), "")

    def search(self, question, principal, family=None, photo=None, budget=None, enable_visual=True):
        policy = policies()
        allowed = [i for i, c in enumerate(self.chunks) if i in self.links and (family is None or c["famille"] == family) and self.links[i]["document_id"] in policy and set(principal.groups).intersection(policy[self.links[i]["document_id"]]["groups"])]
        visual_allowed = [i for i, link in self.visual_links.items() if (family is None or link["document_id"].startswith(family + "/")) and link["document_id"] in policy and set(principal.groups).intersection(policy[link["document_id"]]["groups"])]
        if not allowed and not visual_allowed:
            return [], ["Aucune source autorisée"]
        # Les statistiques lexicales sont elles aussi calculées sur le corpus autorisé.
        words = tokens(question)
        lexicon = {"joint": ["seal", "sealing", "gasket"], "vis": ["screw", "screws"], "support": ["bracket"], "couple": ["torque"], "couples": ["torques"], "écrou": ["nut"], "tableau": ["table"]}
        words = list(dict.fromkeys(words + [word for term in words for word in lexicon.get(term, [])]))
        n = len(allowed)
        idf = {w: math.log(1 + n / (1 + sum(w in self.bags[i] for i in allowed))) for w in words}
        score = {i: sum(idf[w] * min(self.bags[i][w], 3) for w in words) for i in allowed}
        rankings = [sorted((i for i in allowed if score[i] > 0), key=lambda i: (-score[i], i))[:40]]
        notes = []
        try:
            if budget: budget.remaining()
            if budget: budget.consume_model("text_embedding")
            q = encoder("text").encode(question, normalize_embeddings=True)
            if q.shape != (384,): raise ValueError("Dimension de requête incorrecte")
            if os.environ.get("MAINTIDOC_QDRANT_URL"):
                from src.service_storage import qdrant_ranking
                rankings.append([i for i in qdrant_ranking(q, principal, family) if i in allowed])
            # Aucun produit scalaire sur les documents interdits.
            v = np.asarray(self.vectors[allowed])
            v = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)
            scores = v @ q
            rankings.append([allowed[j] for j in np.argsort(scores)[::-1][:40]])
        except (ImportError, OSError, ValueError) as exc:
            notes.append(f"Recherche vectorielle indisponible ({type(exc).__name__}) ; recherche lexicale seule")
        # Un index CLIP doit être préparé explicitement ; aucune image n'est réencodée ici.
        visual_file = DATA / "clip_pages_v1.npz"
        if enable_visual and visual_file.is_file():
            try:
                if budget: budget.remaining()
                from PIL import Image
                import io
                if budget: budget.consume_model("visual_embedding")
                query = encoder("clip-image").encode(Image.open(io.BytesIO(photo))) if photo else encoder("clip-text").encode(question)
                with np.load(visual_file, allow_pickle=False) as visual:
                    indexes = visual["chunk_indexes"]
                    selected = np.flatnonzero(np.isin(indexes, visual_allowed))
                    vectors = visual["vectors"][selected]
                    query = query / max(np.linalg.norm(query), 1e-12)
                    similarity = (vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)) @ query
                    rankings.append([int(indexes[selected[j]]) for j in np.argsort(similarity)[::-1][:40]])
            except (ImportError, OSError, ValueError) as exc:
                notes.append(f"Recherche CLIP indisponible : {type(exc).__name__}")
        elif enable_visual:
            notes.append("Index CLIP absent : recherche visuelle non exécutée")
        registry = {**self.links, **self.visual_links}
        pages, members = fuse_pages(rankings, registry)
        result = []
        for key in pages[:24]:
            indexes = members[key]
            # Le passage pertinent passe avant le contexte de page, afin que le
            # reranker ne perde pas un repère situé en bas de page par troncature.
            first = next((i for i in indexes if i >= 0), indexes[0])
            link = registry[first]
            fragments = [self.chunks[i]["texte"] for i in indexes if i >= 0]
            page_index = next((i for i, value in self.visual_links.items() if (value["document_id"], value["page"], value["element_id"]) == key), None)
            page_text = self.visual_text.get(page_index, "")
            # Une légende demandée peut se trouver hors du passage initial.
            requested = re.findall(r"(?:tableau|table|figure|fig\.?)\s+(\d+)", question, re.IGNORECASE)
            for number in requested:
                found = re.search(r"(?:Table|Figure|Fig\.?)\s+" + re.escape(number) + r"\b", page_text, re.IGNORECASE)
                if found: fragments.insert(0, page_text[max(0,found.start()-40):found.end()+500])
            if not fragments: fragments = [page_text]
            elif page_text: fragments.append(page_text)
            merged = ""
            for fragment in fragments:
                if fragment and fragment not in merged:
                    remaining = 3500 - len(merged)
                    if remaining <= 2: break
                    merged += ("\n\n" if merged else "") + fragment[:remaining-2]
            access = require_document(principal, link["document_id"])
            safe_path(link["image_path"])
            result.append(Evidence(citation=Reference(document_id=link["document_id"], page=link["page"], element_id=link["element_id"]), text=merged, image=link["image_path"], version=access.get("version"), kind="visual" if first < 0 else "text"))
        return result, notes

    def rerank(self, question, evidence, budget):
        if not evidence: return [], []
        try:
            budget.remaining()
            budget.consume_model("reranking")
            scores = reranker().predict([(question, e.text) for e in evidence], batch_size=4)
            return [e for _, e in sorted(zip(scores, evidence), key=lambda p: -float(p[0]))][:3], []
        except (ImportError, OSError, ValueError) as exc:
            return evidence[:3], [f"Reranker indisponible ({type(exc).__name__}) ; classement RRF conservé"]
