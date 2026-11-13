"""Interruption LangGraph : aucun jeton avant reprise humaine explicite."""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from src.ticket_backend import get_ticket_service

class ApprovalState(TypedDict, total=False):
    draft: dict
    approval_token: str

def build_approval_graph(principal, service=None):
    service = service or get_ticket_service()
    def human(state):
        decision = interrupt({"user": principal.user, "draft": state["draft"], "message": "Vérifiez et approuvez explicitement le contenu exact"})
        if not isinstance(decision, dict) or decision.get("confirmed") is not True:
            raise PermissionError("Approbation refusée")
        token = service.approve(principal, **state["draft"], confirmed=True)
        return {"approval_token": token}
    graph = StateGraph(ApprovalState)
    graph.add_node("human_approval", human)
    graph.add_edge(START, "human_approval")
    graph.add_edge("human_approval", END)
    return graph.compile(checkpointer=InMemorySaver())
