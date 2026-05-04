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

from outils.verifier_preuve_runtime_skills_v0 import validate_runtime_skill_evidence


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def copy_runtime_fixture(prefix: str) -> Path:
    root = writable_tmp_dir(prefix)
    runtime_dir = root / "runtime"
    shutil.copytree(PROJECT_ROOT / "tests" / "runtime", runtime_dir)
    summary = load_summary(runtime_dir)
    for case in summary:
        case_name = Path(str(case.get("artifact_dir") or "")).name
        case_dir = runtime_dir / case_name
        audit_name = Path(str(case.get("audit_log") or "")).name
        case["artifact_dir"] = case_dir.as_posix()
        case["audit_log"] = (case_dir / audit_name).as_posix()
        audit_path = case_dir / audit_name
        if audit_path.exists():
            events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for event in events:
                if event.get("event") == "artifact_written" and event.get("path"):
                    event["path"] = (case_dir / Path(str(event["path"])).name).as_posix()
            audit_path.write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n", encoding="utf-8")
    write_summary(runtime_dir, summary)
    return root


def load_summary(runtime_dir: Path) -> list[dict]:
    return json.loads((runtime_dir / "runtime_summary.json").read_text(encoding="utf-8"))


def write_summary(runtime_dir: Path, summary: list[dict]) -> None:
    (runtime_dir / "runtime_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TestPreuveRuntimeSkillsV0(unittest.TestCase):
    def test_project_runtime_skills_evidence_is_ready(self) -> None:
        report = validate_runtime_skill_evidence(PROJECT_ROOT / "tests" / "runtime")

        self.assertTrue(report["ok"], report["errors"])
        self.assertGreaterEqual(report["cases_count"], 1)
        self.assertGreaterEqual(report["audit_logs_checked"], 1)
        self.assertGreaterEqual(report["step_events_checked"], 5)
        self.assertGreaterEqual(report["artifacts_checked"], 10)

    def test_detects_missing_skills_allowed_in_audit_step_start(self) -> None:
        root = copy_runtime_fixture("runtime_skills_audit")
        try:
            runtime_dir = root / "runtime"
            summary = load_summary(runtime_dir)
            audit_path = root / Path(summary[0]["audit_log"])
            events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            for event in events:
                if event.get("event") == "step_start":
                    event.pop("skills_allowed", None)
                    break
            audit_path.write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n", encoding="utf-8")

            report = validate_runtime_skill_evidence(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("skills_allowed audit divergents" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_detects_summary_skills_by_agent_drift(self) -> None:
        root = copy_runtime_fixture("runtime_skills_summary")
        try:
            runtime_dir = root / "runtime"
            summary = load_summary(runtime_dir)
            summary[0]["skills_by_agent"]["redaction"] = []
            write_summary(runtime_dir, summary)

            report = validate_runtime_skill_evidence(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("skills_by_agent divergent" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_detects_json_artifact_skill_context_drift(self) -> None:
        root = copy_runtime_fixture("runtime_skills_artifact")
        try:
            runtime_dir = root / "runtime"
            summary = load_summary(runtime_dir)
            artifact_dir = root / Path(summary[0]["artifact_dir"])
            artifact_path = next(artifact_dir.glob("data-facts.*.json"))
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            payload["agent_skills_allowed"] = []
            artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            report = validate_runtime_skill_evidence(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("agent_skills_allowed artefact divergent" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
