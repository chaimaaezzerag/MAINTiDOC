import json
from pathlib import Path

ROOT = Path("data/processed")
SOURCE = ROOT / "evidence_mmr_vannes.json"
PROMPT = Path("prompts/answer_v1.yaml")
OUTPUT = ROOT / "prompt_rag_test.json"

def lire_bloc_yaml(contenu, nom):
    lignes = contenu.splitlines()
    debut = f"{nom}: |"

    if debut not in lignes:
        raise ValueError(f"Bloc introuvable : {nom}")

    index = lignes.index(debut) + 1
    bloc = []

    for ligne in lignes[index:]:
        if ligne and not ligne.startswith("  "):
            break
        bloc.append(ligne[2:] if ligne.startswith("  ") else "")

    return "\n".join(bloc).strip()

with SOURCE.open("r", encoding="utf-8") as f:
    dossier = json.load(f)

contenu = PROMPT.read_text(encoding="utf-8-sig")
systeme = lire_bloc_yaml(contenu, "system")
template = lire_bloc_yaml(contenu, "user_template")

preuves = []

for numero, preuve in enumerate(dossier["preuves"], 1):
    citation = preuve["citation"]
    preuves.append(
        f"SOURCE {numero}\n"
        f"Document : {citation['document_id']}\n"
        f"Page : {citation['page']}\n"
        f"Element : {citation['element_id']}\n"
        f"Texte : {preuve['texte']}"
    )

evidence = "\n\n".join(preuves)

message = template.replace(
    "{question}", dossier["question"]
).replace(
    "{evidence}", evidence
)

resultat = {
    "system": systeme,
    "user": message
}

if OUTPUT.exists():
    raise SystemExit("Prompt RAG deja assemble. Aucune modification.")

with OUTPUT.open("x", encoding="utf-8") as f:
    json.dump(resultat, f, ensure_ascii=False, indent=2)

print("=== ASSEMBLAGE PROMPT MAINTiDOC ===")
print("Question :", dossier["question"])
print("Sources integrees :", len(dossier["preuves"]))
print("Instructions systeme :", len(systeme), "caracteres")
print("Message utilisateur :", len(message), "caracteres")
print("Fichier :", OUTPUT)
print("PROMPT RAG ASSEMBLE")
