"""Clients explicites Qdrant, PostgreSQL et MinIO, sans repli silencieux."""
import hashlib
import io
import json
import os
import uuid
import numpy as np
from src.settings import DATA, ROOT
from src.security import policies, safe_path

def sync_services():
    import psycopg
    from minio import Minio
    from qdrant_client import QdrantClient, models
    # Secrets uniquement injectés à l'exécution, jamais inclus dans les résultats.
    pg = os.environ["MAINTIDOC_POSTGRES_DSN"]
    client = QdrantClient(url=os.environ["MAINTIDOC_QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=10)
    minio = Minio(os.environ["MAINTIDOC_MINIO_ENDPOINT"], access_key=os.environ["MINIO_ROOT_USER"], secret_key=os.environ["MINIO_ROOT_PASSWORD"], secure=os.environ.get("MINIO_SECURE", "true").lower() == "true")
    vectors = np.load(DATA / "embeddings_search.npy", allow_pickle=False)
    links = [json.loads(x) for x in (DATA / "multimodal_links.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    chunks = [json.loads(x) for x in (DATA / "chunks_search.jsonl").read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    if len(vectors) != len(chunks): raise ValueError("Index désynchronisé")
    policy = policies()
    fingerprint = hashlib.sha256((DATA / "embeddings_search.npy").read_bytes()).hexdigest()[:12]
    collection = "maintidoc_" + fingerprint
    if not client.collection_exists(collection):
        client.create_collection(collection, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
    bucket = "maintidoc"
    if not minio.bucket_exists(bucket): minio.make_bucket(bucket)
    with psycopg.connect(pg) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS maintidoc_documents (document_id TEXT PRIMARY KEY, version TEXT, groups_json JSONB NOT NULL, path TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS maintidoc_elements (element_id TEXT PRIMARY KEY, document_id TEXT REFERENCES maintidoc_documents(document_id), page INTEGER NOT NULL, blob_key TEXT NOT NULL)")
        for doc_id, entry in policy.items():
            conn.execute("INSERT INTO maintidoc_documents VALUES (%s,%s,%s,%s) ON CONFLICT (document_id) DO NOTHING", (doc_id, entry.get("version"), json.dumps(entry["groups"]), entry["path"]))
            path = safe_path(entry["path"])
            key = hashlib.sha256(path.read_bytes()).hexdigest() + ".pdf"
            # Les objets sont adressés par contenu : aucune suppression de l'ancien corpus.
            minio.fput_object(bucket, key, str(path), content_type="application/pdf")
        by_index = {x["chunk_index"]: x for x in links}
        points = []
        for i, chunk in enumerate(chunks):
            link = by_index[i]
            entry = policy.get(link["document_id"])
            if not entry: continue
            points.append(models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk["chunk_id"])), vector=vectors[i].tolist(), payload={"chunk_index": i, "document_id": link["document_id"], "family": chunk["famille"], "groups": entry["groups"]}))
        for start in range(0,len(points),64): client.upsert(collection, points=points[start:start+64], wait=True)
        seen = set()
        for link in links:
            if link["element_id"] in seen: continue
            seen.add(link["element_id"])
            path = safe_path(link["image_path"])
            key = hashlib.sha256(path.read_bytes()).hexdigest() + ".png"
            minio.fput_object(bucket, key, str(path), content_type="image/png")
            conn.execute("INSERT INTO maintidoc_elements VALUES (%s,%s,%s,%s) ON CONFLICT (element_id) DO NOTHING", (link["element_id"],link["document_id"],link["page"],key))
    return {"collection": collection, "points": len(points), "mode": "services", "documents": len(policy)}

def qdrant_ranking(query, principal, family=None):
    from qdrant_client import QdrantClient, models
    must = [models.FieldCondition(key="groups", match=models.MatchAny(any=list(principal.groups)))]
    if family: must.append(models.FieldCondition(key="family", match=models.MatchValue(value=family)))
    client = QdrantClient(url=os.environ["MAINTIDOC_QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"], timeout=5)
    result = client.query_points(collection_name=os.environ["MAINTIDOC_QDRANT_COLLECTION"], query=query.tolist(), query_filter=models.Filter(must=must), limit=40, with_payload=True)
    return [point.payload["chunk_index"] for point in result.points]

if __name__ == "__main__":
    # Ne pas afficher les exceptions de connexion pouvant contenir une DSN.
    try: print(json.dumps(sync_services()))
    except Exception as exc: raise SystemExit("Synchronisation indisponible : " + type(exc).__name__) from None
