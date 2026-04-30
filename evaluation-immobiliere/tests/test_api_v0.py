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
    EVALUATOR_UI_PATH,
    OPS_UI_PATH,
    UI_PATH,
    RuntimeApiHandler,
    list_fixtures,
    load_ops_csv,
    load_ops_json,
    ops_summary,
    resume_session,
    session_artifacts,
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

    def test_evaluator_ui_file_exists(self) -> None:
        self.assertTrue(EVALUATOR_UI_PATH.exists())

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
            (runtime_dir / "ops_doctor_report.json").write_text(json.dumps({"status": "OK"}), encoding="utf-8")
            (runtime_dir / "FILE-REVUE-HUMAINE-V0.csv").write_text("id,priority\nREV-001,P1\n", encoding="utf-8")

            summary = ops_summary(runtime_dir)

        self.assertEqual(summary["readiness_status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(summary["delta_status"], "STABLE")
        self.assertEqual(summary["handoff_status"], "PRET_A_TRANSMETTRE")
        self.assertEqual(summary["schema_validation_status"], "OK")
        self.assertEqual(summary["package_gate_status"], "PRET_A_ENVOYER")
        self.assertEqual(summary["doctor_status"], "OK")
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
                blocked_status, blocked_raw = self.http_request("GET", host, port, "/fixtures")
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
                readiness = self.http_json("GET", host, port, "/ops/readiness")
                review_queue = self.http_json("GET", host, port, "/ops/review_queue")
                infra_contracts = self.http_json("GET", host, port, "/ops/infra_contracts")
                delta = self.http_json("GET", host, port, "/ops/delta")
                handoff = self.http_json("GET", host, port, "/ops/handoff")
                schemas = self.http_json("GET", host, port, "/ops/schema_validation")
                package_gate = self.http_json("GET", host, port, "/ops/package_gate")
                doctor = self.http_json("GET", host, port, "/ops/doctor")
                ops_ui = self.http_text("GET", host, port, "/ops/ui")
                evaluator_ui = self.http_text("GET", host, port, "/review/ui")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.OPS_RUNTIME_DIR = previous_runtime_dir

        self.assertEqual(ops["readiness_status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(readiness["status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(review_queue["rows_count"], 1)
        self.assertTrue(infra_contracts["ok"])
        self.assertEqual(delta["status"], "STABLE")
        self.assertEqual(handoff["status"], "PRET_A_TRANSMETTRE")
        self.assertEqual(schemas["status"], "OK")
        self.assertEqual(package_gate["status"], "PRET_A_ENVOYER")
        self.assertEqual(doctor["status"], "OK")
        self.assertIn("<title>Ops runtime immobilier</title>", ops_ui)
        self.assertIn("<title>Revue evaluateur</title>", evaluator_ui)

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
