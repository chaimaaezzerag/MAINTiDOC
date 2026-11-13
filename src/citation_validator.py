import json
from pathlib import Path

ROOT = Path("data/processed")

def normaliser_citations(citations, preuves):
    autorisees = [
        p["citation"] for p in preuves
    ]

    resultat = []

    for citation in citations:
        document = citation["document_id"]
        page = citation["page"]
        element = citation["element_id"]

        correspondances = [
            ref for ref in autorisees
            if ref["page"] == page
            and ref["element_id"] == element
            and (
                ref["document_id"] == document
                or ref["document_id"].split("/")[-1] == document
            )
        ]

        if len(correspondances) != 1:
            raise ValueError(
                f"Citation invalide ou ambigue : {citation}"
            )

        resultat.append(correspondances[0].copy())

    return resultat


if __name__ == "__main__":
    with (ROOT / "evidence_mmr_vannes.json").open(
        "r", encoding="utf-8"
    ) as f:
        preuves = json.load(f)["preuves"]

    citations_qwen = [
        {
            "document_id": "2bo70en",
            "page": 23,
            "element_id": "2bo70en_page_23"
        },
        {
            "document_id": "2bax70en",
            "page": 16,
            "element_id": "2bax70en_page_16"
        },
        {
            "document_id": "2bax70en",
            "page": 32,
            "element_id": "2bax70en_page_32"
        }
    ]

    corrigees = normaliser_citations(
        citations_qwen, preuves
    )

    print("=== VALIDATION CITATIONS MAINTiDOC ===")
    print(json.dumps(corrigees, indent=2))
    print("CITATIONS NORMALISEES ET VALIDEES")
