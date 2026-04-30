from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from preparer_revue_interne_pilotes_v0 import (
    build_backlog_items,
    build_review_markdown,
    build_waiting_report,
    missing_artifacts,
    review_decision,
)


class TestRevueInternePilotesV0(unittest.TestCase):
    def test_waiting_report_marks_phase_3_dependency(self) -> None:
        report = build_waiting_report(Path("runtime-test"))

        self.assertIn("EN_ATTENTE_EXECUTION_PHASE_3", report)
        self.assertIn("runtime_summary.json", report)

    def test_review_decision_detects_missing_artifacts(self) -> None:
        case = {"artifact_dir": "missing-dir", "status": "PRET_REVISION_FINALE", "blocking_failures": [], "warnings": []}

        self.assertEqual(review_decision(case), "A_CORRIGER_AVANT_EVALUATEURS")
        self.assertIn("compliance-qa.statut_sortie.json", missing_artifacts(case))

    def test_clean_case_is_ready_when_required_artifacts_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact_dir = Path(tmp)
            for name in [
                "compliance-qa.statut_sortie.json",
                "compliance-qa.rapport_non_conformites.json",
                "compliance-qa.recommandations_corrections.md",
                "redaction.brouillon_rapport.md",
            ]:
                (artifact_dir / name).write_text("ok", encoding="utf-8")

            case = {
                "artifact_dir": str(artifact_dir),
                "status": "PRET_REVISION_FINALE",
                "blocking_failures": [],
                "warnings": [],
            }

            self.assertEqual(review_decision(case), "PRET_REVUE_EVALUATEUR")
            self.assertEqual(missing_artifacts(case), [])

    def test_backlog_and_markdown_include_blocking_and_warning_items(self) -> None:
        summary = [
            {
                "artifact_dir": "missing-dir",
                "dossier_id": "D-1",
                "status": "A_REVOIR",
                "blocking_failures": ["B001: blocage"],
                "warnings": ["W001: warning"],
            }
        ]

        backlog = build_backlog_items(summary)
        report = build_review_markdown(summary)

        self.assertTrue(any(item["severity"] == "blocking" for item in backlog))
        self.assertTrue(any(item["severity"] == "warning" for item in backlog))
        self.assertIn("A_CORRIGER_AVANT_EVALUATEURS", report)
        self.assertIn("B001: blocage", report)


if __name__ == "__main__":
    unittest.main()
