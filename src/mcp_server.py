"""Serveur MCP stdio, outils fictifs ; identité vérifiée à chaque appel."""
import os
from mcp.server.fastmcp import FastMCP
from src.security import authenticate
from src.ticket_backend import get_ticket_service

mcp = FastMCP("MAINTiDOC maintenance fictive")

def principal():
    return authenticate(os.environ.get("MAINTIDOC_MCP_TOKEN", ""))

@mcp.tool()
def get_equipment_history(equipment_id: str) -> list[dict]:
    """Consulter les interventions fictives autorisées."""
    actor = principal()
    return get_ticket_service().history(actor, equipment_id)

@mcp.tool()
def get_open_tickets(equipment_id: str) -> list[dict]:
    """Consulter les tickets fictifs autorisés."""
    actor = principal()
    return get_ticket_service().tickets(actor, equipment_id)

@mcp.tool()
def create_ticket(equipment_id: str, title: str, description: str, approval_token: str) -> dict:
    """Créer un ticket fictif avec un jeton d'approbation exact et valide."""
    from src.runtime_models import CreateTicket
    request = CreateTicket(equipment_id=equipment_id, title=title, description=description, approval_token=approval_token)
    actor = principal()
    return get_ticket_service().create(actor, **request.model_dump())

if __name__ == "__main__":
    mcp.run(transport="stdio")
