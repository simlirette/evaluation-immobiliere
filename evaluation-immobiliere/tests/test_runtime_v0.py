from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeEngine, RuntimeStep, PipelineValidationError, validate_pipeline_steps


class TestRuntimeV0(unittest.TestCase):
    def test_pipeline_validation_rejects_empty_writes(self) -> None:
        with self.assertRaises(PipelineValidationError):
            validate_pipeline_steps([RuntimeStep("agent", ["input"], [])])

    def test_run_case_data_persists_case_directory_and_metrics(self) -> None:
        case = {
            "dossier_id": "D-TEST",
            "date_reference": "2026-04-28",
            "comparables": [{"comparable_id": "C1", "prix_vente": 500000, "source_id": "SRC-1"}],
            "ajustements": [{"ajustement_id": "A1", "montant": 10000, "source_id": "SRC-1", "validation_humaine": True}],
            "confidence": 0.85,
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = RuntimeEngine().run_case_data(case, Path(tmp), case_subdir=True)
            self.assertEqual(result["status"], "PRET_REVISION_FINALE")
            self.assertTrue(Path(result["artifact_dir"]).exists())
            self.assertGreaterEqual(result["metrics"]["wall_clock_seconds"], 0)
            self.assertIn("artifact_written", {event["event"] for event in result["events"]})


if __name__ == "__main__":
    unittest.main()
