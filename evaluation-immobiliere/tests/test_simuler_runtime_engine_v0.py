from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from outils.simuler_runtime_engine_v0 import discover_runtime_fixture_paths, run_contract_validation

TEST_TMP_ROOT = Path(__file__).resolve().parents[2] / ".test-tmp" / "test_simuler_runtime_engine_v0"


def writable_tmp_dir(prefix: str) -> Path:
    root = TEST_TMP_ROOT / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestSimulerRuntimeEngineV0(unittest.TestCase):
    def test_discover_runtime_fixture_paths_excludes_real_pilot_fixtures(self) -> None:
        root = writable_tmp_dir("fixtures")
        try:
            fixtures_dir = root
            (fixtures_dir / "case_nominal.json").write_text("{}", encoding="utf-8")
            (fixtures_dir / "case_pilote_reel_001.json").write_text("{}", encoding="utf-8")

            names = [path.name for path in discover_runtime_fixture_paths(fixtures_dir)]
            self.assertEqual(names, ["case_nominal.json"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_run_contract_validation_writes_report_and_fails_on_invalid(self) -> None:
        root = writable_tmp_dir("contracts")
        try:
            runtime_dir = root / "runtime"
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
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
