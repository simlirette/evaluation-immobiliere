from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.tools import run_calculation, score_comparable, search_comparables, validate_schema


class TestToolsV0(unittest.TestCase):
    def test_run_calculation_mean(self) -> None:
        self.assertEqual(run_calculation([1, 2, 3], "mean"), 2.0)

    def test_run_calculation_median_even(self) -> None:
        self.assertEqual(run_calculation([1, 4, 2, 3], "median"), 2.5)

    def test_run_calculation_weighted_mean(self) -> None:
        self.assertEqual(run_calculation([100, 200], "weighted_mean", weights=[1, 3]), 175.0)

    def test_search_comparables_filters_missing_source(self) -> None:
        pool = [
            {"comparable_id": "A", "prix_vente": 300000, "source_id": "SRC-1"},
            {"comparable_id": "B", "prix_vente": 500000},
            {"comparable_id": "C", "prix_vente": 400000, "source_id": "SRC-2"},
        ]
        result = search_comparables(pool, max_items=10)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].comparable_id, "C")

    def test_search_comparables_keeps_date_vente(self) -> None:
        pool = [{"comparable_id": "A", "prix_vente": 300000, "source_id": "SRC-1", "date_vente": "2026-01-15"}]
        result = search_comparables(pool, max_items=10)
        self.assertEqual(result[0].date_vente, "2026-01-15")

    def test_search_comparables_score_is_bounded(self) -> None:
        pool = [{"comparable_id": "A", "prix_vente": 9_000_000, "source_id": "SRC-1", "confidence": 3}]
        result = search_comparables(pool, max_items=10)
        self.assertLessEqual(result[0].score, 1.0)
        self.assertGreaterEqual(result[0].score, 0.0)
        self.assertIn("components", result[0].score_details)

    def test_score_comparable_explains_future_sale_penalty(self) -> None:
        details = score_comparable(
            {
                "comparable_id": "A",
                "prix_vente": 300000,
                "source_id": "SRC-1",
                "date_vente": "2026-05-01",
                "distance_km": 1,
                "surface": {"value": 1000, "unit": "pi2"},
            },
            subject={"surface": {"value": 1000, "unit": "pi2"}},
            date_reference="2026-04-28",
        )
        self.assertIn("future_sale", details["penalties"])
        self.assertLess(details["score"], details["weighted_score"])

    def test_search_comparables_prefers_closer_more_similar_item(self) -> None:
        subject = {"surface": {"value": 1000, "unit": "pi2"}}
        pool = [
            {
                "comparable_id": "FAR",
                "prix_vente": 400000,
                "source_id": "SRC-FAR",
                "date_vente": "2026-01-01",
                "distance_km": 30,
                "surface": {"value": 1800, "unit": "pi2"},
            },
            {
                "comparable_id": "NEAR",
                "prix_vente": 300000,
                "source_id": "SRC-NEAR",
                "date_vente": "2026-03-01",
                "distance_km": 2,
                "surface": {"value": 980, "unit": "pi2"},
            },
        ]
        result = search_comparables(pool, max_items=2, subject=subject, date_reference="2026-04-28")
        self.assertEqual(result[0].comparable_id, "NEAR")

    def test_validate_schema_supports_nested_fields(self) -> None:
        ok, missing = validate_schema({"a": {"b": 1}}, ["a.b", "a.c"])
        self.assertFalse(ok)
        self.assertEqual(missing, ["a.c"])


if __name__ == "__main__":
    unittest.main()
