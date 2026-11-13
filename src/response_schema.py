from typing import Literal
from pydantic import BaseModel, Field

class Citation(BaseModel):
    document_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    element_id: str = Field(min_length=1)

class ReponseMAINTiDOC(BaseModel):
    status: Literal["answered", "clarification", "abstention"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    proposed_action: str | None = None

if __name__ == "__main__":
    exemple = ReponseMAINTiDOC(
        status="clarification",
        answer="Le type exact de vanne n'est pas precise.",
        citations=[],
        uncertainties=[
            "Les procedures peuvent varier selon le modele."
        ],
        clarification_question="Quel est le modele de la vanne ?",
        proposed_action=None
    )

    print("=== SCHEMA REPONSE MAINTiDOC ===")
    print(exemple.model_dump_json(indent=2))
    print("SCHEMA VALIDE")
