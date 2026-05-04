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

from outils.verifier_contrats_artefacts_agents_v0 import validate_agent_artifact_contracts


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_runtime_fixture(prefix: str) -> Path:
    root = writable_tmp_dir(prefix)
    runtime_dir = root / "runtime"
    shutil.copytree(PROJECT_ROOT / "tests" / "runtime", runtime_dir)

    summary = load_json(runtime_dir / "runtime_summary.json")
    assert isinstance(summary, list)
    for case in summary:
        if not isinstance(case, dict):
            continue
        case_name = Path(str(case.get("artifact_dir") or "")).name
        case_dir = runtime_dir / case_name
        case["artifact_dir"] = case_dir.as_posix()
        audit_name = Path(str(case.get("audit_log") or "")).name
        case["audit_log"] = (case_dir / audit_name).as_posix()
        for event in case.get("events", []):
            if not isinstance(event, dict):
                continue
            if event.get("event") == "artifact_written" and event.get("path"):
                event["path"] = (case_dir / Path(str(event["path"])).name).as_posix()
    write_json(runtime_dir / "runtime_summary.json", summary)
    return root


class TestContratsArtefactsAgentsV0(unittest.TestCase):
    def test_project_agent_artifact_contracts_are_ready(self) -> None:
        report = validate_agent_artifact_contracts(PROJECT_ROOT / "tests" / "runtime")

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["agents_checked"], 5)
        self.assertEqual(report["cases_count"], 8)
        self.assertGreaterEqual(report["artifacts_checked"], 100)
        self.assertGreaterEqual(report["artifacts_skipped"], 1)

    def test_detects_missing_expected_runtime_artifact(self) -> None:
        root = copy_runtime_fixture("agent_artifact_missing")
        try:
            runtime_dir = root / "runtime"
            (runtime_dir / "case_nominal" / "data-facts.timeline_faits.json").unlink()

            report = validate_agent_artifact_contracts(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("artefact attendu introuvable" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_detects_business_drift_on_non_review_case(self) -> None:
        root = copy_runtime_fixture("agent_artifact_business")
        try:
            runtime_dir = root / "runtime"
            artifact = runtime_dir / "case_nominal" / "comps-market.comparables_proposes.json"
            payload = load_json(artifact)
            assert isinstance(payload, dict)
            payload["comparables"] = []
            write_json(artifact, payload)

            report = validate_agent_artifact_contracts(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("comparables vide hors A_REVOIR" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_detects_status_drift_between_compliance_artifact_and_summary(self) -> None:
        root = copy_runtime_fixture("agent_artifact_status")
        try:
            runtime_dir = root / "runtime"
            artifact = runtime_dir / "case_nominal" / "compliance-qa.statut_sortie.json"
            payload = load_json(artifact)
            assert isinstance(payload, dict)
            payload["status"] = "BROUILLON"
            write_json(artifact, payload)

            report = validate_agent_artifact_contracts(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("status divergent du resume" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
