from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from auditer_anonymisation_v0 import build_anonymization_audit
from executer_pre_reponses_v0 import (
    PreResponseLockError,
    acquire_lock,
    execute_pre_response_chain,
    read_lock,
    release_lock,
    run_steps,
    build_pre_response_steps,
)
from generer_file_revue_humaine_v0 import build_review_queue
from generer_knowledge_snapshot_v0 import build_knowledge_snapshot
from generer_manifest_runtime_v0 import build_markdown as build_manifest_markdown
from generer_manifest_runtime_v0 import build_runtime_manifest
from generer_registry_runtime_v0 import append_registry_entry, build_registry_entry
from valider_rapports_infra_v0 import build_infra_contract_report
from verifier_readiness_pre_reponses_v0 import build_markdown as build_readiness_markdown
from verifier_readiness_pre_reponses_v0 import build_readiness_report, package_status, run_readiness


def sample_quality_report() -> dict:
    return {
        "cases_count": 2,
        "status_counts": {"BROUILLON": 1, "A_REVOIR": 1},
        "totals": {
            "blocking_failures": 1,
            "warnings": 2,
            "contract_errors": 1,
            "missing_artifacts": 1,
        },
        "cases": [
            {
                "dossier_id": "D-001",
                "status": "BROUILLON",
                "blocking_failures": [],
                "warnings": ["W001: confiance faible"],
                "contract_errors": [],
                "artifacts": {"missing": []},
                "ingestion_pdf": {"review_flags": ["LOW_CONFIDENCE"], "trace_path": "trace.json"},
            },
            {
                "dossier_id": "D-002",
                "status": "A_REVOIR",
                "blocking_failures": ["CONF005: comparable hors fenetre"],
                "warnings": ["W002: comparable eloigne"],
                "contract_errors": [{"artifact": "comparables_proposes.json", "failures": ["CONF005"]}],
                "artifacts": {"missing": ["redaction.brouillon_rapport.md"]},
                "ingestion_pdf": {"review_flags": []},
            },
        ],
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class TestInfraPreReponsesV0(unittest.TestCase):
    def test_runtime_manifest_hashes_files_and_excludes_self_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            case_dir = runtime_dir / "case_001"
            case_dir.mkdir(parents=True)
            (case_dir / "artifact.json").write_text('{"ok": true}', encoding="utf-8")
            (runtime_dir / "runtime_summary.json").write_text("[{}]", encoding="utf-8")
            (runtime_dir / "runtime_manifest.json").write_text("old", encoding="utf-8")
            (runtime_dir / "runtime_delta_report.json").write_text("old", encoding="utf-8")
            (runtime_dir / "ops_handoff_manifest.json").write_text("old", encoding="utf-8")
            (runtime_dir / "schema_validation_report.json").write_text("old", encoding="utf-8")
            (runtime_dir / "paquet_evaluateurs_gate.json").write_text("old", encoding="utf-8")
            (runtime_dir / "ops_doctor_report.json").write_text("old", encoding="utf-8")

            manifest = build_runtime_manifest(runtime_dir)
            markdown = build_manifest_markdown(manifest)

        self.assertEqual(manifest["files_count"], 2)
        self.assertTrue(manifest["fingerprint_sha256"])
        self.assertEqual(manifest["runtime_cases"], 1)
        self.assertNotIn("runtime_manifest.json", [item["path"] for item in manifest["artifacts"]])
        self.assertIn("Manifest runtime", markdown)

    def test_readiness_report_is_ready_when_package_manifest_and_calibration_wait(self) -> None:
        report = build_readiness_report(
            sample_quality_report(),
            {"status": "PRET_A_RECEVOIR_REPONSES", "runtime_questions": [{}, {}]},
            {"fingerprint_sha256": "abc"},
            "PRET_A_ENVOYER",
        )
        markdown = build_readiness_markdown(report)

        self.assertEqual(report["status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(report["risks_to_calibrate"]["open_runtime_questions"], 2)
        self.assertIn("Readiness pre-reponses", markdown)

    def test_run_readiness_reads_package_index_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quality_path = root / "quality.json"
            calibration_path = root / "calibration.json"
            manifest_path = root / "manifest.json"
            package_index = root / "package.md"
            json_out = root / "readiness.json"
            md_out = root / "readiness.md"
            quality_path.write_text(json.dumps(sample_quality_report()), encoding="utf-8")
            calibration_path.write_text(json.dumps({"status": "PRET_A_RECEVOIR_REPONSES"}), encoding="utf-8")
            manifest_path.write_text(json.dumps({"fingerprint_sha256": "abc"}), encoding="utf-8")
            package_index.write_text("- Statut: **PRET_A_ENVOYER**\n", encoding="utf-8")

            report = run_readiness(quality_path, calibration_path, manifest_path, package_index, json_out, md_out)

            self.assertTrue(json_out.exists())
            self.assertTrue(md_out.exists())

        self.assertEqual(package_status(package_index), "PAQUET_ABSENT")
        self.assertEqual(report["status"], "PRET_A_RECEVOIR_REPONSES")

    def test_review_queue_promotes_runtime_signals_to_human_items(self) -> None:
        items = build_review_queue(sample_quality_report())
        targets = {item["target"] for item in items}

        self.assertTrue(any(item["priority"] == "P1" for item in items))
        self.assertIn("CONF005: comparable hors fenetre", targets)
        self.assertIn("redaction.brouillon_rapport.md", targets)
        self.assertIn("LOW_CONFIDENCE", targets)

    def test_anonymization_audit_detects_sensitive_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "case.json").write_text('{"contact": "personne@example.com", "adresse": "123 rue Test"}', encoding="utf-8")

            report = build_anonymization_audit([root])

        self.assertEqual(report["status"], "A_REVOIR_ANONYMISATION")
        self.assertEqual(report["findings_count"], 2)

    def test_anonymization_audit_accepts_masked_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "case.json").write_text('{"adresse": "[ADRESSE]", "telephone": "[NOM]"}', encoding="utf-8")

            report = build_anonymization_audit([root])

        self.assertEqual(report["status"], "OK")
        self.assertEqual(report["findings_count"], 0)

    def test_knowledge_snapshot_reconstructs_case_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "runtime"
            case_dir = runtime_dir / "case_001"
            case_dir.mkdir(parents=True)
            quality_path = runtime_dir / "quality_report.json"
            manifest_path = runtime_dir / "runtime_manifest.json"
            write_json(case_dir / "data-facts.fiche_bien.json", {"date_reference": "2026-04-28", "surface": {"value": 1000}})
            write_json(case_dir / "data-facts.timeline_faits.json", {"events": [{"type": "date_reference"}]})
            write_json(case_dir / "data-facts.source_index.json", {"sources": [{"source_id": "SRC-1"}]})
            write_json(case_dir / "comps-market.source_index.json", {"sources": [{"source_id": "SRC-2"}]})
            write_json(case_dir / "comps-market.comparables_proposes.json", {"comparables": [{"comparable_id": "C1"}]})
            write_json(case_dir / "comps-market.justifications_comparables.json", {"justifications": []})
            write_json(case_dir / "valuation-draft.calculs_approche_comparative.json", {"value": 100, "method": "m", "input_count": 1, "trace": {"ok": True}})
            write_json(case_dir / "valuation-draft.calculs_approche_cout.json", {"value": 100, "trace": {"ok": True}})
            write_json(case_dir / "valuation-draft.calculs_approche_revenu.json", {"value": 100, "trace": {"ok": True}})
            write_json(case_dir / "valuation-draft.hypotheses_explicites.json", {"hypotheses": []})
            write_json(case_dir / "compliance-qa.rapport_non_conformites.json", {"blocking_failures": [], "warnings": []})
            write_json(case_dir / "compliance-qa.statut_sortie.json", {"status": "BROUILLON"})
            write_json(
                quality_path,
                {
                    "cases": [
                        {
                            "case_name": "case_001",
                            "dossier_id": "D-001",
                            "status": "BROUILLON",
                            "artifact_dir": case_dir.as_posix(),
                            "blocking_failures": [],
                            "warnings": [],
                            "sourcing": {"sourced_field_rate": 1.0},
                            "comparables": {"average_score": 0.7},
                            "artifacts": {"missing": []},
                        }
                    ]
                },
            )
            write_json(manifest_path, {"fingerprint_sha256": "abc"})

            snapshot = build_knowledge_snapshot(runtime_dir, quality_path, manifest_path)

        self.assertEqual(snapshot["cases_count"], 1)
        case = snapshot["cases"][0]
        self.assertEqual(case["sources"]["source_ids"], ["SRC-1", "SRC-2"])
        self.assertEqual(case["market_evidence"]["average_score"], 0.7)
        self.assertTrue(case["valuation"]["approche_comparative"]["trace_present"])

    def test_pre_response_orchestrator_dry_run_lists_ordered_steps(self) -> None:
        steps = build_pre_response_steps(Path("evaluation-immobiliere"))
        report = run_steps(steps, cwd=Path("."), dry_run=True)

        self.assertTrue(report["ok"])
        self.assertEqual(report["steps"][0]["name"], "auditer_anonymisation")
        self.assertEqual(report["steps"][1]["name"], "preparer_ingestion_pdf")
        self.assertEqual(report["steps"][-1]["name"], "ops_doctor")
        self.assertIn("executer_dossiers_reels", [step["name"] for step in report["steps"]])
        self.assertIn("generer_knowledge_snapshot", [step["name"] for step in report["steps"]])
        self.assertIn("analyser_delta_runtime", [step["name"] for step in report["steps"]])
        self.assertIn("preparer_handoff_ops", [step["name"] for step in report["steps"]])
        self.assertIn("valider_schemas_ops", [step["name"] for step in report["steps"]])
        self.assertIn("valider_paquet_evaluateurs", [step["name"] for step in report["steps"]])
        self.assertIn("verifier_campagne_terrain_reelle", [step["name"] for step in report["steps"]])
        self.assertEqual(report["steps_count"], len(report["steps"]))
        self.assertIn("duration_seconds", report["steps"][0])

    def test_pre_response_lock_blocks_concurrent_execution_and_releases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_path = Path(tmp) / "runtime" / "pre_reponses.lock"

            lock = acquire_lock(lock_path, ttl_seconds=3600)
            with self.assertRaises(PreResponseLockError):
                acquire_lock(lock_path, ttl_seconds=3600)
            release_lock(lock_path)

        self.assertEqual(lock["status"], "RUNNING")
        self.assertFalse(lock_path.exists())

    def test_pre_response_lock_can_replace_stale_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock_path = Path(tmp) / "pre_reponses.lock"
            old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(microsecond=0).isoformat()
            lock_path.write_text(
                json.dumps({"schema_version": "pre_reponses_lock_v0", "acquired_at_utc": old_timestamp}),
                encoding="utf-8",
            )

            lock = acquire_lock(lock_path, ttl_seconds=60)
            payload = read_lock(lock_path)

        self.assertEqual(lock["status"], "RUNNING")
        self.assertEqual(payload["status"], "RUNNING")

    def test_pre_response_chain_dry_run_writes_report_without_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_path = root / "pre_reponses_run.json"
            lock_path = root / "pre_reponses.lock"

            report = execute_pre_response_chain(report_out=report_path, dry_run=True, lock_file=lock_path)

            self.assertTrue(report["ok"])
            self.assertTrue(report_path.exists())
            self.assertFalse(lock_path.exists())

    def test_runtime_registry_entry_captures_readiness_and_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            runtime_dir.mkdir()
            write_json(runtime_dir / "runtime_manifest.json", {"fingerprint_sha256": "abc"})
            write_json(runtime_dir / "quality_report.json", {"cases_count": 2, "status_counts": {"BROUILLON": 2}, "totals": {"warnings": 1}})
            write_json(runtime_dir / "calibration_evaluateurs.json", {"status": "PRET_A_RECEVOIR_REPONSES"})
            write_json(runtime_dir / "readiness_pre_reponses.json", {"status": "PRET_A_RECEVOIR_REPONSES"})
            write_json(runtime_dir / "pre_reponses_run.json", {"ok": True})

            entry = build_registry_entry(runtime_dir, timestamp_utc="2026-04-28T00:00:00+00:00", commit_sha="commit")
            registry = append_registry_entry(runtime_dir / "runtime_registry.json", entry)

        self.assertEqual(entry["runtime_fingerprint_sha256"], "abc")
        self.assertTrue(entry["pre_response_chain_ok"])
        self.assertEqual(registry["runs_count"], 1)
        self.assertEqual(registry["latest_run_id"], entry["run_id"])

    def test_infra_contract_report_validates_required_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            runtime_dir.mkdir()
            write_json(runtime_dir / "quality_report.json", {"schema_version": "runtime_quality_report_v0", "cases_count": 1, "status_counts": {}, "totals": {}, "cases": []})
            write_json(runtime_dir / "calibration_evaluateurs.json", {"schema_version": "calibration_evaluateurs_v0", "status": "PRET_A_RECEVOIR_REPONSES", "responses_count": 0, "cases": [], "backlog": []})
            write_json(runtime_dir / "runtime_manifest.json", {"schema_version": "runtime_manifest_v0", "fingerprint_sha256": "abc", "files_count": 1, "artifacts": []})
            write_json(runtime_dir / "readiness_pre_reponses.json", {"schema_version": "readiness_pre_reponses_v0", "status": "PRET_A_RECEVOIR_REPONSES", "checks": {}, "risks_to_calibrate": {}})
            write_json(runtime_dir / "knowledge_snapshot.json", {"schema_version": "knowledge_snapshot_v0", "runtime_fingerprint_sha256": "abc", "cases_count": 1, "cases": []})
            write_json(runtime_dir / "runtime_registry.json", {"schema_version": "runtime_registry_v0", "latest_run_id": "RUN", "runs_count": 1, "runs": []})
            write_json(runtime_dir / "runtime_delta_report.json", {"schema_version": "runtime_delta_report_v0", "status": "STABLE", "current": {}, "previous": {}, "deltas": {}, "regressions": []})
            write_json(runtime_dir / "ops_handoff_manifest.json", {"schema_version": "ops_handoff_manifest_v0", "status": "PRET_A_TRANSMETTRE", "files_count": 1, "required_missing": [], "files": []})

            report = build_infra_contract_report(runtime_dir)

        self.assertTrue(report["ok"])
        self.assertEqual(report["files_checked"], 8)


if __name__ == "__main__":
    unittest.main()
