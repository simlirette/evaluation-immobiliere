from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from outils.valider_contrats_runtime_v0 import validate_runtime_contracts


class TestValiderContratsRuntimeV0(unittest.TestCase):
    def test_validate_runtime_contracts_detects_invalid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            case_dir = runtime_dir / "case"
            case_dir.mkdir(parents=True, exist_ok=True)

            invalid = {
                "dossier_id": "D-1",
                "step": "comps-market",
                "artifact": "comparables_proposes.json",
                "source_fixture": "x.json",
                "date_reference": "2026-04-28",
                "comparables": [{"comparable_id": "C1", "score": 0.5}],
            }
            (case_dir / "comps-market.comparables_proposes.json").write_text(__import__("json").dumps(invalid), encoding="utf-8")

            report = validate_runtime_contracts(runtime_dir)
            self.assertFalse(report["ok"])
            self.assertEqual(report["files_checked"], 1)
            self.assertEqual(report["files_invalid"], 1)


if __name__ == "__main__":
    unittest.main()
