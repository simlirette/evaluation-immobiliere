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

from outils.verifier_homologation_metier_v0 import validate_homologation_metier


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
            if isinstance(event, dict) and event.get("event") == "artifact_written" and event.get("path"):
                event["path"] = (case_dir / Path(str(event["path"])).name).as_posix()
    write_json(runtime_dir / "runtime_summary.json", summary)
    return root


class TestHomologationMetierV0(unittest.TestCase):
    def test_project_runtime_is_ready_for_synthetic_business_homologation(self) -> None:
        report = validate_homologation_metier(PROJECT_ROOT / "tests" / "runtime")

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["runtime_decision"], "PRET_HOMOLOGATION_SYNTHETIQUE_EN_ATTENTE_TERRAIN")
        self.assertEqual(report["production_decision"], "GO_PROD_PREPARATION")
        self.assertEqual(report["cases_count"], 8)
        self.assertEqual(report["pilot_cases_count"], 3)
        self.assertEqual(report["external_reviews"]["status"], "REVUES_TERRAIN_EXPLOITABLES")
        self.assertEqual(report["external_reviews"]["reviewed_pilot_cases"], 3)
        self.assertEqual(report["external_reviews"]["gap_counts_by_priority"]["P1"], 1)
        self.assertEqual(report["gap_closure"]["status"], "ECARTS_FERMES_SIGNATURES_SIGNEES")

    def test_detects_ready_case_without_redaction_artifacts(self) -> None:
        root = copy_runtime_fixture("homologation_redaction")
        try:
            runtime_dir = root / "runtime"
            (runtime_dir / "case_nominal" / "redaction.brouillon_rapport.md").unlink()

            report = validate_homologation_metier(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("artefacts de redaction absents" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_detects_draft_warning_not_documented_in_compliance_status(self) -> None:
        root = copy_runtime_fixture("homologation_warning")
        try:
            runtime_dir = root / "runtime"
            status_path = runtime_dir / "case_low_confidence" / "compliance-qa.statut_sortie.json"
            payload = load_json(status_path)
            assert isinstance(payload, dict)
            payload["warnings"] = []
            write_json(status_path, payload)

            report = validate_homologation_metier(runtime_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("warnings non reportes" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_require_external_reviews_blocks_when_field_reviews_are_absent(self) -> None:
        root = copy_runtime_fixture("homologation_external_required")
        try:
            runtime_dir = root / "runtime"
            missing_reviews = root / "missing_reviews.json"

            report = validate_homologation_metier(
                runtime_dir,
                external_reviews_path=missing_reviews,
                require_external_reviews=True,
            )

            self.assertFalse(report["ok"])
            self.assertTrue(any("revues evaluateurs absentes" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_valid_external_reviews_allow_conditional_signature_decision(self) -> None:
        root = copy_runtime_fixture("homologation_external_valid")
        try:
            runtime_dir = root / "runtime"
            reviews_path = root / "reviews.json"
            write_json(
                reviews_path,
                {
                    "schema_version": "homologation_evaluateur_reviews_v1",
                    "reviews": [
                        {"reviewer_id": "EV-1", "dossier_id": "D-PILOTE-RES-001", "decision": "ACCEPTE"},
                        {"reviewer_id": "EV-1", "dossier_id": "D-PILOTE-RES-002", "decision": "A_REVOIR"},
                        {"reviewer_id": "EV-2", "dossier_id": "D-PILOTE-RES-003", "decision": "A_REVOIR"},
                    ],
                },
            )

            report = validate_homologation_metier(
                runtime_dir,
                external_reviews_path=reviews_path,
                require_external_reviews=True,
                closure_register_path=root / "missing_register.json",
            )

            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["external_reviews"]["status"], "REVUES_TERRAIN_EXPLOITABLES")
            self.assertEqual(report["production_decision"], "GO_CONDITIONNEL_SIGNATURE_METIER")
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
