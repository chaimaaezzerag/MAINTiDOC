"""Choisir explicitement la base ; aucun repli si PostgreSQL échoue."""
import os
from src.ticket_service import TicketService

def get_ticket_service():
    backend = os.environ.get("MAINTIDOC_TICKET_BACKEND", "sqlite-demo")
    if backend == "sqlite-demo": return TicketService()
    if backend == "postgres":
        from src.postgres_tickets import PostgresTicketService
        return PostgresTicketService(os.environ["MAINTIDOC_POSTGRES_DSN"])
    raise ValueError("Backend de tickets inconnu")
