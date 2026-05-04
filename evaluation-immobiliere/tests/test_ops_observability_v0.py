from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from analyser_delta_runtime_v0 import build_delta_report, build_markdown as build_delta_markdown, generate_delta_report
from preparer_handoff_ops_v0 import HandoffFile, build_handoff_manifest, build_markdown as build_handoff_markdown


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestOpsObservabilityV0(unittest.TestCase):
    def test_delta_report_is_initial_without_registry_history(self) -> None:
        report = build_delta_report(
            {"cases_count": 1, "status_counts": {"BROUILLON": 1}, "totals": {"warnings": 1}},
            {},
        )
        markdown = build_delta_markdown(report)

        self.assertEqual(report["status"], "OBSERVATION_INITIALE")
        self.assertEqual(report["deltas"]["totals"]["warnings"], 1)
        self.assertIn("Rapport delta runtime", markdown)

    def test_delta_report_detects_regression_against_latest_registry_run(self) -> None:
        report = build_delta_report(
            {
                "cases_count": 2,
                "status_counts": {"BROUILLON": 1, "A_REVOIR": 1},
                "totals": {"blocking_failures": 2, "warnings": 3, "contract_errors": 1, "missing_artifacts": 2},
            },
            {
                "runs": [
                    {
                        "run_id": "RUN-OLD",
                        "cases_count": 2,
                        "status_counts": {"BROUILLON": 2},
                        "totals": {"blocking_failures": 1, "warnings": 3, "contract_errors": 0, "missing_artifacts": 2},
                    }
                ]
            },
        )

        self.assertEqual(report["status"], "A_CONTROLER")
        self.assertEqual(report["deltas"]["totals"]["blocking_failures"], 1)
        self.assertIn("status_counts.A_REVOIR", {item["metric"] for item in report["regressions"]})

    def test_generate_delta_report_writes_json_and_markdown(self) -> None:
        root = writable_tmp_dir("ops_delta")
        try:
            quality_path = root / "quality.json"
            registry_path = root / "registry.json"
            json_out = root / "delta.json"
            md_out = root / "delta.md"
            write_json(quality_path, {"cases_count": 1, "status_counts": {"BROUILLON": 1}, "totals": {"warnings": 0}})
            write_json(registry_path, {"runs": [{"run_id": "RUN-1", "cases_count": 1, "status_counts": {"BROUILLON": 1}, "totals": {"warnings": 0}}]})

            report = generate_delta_report(quality_path, registry_path, json_out, md_out)

            self.assertTrue(json_out.exists())
            self.assertTrue(md_out.exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(report["status"], "STABLE")

    def test_handoff_manifest_hashes_present_files_and_lists_missing_required(self) -> None:
        runtime_dir = writable_tmp_dir("ops_handoff")
        try:
            (runtime_dir / "quality_report.json").write_text('{"ok": true}', encoding="utf-8")
            files = [
                HandoffFile("quality", "quality_report.json", "quality"),
                HandoffFile("readiness", "readiness_pre_reponses.json", "readiness"),
                HandoffFile("optional", "infra_contracts_report.json", "contracts", required=False),
            ]

            manifest = build_handoff_manifest(runtime_dir, files)
            markdown = build_handoff_markdown(manifest)
        finally:
            shutil.rmtree(runtime_dir, ignore_errors=True)

        self.assertEqual(manifest["status"], "A_COMPLETER")
        self.assertEqual(manifest["required_present"], 1)
        self.assertEqual(manifest["required_missing"], ["readiness_pre_reponses.json"])
        self.assertTrue(manifest["files"][0]["sha256"])
        self.assertIn("Manifest handoff ops", markdown)


if __name__ == "__main__":
    unittest.main()
