from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeEngine
from engine.valuation import calculate_all_valuation_traces, calculate_valuation_trace


def case_payload() -> dict:
    return {
        "dossier_id": "D-CALC",
        "date_reference": "2026-04-28",
        "surface": {"value": 1000, "unit": "pi2"},
        "comparables": [
            {
                "comparable_id": "C1",
                "prix_vente": 300000,
                "source_id": "SRC-1",
                "date_vente": "2026-03-01",
                "distance_km": 2,
                "surface": {"value": 980, "unit": "pi2"},
                "confidence": 0.9,
            },
            {
                "comparable_id": "C2",
                "prix_vente": 450000,
                "source_id": "SRC-2",
                "date_vente": "2025-10-01",
                "distance_km": 18,
                "surface": {"value": 1500, "unit": "pi2"},
                "confidence": 0.7,
            },
        ],
        "ajustements": [
            {"ajustement_id": "A1", "montant": 10000, "source_id": "SRC-A", "validation_humaine": True},
            {"ajustement_id": "A2", "montant": 999999, "source_id": "SRC-B", "validation_humaine": False},
        ],
        "confidence": 0.85,
    }


class TestValuationV0(unittest.TestCase):
    def test_calculate_comparative_trace_is_deterministic_and_auditable(self) -> None:
        trace = calculate_valuation_trace(case_payload(), "approche_comparative")
        self.assertEqual(trace["method"], "weighted_mean_score_v0")
        self.assertEqual(trace["input_count"], 2)
        self.assertGreater(trace["value"], 0)
        self.assertEqual(trace["trace"]["adjustment_total_validated"], 10000)
        self.assertEqual(len(trace["trace"]["selected_comparables"]), 2)
        self.assertIn("score_details", trace["trace"]["selected_comparables"][0])

    def test_calculate_all_valuation_traces_returns_three_approaches(self) -> None:
        traces = calculate_all_valuation_traces(case_payload())
        self.assertEqual(set(traces), {"approche_comparative", "approche_cout", "approche_revenu"})

    def test_runtime_writes_valuation_trace_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = RuntimeEngine().run_case_data(case_payload(), Path(tmp), case_subdir=True)
            artifact = Path(result["artifact_dir"]) / "valuation-draft.calculs_approche_comparative.json"
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            self.assertIn("trace", payload)
            self.assertIn("selected_comparables", payload["trace"])
            self.assertIn("score_details", payload["trace"]["selected_comparables"][0])


if __name__ == "__main__":
    unittest.main()
