"""Schémas stricts partagés par API, workflow et vérificateur."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

class Reference(StrictModel):
    document_id: str = Field(min_length=1, max_length=200)
    page: int = Field(ge=1)
    element_id: str = Field(min_length=1, max_length=250)

class Evidence(StrictModel):
    citation: Reference
    text: str
    image: str | None = None
    version: str | None = None
    kind: Literal["text", "visual"] = "text"

class Answer(StrictModel):
    status: Literal["answered", "needs_clarification", "abstention"]
    answer: str = Field(max_length=4000)
    citations: list[Reference] = Field(max_length=8)
    uncertainties: list[str] = Field(max_length=10)
    clarification_question: str | None = None
    proposed_action: str | None = None

class ClaimCheck(StrictModel):
    claim: str
    verdict: Literal["supported", "contradicted", "insufficient"]
    basis: Literal["document", "visual", "hypothesis"]
    citation: Reference | None
    quote: str
    reason: str

class EvidenceReport(StrictModel):
    claims: list[ClaimCheck] = Field(max_length=20)

class Ask(StrictModel):
    question: str = Field(min_length=3, max_length=1500)
    family: Literal["pompes", "vannes"] | None = None
    mode: Literal["multimodal", "text_only"] = "multimodal"
    session_id: str = Field(default="default", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    photo_base64: str | None = Field(default=None, max_length=7000000)
    equipment_id: str | None = Field(default=None, max_length=100)

class Draft(StrictModel):
    equipment_id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=3000)

class Approval(Draft):
    confirmed: bool

class CreateTicket(Draft):
    approval_token: str = Field(max_length=2000)
