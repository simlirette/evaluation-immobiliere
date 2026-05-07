from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import http.client
import os
import tempfile
import threading
from http.server import ThreadingHTTPServer

import api
from api import (
    AUTH_CLIENT_PATH,
    EVALUATOR_UI_PATH,
    OPS_UI_PATH,
    PRODUCT_UI_PATH,
    UI_PATH,
    RuntimeApiHandler,
    assistant_message,
    assistant_workbench,
    dossier_review_summary,
    list_session_records,
    list_fixtures,
    load_ops_csv,
    load_ops_json,
    ops_observability_snapshot,
    ops_summary,
    product_summary,
    generate_v1_package_for_session,
    review_campaign_summary,
    review_workbench_summary,
    resume_session,
    save_review,
    session_package_summary,
    session_artifact_content,
    session_artifacts,
    session_summary,
    session_status,
    start_runtime,
)


class QuietRuntimeApiHandler(RuntimeApiHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class TestApiV0(unittest.TestCase):
    def test_list_fixtures_excludes_templates(self) -> None:
        fixtures = list_fixtures()
        names = {fixture["name"] for fixture in fixtures}
        self.assertIn("case_nominal.json", names)
        self.assertNotIn("template_dossier_anonymise.json", names)

    def test_ui_file_exists(self) -> None:
        self.assertTrue(UI_PATH.exists())

    def test_ops_ui_file_exists(self) -> None:
        self.assertTrue(OPS_UI_PATH.exists())

    def test_product_ui_file_exists(self) -> None:
        self.assertTrue(PRODUCT_UI_PATH.exists())

    def test_auth_client_file_exists(self) -> None:
        self.assertTrue(AUTH_CLIENT_PATH.exists())

    def test_evaluator_ui_file_exists(self) -> None:
        self.assertTrue(EVALUATOR_UI_PATH.exists())

    def test_product_summary_consolidates_runtime_project_and_routes(self) -> None:
        summary = product_summary()

        self.assertEqual(summary["schema_version"], "product_cockpit_summary_v1")
        self.assertTrue(summary["ok"])
        self.assertIn("PROD_BLOQUEE", summary["status"])
        self.assertTrue(summary["production_blocked"])
        self.assertGreaterEqual(summary["runtime"]["cases_count"], 1)
        self.assertGreaterEqual(summary["fixtures"]["count"], 1)
        self.assertEqual(summary["routes"]["product"], "/product")
        self.assertEqual(summary["routes"]["session_summary"], "/session/summary")
        self.assertEqual(summary["routes"]["artifact_content"], "/artifact")
        self.assertEqual(summary["routes"]["dossier_review"], "/review/dossier")
        self.assertEqual(summary["routes"]["ops_snapshot"], "/ops/snapshot")
        self.assertEqual(summary["routes"]["sessions"], "/sessions")
        self.assertEqual(summary["routes"]["review_workbench"], "/review/workbench")
        self.assertEqual(summary["routes"]["review_campaign"], "/review/campaign")
        self.assertEqual(summary["routes"]["review_package"], "/review/package")
        self.assertEqual(summary["routes"]["assistant_workbench"], "/assistant/workbench")
        self.assertEqual(summary["routes"]["assistant_message"], "/assistant/message")
        self.assertEqual(summary["ops_snapshot"]["schema_version"], "ops_observability_snapshot_v1")
        self.assertEqual(summary["review_campaign"]["schema_version"], "review_campaign_v1")
        self.assertEqual(summary["session_packages"]["schema_version"], "session_packages_summary_v1")
        self.assertIn("terrain", summary)
        self.assertIn("phase_h_gate_status", summary["ops"])
        self.assertIn("release_candidate_decision", summary)

    def test_ops_summary_reads_generated_reports_from_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            (runtime_dir / "readiness_pre_reponses.json").write_text(
                json.dumps({"status": "PRET_A_RECEVOIR_REPONSES", "runtime_fingerprint_sha256": "abc"}),
                encoding="utf-8",
            )
            (runtime_dir / "quality_report.json").write_text(json.dumps({"cases_count": 3}), encoding="utf-8")
            (runtime_dir / "runtime_registry.json").write_text(json.dumps({"runs_count": 2}), encoding="utf-8")
            (runtime_dir / "runtime_delta_report.json").write_text(json.dumps({"status": "STABLE"}), encoding="utf-8")
            (runtime_dir / "ops_handoff_manifest.json").write_text(json.dumps({"status": "PRET_A_TRANSMETTRE"}), encoding="utf-8")
            (runtime_dir / "schema_validation_report.json").write_text(json.dumps({"status": "OK"}), encoding="utf-8")
            (runtime_dir / "paquet_evaluateurs_gate.json").write_text(json.dumps({"status": "PRET_A_ENVOYER"}), encoding="utf-8")
            (runtime_dir / "phase_h_campagne_terrain_gate.json").write_text(
                json.dumps({"decision": "PRET_A_RECEVOIR_REPONSES_TERRAIN", "mode": "active", "active_cases_count": 3, "errors": []}),
                encoding="utf-8",
            )
            (runtime_dir / "ops_doctor_report.json").write_text(json.dumps({"status": "OK"}), encoding="utf-8")
            (runtime_dir / "FILE-REVUE-HUMAINE-V0.csv").write_text("id,priority\nREV-001,P1\n", encoding="utf-8")

            summary = ops_summary(runtime_dir)

        self.assertEqual(summary["readiness_status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(summary["delta_status"], "STABLE")
        self.assertEqual(summary["handoff_status"], "PRET_A_TRANSMETTRE")
        self.assertEqual(summary["schema_validation_status"], "OK")
        self.assertEqual(summary["package_gate_status"], "PRET_A_ENVOYER")
        self.assertEqual(summary["phase_h_gate_status"], "PRET_A_RECEVOIR_REPONSES_TERRAIN")
        self.assertEqual(summary["phase_h_active_cases_count"], 3)
        self.assertFalse(summary["waiting_for_real_inputs"])
        self.assertEqual(summary["doctor_status"], "OK")
        self.assertEqual(summary["quality_cases_count"], 3)
        self.assertEqual(summary["registry_runs_count"], 2)
        self.assertEqual(summary["review_queue_items"], 1)
        self.assertEqual(summary["blocking_counts"]["phase_h_errors"], 0)

    def test_ops_summary_surfaces_waiting_phase_h_without_runtime_cases(self) -> None:
        waiting = "EN_ATTENTE_ENTREES_TERRAIN_REELLES"
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            (runtime_dir / "readiness_pre_reponses.json").write_text(json.dumps({"status": waiting}), encoding="utf-8")
            (runtime_dir / "runtime_delta_report.json").write_text(json.dumps({"status": "STABLE"}), encoding="utf-8")
            (runtime_dir / "ops_handoff_manifest.json").write_text(
                json.dumps({"status": waiting, "required_missing_blocking": []}),
                encoding="utf-8",
            )
            (runtime_dir / "infra_contracts_report.json").write_text(json.dumps({"ok": True, "files_invalid_blocking": 0}), encoding="utf-8")
            (runtime_dir / "schema_validation_report.json").write_text(json.dumps({"status": waiting, "files_invalid_blocking": 0}), encoding="utf-8")
            (runtime_dir / "paquet_evaluateurs_gate.json").write_text(json.dumps({"status": waiting, "blocking_issues_count": 0}), encoding="utf-8")
            (runtime_dir / "phase_h_campagne_terrain_gate.json").write_text(
                json.dumps({"decision": waiting, "mode": "waiting", "active_cases_count": 0, "errors": []}),
                encoding="utf-8",
            )
            (runtime_dir / "ops_doctor_report.json").write_text(json.dumps({"status": waiting, "issues": []}), encoding="utf-8")

            summary = ops_summary(runtime_dir)

        self.assertTrue(summary["waiting_for_real_inputs"])
        self.assertEqual(summary["phase_h_gate_status"], waiting)
        self.assertEqual(summary["phase_h_active_cases_count"], 0)
        self.assertEqual(sum(summary["blocking_counts"].values()), 0)

    def test_ops_observability_snapshot_counts_present_missing_and_last_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            (runtime_dir / "readiness_pre_reponses.json").write_text(json.dumps({"status": "PRET_A_RECEVOIR_REPONSES"}), encoding="utf-8")
            (runtime_dir / "FILE-REVUE-HUMAINE-V0.csv").write_text("id,priority\nREV-001,P1\n", encoding="utf-8")
            (runtime_dir / "pre_reponses_run.json").write_text(
                json.dumps({"ok": True, "steps_count": 20, "failed_step": "", "duration_seconds": 1.25}),
                encoding="utf-8",
            )
            (runtime_dir / "pre_reponses.lock").write_text(json.dumps({"status": "RUNNING", "ttl_seconds": 3600}), encoding="utf-8")

            snapshot = ops_observability_snapshot(runtime_dir)

        self.assertEqual(snapshot["schema_version"], "ops_observability_snapshot_v1")
        self.assertEqual(snapshot["status"], "OBSERVABILITE_PARTIELLE")
        self.assertEqual(snapshot["present_reports_count"], 2)
        self.assertGreater(snapshot["missing_reports_count"], 0)
        self.assertTrue(snapshot["last_run"]["exists"])
        self.assertTrue(snapshot["last_run"]["ok"])
        self.assertTrue(snapshot["lock"]["active"])
        self.assertEqual(snapshot["next_action"], "EXECUTER_PRE_REPONSES")

    def test_load_ops_reports_mark_absent_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)

            json_report = load_ops_json("readiness", runtime_dir)
            csv_report = load_ops_csv("review_queue", runtime_dir)

        self.assertEqual(json_report["status"], "ABSENT")
        self.assertEqual(csv_report["status"], "ABSENT")

    def test_start_runtime_persists_resumeable_session_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime({"fixture": "case_nominal.json"})
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                resume = resume_session(session["session_id"])
                artifact_index_exists = Path(session["artifact_index_path"]).exists()
                knowledge_snapshot_exists = Path(session["knowledge_snapshot_path"]).exists()
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(result["status"], "PRET_REVISION_FINALE")
        self.assertEqual(result["events"][0]["session_id"], session["session_id"])
        self.assertEqual(result["events"][0]["run_id"], session["run_id"])
        self.assertTrue(result["events"][0]["event_id"].startswith(session["run_id"]))
        self.assertTrue(artifact_index_exists)
        self.assertTrue(knowledge_snapshot_exists)
        self.assertTrue(status["integrity"]["ok"])
        self.assertGreater(artifacts["artifacts_count"], 0)
        self.assertEqual(resume["resume"]["status"], "RESUME_READY")

    def test_session_http_status_artifacts_review_and_resume_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = self.http_json("POST", host, port, "/start", {"fixture": "case_nominal.json"})
                session_id = started["session"]["session_id"]
                status = self.http_json("GET", host, port, f"/status?session_id={session_id}")
                artifacts = self.http_json("GET", host, port, f"/artifacts?session_id={session_id}")
                review = self.http_json(
                    "POST",
                    host,
                    port,
                    "/review",
                    {"session_id": session_id, "decision": "PRET_REVUE", "reviewer": "QA Runtime"},
                )
                resumed = self.http_json("POST", host, port, "/resume", {"session_id": session_id})
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertTrue(status["integrity"]["ok"])
        self.assertGreater(artifacts["artifacts_count"], 0)
        self.assertEqual(review["review"]["decision"], "PRET_REVUE")
        self.assertEqual(resumed["resume"]["status"], "RESUME_READY")

    def test_rbac_token_and_access_audit_when_auth_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            previous_token = os.environ.get("EVAL_RUNTIME_API_TOKEN")
            api.SESSIONS_DIR = Path(tmp)
            os.environ["EVAL_RUNTIME_API_TOKEN"] = "secret-token"
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                health_status, _ = self.http_request("GET", host, port, "/health")
                auth_missing = self.http_json("GET", host, port, "/auth/status")
                blocked_status, blocked_raw = self.http_request("GET", host, port, "/fixtures")
                auth_allowed = self.http_json(
                    "GET",
                    host,
                    port,
                    "/auth/status",
                    headers={"Authorization": "Bearer secret-token", "X-Runtime-Role": "supervisor"},
                )
                allowed = self.http_json(
                    "GET",
                    host,
                    port,
                    "/fixtures",
                    headers={"Authorization": "Bearer secret-token", "X-Runtime-Role": "evaluator"},
                )
                forbidden_status, forbidden_raw = self.http_request(
                    "POST",
                    host,
                    port,
                    "/ops/pre-response-run",
                    {"dry_run": True},
                    headers={"Authorization": "Bearer secret-token", "X-Runtime-Role": "evaluator"},
                )
                audit_path = api.access_audit_path()
                audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir
                if previous_token is None:
                    os.environ.pop("EVAL_RUNTIME_API_TOKEN", None)
                else:
                    os.environ["EVAL_RUNTIME_API_TOKEN"] = previous_token

        self.assertEqual(health_status, 200)
        self.assertTrue(auth_missing["enabled"])
        self.assertFalse(auth_missing["authorized"])
        self.assertEqual(auth_missing["reason"], "token_missing")
        self.assertTrue(auth_allowed["authorized"])
        self.assertIn("ops_write", auth_allowed["permissions"])
        self.assertEqual(blocked_status, 401)
        self.assertEqual(json.loads(blocked_raw)["code"], "token_missing")
        self.assertIn("fixtures", allowed)
        self.assertEqual(forbidden_status, 403)
        self.assertEqual(json.loads(forbidden_raw)["code"], "RBAC_FORBIDDEN")
        self.assertTrue(any('"status": 401' in line for line in audit_lines))
        self.assertTrue(any('"status": 403' in line for line in audit_lines))

    def test_ops_http_endpoints_read_runtime_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            (runtime_dir / "readiness_pre_reponses.json").write_text(
                json.dumps({"status": "PRET_A_RECEVOIR_REPONSES", "runtime_fingerprint_sha256": "abc"}),
                encoding="utf-8",
            )
            (runtime_dir / "quality_report.json").write_text(json.dumps({"cases_count": 3}), encoding="utf-8")
            (runtime_dir / "runtime_registry.json").write_text(json.dumps({"runs_count": 2}), encoding="utf-8")
            (runtime_dir / "infra_contracts_report.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
            (runtime_dir / "runtime_delta_report.json").write_text(json.dumps({"status": "STABLE"}), encoding="utf-8")
            (runtime_dir / "ops_handoff_manifest.json").write_text(
                json.dumps({"status": "PRET_A_TRANSMETTRE", "required_present": 2, "required_count": 2, "required_missing": []}),
                encoding="utf-8",
            )
            (runtime_dir / "schema_validation_report.json").write_text(json.dumps({"status": "OK"}), encoding="utf-8")
            (runtime_dir / "paquet_evaluateurs_gate.json").write_text(json.dumps({"status": "PRET_A_ENVOYER"}), encoding="utf-8")
            (runtime_dir / "phase_h_campagne_terrain_gate.json").write_text(
                json.dumps({"decision": "PRET_A_RECEVOIR_REPONSES_TERRAIN", "mode": "active", "active_cases_count": 3, "errors": []}),
                encoding="utf-8",
            )
            (runtime_dir / "ops_doctor_report.json").write_text(json.dumps({"status": "OK", "issues": []}), encoding="utf-8")
            (runtime_dir / "FILE-REVUE-HUMAINE-V0.csv").write_text("id,priority\nREV-001,P1\n", encoding="utf-8")

            previous_runtime_dir = api.OPS_RUNTIME_DIR
            api.OPS_RUNTIME_DIR = runtime_dir
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                ops = self.http_json("GET", host, port, "/ops")
                ops_snapshot = self.http_json("GET", host, port, "/ops/snapshot")
                readiness = self.http_json("GET", host, port, "/ops/readiness")
                review_queue = self.http_json("GET", host, port, "/ops/review_queue")
                infra_contracts = self.http_json("GET", host, port, "/ops/infra_contracts")
                delta = self.http_json("GET", host, port, "/ops/delta")
                handoff = self.http_json("GET", host, port, "/ops/handoff")
                schemas = self.http_json("GET", host, port, "/ops/schema_validation")
                package_gate = self.http_json("GET", host, port, "/ops/package_gate")
                phase_h_gate = self.http_json("GET", host, port, "/ops/phase_h_gate")
                doctor = self.http_json("GET", host, port, "/ops/doctor")
                ops_ui = self.http_text("GET", host, port, "/ops/ui")
                evaluator_ui = self.http_text("GET", host, port, "/review/ui")
                product_ui = self.http_text("GET", host, port, "/product")
                runtime_ui = self.http_text("GET", host, port, "/ui")
                auth_client = self.http_text("GET", host, port, "/auth/client.js")
                product_summary_payload = self.http_json("GET", host, port, "/product/summary")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.OPS_RUNTIME_DIR = previous_runtime_dir

        self.assertEqual(ops["readiness_status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(ops_snapshot["schema_version"], "ops_observability_snapshot_v1")
        self.assertGreaterEqual(ops_snapshot["present_reports_count"], 1)
        self.assertEqual(readiness["status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(review_queue["rows_count"], 1)
        self.assertTrue(infra_contracts["ok"])
        self.assertEqual(delta["status"], "STABLE")
        self.assertEqual(handoff["status"], "PRET_A_TRANSMETTRE")
        self.assertEqual(schemas["status"], "OK")
        self.assertEqual(package_gate["status"], "PRET_A_ENVOYER")
        self.assertEqual(phase_h_gate["decision"], "PRET_A_RECEVOIR_REPONSES_TERRAIN")
        self.assertEqual(doctor["status"], "OK")
        self.assertIn("<title>Ops runtime immobilier</title>", ops_ui)
        self.assertIn("<title>Revue dossier</title>", evaluator_ui)
        self.assertIn("Sessions existantes", evaluator_ui)
        self.assertIn("Campagne revue", evaluator_ui)
        self.assertIn("generatePackage", evaluator_ui)
        self.assertIn("Fichiers paquet V1", evaluator_ui)
        self.assertIn("Gate paquet V1", evaluator_ui)
        self.assertIn("URLSearchParams(window.location.search)", evaluator_ui)
        self.assertIn("<title>Produit evaluation immobiliere</title>", product_ui)
        self.assertIn("reviewCampaign", product_ui)
        self.assertIn("generatePackage", product_ui)
        self.assertIn("RuntimeAuth.mount", product_ui)
        self.assertIn("openReview", product_ui)
        self.assertIn("external_evaluator_responses_included=false", product_ui)
        self.assertIn("Evaluateur AI", product_ui)
        self.assertIn("askAssistant", product_ui)
        self.assertIn("assistantWorkbench", product_ui)
        self.assertIn("/assistant/workbench", product_ui)
        self.assertIn("/assistant/message", product_ui)
        self.assertIn("/ops/snapshot", product_ui)
        self.assertIn("RuntimeAuth.mount", evaluator_ui)
        self.assertIn("RuntimeAuth.mount", ops_ui)
        self.assertIn("Phase H", ops_ui)
        self.assertIn("Terrain Phase H", product_ui)
        self.assertIn("RuntimeAuth.mount", runtime_ui)
        self.assertIn("window.RuntimeAuth", auth_client)
        self.assertEqual(product_summary_payload["schema_version"], "product_cockpit_summary_v1")
        self.assertIn("terrain", product_summary_payload)
        self.assertIn("review_campaign", product_summary_payload)
        self.assertIn("session_packages", product_summary_payload)

    def test_session_summary_and_artifact_content_are_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime({"fixture": "case_nominal.json"})
                session_id = started["session"]["session_id"]
                summary = session_summary(session_id)
                dossier_review = dossier_review_summary(session_id)
                first_artifact = summary["artifacts"]["artifacts"][0]
                content = session_artifact_content(session_id, event_id=first_artifact["event_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(summary["schema_version"], "session_summary_v1")
        self.assertTrue(summary["integrity"]["ok"])
        self.assertEqual(summary["result"]["status"], "PRET_REVISION_FINALE")
        self.assertEqual(content["schema_version"], "session_artifact_content_v1")
        self.assertEqual(content["session_id"], session_id)
        self.assertIn("text", content)
        self.assertFalse(content["truncated"])
        self.assertEqual(dossier_review["schema_version"], "dossier_review_summary_v1")
        self.assertEqual(dossier_review["comparables"]["count"], 1)
        self.assertEqual(dossier_review["coverage"]["missing_count"], 0)

    def test_assistant_message_answers_from_session_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime({"fixture": "case_nominal.json"})
                session_id = started["session"]["session_id"]
                answer = assistant_message(
                    {
                        "session_id": session_id,
                        "agent": "auto",
                        "message": "Explique la valeur et les comparables du dossier.",
                    }
                )
                supervisor = assistant_message(
                    {
                        "session_id": session_id,
                        "agent": "superviseur-evaluateur-ai",
                        "message": "Donne la synthese globale.",
                    }
                )
                session = api.load_session(session_id)
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(answer["schema_version"], "assistant_message_v1")
        self.assertEqual(answer["session_id"], session_id)
        self.assertIn(answer["agent"], {"comps-market", "valuation-draft"})
        self.assertFalse(answer["limits"]["external_evaluator_responses_included"])
        self.assertTrue(answer["limits"]["requires_human_validation"])
        self.assertIn("D-001", answer["answer"])
        self.assertGreaterEqual(answer["context_summary"]["artifacts_count"], 1)
        self.assertGreaterEqual(len(answer["citations"]), 3)
        self.assertEqual(session["assistant_messages_count"], 2)
        self.assertEqual(supervisor["agent"], "superviseur-evaluateur-ai")

    def test_assistant_workbench_exposes_agent_orchestration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime({"fixture": "case_nominal.json"})
                session_id = started["session"]["session_id"]
                before = assistant_workbench(session_id)
                assistant_message(
                    {
                        "session_id": session_id,
                        "agent": "compliance-qa",
                        "message": "Quels gates doivent etre valides avant le paquet?",
                    }
                )
                after = assistant_workbench(session_id)
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(before["schema_version"], "assistant_workbench_v1")
        self.assertEqual(before["session_id"], session_id)
        self.assertEqual(before["agents_count"], 5)
        self.assertEqual(before["supervisor"]["agent"], "superviseur-evaluateur-ai")
        self.assertFalse(before["limits"]["external_evaluator_responses_included"])
        self.assertFalse(before["limits"]["llm_native_agent_loop_connected"])
        self.assertIn("SAISIR_REVUE_INTERNE", {item["action"] for item in before["next_actions"]})
        self.assertTrue(all(item["agent_config"].endswith(".yaml") for item in before["agents"]))
        self.assertEqual(after["transcript"]["messages_count"], 1)
        self.assertEqual(after["transcript"]["latest_agent"], "compliance-qa")

    def test_review_workbench_lists_persisted_sessions_and_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                first = start_runtime({"fixture": "case_nominal.json"})
                second = start_runtime({"fixture": "case_low_confidence.json"})
                save_review(
                    {
                        "session_id": first["session"]["session_id"],
                        "decision": "VALIDE",
                        "reviewer": "QA produit",
                        "notes": "Validation interne sur fixture nominale.",
                    }
                )
                sessions = list_session_records()
                workbench = review_workbench_summary()
                campaign = review_campaign_summary()
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(len(sessions), 2)
        self.assertEqual(workbench["schema_version"], "review_workbench_summary_v1")
        self.assertEqual(campaign["schema_version"], "review_campaign_v1")
        self.assertFalse(campaign["external_evaluator_responses_included"])
        self.assertEqual(workbench["sessions_count"], 2)
        self.assertEqual(campaign["sessions_count"], 2)
        self.assertEqual(campaign["reviews_count"], 1)
        self.assertEqual(workbench["validated_count"], 1)
        self.assertEqual(campaign["validated_count"], 1)
        self.assertEqual(campaign["ready_for_package_count"], 1)
        self.assertEqual(workbench["pending_count"], 1)
        self.assertEqual(workbench["integrity_blocked_count"], 0)
        self.assertIn("VALIDE", workbench["decision_counts"])
        self.assertEqual({item["dossier_id"] for item in workbench["sessions"]}, {"D-001", "D-005"})
        self.assertTrue(all(item["artifacts_count"] > 0 for item in workbench["sessions"]))
        self.assertTrue(all(item["next_action"] for item in workbench["sessions"]))
        self.assertNotEqual(second["session"]["session_id"], first["session"]["session_id"])

    def test_v1_package_requires_validated_session_and_writes_local_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime({"fixture": "case_nominal.json"})
                session_id = started["session"]["session_id"]
                absent = session_package_summary(session_id)
                with self.assertRaisesRegex(ValueError, "internal_review_valide_required"):
                    generate_v1_package_for_session(session_id)
                save_review(
                    {
                        "session_id": session_id,
                        "decision": "VALIDE",
                        "reviewer": "QA produit",
                        "notes": "Validation interne avant paquet V1.",
                    }
                )
                package = generate_v1_package_for_session(session_id)
                loaded = session_package_summary(session_id)
                campaign = review_campaign_summary()
                manifest_path = Path(package["manifest_path"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

            self.assertEqual(absent["status"], "ABSENT")
            self.assertFalse(absent["gate"]["ok"])
            self.assertEqual(package["schema_version"], "session_package_v1")
            self.assertEqual(package["status"], "PRET_REVUE_EVALUATEUR_AGREE")
            self.assertTrue(package["gate"]["ok"])
            self.assertFalse(package["external_evaluator_responses_included"])
            self.assertTrue(manifest_path.exists())
            self.assertEqual(package["manifest"]["package_origin"], "validated_runtime_session")
            self.assertEqual(package["manifest"]["source_session_id"], session_id)
            self.assertEqual(package["manifest"]["internal_review_decision"], "VALIDE")
            self.assertFalse(package["manifest"]["external_evaluator_responses_included"])
            self.assertEqual(loaded["status"], "PRET_REVUE_EVALUATEUR_AGREE")
            self.assertEqual(campaign["package_generated_count"], 1)
            self.assertIn(session_id, campaign["package_session_ids"])

    def test_http_session_summary_artifact_and_review_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = self.http_json("POST", host, port, "/start", {"fixture": "case_nominal.json"})
                session_id = started["session"]["session_id"]
                summary = self.http_json("GET", host, port, f"/session/summary?session_id={session_id}")
                dossier_review = self.http_json("GET", host, port, f"/review/dossier?session_id={session_id}")
                event_id = summary["artifacts"]["artifacts"][0]["event_id"]
                artifact = self.http_json("GET", host, port, f"/artifact?session_id={session_id}&event_id={event_id}")
                invalid_status, invalid_raw = self.http_request(
                    "POST",
                    host,
                    port,
                    "/review",
                    {"session_id": session_id, "decision": "VALIDE", "reviewer": "QA produit"},
                )
                valid_review = self.http_json(
                    "POST",
                    host,
                    port,
                    "/review",
                    {
                        "session_id": session_id,
                        "decision": "VALIDE",
                        "reviewer": "QA produit",
                        "notes": "Validation produit sur fixture nominale.",
                    },
                )
                package = self.http_json("POST", host, port, "/review/package", {"session_id": session_id})
                package_get = self.http_json("GET", host, port, f"/review/package?session_id={session_id}")
                assistant = self.http_json(
                    "POST",
                    host,
                    port,
                    "/assistant/message",
                    {
                        "session_id": session_id,
                        "agent": "valuation-draft",
                        "message": "Explique la valeur proposee.",
                    },
                )
                assistant_workbench_payload = self.http_json("GET", host, port, f"/assistant/workbench?session_id={session_id}")
                sessions_payload = self.http_json("GET", host, port, "/sessions?limit=10")
                workbench_payload = self.http_json("GET", host, port, "/review/workbench")
                campaign_payload = self.http_json("GET", host, port, "/review/campaign")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(summary["schema_version"], "session_summary_v1")
        self.assertEqual(dossier_review["schema_version"], "dossier_review_summary_v1")
        self.assertEqual(dossier_review["valuation"]["approaches"][0]["value"], 510000.0)
        self.assertEqual(artifact["schema_version"], "session_artifact_content_v1")
        self.assertEqual(invalid_status, 400)
        self.assertIn("notes requises", json.loads(invalid_raw)["error"])
        self.assertEqual(valid_review["review"]["decision"], "VALIDE")
        self.assertEqual(package["status"], "PRET_REVUE_EVALUATEUR_AGREE")
        self.assertTrue(package["gate"]["ok"])
        self.assertEqual(package_get["status"], "PRET_REVUE_EVALUATEUR_AGREE")
        self.assertFalse(package_get["external_evaluator_responses_included"])
        self.assertEqual(assistant["schema_version"], "assistant_message_v1")
        self.assertEqual(assistant["agent"], "valuation-draft")
        self.assertIn("510000", assistant["answer"])
        self.assertFalse(assistant["limits"]["certification_automatic"])
        self.assertEqual(assistant_workbench_payload["schema_version"], "assistant_workbench_v1")
        self.assertEqual(assistant_workbench_payload["status"], "PRET_REVUE_EVALUATEUR_AGREE")
        self.assertEqual(assistant_workbench_payload["transcript"]["messages_count"], 1)
        self.assertIn("PREPARER_REVUE_EVALUATEUR_AGREE", {item["action"] for item in assistant_workbench_payload["next_actions"]})
        self.assertEqual(sessions_payload["schema_version"], "runtime_sessions_v1")
        self.assertEqual(sessions_payload["sessions_count"], 1)
        self.assertEqual(sessions_payload["sessions"][0]["review_decision"], "VALIDE")
        self.assertEqual(sessions_payload["sessions"][0]["package_status"], "PRET_REVUE_EVALUATEUR_AGREE")
        self.assertEqual(workbench_payload["schema_version"], "review_workbench_summary_v1")
        self.assertEqual(workbench_payload["validated_count"], 1)
        self.assertEqual(campaign_payload["schema_version"], "review_campaign_v1")
        self.assertEqual(campaign_payload["ready_for_package_count"], 1)
        self.assertEqual(campaign_payload["package_generated_count"], 1)
        self.assertFalse(campaign_payload["external_evaluator_responses_included"])

    def test_product_demo_endpoint_runs_default_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                payload = self.http_json("POST", host, port, "/product/demo", {})
                session_id = payload["session"]["session_id"]
                status = self.http_json("GET", host, port, f"/status?session_id={session_id}")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(payload["result"]["status"], "PRET_REVISION_FINALE")
        self.assertTrue(status["integrity"]["ok"])

    def test_ops_http_pre_response_dry_run_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp)
            previous_runtime_dir = api.OPS_RUNTIME_DIR
            api.OPS_RUNTIME_DIR = runtime_dir
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                payload = self.http_json("POST", host, port, "/ops/pre-response-run", {"dry_run": True})
                self.assertTrue((runtime_dir / "pre_reponses_run.json").exists())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.OPS_RUNTIME_DIR = previous_runtime_dir

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["steps"][0]["status"], "DRY_RUN")

    def http_json(
        self,
        method: str,
        host: str,
        port: int,
        path: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        status, raw = self.http_request(method, host, port, path, body, headers)
        self.assertEqual(status, 200)
        return json.loads(raw)

    def http_text(
        self,
        method: str,
        host: str,
        port: int,
        path: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        status, raw = self.http_request(method, host, port, path, body, headers)
        self.assertEqual(status, 200)
        return raw

    def http_request(
        self,
        method: str,
        host: str,
        port: int,
        path: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        encoded = None if body is None else json.dumps(body).encode("utf-8")
        request_headers = {"Content-Type": "application/json"} if encoded else {}
        request_headers.update(headers or {})
        connection = http.client.HTTPConnection(host, port, timeout=10)
        try:
            connection.request(method, path, encoded, request_headers)
            response = connection.getresponse()
            raw = response.read().decode("utf-8")
            return response.status, raw
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
