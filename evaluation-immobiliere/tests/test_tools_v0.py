from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.tools import run_calculation, search_comparables, validate_schema


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

    def test_validate_schema_supports_nested_fields(self) -> None:
        ok, missing = validate_schema({"a": {"b": 1}}, ["a.b", "a.c"])
        self.assertFalse(ok)
        self.assertEqual(missing, ["a.c"])


if __name__ == "__main__":
    unittest.main()
