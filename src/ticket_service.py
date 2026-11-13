"""Service fictif transactionnel : approbation exacte, expiration et idempotence."""
import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from src.security import require_equipment
from src.settings import STATE

def canonical(user, equipment_id, title, description):
    return json.dumps([user, equipment_id, title, description], ensure_ascii=False, separators=(",", ":"))

def validate_approval(secret, principal, equipment_id, title, description, approval_token):
    try:
        payload, signature = approval_token.split(".")
        expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(payload))
        digest = hashlib.sha256(canonical(principal.user, equipment_id, title, description).encode()).hexdigest()
        if data["user"] != principal.user or data["digest"] != digest:
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise PermissionError("Approbation invalide ou contenu modifié") from None
    approval = hashlib.sha256(approval_token.encode()).hexdigest()
    return data, approval


class TicketService:
    def __init__(self, directory=STATE):
        directory.mkdir(parents=True, exist_ok=True)
        self.database = directory / "maintenance.sqlite3"
        secret = directory / "approval.key"
        try:
            with secret.open("xb") as out:
                out.write(secrets.token_bytes(32))
        except FileExistsError:
            pass
        self.secret = secret.read_bytes()
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, user TEXT, equipment TEXT, title TEXT, description TEXT, approval TEXT UNIQUE)")
            conn.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, ts REAL, user TEXT, operation TEXT, equipment TEXT, ticket INTEGER)")

    def connect(self):
        conn = sqlite3.connect(self.database, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def approve(self, principal, equipment_id, title, description, confirmed):
        require_equipment(principal, equipment_id)
        if confirmed is not True:
            raise PermissionError("Approbation humaine explicite requise")
        digest = hashlib.sha256(canonical(principal.user, equipment_id, title, description).encode()).hexdigest()
        data = json.dumps(dict(user=principal.user, digest=digest, expires=int(time.time()) + 300, nonce=secrets.token_hex(16)), sort_keys=True).encode()
        payload = base64.urlsafe_b64encode(data).decode()
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        return payload + "." + signature

    def create(self, principal, equipment_id, title, description, approval_token):
        require_equipment(principal, equipment_id)
        data, approval = validate_approval(self.secret, principal, equipment_id, title, description, approval_token)
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute("SELECT id FROM tickets WHERE approval=?", (approval,)).fetchone()
            if existing:
                return dict(ticket_id=existing["id"], duplicate=True)
            if data["expires"] < time.time():
                raise PermissionError("Approbation expirée")
            cursor = conn.execute("INSERT INTO tickets(user,equipment,title,description,approval) VALUES(?,?,?,?,?)", (principal.user, equipment_id, title, description, approval))
            conn.execute("INSERT INTO audit(ts,user,operation,equipment,ticket) VALUES(?,?,?,?,?)", (time.time(), principal.user, "create_ticket", equipment_id, cursor.lastrowid))
            return dict(ticket_id=cursor.lastrowid, duplicate=False)

    def history(self, principal, equipment_id):
        require_equipment(principal, equipment_id)
        return [dict(equipment_id=equipment_id, date="2026-01-15", event="Inspection fictive de démonstration", synthetic=True)]

    def tickets(self, principal, equipment_id):
        require_equipment(principal, equipment_id)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT id,equipment,title,description FROM tickets WHERE equipment=? ORDER BY id", (equipment_id,))]
