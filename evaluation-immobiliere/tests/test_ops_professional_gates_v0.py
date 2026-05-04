from __future__ import annotations

import csv
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from ops_doctor_v0 import build_ops_doctor_report, exit_code
from valider_paquet_evaluateurs_v0 import REQUIRED_FILES, build_paquet_gate_report
from valider_schemas_ops_v0 import SchemaTarget, build_schema_validation_report, validate_schema


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, header: list[str], rows: list[list[str]] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows or [])


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestOpsProfessionalGatesV0(unittest.TestCase):
    def test_schema_validator_reports_required_and_const_failures(self) -> None:
        failures = validate_schema(
            {"schema_version": "wrong"},
            {"type": "object", "required": ["schema_version", "status"], "properties": {"schema_version": {"const": "expected"}}},
        )

        self.assertIn("$:REQUIRED:status", failures)
        self.assertIn("$.schema_version:CONST:expected", failures)

    def test_schema_validation_report_checks_target_file(self) -> None:
        root = writable_tmp_dir("schema_gate")
        try:
            runtime_dir = root / "runtime"
            schemas_dir = root / "schemas"
            write_json(runtime_dir / "report.json", {"schema_version": "sample_v0", "status": "OK"})
            write_json(
                schemas_dir / "sample.schema.json",
                {"type": "object", "required": ["schema_version", "status"], "properties": {"schema_version": {"const": "sample_v0"}}},
            )

            report = build_schema_validation_report(
                runtime_dir,
                schemas_dir,
                [SchemaTarget("sample", "report.json", "sample.schema.json")],
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(report["status"], "OK")
        self.assertEqual(report["files_checked"], 1)

    def test_schema_validation_report_allows_missing_quality_while_waiting_for_real_inputs(self) -> None:
        root = writable_tmp_dir("schema_gate_waiting")
        try:
            runtime_dir = root / "runtime"
            schemas_dir = root / "schemas"
            write_json(runtime_dir / "readiness_pre_reponses.json", {"status": "EN_ATTENTE_ENTREES_TERRAIN_REELLES"})
            write_json(runtime_dir / "ops_handoff_manifest.json", {"status": "EN_ATTENTE_ENTREES_TERRAIN_REELLES"})
            write_json(
                schemas_dir / "quality.schema.json",
                {"type": "object", "required": ["schema_version"]},
            )

            report = build_schema_validation_report(
                runtime_dir,
                schemas_dir,
                [SchemaTarget("quality", "quality_report.json", "quality.schema.json")],
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(report["status"], "EN_ATTENTE_ENTREES_TERRAIN_REELLES")
        self.assertEqual(report["files_invalid"], 1)
        self.assertEqual(report["files_invalid_blocking"], 0)

    def test_package_gate_accepts_ready_package(self) -> None:
        root = writable_tmp_dir("package_ready")
        try:
            runtime_dir = root / "runtime"
            package_dir = root / "package"
            atelier_dir = root / "atelier"
            response_header = ["respondant_id", "role", "segment"]
            calibration_header = ["respondant_id", "role", "dossier_id"]
            write_json(runtime_dir / "runtime_summary.json", [{"dossier_id": "D-001"}])
            write_json(runtime_dir / "anonymisation_audit.json", {"status": "OK"})
            (package_dir / "PAQUET-EVALUATEURS-V0.md").parent.mkdir(parents=True)
            (package_dir / "PAQUET-EVALUATEURS-V0.md").write_text("- Statut: **PRET_A_ENVOYER**\n", encoding="utf-8")
            (package_dir / "CHECKLIST-ENVOI-EVALUATEURS.md").write_text("# Checklist\n", encoding="utf-8")
            write_csv(package_dir / "MANIFESTE-CAS-PILOTES.csv", ["cas", "dossier_id", "statut_runtime", "blocages", "warnings", "artefacts"], [["case", "D-001", "BROUILLON", "0", "0", "runtime/case"]])
            write_csv(package_dir / "REPONSES-EVALUATEURS-A-REMPLIR.csv", response_header)
            write_csv(package_dir / "CALIBRATION-EVALUATEURS-A-REMPLIR.csv", calibration_header)
            write_csv(atelier_dir / "REPONSES-EVALUATEURS-TEMPLATE.csv", response_header)
            write_csv(atelier_dir / "CALIBRATION-EVALUATEURS-TEMPLATE.csv", calibration_header)

            report = build_paquet_gate_report(package_dir, runtime_dir, atelier_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(report["status"], "PRET_A_ENVOYER")
        self.assertEqual(report["issues"], [])

    def test_package_gate_waits_for_real_inputs_when_package_is_structurally_ready(self) -> None:
        root = writable_tmp_dir("package_waiting")
        try:
            runtime_dir = root / "runtime"
            package_dir = root / "package"
            atelier_dir = root / "atelier"
            response_header = ["respondant_id", "role", "segment"]
            calibration_header = ["respondant_id", "role", "dossier_id"]
            write_json(runtime_dir / "anonymisation_audit.json", {"status": "OK"})
            package_dir.mkdir()
            (package_dir / "PAQUET-EVALUATEURS-V0.md").write_text("- Statut: **EN_ATTENTE_DOSSIERS_REELS**\n", encoding="utf-8")
            (package_dir / "CHECKLIST-ENVOI-EVALUATEURS.md").write_text("# Checklist\n", encoding="utf-8")
            write_csv(package_dir / "MANIFESTE-CAS-PILOTES.csv", ["cas", "dossier_id", "statut_runtime", "blocages", "warnings", "artefacts"])
            write_csv(package_dir / "REPONSES-EVALUATEURS-A-REMPLIR.csv", response_header)
            write_csv(package_dir / "CALIBRATION-EVALUATEURS-A-REMPLIR.csv", calibration_header)
            write_csv(atelier_dir / "REPONSES-EVALUATEURS-TEMPLATE.csv", response_header)
            write_csv(atelier_dir / "CALIBRATION-EVALUATEURS-TEMPLATE.csv", calibration_header)

            report = build_paquet_gate_report(package_dir, runtime_dir, atelier_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(report["status"], "EN_ATTENTE_ENTREES_TERRAIN_REELLES")
        self.assertEqual(report["blocking_issues_count"], 0)
        self.assertIn("PACKAGE_WAITING_REAL_INPUTS", {item["code"] for item in report["issues"]})

    def test_package_gate_rejects_sensitive_package_content(self) -> None:
        root = writable_tmp_dir("package_sensitive")
        try:
            runtime_dir = root / "runtime"
            package_dir = root / "package"
            atelier_dir = root / "atelier"
            write_json(runtime_dir / "runtime_summary.json", [])
            write_json(runtime_dir / "anonymisation_audit.json", {"status": "OK"})
            package_dir.mkdir()
            for filename in REQUIRED_FILES:
                (package_dir / filename).write_text("- Statut: **PRET_A_ENVOYER**\nC:\\Users\\simon\\secret\n", encoding="utf-8")

            report = build_paquet_gate_report(package_dir, runtime_dir, atelier_dir)
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(report["status"], "A_CORRIGER")
        self.assertIn("SENSITIVE_PATTERN", {item["code"] for item in report["issues"]})

    def test_ops_doctor_returns_ok_when_all_gates_are_ready(self) -> None:
        runtime_dir = writable_tmp_dir("ops_doctor_ok")
        try:
            write_json(runtime_dir / "readiness_pre_reponses.json", {"status": "PRET_A_RECEVOIR_REPONSES"})
            write_json(runtime_dir / "runtime_delta_report.json", {"status": "STABLE"})
            write_json(runtime_dir / "ops_handoff_manifest.json", {"status": "PRET_A_TRANSMETTRE"})
            write_json(runtime_dir / "infra_contracts_report.json", {"ok": True})
            write_json(runtime_dir / "schema_validation_report.json", {"status": "OK"})
            write_json(runtime_dir / "paquet_evaluateurs_gate.json", {"status": "PRET_A_ENVOYER"})
            write_json(runtime_dir / "anonymisation_audit.json", {"status": "OK"})
            write_csv(runtime_dir / "FILE-REVUE-HUMAINE-V0.csv", ["id", "priority"])

            report = build_ops_doctor_report(runtime_dir)
        finally:
            shutil.rmtree(runtime_dir, ignore_errors=True)

        self.assertEqual(report["status"], "OK")
        self.assertEqual(exit_code(report["status"]), 0)

    def test_ops_doctor_returns_waiting_when_all_gates_wait_for_real_inputs(self) -> None:
        runtime_dir = writable_tmp_dir("ops_doctor_waiting")
        try:
            write_json(runtime_dir / "readiness_pre_reponses.json", {"status": "EN_ATTENTE_ENTREES_TERRAIN_REELLES"})
            write_json(runtime_dir / "runtime_delta_report.json", {"status": "STABLE"})
            write_json(runtime_dir / "ops_handoff_manifest.json", {"status": "EN_ATTENTE_ENTREES_TERRAIN_REELLES"})
            write_json(runtime_dir / "infra_contracts_report.json", {"ok": True})
            write_json(runtime_dir / "schema_validation_report.json", {"status": "EN_ATTENTE_ENTREES_TERRAIN_REELLES"})
            write_json(runtime_dir / "paquet_evaluateurs_gate.json", {"status": "EN_ATTENTE_ENTREES_TERRAIN_REELLES"})
            write_json(runtime_dir / "anonymisation_audit.json", {"status": "OK"})

            report = build_ops_doctor_report(runtime_dir)
        finally:
            shutil.rmtree(runtime_dir, ignore_errors=True)

        self.assertEqual(report["status"], "EN_ATTENTE_ENTREES_TERRAIN_REELLES")
        self.assertEqual(report["issues"], [])
        self.assertEqual(exit_code(report["status"]), 0)

    def test_ops_doctor_escalates_correction_failures(self) -> None:
        runtime_dir = writable_tmp_dir("ops_doctor_fail")
        try:
            write_json(runtime_dir / "readiness_pre_reponses.json", {"status": "PRET_A_RECEVOIR_REPONSES"})
            write_json(runtime_dir / "runtime_delta_report.json", {"status": "STABLE"})
            write_json(runtime_dir / "ops_handoff_manifest.json", {"status": "PRET_A_TRANSMETTRE"})
            write_json(runtime_dir / "infra_contracts_report.json", {"ok": False, "files_invalid": 1})
            write_json(runtime_dir / "schema_validation_report.json", {"status": "OK"})
            write_json(runtime_dir / "paquet_evaluateurs_gate.json", {"status": "PRET_A_ENVOYER"})
            write_json(runtime_dir / "anonymisation_audit.json", {"status": "OK"})

            report = build_ops_doctor_report(runtime_dir)
        finally:
            shutil.rmtree(runtime_dir, ignore_errors=True)

        self.assertEqual(report["status"], "A_CORRIGER")
        self.assertEqual(exit_code(report["status"]), 2)


if __name__ == "__main__":
    unittest.main()
