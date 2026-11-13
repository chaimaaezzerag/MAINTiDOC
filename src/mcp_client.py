"""Client MCP réel par stdio ; outils fixes, budget et délai contrôlés."""
import os
import sys
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.settings import ROOT, MAX_MCP_CALLS

async def call_tool(token, tool, arguments, budget):
    if tool not in {"get_equipment_history", "get_open_tickets", "create_ticket"}:
        raise PermissionError("Outil non autorisé")
    if budget.mcp_calls >= MAX_MCP_CALLS:
        raise RuntimeError("Budget MCP dépassé")
    budget.mcp_calls += 1
    env = {key: value for key, value in os.environ.items() if key.upper() in {"PATH", "SYSTEMROOT", "TEMP", "TMP", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}}
    for key in ("MAINTIDOC_TICKET_BACKEND", "MAINTIDOC_POSTGRES_DSN"):
        if key in os.environ: env[key] = os.environ[key]
    env["MAINTIDOC_MCP_TOKEN"] = token
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONIOENCODING"] = "utf-8"
    params = StdioServerParameters(command=sys.executable, args=["-m", "src.mcp_server"], cwd=str(ROOT), env=env)
    with anyio.fail_after(min(12, budget.remaining())):
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments)
                if result.isError:
                    raise PermissionError("Appel MCP refusé ou invalide")
                return result.model_dump(mode="json")
