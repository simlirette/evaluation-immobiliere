from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from outils.simuler_runtime_engine_v0 import run_contract_validation


class TestSimulerRuntimeEngineV0(unittest.TestCase):
    def test_run_contract_validation_writes_report_and_fails_on_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            case_dir = runtime_dir / "case_x"
            case_dir.mkdir(parents=True, exist_ok=True)

            payload = {
                "dossier_id": "D-1",
                "step": "comps-market",
                "artifact": "comparables_proposes.json",
                "source_fixture": "f.json",
                "date_reference": "2026-04-28",
                "comparables": [{"comparable_id": "C1", "score": 0.9}],
            }
            (case_dir / "comps-market.comparables_proposes.json").write_text(json.dumps(payload), encoding="utf-8")

            report_path = runtime_dir / "contracts_report.json"
            ok = run_contract_validation(runtime_dir, report_path)
            self.assertFalse(ok)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertEqual(report["files_invalid"], 1)


if __name__ == "__main__":
    unittest.main()
