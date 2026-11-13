"""Tests sur des PDF synthétiques temporaires, sans toucher au corpus."""

import csv
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter

from src.manifest import ERROR_FIELDS, FIELDS, generate_manifest


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parents[1] / "tests",
        )
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def make_pdf(self, name, password=None):
        """Créer deux pages ; None signifie aucune protection."""
        pdf = self.root / "data/raw" / name
        pdf.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.add_blank_page(width=72, height=72)
        if password is not None:
            writer.encrypt(user_password=password, owner_password="test-owner")
        with pdf.open("wb") as target:
            writer.write(target)
        return pdf

    def read_csv(self, name):
        with (self.root / "data/processed" / name).open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            return reader.fieldnames, list(reader)

    def test_pdf_metadata(self):
        pdf = self.make_pdf("pompes/sous-dossier/exemple.PDF")
        original = pdf.read_bytes()
        self.assertEqual(generate_manifest(self.root), {"pompes": 1, "vannes": 0})
        fields, rows = self.read_csv("manifest.csv")
        self.assertEqual(fields, list(FIELDS))
        self.assertEqual(rows, [dict(zip(FIELDS, (
            "exemple.PDF", "pompes", "2", str(len(original)),
            "data/raw/pompes/sous-dossier/exemple.PDF",
        )))])
        self.assertEqual(pdf.read_bytes(), original)
        self.assertEqual(self.read_csv("manifest_errors.csv"), (list(ERROR_FIELDS), []))

    def test_empty_corpus(self):
        self.assertEqual(generate_manifest(self.root), {"pompes": 0, "vannes": 0})
        self.assertEqual(self.read_csv("manifest.csv"), (list(FIELDS), []))
        self.assertEqual(self.read_csv("manifest_errors.csv"), (list(ERROR_FIELDS), []))

    def test_encrypted_with_empty_password(self):
        pdf = self.make_pdf("vannes/ouvert.pdf", password="")
        original = pdf.read_bytes()
        self.assertEqual(generate_manifest(self.root), {"pompes": 0, "vannes": 1})
        self.assertEqual(self.read_csv("manifest.csv")[1][0]["nombre_pages"], "2")
        self.assertEqual(self.read_csv("manifest_errors.csv")[1], [])
        self.assertEqual(pdf.read_bytes(), original)

    def test_protected_pdf_is_reported_and_processing_continues(self):
        protected = self.make_pdf("pompes/a-protege.pdf", password="required-password")
        original = protected.read_bytes()
        self.make_pdf("pompes/z-valide.pdf")
        self.assertEqual(generate_manifest(self.root), {"pompes": 1, "vannes": 0})
        self.assertEqual(self.read_csv("manifest.csv")[1][0]["nom_fichier"], "z-valide.pdf")
        errors = self.read_csv("manifest_errors.csv")[1]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["chemin_relatif"], "data/raw/pompes/a-protege.pdf")
        self.assertEqual(errors[0]["type_erreur"], "pdf_protege")
        self.assertIn("sans mot de passe refusée", errors[0]["message"])
        self.assertEqual(protected.read_bytes(), original)

    def test_unreadable_pdf_is_reported_and_processing_continues(self):
        pdf = self.root / "data/raw/vannes/a-invalide.pdf"
        pdf.parent.mkdir(parents=True)
        pdf.write_bytes(b"invalid PDF")
        self.make_pdf("vannes/z-valide.pdf")
        self.assertEqual(generate_manifest(self.root), {"pompes": 0, "vannes": 1})
        self.assertEqual(self.read_csv("manifest.csv")[1][0]["nom_fichier"], "z-valide.pdf")
        errors = self.read_csv("manifest_errors.csv")[1]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["chemin_relatif"], "data/raw/vannes/a-invalide.pdf")
        self.assertEqual(errors[0]["type_erreur"], "lecture_impossible")
        self.assertTrue(errors[0]["message"])
        self.assertEqual(pdf.read_bytes(), b"invalid PDF")

    def test_unknown_family_does_not_stop_valid_pdf(self):
        self.make_pdf("inconnu.pdf")
        self.make_pdf("pompes/valide.pdf")
        self.assertEqual(generate_manifest(self.root), {"pompes": 1, "vannes": 0})
        self.assertEqual(self.read_csv("manifest_errors.csv")[1][0]["type_erreur"], "famille_inconnue")

    def test_error_report_is_refreshed(self):
        self.make_pdf("vannes/document.pdf", password="required-password")
        generate_manifest(self.root)
        self.assertEqual(len(self.read_csv("manifest_errors.csv")[1]), 1)
        # Remplacement uniquement d'une fixture synthétique temporaire.
        self.make_pdf("vannes/document.pdf")
        self.assertEqual(generate_manifest(self.root), {"pompes": 0, "vannes": 1})
        self.assertEqual(self.read_csv("manifest_errors.csv")[1], [])


if __name__ == "__main__":
    unittest.main()
