"""Initialiser des identités fictives ; ne jamais afficher les jetons."""
import hashlib
import json
import secrets
from src.settings import STATE

def main():
    STATE.mkdir(exist_ok=True)
    auth = STATE / "auth.json"
    if auth.exists():
        print("Identités existantes conservées.")
        return
    users = []
    for name, groups, equipment in [("technicien-demo", ["maintenance"], ["PUMP-001", "VALVE-001"]), ("lecteur-demo", ["visiteur"], [])]:
        token = secrets.token_urlsafe(48)
        (STATE / (name + ".token")).write_text(token, encoding="utf-8")
        users.append(dict(user=name, groups=groups, equipment=equipment, token_hash=hashlib.sha256(token.encode()).hexdigest()))
    auth.write_text(json.dumps(users, indent=2), encoding="utf-8")
    print("Identités fictives créées dans .local ; jetons exclus des journaux et de Git.")

if __name__ == "__main__":
    main()
