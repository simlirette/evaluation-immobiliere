from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import tempfile

from api import UI_PATH, load_ops_csv, load_ops_json, ops_summary, list_fixtures


class TestApiV0(unittest.TestCase):
    def test_list_fixtures_excludes_templates(self) -> None:
        fixtures = list_fixtures()
        names = {fixture["name"] for fixture in fixtures}
        self.assertIn("case_nominal.json", names)
        self.assertNotIn("template_dossier_anonymise.json", names)

    def test_ui_file_exists(self) -> None:
        self.assertTrue(UI_PATH.exists())

    def test_ops_summary_reads_generated_reports_from_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            (runtime_dir / "readiness_pre_reponses.json").write_text(
                json.dumps({"status": "PRET_A_RECEVOIR_REPONSES", "runtime_fingerprint_sha256": "abc"}),
                encoding="utf-8",
            )
            (runtime_dir / "quality_report.json").write_text(json.dumps({"cases_count": 3}), encoding="utf-8")
            (runtime_dir / "runtime_registry.json").write_text(json.dumps({"runs_count": 2}), encoding="utf-8")
            (runtime_dir / "FILE-REVUE-HUMAINE-V0.csv").write_text("id,priority\nREV-001,P1\n", encoding="utf-8")

            summary = ops_summary(runtime_dir)

        self.assertEqual(summary["readiness_status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(summary["quality_cases_count"], 3)
        self.assertEqual(summary["registry_runs_count"], 2)
        self.assertEqual(summary["review_queue_items"], 1)

    def test_load_ops_reports_mark_absent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)

            json_report = load_ops_json("readiness", runtime_dir)
            csv_report = load_ops_csv("review_queue", runtime_dir)

        self.assertEqual(json_report["status"], "ABSENT")
        self.assertEqual(csv_report["status"], "ABSENT")


if __name__ == "__main__":
    unittest.main()
