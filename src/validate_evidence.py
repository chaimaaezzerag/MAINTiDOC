import json
from pathlib import Path
from pydantic import BaseModel, Field

SOURCE = Path("data/processed/evidence_mmr_vannes.json")

class Citation(BaseModel):
    document_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    element_id: str = Field(min_length=1)

class Preuve(BaseModel):
    texte: str = Field(min_length=1)
    image: str = Field(min_length=1)
    citation: Citation
    similarite: float = Field(ge=-1, le=1)

class DossierPreuves(BaseModel):
    question: str = Field(min_length=1)
    famille: str
    methode_recherche: str
    preuves: list[Preuve] = Field(min_length=1)

with SOURCE.open("r", encoding="utf-8") as f:
    donnees = json.load(f)

dossier = DossierPreuves.model_validate(donnees)

print("=== VALIDATION DES PREUVES MAINTiDOC ===")
print("Question :", dossier.question)
print("Nombre de preuves :", len(dossier.preuves))

for numero, preuve in enumerate(dossier.preuves, 1):
    image = Path(preuve.image)

    if not image.is_file():
        raise FileNotFoundError(image)

    print(
        f"Preuve {numero} : VALIDE | "
        f"{preuve.citation.document_id} | "
        f"page {preuve.citation.page} | "
        f"image presente"
    )

print("VALIDATION TERMINEE")
