import base64
import json
import urllib.request
from pathlib import Path

image = Path(
    "data/processed/pages_visual/vannes/"
    "2bax70en/2bax70en_page_16.png"
)

if not image.is_file():
    raise SystemExit(f"Image introuvable : {image}")

with image.open("rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("ascii")

payload = {
    "model": "qwen2.5vl:3b",
    "stream": False,
    "messages": [
        {
            "role": "system",
            "content": (
                "Tu es MAINTiDOC. Analyse uniquement "
                "les informations visibles sur l'image. "
                "Reponds en francais. "
                "Ne devine pas les details illisibles. "
                "Ne donne pas d'instructions de maintenance "
                "non justifiees par cette page."
            )
        },
        {
            "role": "user",
            "content": (
                "Que contient cette page de manuel industriel ? "
                "Decris les textes, schemas ou figures visibles. "
                "Signale les informations illisibles."
            ),
            "images": [image_base64]
        }
    ],
    "options": {
        "temperature": 0,
        "num_predict": 500
    }
}

request = urllib.request.Request(
    "http://127.0.0.1:11434/api/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("=== TEST VISION MAINTiDOC ===", flush=True)
print("Image :", image)

with urllib.request.urlopen(request, timeout=300) as response:
    resultat = json.load(response)

print("Raison de fin :", resultat.get("done_reason"))
print("=== ANALYSE VISUELLE ===")
print(resultat["message"]["content"])
print("TEST VISION TERMINE")
