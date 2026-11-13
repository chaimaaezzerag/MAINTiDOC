"""Inventorier les PDF du corpus sans modifier les documents sources."""

import argparse
import csv
from pathlib import Path

from pypdf import PdfReader


FAMILIES = ("pompes", "vannes")
FIELDS = ("nom_fichier", "famille", "nombre_pages", "taille_octets", "chemin_relatif")
ERROR_FIELDS = ("chemin_relatif", "type_erreur", "message")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_pdf_metadata(path: Path) -> tuple[int, int]:
    """Lire pages et taille en autorisant uniquement un mot de passe vide.

    L'ouverture reste en mémoire : aucun PDF déchiffré n'est enregistré.
    Aucun mot de passe non vide ni extraction de contenu n'est tenté.
    Chaque objet de page est parcouru pour vérifier son accessibilité.
    """
    with path.open("rb") as source:
        reader = PdfReader(source)
        if reader.is_encrypted and not reader.decrypt(""):
            raise PermissionError("PDF protégé : ouverture sans mot de passe refusée")
        pages = sum(1 for _ in reader.pages)
        size = path.stat().st_size
    return pages, size


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    """Écrire un CSV UTF-8, avec en-tête même sans lignes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, int]:
    """Créer data/processed/manifest.csv et retourner les effectifs par famille.

    Les chemins sont relatifs au projet et les tailles exprimées en octets.
    Les sous-dossiers de chaque famille sont parcourus récursivement.
    Les PDF accessibles sans mot de passe sont inclus, même s'ils sont chiffrés.
    Les PDF illisibles, protégés ou hors des familles connues sont signalés dans
    manifest_errors.csv et ignorés. Les compteurs portent sur les PDF inclus.
    Les deux CSV sont régénérés à chaque exécution.
    """
    project_root = Path(project_root).resolve()
    raw = project_root / "data" / "raw"
    counts = dict.fromkeys(FAMILIES, 0)
    rows = []
    errors = []
    for path in sorted(raw.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue
        relative = path.relative_to(raw)
        project_relative = path.relative_to(project_root).as_posix()
        if len(relative.parts) < 2 or relative.parts[0] not in FAMILIES:
            errors.append(dict(zip(ERROR_FIELDS, (
                project_relative, "famille_inconnue", "PDF hors des familles pompes/vannes",
            ))))
            continue
        family = relative.parts[0]
        try:
            pages, size = read_pdf_metadata(path)
        except Exception as exc:
            errors.append(dict(zip(ERROR_FIELDS, (
                project_relative,
                "pdf_protege" if isinstance(exc, PermissionError) else "lecture_impossible",
                f"{type(exc).__name__}: {exc}",
            ))))
            continue
        rows.append(dict(zip(FIELDS, (
            path.name, family, pages, size,
            project_relative,
        ))))
        counts[family] += 1

    output = project_root / "data" / "processed" / "manifest.csv"
    write_csv(output, FIELDS, rows)
    write_csv(output.with_name("manifest_errors.csv"), ERROR_FIELDS, errors)
    return counts


def main() -> None:
    """Exécuter l'inventaire du projet depuis la ligne de commande."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        counts = generate_manifest()
    except OSError as exc:
        parser.exit(1, f"Erreur : {exc}\n")
    for family, count in counts.items():
        print(f"{family} : {count} PDF")
    print("Manifeste : data/processed/manifest.csv")
    report = PROJECT_ROOT / "data/processed/manifest_errors.csv"
    with report.open(encoding="utf-8", newline="") as source:
        error_count = sum(1 for _ in csv.DictReader(source))
    print(f"Documents ignorés : {error_count} (rapport : data/processed/manifest_errors.csv)")


if __name__ == "__main__":
    main()
