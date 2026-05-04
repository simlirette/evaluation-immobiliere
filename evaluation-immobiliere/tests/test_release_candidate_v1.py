from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from verifier_release_candidate_v1 import (  # noqa: E402
    MANIFEST_DEFAULT,
    build_rollback_markdown,
    build_staging_markdown,
    validate_release_candidate,
    write_outputs,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TestReleaseCandidateV1(unittest.TestCase):
    def test_project_release_candidate_is_ready_for_controlled_go_live(self) -> None:
        report = validate_release_candidate(MANIFEST_DEFAULT, strict=True)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["decision"], "PRET_GO_LIVE_CONTROLE")
        self.assertEqual(report["homologation_decision"], "GO_PROD_PREPARATION")
        self.assertEqual(report["closure_decision"], "GO_PROD_PREPARATION")
        self.assertGreaterEqual(report["staging_scenarios_count"], 3)
        self.assertIn("PRET_GO_LIVE_CONTROLE", build_staging_markdown(report))

    def test_missing_required_artifact_blocks_release_candidate(self) -> None:
        root = writable_tmp_dir("rc_missing_artifact")
        try:
            manifest = load_json(MANIFEST_DEFAULT)
            manifest["required_artifacts"] = ["evaluation-immobiliere/atelier/ABSENT-RC.md"]
            manifest_path = root / "manifest.json"
            write_json(manifest_path, manifest)

            report = validate_release_candidate(manifest_path, strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("artefact requis absent" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_no_go_homologation_blocks_release_candidate(self) -> None:
        root = writable_tmp_dir("rc_no_go")
        try:
            homologation = root / "homologation.json"
            write_json(homologation, {"ok": True, "production_decision": "NO_GO_PROD_PREPARATION"})

            report = validate_release_candidate(
                MANIFEST_DEFAULT,
                homologation_report_path=homologation,
                strict=True,
            )

            self.assertFalse(report["ok"])
            self.assertTrue(any("production_decision invalide" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_incomplete_rollback_runbook_blocks_release_candidate(self) -> None:
        root = writable_tmp_dir("rc_rollback")
        try:
            rollback = root / "rollback.md"
            rollback.write_text("# RUNBOOK ROLLBACK V1\n", encoding="utf-8")

            report = validate_release_candidate(MANIFEST_DEFAULT, rollback_runbook_path=rollback, strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("rollback runbook incomplet" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_write_outputs_writes_release_staging_and_rollback_reports(self) -> None:
        root = writable_tmp_dir("rc_outputs")
        try:
            report = validate_release_candidate(MANIFEST_DEFAULT, strict=True)
            json_out = root / "report.json"
            markdown_out = root / "report.md"
            staging_out = root / "staging.md"
            rollback_out = root / "rollback.md"

            write_outputs(report, json_out, markdown_out, staging_out, rollback_out)

            self.assertTrue(json_out.exists())
            self.assertIn("Release Candidate Evidence V1", markdown_out.read_text(encoding="utf-8"))
            self.assertIn("Rapport dress rehearsal staging V1", staging_out.read_text(encoding="utf-8"))
            self.assertIn("Rapport rollback rehearsal V1", rollback_out.read_text(encoding="utf-8"))
            self.assertIn("SIMULE_OK", build_rollback_markdown(report))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
