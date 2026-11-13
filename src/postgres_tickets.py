"""Backend PostgreSQL explicite ; intégration requiert un serveur disponible."""
import hashlib
import secrets
import time
import psycopg
from psycopg.rows import dict_row
from src.settings import STATE
from src.security import require_equipment
from src.ticket_service import TicketService, validate_approval

class PostgresTicketService(TicketService):
    def __init__(self, dsn, directory=STATE):
        self.dsn = dsn
        directory.mkdir(parents=True, exist_ok=True)
        secret = directory / "approval.key"
        try:
            with secret.open("xb") as out: out.write(secrets.token_bytes(32))
        except FileExistsError:
            pass
        self.secret = secret.read_bytes()
        with self.connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS maintidoc_tickets (id BIGSERIAL PRIMARY KEY, user_id TEXT NOT NULL, equipment TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL, approval TEXT UNIQUE NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS maintidoc_ticket_audit (id BIGSERIAL PRIMARY KEY, ts DOUBLE PRECISION NOT NULL, user_id TEXT NOT NULL, operation TEXT NOT NULL, equipment TEXT NOT NULL, ticket BIGINT NOT NULL)")

    def connect(self):
        return psycopg.connect(self.dsn, connect_timeout=5, row_factory=dict_row)

    def create(self, principal, equipment_id, title, description, approval_token):
        require_equipment(principal, equipment_id)
        data, approval = validate_approval(self.secret, principal, equipment_id, title, description, approval_token)
        lock_id = int.from_bytes(hashlib.sha256(approval.encode()).digest()[:8], "big", signed=True)
        with self.connect() as conn:
            # Le verrou de transaction sérialise seulement les tentatives du même jeton.
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (lock_id,))
            existing = conn.execute("SELECT id FROM maintidoc_tickets WHERE approval=%s", (approval,)).fetchone()
            if existing: return dict(ticket_id=existing["id"], duplicate=True)
            if data["expires"] < time.time(): raise PermissionError("Approbation expirée")
            row = conn.execute("INSERT INTO maintidoc_tickets(user_id,equipment,title,description,approval) VALUES(%s,%s,%s,%s,%s) RETURNING id", (principal.user,equipment_id,title,description,approval)).fetchone()
            conn.execute("INSERT INTO maintidoc_ticket_audit(ts,user_id,operation,equipment,ticket) VALUES(%s,%s,%s,%s,%s)", (time.time(),principal.user,"create_ticket",equipment_id,row["id"]))
            return dict(ticket_id=row["id"], duplicate=False)

    def tickets(self, principal, equipment_id):
        require_equipment(principal, equipment_id)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT id,equipment,title,description FROM maintidoc_tickets WHERE equipment=%s ORDER BY id",(equipment_id,))]
