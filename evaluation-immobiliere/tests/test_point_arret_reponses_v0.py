from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from valider_reponses_evaluateurs import ValidationResult
from verifier_point_arret_reponses_v0 import (
    build_stop_report,
    package_status,
    stop_status,
    validation_status,
)


def result(active_rows: int = 0, errors: list = None) -> ValidationResult:
    return ValidationResult(
        path=Path("responses.csv"),
        total_rows=active_rows,
        active_rows=active_rows,
        respondent_count=active_rows,
        errors=errors or [],
        warnings=[],
    )


class TestPointArretReponsesV0(unittest.TestCase):
    def test_validation_status_is_ready_when_no_active_rows(self) -> None:
        self.assertEqual(validation_status(result()), "PRET_A_RECEVOIR")

    def test_stop_status_ready_only_when_package_ready_and_no_responses(self) -> None:
        self.assertEqual(stop_status(result(), "PRET_A_ENVOYER"), "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(stop_status(result(), "EN_ATTENTE_DOSSIERS_REELS"), "EN_ATTENTE_AVANT_REPONSES")

    def test_stop_status_detects_existing_responses(self) -> None:
        self.assertEqual(stop_status(result(active_rows=2), "PRET_A_ENVOYER"), "REPONSES_DEJA_PRESENTES")

    def test_package_status_reads_index_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.md"
            path.write_text("- Statut: **PRET_A_ENVOYER**\n", encoding="utf-8")

            self.assertEqual(package_status(path), "PRET_A_ENVOYER")

    def test_package_status_marks_absent_index(self) -> None:
        self.assertEqual(package_status(Path("missing-index.md")), "PAQUET_ABSENT")

    def test_stop_report_includes_rules_against_invented_responses(self) -> None:
        report = build_stop_report(result(), "EN_ATTENTE_DOSSIERS_REELS", Path("report.md"), Path("package.md"))

        self.assertIn("Ne pas inventer", report)
        self.assertIn("EN_ATTENTE_AVANT_REPONSES", report)


if __name__ == "__main__":
    unittest.main()
