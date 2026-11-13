"""Client réseau restreint à Ollama local, schémas stricts et budget partagé."""
import base64
import io
import os
import json
import time
import urllib.request
from PIL import Image
from src.settings import MODEL, MAX_SECONDS, MAX_MODEL_CALLS, MAX_IMAGE_BYTES

class Budget:
    def __init__(self):
        self.start = time.monotonic()
        self.model_calls = 0
        self.mcp_calls = 0
        self.model_roles = {}
    def consume_model(self, role):
        self.remaining()
        if self.model_calls >= MAX_MODEL_CALLS:
            raise RuntimeError("Budget de six appels modèle dépassé")
        self.model_calls += 1
        self.model_roles[role] = self.model_roles.get(role, 0) + 1

    def remaining(self):
        value = MAX_SECONDS - (time.monotonic() - self.start)
        if value <= 0:
            raise TimeoutError("Budget de 60 secondes dépassé")
        return value

def validate_photo(encoded):
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Image trop volumineuse")
    with Image.open(io.BytesIO(raw)) as im:
        if im.width * im.height > 16000000:
            raise ValueError("Image trop grande")
        im.verify()
    return raw

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PermissionError("Redirection réseau interdite")

class Ollama:
    def generate(self, system, payload, schema, budget, images=None):
        budget.remaining()
        budget.consume_model("vlm")
        message = dict(role="user", content=json.dumps(payload, ensure_ascii=False))
        if images:
            bounded_images = []
            for encoded in images[:2]:
                raw = base64.b64decode(encoded, validate=True)
                with Image.open(io.BytesIO(raw)) as source:
                    if source.width * source.height > 16000000:
                        raise ValueError("Image trop grande")
                    picture = source.convert("RGB")
                    picture.thumbnail((896, 896))
                    target = io.BytesIO()
                    picture.save(target, format="JPEG", quality=90)
                    bounded_images.append(base64.b64encode(target.getvalue()).decode())
            message["images"] = bounded_images
        body = dict(model=MODEL, stream=False, format=schema.model_json_schema(), messages=[dict(role="system", content=system), message], options=dict(temperature=0, num_predict={"Visual":160,"Answer":320,"EvidenceReport":600}.get(schema.__name__,320), num_ctx=4096, num_thread=4, num_gpu=0), keep_alive="15m")
        endpoint = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        if endpoint not in {"http://127.0.0.1:11434", "http://host.docker.internal:11434"}:
            raise PermissionError("Destination Ollama interdite")
        request = urllib.request.Request(endpoint + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        # Aucun proxy, redirection ou destination fourni par les documents.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=min(35 if images else 28, budget.remaining())) as response:
            result = json.load(response)
        budget.remaining()
        if result.get("done_reason") != "stop":
            raise ValueError("Génération incomplète")
        return schema.model_validate_json(result["message"]["content"])
