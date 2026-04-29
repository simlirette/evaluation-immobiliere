from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from generer_rapport_pilote_runtime_v0 import build_markdown, summarize


class TestRapportPiloteV0(unittest.TestCase):
    def test_summarize_counts_statuses_and_issues(self) -> None:
        metrics = summarize(
            [
                {
                    "status": "PRET_REVISION_FINALE",
                    "blocking_failures": [],
                    "warnings": [],
                    "events": [{"event": "step_start"}],
                },
                {
                    "status": "A_REVOIR",
                    "blocking_failures": ["B001"],
                    "warnings": ["W001"],
                    "events": [{"event": "step_start"}, {"event": "blocking_detected"}],
                },
            ]
        )
        self.assertEqual(metrics["cases"], 2)
        self.assertEqual(metrics["ready_for_review"], 1)
        self.assertEqual(metrics["needs_review"], 1)
        self.assertEqual(metrics["total_blocking_failures"], 1)
        self.assertEqual(metrics["total_runtime_events"], 3)

    def test_build_markdown_includes_case_table_and_product_reading(self) -> None:
        markdown = build_markdown(
            [
                {
                    "dossier_id": "D-001",
                    "status": "BROUILLON",
                    "blocking_failures": [],
                    "warnings": ["W001"],
                    "events": [],
                    "artifact_dir": "evaluation-immobiliere/tests/runtime/case_low_confidence",
                }
            ]
        )
        self.assertIn("# Rapport pilote runtime v0", markdown)
        self.assertIn("| case_low_confidence | D-001 | BROUILLON", markdown)
        self.assertIn("Lecture produit", markdown)


if __name__ == "__main__":
    unittest.main()
