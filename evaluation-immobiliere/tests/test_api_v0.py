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
import py_compile
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
    app_state,
    app_start_demo,
    app_validate_review,
    assistant_message,
    assistant_workbench,
    beta_ea_readiness,
    beta_start_dossier,
    dossier_review_summary,
    execute_session_slash_command,
    list_session_records,
    list_fixtures,
    load_ops_csv,
    load_ops_json,
    ops_observability_snapshot,
    ops_summary,
    product_summary,
    generate_v1_package_for_session,
    knowledge_immobilier_summary,
    review_campaign_summary,
    review_workbench_summary,
    resume_session,
    save_review,
    session_package_summary,
    session_artifact_lineage,
    session_agents,
    session_agent_prompts,
    session_artifact_content,
    session_artifacts,
    session_claude_action,
    session_claude_bundle,
    session_commands,
    session_command_history,
    session_handoffs,
    session_hooks,
    session_live_replay,
    session_model_client,
    session_permissions,
    session_provider_diagnostics,
    session_runtime_state,
    session_settings,
    session_skills,
    session_summary,
    session_tasks,
    session_tools,
    session_transcript,
    session_status,
    start_runtime,
    update_session_permissions,
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
        html = PRODUCT_UI_PATH.read_text(encoding="utf-8")
        self.assertIn("/session/claude", html)
        self.assertIn("/session/claude/action", html)
        self.assertIn("/session/claude/action/snapshot", html)
        self.assertIn("/session/artifact-lineage", html)
        self.assertIn("/session/runtime-state", html)
        self.assertIn("/session/agents", html)
        self.assertIn("/session/agent-prompts", html)
        self.assertIn("/session/live-replay", html)
        self.assertIn("/session/provider-diagnostics", html)
        self.assertIn("/session/skills", html)
        self.assertIn("/session/settings", html)
        self.assertIn("/session/handoffs", html)
        self.assertIn("/session/command-history", html)
        self.assertIn("claudeBundle.summary", html)
        self.assertIn("claudeActions", html)
        self.assertIn("claudeActionSnapshot", html)
        self.assertIn("claudeLineage", html)
        self.assertIn("claudeRuntimeState", html)
        self.assertIn("claudeAgentManifest", html)
        self.assertIn("claudeAgentPrompts", html)
        self.assertIn("claudeSkills", html)
        self.assertIn("claudeSettings", html)
        self.assertIn("claudeHandoffs", html)
        self.assertIn("claudeCommandHistory", html)
        self.assertIn("openClaudeActionSnapshot", html)
        self.assertIn("claudeCommand", html)
        self.assertIn("runClaudeCommand", html)
        self.assertIn("refreshClaudeController", html)
        self.assertIn("applyClaudePermission", html)
        self.assertIn("postClaudeControllerAction", html)

    def test_claude_live_provider_smoke_harness_and_runbook_exist(self) -> None:
        harness = PROJECT_ROOT / "outils" / "claude_live_provider_smoke_v0.py"
        runbook = PROJECT_ROOT / "integration" / "CLAUDE-LIVE-PROVIDER-SMOKE-RUNBOOK.md"
        self.assertTrue(harness.exists())
        self.assertTrue(runbook.exists())
        py_compile.compile(str(harness), doraise=True)
        harness_text = harness.read_text(encoding="utf-8")
        runbook_text = runbook.read_text(encoding="utf-8")
        self.assertIn("EVAL_IMMO_RUN_LIVE_SMOKE", harness_text)
        self.assertIn("--execute", harness_text)
        self.assertIn("diagnostics-only", runbook_text)
        self.assertIn("/session/live-replay", runbook_text)

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
        self.assertEqual(summary["routes"]["knowledge_immobilier"], "/knowledge/immobilier")
        self.assertEqual(summary["routes"]["assistant_workbench"], "/assistant/workbench")
        self.assertEqual(summary["routes"]["assistant_message"], "/assistant/message")
        self.assertEqual(summary["routes"]["app_state"], "/app/state")
        self.assertEqual(summary["routes"]["app_demo"], "/app/demo")
        self.assertEqual(summary["routes"]["app_message"], "/app/message")
        self.assertEqual(summary["routes"]["app_validate_review"], "/app/review/validate")
        self.assertEqual(summary["routes"]["app_package"], "/app/package")
        self.assertEqual(summary["routes"]["session_claude"], "/session/claude")
        self.assertEqual(summary["routes"]["session_claude_action"], "/session/claude/action")
        self.assertEqual(summary["routes"]["session_claude_action_snapshot"], "/session/claude/action/snapshot")
        self.assertEqual(summary["routes"]["session_command"], "/session/command")
        self.assertEqual(summary["routes"]["session_commands"], "/session/commands")
        self.assertEqual(summary["routes"]["session_command_history"], "/session/command-history")
        self.assertEqual(summary["routes"]["session_agent_prompts"], "/session/agent-prompts")
        self.assertEqual(summary["routes"]["session_model_client"], "/session/model-client")
        self.assertEqual(summary["routes"]["session_live_replay"], "/session/live-replay")
        self.assertEqual(summary["routes"]["session_provider_diagnostics"], "/session/provider-diagnostics")
        self.assertEqual(summary["routes"]["session_skills"], "/session/skills")
        self.assertEqual(summary["routes"]["session_settings"], "/session/settings")
        self.assertEqual(summary["routes"]["session_handoffs"], "/session/handoffs")
        self.assertEqual(summary["routes"]["session_hooks"], "/session/hooks")
        self.assertEqual(summary["routes"]["session_permissions"], "/session/permissions")
        self.assertEqual(summary["routes"]["session_tasks"], "/session/tasks")
        self.assertEqual(summary["routes"]["session_tools"], "/session/tools")
        self.assertEqual(summary["routes"]["session_transcript"], "/session/transcript")
        self.assertEqual(summary["ops_snapshot"]["schema_version"], "ops_observability_snapshot_v1")
        self.assertEqual(summary["review_campaign"]["schema_version"], "review_campaign_v1")
        self.assertEqual(summary["session_packages"]["schema_version"], "session_packages_summary_v1")
        self.assertIn("terrain", summary)
        self.assertIn("phase_h_gate_status", summary["ops"])
        self.assertIn("release_candidate_decision", summary)

    def test_app_state_exposes_frontend_ready_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = app_start_demo({"fixture": "case_pilote_residentiel_standard.json"})
                session_id = started["state"]["active_session_id"]
                state = app_state(session_id)
                validated = app_validate_review({"session_id": session_id})
                refreshed = validated["state"]
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(state["schema_version"], "evaluateur_ai_app_state_v1")
        self.assertEqual(state["status"], "PRET_APP_PRODUIT")
        self.assertEqual(state["routes"]["claude"], "/session/claude")
        self.assertEqual(state["routes"]["claude_action"], "/session/claude/action")
        self.assertEqual(state["routes"]["claude_action_snapshot"], "/session/claude/action/snapshot")
        self.assertEqual(state["routes"]["artifact_lineage"], "/session/artifact-lineage")
        self.assertEqual(state["routes"]["runtime_state"], "/session/runtime-state")
        self.assertEqual(state["routes"]["agents"], "/session/agents")
        self.assertEqual(state["routes"]["agent_prompts"], "/session/agent-prompts")
        self.assertEqual(state["routes"]["model_client"], "/session/model-client")
        self.assertEqual(state["routes"]["live_replay"], "/session/live-replay")
        self.assertEqual(state["routes"]["provider_diagnostics"], "/session/provider-diagnostics")
        self.assertEqual(state["routes"]["skills"], "/session/skills")
        self.assertEqual(state["routes"]["settings"], "/session/settings")
        self.assertEqual(state["routes"]["handoffs"], "/session/handoffs")
        self.assertEqual(state["routes"]["command"], "/session/command")
        self.assertEqual(state["routes"]["commands"], "/session/commands")
        self.assertEqual(state["routes"]["command_history"], "/session/command-history")
        self.assertEqual(state["routes"]["hooks"], "/session/hooks")
        self.assertEqual(state["routes"]["permissions"], "/session/permissions")
        self.assertEqual(state["routes"]["tasks"], "/session/tasks")
        self.assertEqual(state["routes"]["tools"], "/session/tools")
        self.assertEqual(state["routes"]["transcript"], "/session/transcript")
        self.assertEqual(state["active"]["dossier"]["id"], session_id)
        self.assertEqual(state["active"]["claude"]["schema_version"], "app_claude_controller_v1")
        self.assertFalse(state["active"]["claude"]["available"])
        self.assertEqual(state["active"]["claude"]["status"], "NON_CLAUDE_RUNTIME")
        self.assertEqual(state["active"]["claude"]["routes"]["bundle"], "/session/claude")
        self.assertEqual(state["active"]["claude"]["routes"]["action"], "/session/claude/action")
        self.assertEqual(state["active"]["claude"]["routes"]["action_snapshot"], "/session/claude/action/snapshot")
        self.assertEqual(state["active"]["claude"]["routes"]["artifact_lineage"], "/session/artifact-lineage")
        self.assertEqual(state["active"]["claude"]["routes"]["runtime_state"], "/session/runtime-state")
        self.assertEqual(state["active"]["claude"]["routes"]["agents"], "/session/agents")
        self.assertEqual(state["active"]["claude"]["routes"]["agent_prompts"], "/session/agent-prompts")
        self.assertEqual(state["active"]["claude"]["routes"]["model_client"], "/session/model-client")
        self.assertEqual(state["active"]["claude"]["routes"]["live_replay"], "/session/live-replay")
        self.assertEqual(state["active"]["claude"]["routes"]["skills"], "/session/skills")
        self.assertEqual(state["active"]["claude"]["routes"]["settings"], "/session/settings")
        self.assertEqual(state["active"]["claude"]["routes"]["handoffs"], "/session/handoffs")
        self.assertEqual(state["active"]["claude"]["routes"]["command_history"], "/session/command-history")
        self.assertGreaterEqual(len(state["active"]["documents"]), 1)
        self.assertGreaterEqual(len(state["active"]["fact_chips"]), 4)
        self.assertEqual(len(state["active"]["comparables"]), 3)
        self.assertEqual(len(state["active"]["adjustments"]), 3)
        self.assertEqual(state["active"]["valuation"]["status"], "A_VALIDER_PAR_EVALUATEUR_AGREE")
        self.assertFalse(state["limits"]["external_evaluator_responses_included"])
        self.assertTrue(refreshed["active"]["workflow"]["can_generate_package"])

    def test_app_state_exposes_claude_controller_for_claude_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                state = app_state(session_id)
                bundle = session_claude_bundle(session_id, limit=10)
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        claude = state["active"]["claude"]
        self.assertEqual(claude["schema_version"], "app_claude_controller_v1")
        self.assertTrue(claude["available"])
        self.assertEqual(claude["status"], "CLAUDE_CONTROLLER_READY")
        self.assertEqual(claude["bundle_schema_version"], "session_claude_bundle_v1")
        self.assertEqual(claude["routes"]["bundle"], "/session/claude")
        self.assertEqual(claude["routes"]["action"], "/session/claude/action")
        self.assertEqual(claude["routes"]["action_snapshot"], "/session/claude/action/snapshot")
        self.assertEqual(claude["routes"]["artifact_lineage"], "/session/artifact-lineage")
        self.assertEqual(claude["routes"]["runtime_state"], "/session/runtime-state")
        self.assertEqual(claude["routes"]["agents"], "/session/agents")
        self.assertEqual(claude["routes"]["agent_prompts"], "/session/agent-prompts")
        self.assertEqual(claude["routes"]["model_client"], "/session/model-client")
        self.assertEqual(claude["routes"]["live_replay"], "/session/live-replay")
        self.assertEqual(claude["routes"]["provider_diagnostics"], "/session/provider-diagnostics")
        self.assertEqual(claude["routes"]["skills"], "/session/skills")
        self.assertEqual(claude["routes"]["settings"], "/session/settings")
        self.assertEqual(claude["routes"]["handoffs"], "/session/handoffs")
        self.assertEqual(claude["routes"]["command_history"], "/session/command-history")
        self.assertEqual(claude["session_id"], session_id)
        self.assertEqual(claude["agents"], ["data-facts"])
        self.assertEqual(claude["counts"]["all_tools"], bundle["counts"]["all_tools"])
        self.assertEqual(claude["counts"]["all_transcript_entries"], bundle["counts"]["all_transcript_entries"])
        self.assertEqual(claude["commands"]["count"], bundle["commands"]["commands_count"])
        self.assertEqual(claude["permissions"]["decisions_count"], bundle["permissions"]["permission_summary"]["decisions_count"])
        self.assertEqual(claude["actions"]["count"], 0)
        self.assertEqual(claude["actions"]["mutation_count"], 0)
        self.assertEqual(claude["hooks"]["count"], bundle["hooks"]["all_invocations_count"])
        self.assertEqual(claude["tasks"]["count"], bundle["tasks"]["all_tasks_count"])
        self.assertEqual(claude["tools"]["count"], bundle["tools"]["all_tools_count"])
        self.assertEqual(claude["tools"]["model_facing_count"], len(bundle["tools"]["model_facing_tools"]))
        self.assertEqual(claude["transcript"]["entries_count"], bundle["transcript"]["all_entries_count"])
        self.assertFalse(claude["artifact_lineage"]["available"])
        self.assertEqual(claude["artifact_lineage"]["artifacts_count"], 0)
        self.assertTrue(claude["runtime_state"]["available"])
        self.assertEqual(claude["runtime_state"]["agents_count"], 1)
        self.assertGreater(claude["runtime_state"]["estimated_tokens"], 0)
        self.assertTrue(claude["agent_manifest"]["available"])
        self.assertEqual(claude["agent_manifest"]["agents_count"], 1)
        self.assertGreater(claude["agent_manifest"]["tools_count"], 0)
        self.assertTrue(claude["agent_prompts"]["available"])
        self.assertEqual(claude["agent_prompts"]["prompts_count"], 1)
        self.assertEqual(claude["agent_prompts"]["sections_count"], 3)
        self.assertGreater(claude["agent_prompts"]["rendered_chars"], 0)
        self.assertFalse(claude["model_client"]["available"])
        self.assertFalse(claude["model_client"]["enabled"])
        self.assertEqual(claude["model_client"]["requests_count"], 0)
        self.assertFalse(claude["live_replay"]["available"])
        self.assertEqual(claude["live_replay"]["retry_candidates_count"], 0)
        self.assertTrue(claude["provider_diagnostics"]["available"])
        self.assertEqual(claude["provider_diagnostics"]["provider"], "fake")
        self.assertTrue(claude["provider_diagnostics"]["api_runtime_ready"])
        self.assertEqual(claude["provider_diagnostics"]["missing_guardrails"], [])
        self.assertTrue(claude["skills"]["available"])
        self.assertGreater(claude["skills"]["skills_count"], 0)
        self.assertTrue(claude["settings"]["available"])
        self.assertGreaterEqual(claude["settings"]["sources_count"], 1)
        self.assertEqual(claude["settings"]["permission_mode"], "default")
        self.assertFalse(claude["handoffs"]["available"])
        self.assertEqual(claude["handoffs"]["handoffs_count"], 0)
        self.assertEqual(claude["handoffs"]["created_count"], 0)
        self.assertEqual(claude["handoffs"]["received_count"], 0)
        self.assertFalse(claude["command_history"]["available"])
        self.assertEqual(claude["command_history"]["commands_count"], 0)
        self.assertEqual(claude["command_history"]["blocked_count"], 0)
        self.assertTrue(claude["section_health"]["tools"])
        self.assertTrue(claude["section_health"]["agent_prompts"])
        self.assertTrue(claude["section_health"]["live_replay"])
        self.assertTrue(claude["section_health"]["skills"])
        self.assertTrue(claude["section_health"]["settings"])
        self.assertTrue(claude["section_health"]["handoffs"])
        self.assertTrue(claude["section_health"]["command_history"])
        self.assertTrue(claude["integrity"]["ok"])
        self.assertTrue(claude["ok"])

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
                knowledge = knowledge_immobilier_summary(session["session_id"])
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
        self.assertEqual(knowledge["schema_version"], "knowledge_immobilier_session_v1")
        self.assertEqual(knowledge["mandate"]["dossier_id"], "D-001")
        self.assertFalse(knowledge["limits"]["external_evaluator_responses_included"])
        self.assertEqual(resume["resume"]["status"], "RESUME_READY")

    def test_start_runtime_can_run_opt_in_claude_data_facts_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                        "claude_settings": {
                            "commands": {
                                "include_builtin": False,
                                "disabled": ["analyse-extraction-faits"],
                            }
                        },
                    }
                )
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
                knowledge_snapshot_exists = Path(session["knowledge_snapshot_path"]).exists()
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent:data-facts")
        self.assertEqual(result["agent_type"], "data-facts")
        self.assertTrue(status["integrity"]["ok"])
        self.assertTrue(knowledge_snapshot_exists)
        self.assertEqual(artifacts["artifacts_count"], 3)
        self.assertEqual(knowledge["schema_version"], "knowledge_immobilier_session_v1")
        self.assertEqual(knowledge["mandate"]["dossier_id"], "D-001")
        self.assertFalse(result["command_context"]["include_builtin_commands"])
        self.assertNotIn("compact", result["command_context"]["command_names"])
        self.assertNotIn("analyse-extraction-faits", result["command_context"]["command_names"])
        self.assertEqual(result["command_context"]["disabled_command_names"], ["analyse-extraction-faits"])
        self.assertEqual(session["command_context"]["settings_filtered_commands_count"], 1)
        self.assertIn("sessionSettings", result["settings_context"]["active_sources"])
        self.assertEqual(result["events"][0]["event"], "agent_session_start")
        self.assertIn("tool_start", {event["event"] for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_live_data_facts_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0,
                        "claude_model_provider": {
                            "provider": "fake",
                            "api_key": "sk-not-persisted",
                            "api_key_env": "ANTHROPIC_API_KEY",
                        },
                    }
                )
                session = payload["session"]
                result = payload["result"]
                model_client = session_model_client(session["session_id"])
                live_replay = session_live_replay(session["session_id"])
                provider_diagnostics = session_provider_diagnostics(session["session_id"])
                summary = session_summary(session["session_id"])
                resume = resume_session(session["session_id"])
                status = session_status(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
                replay_action = session_claude_action(
                    {"session_id": session["session_id"], "action": "live_replay"}
                )
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        events = [event["event"] for event in result["events"]]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent_live:data-facts")
        self.assertEqual(result["agent_type"], "data-facts")
        self.assertEqual(result["live_adapter"]["schema_version"], "claude_live_adapter_v0")
        self.assertTrue(result["live_adapter"]["enabled"])
        self.assertEqual(result["live_adapter"]["provider"], "fake")
        self.assertEqual(result["live_adapter"]["provider_config"]["schema_version"], "claude_model_provider_config_v0")
        self.assertEqual(result["live_adapter"]["provider_config"]["provider"], "fake")
        self.assertEqual(result["live_adapter"]["provider_config"]["adapter"], "fake_local_v0")
        self.assertTrue(result["live_adapter"]["provider_config"]["adapter_available"])
        self.assertFalse(result["live_adapter"]["provider_config"]["network_execution_enabled"])
        self.assertTrue(result["live_adapter"]["provider_config"]["api_key_present"])
        self.assertTrue(result["live_adapter"]["provider_config"]["redacted"])
        self.assertNotIn("sk-not-persisted", json.dumps(result["live_adapter"], ensure_ascii=False))
        self.assertTrue(result["model_client"]["enabled"])
        self.assertEqual(model_client["schema_version"], "session_model_client_v1")
        self.assertTrue(model_client["available"])
        self.assertEqual(model_client["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0)
        self.assertEqual(model_client["model_client"]["provider"], "fake")
        self.assertEqual(model_client["model_client"]["requests_count"], 1)
        self.assertEqual(model_client["model_client"]["responses_count"], 1)
        self.assertEqual(model_client["live_tool_loop"]["stop_reason"], "completion")
        self.assertEqual(model_client["live_tool_loop"]["turns_count"], 1)
        self.assertEqual(len(model_client["requests"]), 1)
        self.assertEqual(len(model_client["responses"]), 1)
        self.assertEqual(model_client["request"]["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0)
        self.assertEqual(model_client["response"]["provider"], "fake")
        self.assertTrue(model_client["ok"])
        self.assertEqual(live_replay["schema_version"], "session_live_replay_v1")
        self.assertTrue(live_replay["available"])
        self.assertTrue(live_replay["ok"], live_replay["validation"])
        self.assertEqual(live_replay["live_tool_loop"]["stop_reason"], "completion")
        self.assertGreater(live_replay["transcript_replay"]["tool_use_count"], 0)
        self.assertGreater(live_replay["transcript_replay"]["tool_result_count"], 0)
        self.assertTrue(live_replay["transcript_replay"]["validation"]["ok"])
        self.assertTrue(live_replay["permission_replay"]["ok"])
        self.assertEqual(live_replay["retry_candidates_count"], 0)
        self.assertEqual(live_replay["permission_requests_count"], 0)
        self.assertEqual(provider_diagnostics["schema_version"], "session_provider_diagnostics_v1")
        self.assertTrue(provider_diagnostics["available"])
        self.assertEqual(provider_diagnostics["source"], "session_live_adapter")
        self.assertEqual(provider_diagnostics["provider"], "fake")
        self.assertTrue(provider_diagnostics["api_runtime"]["ready"])
        self.assertEqual(provider_diagnostics["missing_guardrails"], [])
        self.assertEqual(summary["model_client"]["model_client"]["requests_count"], 1)
        self.assertEqual(summary["live_adapter"]["provider"], "fake")
        self.assertEqual(resume["resume"]["model_client"]["model_client"]["responses_count"], 1)
        self.assertTrue(resume["resume"]["live_replay"]["available"])
        self.assertTrue(status["integrity"]["model_client_enabled"])
        self.assertTrue(status["integrity"]["model_client_ok"])
        self.assertTrue(bundle["section_health"]["model_client"])
        self.assertTrue(bundle["section_health"]["provider_diagnostics"])
        self.assertEqual(bundle["counts"]["model_client_requests"], 1)
        self.assertEqual(bundle["counts"]["model_client_responses"], 1)
        self.assertEqual(bundle["counts"]["model_live_turns"], 1)
        self.assertEqual(bundle["counts"]["model_live_tool_calls"], 0)
        self.assertEqual(bundle["counts"]["live_retry_candidates"], 0)
        self.assertEqual(bundle["counts"]["live_permission_requests"], 0)
        self.assertTrue(bundle["section_health"]["live_replay"])
        self.assertEqual(bundle["model_client"]["live_tool_loop"]["stop_reason"], "completion")
        self.assertTrue(bundle["live_replay"]["ok"])
        self.assertEqual(bundle["counts"]["provider_missing_guardrails"], 0)
        self.assertEqual(bundle["model_client"]["model_client"]["provider"], "fake")
        self.assertEqual(bundle["provider_diagnostics"]["provider"], "fake")
        self.assertEqual(replay_action["action"], "live_replay")
        self.assertFalse(replay_action["mutation_applied"])
        self.assertTrue(replay_action["action_result"]["available"])
        self.assertTrue(replay_action["ok"])
        self.assertIn("model_request_started", events)
        self.assertIn("model_response_received", events)

    def test_live_runtime_rejects_real_provider_until_sdk_adapter_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                with self.assertRaises(ValueError) as raised:
                    start_runtime(
                        {
                            "fixture": "case_nominal.json",
                            "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0,
                            "claude_model_provider": {
                                "provider": "anthropic",
                                "api_key": "sk-not-persisted",
                                "allow_network": True,
                            },
                        }
                    )
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertIn("provider_not_executable:anthropic", str(raised.exception))
        self.assertNotIn("sk-not-persisted", str(raised.exception))

    def test_live_runtime_uses_anthropic_sdk_only_with_operator_flag_and_mock_factory(self) -> None:
        sdk_instances: list[object] = []

        class MockSDKResponse:
            def model_dump(self) -> dict[str, object]:
                return {
                    "id": "msg_runtime_mock_001",
                    "model": "claude-sonnet-4-6",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "Reponse runtime SDK simulee."}],
                    "usage": {"input_tokens": 31, "output_tokens": 11},
                }

        class MockMessages:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def create(self, **params: object) -> MockSDKResponse:
                self.calls.append(dict(params))
                return MockSDKResponse()

        class MockAnthropicSDK:
            def __init__(self, **kwargs: object) -> None:
                self.kwargs = dict(kwargs)
                self.messages = MockMessages()
                sdk_instances.append(self)

        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            previous_factory = api.ANTHROPIC_SDK_FACTORY_OVERRIDE
            previous_key = os.environ.get("ANTHROPIC_API_KEY")
            previous_runtime_flag = os.environ.get("EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME")
            previous_sdk_flag = os.environ.get("EVAL_IMMO_ENABLE_ANTHROPIC_SDK")
            api.SESSIONS_DIR = Path(tmp)
            api.ANTHROPIC_SDK_FACTORY_OVERRIDE = MockAnthropicSDK
            os.environ["ANTHROPIC_API_KEY"] = "sk-not-persisted"
            os.environ["EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME"] = "true"
            os.environ.pop("EVAL_IMMO_ENABLE_ANTHROPIC_SDK", None)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0,
                        "claude_model_provider": {
                            "provider": "anthropic",
                            "api_key_env": "ANTHROPIC_API_KEY",
                            "model": "claude-sonnet-4-6",
                            "allow_network": True,
                            "enable_sdk_execution": True,
                            "timeout_seconds": 9,
                            "max_retries": 3,
                            "max_tokens": 2048,
                        },
                    }
                )
                session = payload["session"]
                result = payload["result"]
                diagnostics = session_provider_diagnostics(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir
                api.ANTHROPIC_SDK_FACTORY_OVERRIDE = previous_factory
                if previous_key is None:
                    os.environ.pop("ANTHROPIC_API_KEY", None)
                else:
                    os.environ["ANTHROPIC_API_KEY"] = previous_key
                if previous_runtime_flag is None:
                    os.environ.pop("EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME", None)
                else:
                    os.environ["EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME"] = previous_runtime_flag
                if previous_sdk_flag is None:
                    os.environ.pop("EVAL_IMMO_ENABLE_ANTHROPIC_SDK", None)
                else:
                    os.environ["EVAL_IMMO_ENABLE_ANTHROPIC_SDK"] = previous_sdk_flag

        self.assertEqual(result["live_adapter"]["provider"], "anthropic")
        self.assertTrue(result["live_adapter"]["provider_config"]["ok"])
        self.assertTrue(result["live_adapter"]["provider_config"]["network_execution_enabled"])
        self.assertTrue(result["live_adapter"]["provider_diagnostics"]["api_runtime"]["ready"])
        self.assertEqual(result["model_client"]["provider"], "anthropic")
        self.assertEqual(result["model_response"]["provider"], "anthropic")
        self.assertEqual(result["model_response"]["raw_response_id"], "msg_runtime_mock_001")
        self.assertEqual(result["model_response"]["usage"]["input_tokens"], 31)
        self.assertEqual(result["model_response"]["usage"]["output_tokens"], 11)
        self.assertEqual(sdk_instances[0].kwargs["api_key"], "sk-not-persisted")
        self.assertEqual(sdk_instances[0].kwargs["timeout"], 9)
        self.assertEqual(sdk_instances[0].kwargs["max_retries"], 3)
        self.assertEqual(sdk_instances[0].messages.calls[0]["max_tokens"], 2048)
        self.assertEqual(diagnostics["provider"], "anthropic")
        self.assertTrue(diagnostics["api_runtime"]["ready"])
        self.assertEqual(diagnostics["missing_guardrails"], [])
        self.assertTrue(bundle["provider_diagnostics"]["api_runtime"]["ready"])
        self.assertTrue(bundle["section_health"]["provider_diagnostics"])
        encoded = json.dumps({"result": result, "diagnostics": diagnostics, "bundle": bundle}, ensure_ascii=False)
        self.assertNotIn("sk-not-persisted", encoded)

    def test_live_runtime_rejects_anthropic_when_operator_flag_is_partial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            previous_factory = api.ANTHROPIC_SDK_FACTORY_OVERRIDE
            previous_key = os.environ.get("ANTHROPIC_API_KEY")
            previous_runtime_flag = os.environ.get("EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME")
            api.SESSIONS_DIR = Path(tmp)
            api.ANTHROPIC_SDK_FACTORY_OVERRIDE = lambda **kwargs: object()
            os.environ["ANTHROPIC_API_KEY"] = "sk-not-persisted"
            os.environ["EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME"] = "true"
            try:
                with self.assertRaises(ValueError) as raised:
                    start_runtime(
                        {
                            "fixture": "case_nominal.json",
                            "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0,
                            "claude_model_provider": {
                                "provider": "anthropic",
                                "api_key_env": "ANTHROPIC_API_KEY",
                                "model": "claude-sonnet-4-6",
                                "allow_network": True,
                            },
                        }
                    )
            finally:
                api.SESSIONS_DIR = previous_sessions_dir
                api.ANTHROPIC_SDK_FACTORY_OVERRIDE = previous_factory
                if previous_key is None:
                    os.environ.pop("ANTHROPIC_API_KEY", None)
                else:
                    os.environ["ANTHROPIC_API_KEY"] = previous_key
                if previous_runtime_flag is None:
                    os.environ.pop("EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME", None)
                else:
                    os.environ["EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME"] = previous_runtime_flag

        self.assertIn("sdk_execution_not_enabled", str(raised.exception))
        self.assertNotIn("sk-not-persisted", str(raised.exception))

    def test_session_provider_diagnostics_reports_anthropic_guardrails_without_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                diagnostics = session_provider_diagnostics(
                    payload["session"]["session_id"],
                    provider_options={
                        "provider": "anthropic",
                        "api_key_env": "ANTHROPIC_API_KEY",
                        "model": "claude-sonnet-4-6",
                        "allow_network": True,
                        "enable_sdk_execution": True,
                    },
                    env={"ANTHROPIC_API_KEY": "sk-not-persisted"},
                    sdk_available=True,
                )
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(diagnostics["schema_version"], "session_provider_diagnostics_v1")
        self.assertEqual(diagnostics["source"], "request")
        self.assertEqual(diagnostics["provider"], "anthropic")
        self.assertFalse(diagnostics["default_runtime"]["ready"])
        self.assertTrue(diagnostics["sdk_transport"]["ready"])
        self.assertFalse(diagnostics["api_runtime"]["ready"])
        self.assertFalse(diagnostics["sdk_transport"]["client_constructed"])
        self.assertFalse(diagnostics["api_runtime"]["client_constructed"])
        self.assertIn("provider_not_executable:anthropic", diagnostics["default_runtime"]["errors"])
        self.assertIn("operator_runtime_enabled", diagnostics["missing_guardrails"])
        self.assertNotIn("sk-not-persisted", json.dumps(diagnostics, ensure_ascii=False))

    def test_start_runtime_can_run_opt_in_claude_live_comps_market_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                model_client = session_model_client(session["session_id"])
                summary = session_summary(session["session_id"])
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        events = [event["event"] for event in result["events"]]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent_live:comps-market")
        self.assertEqual(result["agent_type"], "comps-market")
        self.assertEqual(result["live_adapter"]["schema_version"], "claude_live_adapter_v0")
        self.assertTrue(result["live_adapter"]["enabled"])
        self.assertEqual(result["live_adapter"]["agent_type"], "comps-market")
        self.assertEqual(result["live_adapter"]["provider"], "fake")
        self.assertTrue(result["model_client"]["enabled"])
        self.assertEqual(model_client["schema_version"], "session_model_client_v1")
        self.assertTrue(model_client["available"])
        self.assertEqual(model_client["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0)
        self.assertEqual(model_client["model_client"]["provider"], "fake")
        self.assertEqual(model_client["model_client"]["requests_count"], 1)
        self.assertEqual(model_client["request"]["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0)
        self.assertIn("search_comparables", model_client["request"]["tools"])
        self.assertEqual(model_client["response"]["provider"], "fake")
        self.assertTrue(status["integrity"]["ok"])
        self.assertTrue(status["integrity"]["model_client_enabled"])
        self.assertTrue(status["integrity"]["model_client_ok"])
        self.assertEqual(artifacts["artifacts_count"], 3)
        self.assertEqual(knowledge["market_evidence"]["comparables_count"], 1)
        self.assertEqual(summary["live_adapter"]["agent_type"], "comps-market")
        self.assertTrue(bundle["section_health"]["model_client"])
        self.assertEqual(bundle["counts"]["model_client_requests"], 1)
        self.assertIn("model_request_started", events)
        self.assertIn("model_response_received", events)
        self.assertIn("search_comparables", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_comps_market_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_COMPS_MARKET_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_COMPS_MARKET_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_COMPS_MARKET_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent:comps-market")
        self.assertEqual(result["agent_type"], "comps-market")
        self.assertTrue(status["integrity"]["ok"])
        self.assertEqual(artifacts["artifacts_count"], 3)
        self.assertEqual(knowledge["market_evidence"]["comparables_count"], 1)
        self.assertIn("search_comparables", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_valuation_draft_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_VALUATION_DRAFT_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_VALUATION_DRAFT_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_VALUATION_DRAFT_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent:valuation-draft")
        self.assertEqual(result["agent_type"], "valuation-draft")
        self.assertTrue(status["integrity"]["ok"])
        self.assertEqual(artifacts["artifacts_count"], 5)
        self.assertGreater(knowledge["valuation"]["values"]["approche_comparative"], 0)
        self.assertIn("run_calculation", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_live_valuation_draft_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                model_client = session_model_client(session["session_id"])
                summary = session_summary(session["session_id"])
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        events = [event["event"] for event in result["events"]]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent_live:valuation-draft")
        self.assertEqual(result["agent_type"], "valuation-draft")
        self.assertEqual(result["live_adapter"]["schema_version"], "claude_live_adapter_v0")
        self.assertTrue(result["live_adapter"]["enabled"])
        self.assertEqual(result["live_adapter"]["agent_type"], "valuation-draft")
        self.assertEqual(result["live_adapter"]["provider"], "fake")
        self.assertTrue(result["model_client"]["enabled"])
        self.assertEqual(model_client["schema_version"], "session_model_client_v1")
        self.assertTrue(model_client["available"])
        self.assertEqual(model_client["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0)
        self.assertEqual(model_client["model_client"]["provider"], "fake")
        self.assertEqual(model_client["model_client"]["requests_count"], 1)
        self.assertEqual(model_client["request"]["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0)
        self.assertIn("run_calculation", model_client["request"]["tools"])
        self.assertEqual(model_client["response"]["provider"], "fake")
        self.assertTrue(status["integrity"]["ok"])
        self.assertTrue(status["integrity"]["model_client_enabled"])
        self.assertTrue(status["integrity"]["model_client_ok"])
        self.assertEqual(artifacts["artifacts_count"], 5)
        self.assertGreater(knowledge["valuation"]["values"]["approche_comparative"], 0)
        self.assertEqual(summary["live_adapter"]["agent_type"], "valuation-draft")
        self.assertTrue(bundle["section_health"]["model_client"])
        self.assertEqual(bundle["counts"]["model_client_requests"], 1)
        self.assertIn("model_request_started", events)
        self.assertIn("model_response_received", events)
        self.assertIn("run_calculation", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_compliance_qa_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_COMPLIANCE_QA_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_COMPLIANCE_QA_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_COMPLIANCE_QA_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent:compliance-qa")
        self.assertEqual(result["agent_type"], "compliance-qa")
        self.assertTrue(status["integrity"]["ok"])
        self.assertEqual(artifacts["artifacts_count"], 3)
        self.assertEqual(knowledge["compliance"]["status"], "PRET_REVISION_FINALE")
        self.assertIn("validate_schema", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_live_compliance_qa_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                model_client = session_model_client(session["session_id"])
                summary = session_summary(session["session_id"])
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        events = [event["event"] for event in result["events"]]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent_live:compliance-qa")
        self.assertEqual(result["agent_type"], "compliance-qa")
        self.assertEqual(result["live_adapter"]["schema_version"], "claude_live_adapter_v0")
        self.assertTrue(result["live_adapter"]["enabled"])
        self.assertEqual(result["live_adapter"]["agent_type"], "compliance-qa")
        self.assertEqual(result["live_adapter"]["provider"], "fake")
        self.assertTrue(result["model_client"]["enabled"])
        self.assertEqual(model_client["schema_version"], "session_model_client_v1")
        self.assertTrue(model_client["available"])
        self.assertEqual(model_client["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0)
        self.assertEqual(model_client["model_client"]["provider"], "fake")
        self.assertEqual(model_client["model_client"]["requests_count"], 1)
        self.assertEqual(model_client["request"]["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0)
        self.assertIn("validate_schema", model_client["request"]["tools"])
        self.assertEqual(model_client["response"]["provider"], "fake")
        self.assertTrue(status["integrity"]["ok"])
        self.assertTrue(status["integrity"]["model_client_enabled"])
        self.assertTrue(status["integrity"]["model_client_ok"])
        self.assertEqual(artifacts["artifacts_count"], 3)
        self.assertEqual(knowledge["compliance"]["status"], "PRET_REVISION_FINALE")
        self.assertEqual(summary["live_adapter"]["agent_type"], "compliance-qa")
        self.assertTrue(bundle["section_health"]["model_client"])
        self.assertEqual(bundle["counts"]["model_client_requests"], 1)
        self.assertIn("model_request_started", events)
        self.assertIn("model_response_received", events)
        self.assertIn("validate_schema", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_redaction_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_REDACTION_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_REDACTION_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_REDACTION_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent:redaction")
        self.assertEqual(result["agent_type"], "redaction")
        self.assertTrue(status["integrity"]["ok"])
        self.assertEqual(artifacts["artifacts_count"], 2)
        self.assertTrue(knowledge["redaction"]["brouillon_rapport_available"])
        self.assertIn("format_document", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_live_redaction_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                model_client = session_model_client(session["session_id"])
                summary = session_summary(session["session_id"])
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        events = [event["event"] for event in result["events"]]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0)
        self.assertEqual(result["pipeline_scope"], "single_agent_live:redaction")
        self.assertEqual(result["agent_type"], "redaction")
        self.assertEqual(result["live_adapter"]["schema_version"], "claude_live_adapter_v0")
        self.assertTrue(result["live_adapter"]["enabled"])
        self.assertEqual(result["live_adapter"]["agent_type"], "redaction")
        self.assertEqual(result["live_adapter"]["provider"], "fake")
        self.assertTrue(result["model_client"]["enabled"])
        self.assertEqual(model_client["schema_version"], "session_model_client_v1")
        self.assertTrue(model_client["available"])
        self.assertEqual(model_client["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0)
        self.assertEqual(model_client["model_client"]["provider"], "fake")
        self.assertEqual(model_client["model_client"]["requests_count"], 1)
        self.assertEqual(model_client["request"]["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0)
        self.assertIn("format_document", model_client["request"]["tools"])
        self.assertEqual(model_client["response"]["provider"], "fake")
        self.assertTrue(status["integrity"]["ok"])
        self.assertTrue(status["integrity"]["model_client_enabled"])
        self.assertTrue(status["integrity"]["model_client_ok"])
        self.assertEqual(artifacts["artifacts_count"], 2)
        self.assertTrue(knowledge["redaction"]["brouillon_rapport_available"])
        self.assertEqual(summary["live_adapter"]["agent_type"], "redaction")
        self.assertTrue(bundle["section_health"]["model_client"])
        self.assertEqual(bundle["counts"]["model_client_requests"], 1)
        self.assertIn("model_request_started", events)
        self.assertIn("model_response_received", events)
        self.assertIn("format_document", {event.get("tool") for event in result["events"]})

    def test_start_runtime_can_run_opt_in_claude_pipeline_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_PIPELINE_V0,
                    }
                )
                session = payload["session"]
                result = payload["result"]
                status = session_status(session["session_id"])
                artifacts = session_artifacts(session["session_id"])
                knowledge = knowledge_immobilier_summary(session["session_id"])
                summary = session_summary(session["session_id"])
                resume = resume_session(session["session_id"])
                command_palette = session_commands(session["session_id"])
                hooks = session_hooks(session["session_id"])
                data_facts_pre_tool_hooks = session_hooks(
                    session["session_id"],
                    agent="data-facts",
                    hook_event="PreToolUse",
                )
                tasks = session_tasks(session["session_id"])
                data_facts_completed_tasks = session_tasks(
                    session["session_id"],
                    agent="data-facts",
                    status="completed",
                )
                tools = session_tools(session["session_id"])
                data_facts_read_tools = session_tools(
                    session["session_id"],
                    agent="data-facts",
                    permission="runtime_read",
                )
                transcript_browser = session_transcript(session["session_id"], limit=5)
                data_facts_tool_use_transcript = session_transcript(
                    session["session_id"],
                    agent="data-facts",
                    block_type="tool_use",
                    limit=10,
                )
                artifact_lineage = session_artifact_lineage(session["session_id"])
                data_facts_lineage = session_artifact_lineage(session["session_id"], agent="data-facts")
                terminal_lineage = session_artifact_lineage(session["session_id"], terminal_only=True)
                runtime_state = session_runtime_state(session["session_id"])
                data_facts_runtime_state = session_runtime_state(session["session_id"], agent="data-facts")
                agent_manifest = session_agents(session["session_id"])
                data_facts_agent_manifest = session_agents(session["session_id"], agent="data-facts")
                agent_prompts = session_agent_prompts(session["session_id"])
                data_facts_agent_prompts = session_agent_prompts(session["session_id"], agent="data-facts")
                settings_surface = session_settings(session["session_id"])
                runtime_permission_setting = session_settings(
                    session["session_id"],
                    key="permissions.defaultMode",
                )
                skill_palette = session_skills(session["session_id"])
                data_facts_skill_palette = session_skills(session["session_id"], agent="data-facts")
                data_facts_skills = session_skills(
                    session["session_id"],
                    agent="data-facts",
                    skill="analyse-extraction-faits",
                )
                handoffs = session_handoffs(session["session_id"])
                data_facts_handoffs = session_handoffs(session["session_id"], agent="data-facts")
                comps_received_handoffs = session_handoffs(
                    session["session_id"],
                    agent="comps-market",
                    direction="received",
                )
                claude_bundle = session_claude_bundle(
                    session["session_id"],
                    agent="data-facts",
                    hook_event="PreToolUse",
                    task_status="completed",
                    permission="runtime_read",
                    block_type="tool_use",
                    limit=3,
                )
                transcript_path = Path(session["claude_transcript_path"])
                transcript_exists = transcript_path.exists()
                permission_state_path = Path(session["permission_state_path"])
                permission_state_exists = permission_state_path.exists()
                transcript_entries = [
                    json.loads(line)
                    for line in transcript_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        expected_agents = ["data-facts", "comps-market", "valuation-draft", "compliance-qa", "redaction"]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_PIPELINE_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_PIPELINE_V0)
        self.assertEqual(result["pipeline_scope"], "multi_agent:claude")
        self.assertEqual(result["agent_type"], "claude-pipeline")
        self.assertEqual(result["agents"], expected_agents)
        self.assertTrue(result["message_envelope_summary"]["ok"])
        self.assertTrue(result["event_envelope_summary"]["ok"])
        self.assertEqual(result["token_budget"]["agents_count"], 5)
        self.assertEqual(result["token_budget"]["models"], ["claude-sonnet-4-6"])
        self.assertEqual(result["metrics"]["total_tokens"], result["token_budget"]["estimated_tokens"])
        self.assertEqual(result["usage_accounting"]["agents_count"], 5)
        self.assertEqual(result["metrics"]["total_cost_usd"], result["usage_accounting"]["total_cost_usd"])
        self.assertEqual(result["tool_registry_summary"]["schema_version"], "claude_tool_registry_summary_v0")
        self.assertTrue(result["tool_registry_summary"]["ok"])
        self.assertEqual(tools["schema_version"], "session_tools_v1")
        self.assertTrue(tools["available"])
        self.assertTrue(tools["validation"]["ok"], tools["validation"]["errors"])
        self.assertEqual(tools["all_tool_names"], result["tool_registry_summary"]["tool_names"])
        self.assertEqual(tools["all_tools_count"], result["tool_registry_summary"]["tools_count"])
        self.assertEqual(tools["tools_count"], result["tool_registry_summary"]["tools_count"])
        self.assertEqual(set(tools["agents"]), set(expected_agents))
        self.assertEqual(set(tools["tools_by_agent"]), set(expected_agents))
        self.assertIn("runtime_read", tools["permissions"])
        self.assertIn("runtime_write", tools["permissions"])
        self.assertIn("runtime_execute", tools["permissions"])
        self.assertIn("write_file", tools["all_summary"]["destructive_tools"])
        self.assertTrue(all(tool["model_facing_schema"]["name"] == tool["name"] for tool in tools["tools"]))
        self.assertEqual(data_facts_read_tools["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_read_tools["filters"]["permission"], "runtime_read")
        self.assertGreater(data_facts_read_tools["tools_count"], 0)
        self.assertTrue(all(tool["permission"] == "runtime_read" for tool in data_facts_read_tools["tools"]))
        self.assertTrue(all("data-facts" in tool["agents"] for tool in data_facts_read_tools["tools"]))
        self.assertEqual(claude_bundle["schema_version"], "session_claude_bundle_v1")
        self.assertTrue(claude_bundle["ok"], claude_bundle["section_health"])
        self.assertEqual(claude_bundle["routes"]["bundle"], "/session/claude")
        self.assertEqual(claude_bundle["routes"]["action"], "/session/claude/action")
        self.assertEqual(claude_bundle["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["filters"]["hook_event"], "PreToolUse")
        self.assertEqual(claude_bundle["filters"]["task_status"], "completed")
        self.assertEqual(claude_bundle["filters"]["permission"], "runtime_read")
        self.assertEqual(claude_bundle["filters"]["block_type"], "tool_use")
        self.assertEqual(claude_bundle["summary"]["schema_version"], "session_summary_v1")
        self.assertEqual(claude_bundle["commands"]["commands_count"], command_palette["commands_count"])
        self.assertEqual(
            claude_bundle["permissions"]["permission_summary"]["decisions_count"],
            result["permission_summary"]["decisions_count"],
        )
        self.assertEqual(claude_bundle["hooks"]["invocations_count"], data_facts_pre_tool_hooks["invocations_count"])
        self.assertEqual(claude_bundle["tasks"]["tasks_count"], data_facts_completed_tasks["tasks_count"])
        self.assertEqual(claude_bundle["tools"]["tools_count"], data_facts_read_tools["tools_count"])
        self.assertEqual(claude_bundle["transcript"]["entries_count"], 3)
        self.assertEqual(
            claude_bundle["transcript"]["filtered_entries_count"],
            data_facts_tool_use_transcript["filtered_entries_count"],
        )
        self.assertEqual(claude_bundle["counts"]["all_tools"], result["tool_registry_summary"]["tools_count"])
        self.assertEqual(claude_bundle["counts"]["all_transcript_entries"], result["transcript_summary"]["entries_count"])
        self.assertEqual(claude_bundle["routes"]["artifact_lineage"], "/session/artifact-lineage")
        self.assertEqual(claude_bundle["routes"]["runtime_state"], "/session/runtime-state")
        self.assertEqual(claude_bundle["routes"]["agents"], "/session/agents")
        self.assertEqual(claude_bundle["routes"]["agent_prompts"], "/session/agent-prompts")
        self.assertEqual(claude_bundle["routes"]["skills"], "/session/skills")
        self.assertEqual(claude_bundle["routes"]["settings"], "/session/settings")
        self.assertEqual(claude_bundle["routes"]["handoffs"], "/session/handoffs")
        self.assertEqual(claude_bundle["routes"]["command_history"], "/session/command-history")
        self.assertTrue(claude_bundle["section_health"]["agents"])
        self.assertTrue(claude_bundle["section_health"]["agent_prompts"])
        self.assertTrue(claude_bundle["section_health"]["skills"])
        self.assertTrue(claude_bundle["section_health"]["settings"])
        self.assertTrue(claude_bundle["section_health"]["handoffs"])
        self.assertTrue(claude_bundle["section_health"]["command_history"])
        self.assertTrue(claude_bundle["section_health"]["artifact_lineage"])
        self.assertTrue(claude_bundle["section_health"]["runtime_state"])
        self.assertEqual(claude_bundle["agent_manifest"]["schema_version"], "session_claude_agent_manifest_v1")
        self.assertEqual(claude_bundle["agent_manifest"]["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["agent_manifest"]["agents_count"], data_facts_agent_manifest["agents_count"])
        self.assertEqual(claude_bundle["counts"]["agents"], data_facts_agent_manifest["agents_count"])
        self.assertEqual(claude_bundle["agent_prompts"]["schema_version"], "session_claude_agent_prompts_v1")
        self.assertEqual(claude_bundle["agent_prompts"]["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["agent_prompts"]["prompts_count"], data_facts_agent_prompts["prompts_count"])
        self.assertEqual(claude_bundle["counts"]["agent_prompts"], data_facts_agent_prompts["prompts_count"])
        self.assertEqual(claude_bundle["skills"]["schema_version"], "session_skills_v1")
        self.assertEqual(claude_bundle["skills"]["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["skills"]["skills_count"], data_facts_skill_palette["skills_count"])
        self.assertEqual(claude_bundle["counts"]["skills"], data_facts_skill_palette["skills_count"])
        self.assertEqual(claude_bundle["settings"]["schema_version"], "session_settings_v1")
        self.assertEqual(claude_bundle["settings"]["runtime_options"]["permission_mode"], "default")
        self.assertEqual(claude_bundle["counts"]["all_settings_sources"], settings_surface["all_sources_count"])
        self.assertEqual(claude_bundle["handoffs"]["schema_version"], "session_handoffs_v1")
        self.assertEqual(claude_bundle["handoffs"]["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["handoffs"]["handoffs_count"], data_facts_handoffs["handoffs_count"])
        self.assertEqual(claude_bundle["counts"]["handoffs"], data_facts_handoffs["handoffs_count"])
        self.assertEqual(claude_bundle["counts"]["all_handoffs"], handoffs["all_handoffs_count"])
        self.assertEqual(claude_bundle["artifact_lineage"]["schema_version"], "session_artifact_lineage_v1")
        self.assertEqual(claude_bundle["artifact_lineage"]["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["artifact_lineage"]["artifacts_count"], data_facts_lineage["artifacts_count"])
        self.assertEqual(claude_bundle["counts"]["artifact_lineage"], data_facts_lineage["artifacts_count"])
        self.assertEqual(claude_bundle["runtime_state"]["schema_version"], "session_claude_runtime_state_v1")
        self.assertEqual(claude_bundle["runtime_state"]["filters"]["agent"], "data-facts")
        self.assertEqual(claude_bundle["runtime_state"]["summary"]["agents_count"], 1)
        self.assertEqual(
            claude_bundle["runtime_state"]["summary"]["estimated_tokens"],
            data_facts_runtime_state["summary"]["estimated_tokens"],
        )
        self.assertGreater(claude_bundle["counts"]["runtime_estimated_tokens"], 0)
        self.assertTrue(claude_bundle["integrity"]["ok"])
        self.assertEqual(result["settings_context"]["schema_version"], "claude_settings_context_v0")
        self.assertIn("defaultSettings", result["settings_context"]["active_sources"])
        self.assertIn("projectSettings", result["settings_context"]["active_sources"])
        self.assertEqual(result["settings_context"]["runtime_options"]["permission_mode"], "default")
        self.assertEqual(
            result["settings_context"]["runtime_options"]["additional_directories"],
            ["C:\\Users\\simon\\claude-code-project"],
        )
        self.assertTrue(result["settings_context"]["ok"])
        self.assertEqual(settings_surface["schema_version"], "session_settings_v1")
        self.assertTrue(settings_surface["available"])
        self.assertTrue(settings_surface["validation"]["ok"], settings_surface["validation"]["errors"])
        self.assertIn("defaultSettings", settings_surface["active_sources"])
        self.assertIn("projectSettings", settings_surface["active_sources"])
        self.assertEqual(settings_surface["runtime_options"]["permission_mode"], "default")
        self.assertIn("permissions.defaultMode", settings_surface["all_effective_keys"])
        self.assertIn("permissions.additionalDirectories", settings_surface["all_effective_keys"])
        self.assertEqual(runtime_permission_setting["filters"]["key"], "permissions.defaultMode")
        self.assertEqual(runtime_permission_setting["effective_items"][0]["value"], "default")
        self.assertEqual(result["skill_context"]["schema_version"], "claude_skill_pipeline_context_v0")
        self.assertEqual(result["skill_context"]["agents_count"], 5)
        self.assertEqual(result["skill_context"]["loaded_from"], ["skills"])
        self.assertEqual(result["skill_context"]["plugins_count"], 0)
        self.assertTrue(result["skill_context"]["ok"])
        self.assertEqual(skill_palette["schema_version"], "session_skills_v1")
        self.assertTrue(skill_palette["available"])
        self.assertTrue(skill_palette["validation"]["ok"], skill_palette["validation"]["errors"])
        self.assertEqual(set(skill_palette["agents"]), set(expected_agents))
        self.assertEqual(skill_palette["all_summary"]["agents_count"], len(expected_agents))
        self.assertIn("analyse-extraction-faits", skill_palette["all_skill_names"])
        self.assertEqual(skill_palette["loaded_from"], ["skills"])
        self.assertEqual(data_facts_skills["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_skills["filters"]["skill"], "analyse-extraction-faits")
        self.assertEqual(data_facts_skills["skills_count"], 1)
        self.assertEqual(data_facts_skills["skills"][0]["name"], "analyse-extraction-faits")
        self.assertIn("data-facts", data_facts_skills["skills"][0]["agents"])
        self.assertEqual(data_facts_skills["skills"][0]["schema_version"], "claude_skill_spec_v0")
        self.assertEqual(result["command_context"]["schema_version"], "claude_command_pipeline_context_v0")
        self.assertEqual(result["command_context"]["agents_count"], 5)
        self.assertIn("compact", result["command_context"]["command_names"])
        self.assertIn("redaction-rapport-evaluation", result["command_context"]["model_invocable_command_names"])
        self.assertTrue(result["command_context"]["ok"])
        self.assertEqual(command_palette["schema_version"], "session_slash_command_palette_v1")
        self.assertIn("status", command_palette["executable_command_names"])
        self.assertIn("redaction-rapport-evaluation", command_palette["model_invocable_command_names"])
        compact_command = next(command for command in command_palette["commands"] if command["name"] == "compact")
        self.assertEqual(set(compact_command["agents"]), set(expected_agents))
        self.assertTrue(result["conversation_state"]["ok"])
        self.assertEqual(result["conversation_state"]["tool_use_count"], 25)
        self.assertEqual(result["conversation_state"]["tool_result_count"], 25)
        self.assertFalse(result["context_state"]["needs_compaction"])
        self.assertGreater(result["context_state"]["estimated_tokens"], 0)
        self.assertEqual(runtime_state["schema_version"], "session_claude_runtime_state_v1")
        self.assertTrue(runtime_state["available"])
        self.assertTrue(runtime_state["validation"]["ok"], runtime_state["validation"]["errors"])
        self.assertEqual(runtime_state["agents_count"], 5)
        self.assertEqual(runtime_state["summary"]["messages_count"], result["conversation_state"]["messages_count"])
        self.assertEqual(runtime_state["summary"]["tool_use_count"], result["conversation_state"]["tool_use_count"])
        self.assertEqual(runtime_state["summary"]["estimated_tokens"], result["token_budget"]["estimated_tokens"])
        self.assertEqual(runtime_state["summary"]["total_cost_usd"], result["usage_accounting"]["total_cost_usd"])
        self.assertEqual(set(runtime_state["conversation_state_by_agent"]), set(expected_agents))
        self.assertEqual(data_facts_runtime_state["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_runtime_state["summary"]["agents_count"], 1)
        self.assertEqual(set(data_facts_runtime_state["conversation_state_by_agent"]), {"data-facts"})
        self.assertGreater(data_facts_runtime_state["summary"]["estimated_tokens"], 0)
        self.assertEqual(agent_manifest["schema_version"], "session_claude_agent_manifest_v1")
        self.assertTrue(agent_manifest["available"])
        self.assertTrue(agent_manifest["validation"]["ok"], agent_manifest["validation"]["errors"])
        self.assertEqual(agent_manifest["all_agents_count"], 5)
        self.assertEqual(agent_manifest["agents_count"], 5)
        self.assertEqual(set(agent_manifest["all_agent_types"]), set(expected_agents))
        self.assertEqual(agent_manifest["all_summary"]["models"], ["claude-sonnet-4-6"])
        self.assertIn("write_file", agent_manifest["all_summary"]["tool_names"])
        self.assertIn("redaction-rapport-evaluation", agent_manifest["all_summary"]["command_names"])
        self.assertEqual(data_facts_agent_manifest["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_agent_manifest["agents_count"], 1)
        self.assertEqual(data_facts_agent_manifest["agents"][0]["agent_type"], "data-facts")
        self.assertEqual(
            data_facts_agent_manifest["agents"][0]["model_profile"]["schema_version"],
            "claude_model_profile_v0",
        )
        self.assertGreater(data_facts_agent_manifest["agents"][0]["tools_count"], 0)
        self.assertGreater(data_facts_agent_manifest["agents"][0]["skills_count"], 0)
        self.assertEqual(agent_prompts["schema_version"], "session_claude_agent_prompts_v1")
        self.assertTrue(agent_prompts["available"])
        self.assertTrue(agent_prompts["validation"]["ok"], agent_prompts["validation"]["errors"])
        self.assertEqual(agent_prompts["all_prompts_count"], 5)
        self.assertEqual(set(agent_prompts["all_agents"]), set(expected_agents))
        self.assertEqual(agent_prompts["all_summary"]["sections_count"], 15)
        self.assertGreater(agent_prompts["all_summary"]["rendered_chars"], 0)
        self.assertEqual(data_facts_agent_prompts["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_agent_prompts["prompts_count"], 1)
        self.assertEqual(data_facts_agent_prompts["prompts"][0]["agent_type"], "data-facts")
        self.assertEqual(data_facts_agent_prompts["prompts"][0]["sections_count"], 3)
        self.assertIn("Dossier: D-001", data_facts_agent_prompts["prompts"][0]["rendered_prompt"])
        self.assertIn("tools_allowed: read_file", data_facts_agent_prompts["prompts"][0]["rendered_prompt"])
        self.assertEqual(result["permission_summary"]["decisions_count"], 25)
        self.assertEqual(result["permission_summary"]["allowed_count"], 25)
        self.assertEqual(result["permission_summary"]["denied_count"], 0)
        self.assertTrue(permission_state_exists)
        self.assertEqual(session["permission_state_summary"]["schema_version"], "claude_permission_state_summary_v0")
        self.assertTrue(session["permission_state_summary"]["ok"])
        self.assertEqual(session["permission_state_summary"]["additional_working_directories_count"], 1)
        self.assertIn(
            {"path": "C:\\Users\\simon\\claude-code-project", "source": "projectSettings"},
            result["permission_state"]["additionalWorkingDirectories"],
        )
        self.assertEqual(result["task_summary"]["tasks_count"], 16)
        self.assertEqual(result["task_summary"]["completed_count"], 16)
        self.assertTrue(result["task_summary"]["ok"])
        self.assertEqual(tasks["schema_version"], "session_tasks_v1")
        self.assertTrue(tasks["available"])
        self.assertTrue(tasks["validation"]["ok"], tasks["validation"]["errors"])
        self.assertEqual(tasks["all_tasks_count"], result["task_summary"]["tasks_count"])
        self.assertEqual(tasks["summary"]["tasks_count"], result["task_summary"]["tasks_count"])
        self.assertEqual(tasks["summary"]["completed_count"], result["task_summary"]["completed_count"])
        self.assertEqual(set(tasks["agents"]), set(expected_agents))
        self.assertEqual(set(tasks["task_state_by_agent"]), set(expected_agents))
        self.assertEqual(tasks["statuses"], ["completed"])
        self.assertEqual(data_facts_completed_tasks["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_completed_tasks["filters"]["status"], "completed")
        self.assertEqual(data_facts_completed_tasks["tasks_count"], 3)
        self.assertTrue(all(task["agent_type"] == "data-facts" for task in data_facts_completed_tasks["tasks"]))
        self.assertEqual(result["hook_summary"]["invocations_count"], 60)
        self.assertEqual(result["hook_summary"]["hook_events"]["PreToolUse"], 25)
        self.assertEqual(result["hook_summary"]["hook_events"]["PostToolUse"], 25)
        self.assertEqual(hooks["schema_version"], "session_hooks_v1")
        self.assertTrue(hooks["available"])
        self.assertTrue(hooks["validation"]["ok"], hooks["validation"]["errors"])
        self.assertEqual(hooks["all_invocations_count"], result["hook_summary"]["invocations_count"])
        self.assertEqual(hooks["summary"]["invocations_count"], result["hook_summary"]["invocations_count"])
        self.assertEqual(set(hooks["agents"]), set(expected_agents))
        self.assertIn("SessionStart", hooks["hook_events"])
        self.assertIn("data-facts", hooks["summary_by_agent"])
        self.assertEqual(data_facts_pre_tool_hooks["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_pre_tool_hooks["filters"]["hook_event"], "PreToolUse")
        self.assertEqual(data_facts_pre_tool_hooks["summary"]["hook_events"], {"PreToolUse": 3})
        self.assertEqual(result["handoff_summary"]["handoffs_count"], 4)
        self.assertEqual(result["handoffs"][0]["from_agent"], "data-facts")
        self.assertEqual(result["handoffs"][0]["to_agent"], "comps-market")
        self.assertEqual(handoffs["schema_version"], "session_handoffs_v1")
        self.assertTrue(handoffs["available"])
        self.assertTrue(handoffs["validation"]["ok"], handoffs["validation"]["errors"])
        self.assertEqual(handoffs["all_created_handoffs_count"], 4)
        self.assertEqual(handoffs["all_received_handoffs_count"], 4)
        self.assertEqual(handoffs["all_summary"]["created_handoffs_count"], 4)
        self.assertEqual(handoffs["all_summary"]["received_handoffs_count"], 4)
        self.assertEqual(handoffs["all_summary"]["handoffs_count"], 8)
        self.assertEqual(data_facts_handoffs["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_handoffs["summary"]["created_handoffs_count"], 1)
        self.assertEqual(data_facts_handoffs["summary"]["received_handoffs_count"], 0)
        self.assertEqual(comps_received_handoffs["filters"]["direction"], "received")
        self.assertEqual(comps_received_handoffs["handoffs_count"], 1)
        self.assertEqual(comps_received_handoffs["handoffs"][0]["from_agent"], "data-facts")
        self.assertEqual(result["artifact_lineage"]["schema_version"], "claude_pipeline_artifact_lineage_v1")
        self.assertTrue(result["artifact_lineage"]["ok"])
        self.assertEqual(result["artifact_lineage"]["artifacts_count"], 16)
        self.assertEqual(result["artifact_lineage"]["handoff_edges_count"], 4)
        self.assertEqual(summary["artifact_lineage"]["schema_version"], "claude_pipeline_artifact_lineage_v1")
        self.assertEqual(summary["artifact_lineage"]["artifacts_count"], result["artifact_lineage"]["artifacts_count"])
        self.assertEqual(
            summary["artifact_lineage"]["terminal_artifact_keys"],
            result["artifact_lineage"]["terminal_artifact_keys"],
        )
        self.assertEqual(artifact_lineage["schema_version"], "session_artifact_lineage_v1")
        self.assertTrue(artifact_lineage["available"])
        self.assertTrue(artifact_lineage["validation"]["ok"], artifact_lineage["validation"]["errors"])
        self.assertEqual(artifact_lineage["all_artifacts_count"], 16)
        self.assertEqual(artifact_lineage["artifacts_count"], 16)
        self.assertEqual(artifact_lineage["handoff_edges_count"], 4)
        self.assertEqual(data_facts_lineage["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_lineage["artifacts_count"], 3)
        self.assertEqual(data_facts_lineage["handoff_edges_count"], 1)
        self.assertEqual(terminal_lineage["filters"]["terminal_only"], True)
        self.assertEqual(terminal_lineage["artifacts_count"], len(terminal_lineage["terminal_artifact_keys"]))
        self.assertTrue(all(item["terminal"] for item in terminal_lineage["artifacts"]))
        self.assertTrue(transcript_exists)
        self.assertEqual(result["transcript_summary"]["session_id"], session["session_id"])
        self.assertEqual(result["transcript_summary"]["run_id"], session["run_id"])
        self.assertEqual(result["transcript_summary"]["entries_count"], result["conversation_state"]["messages_count"])
        self.assertEqual(transcript_browser["schema_version"], "session_transcript_v1")
        self.assertTrue(transcript_browser["available"])
        self.assertTrue(transcript_browser["validation"]["ok"], transcript_browser["validation"]["errors"])
        self.assertEqual(transcript_browser["all_entries_count"], result["transcript_summary"]["entries_count"])
        self.assertEqual(transcript_browser["entries_count"], 5)
        self.assertTrue(transcript_browser["has_more"])
        self.assertEqual(set(transcript_browser["agents"]), set(expected_agents))
        self.assertIn("assistant", transcript_browser["roles"])
        self.assertIn("tool_use", transcript_browser["block_types"])
        self.assertEqual(data_facts_tool_use_transcript["filters"]["agent"], "data-facts")
        self.assertEqual(data_facts_tool_use_transcript["filters"]["block_type"], "tool_use")
        self.assertGreater(data_facts_tool_use_transcript["entries_count"], 0)
        self.assertTrue(all(entry["agent_type"] == "data-facts" for entry in data_facts_tool_use_transcript["entries"]))
        self.assertTrue(all("tool_use" in entry["block_types"] for entry in data_facts_tool_use_transcript["entries"]))
        self.assertEqual(transcript_entries[0]["session_id"], session["session_id"])
        self.assertEqual(transcript_entries[0]["message_schema_version"], "claude_message_envelope_v0")
        self.assertTrue(result["transcript_summary"]["validation"]["ok"])
        self.assertTrue(status["integrity"]["claude_transcript_validation"]["ok"])
        self.assertEqual(status["integrity"]["claude_transcript_entries_count"], result["transcript_summary"]["entries_count"])
        self.assertEqual(summary["claude_transcript"]["entries_count"], result["transcript_summary"]["entries_count"])
        self.assertEqual(summary["hooks"]["invocations_count"], result["hook_summary"]["invocations_count"])
        self.assertEqual(summary["tasks"]["tasks_count"], result["task_summary"]["tasks_count"])
        self.assertEqual(summary["tools"]["tools_count"], result["tool_registry_summary"]["tools_count"])
        self.assertEqual(summary["runtime_state"]["summary"]["estimated_tokens"], result["token_budget"]["estimated_tokens"])
        self.assertEqual(summary["agent_manifest"]["all_agents_count"], len(expected_agents))
        self.assertEqual(summary["agent_prompts"]["all_prompts_count"], agent_prompts["all_prompts_count"])
        self.assertEqual(summary["settings"]["all_sources_count"], settings_surface["all_sources_count"])
        self.assertEqual(summary["skills"]["all_skills_count"], skill_palette["all_skills_count"])
        self.assertEqual(summary["handoffs"]["all_handoffs_count"], handoffs["all_handoffs_count"])
        self.assertTrue(summary["permission_state"]["ok"])
        self.assertTrue(summary["settings_context"]["ok"])
        self.assertTrue(summary["skill_context"]["ok"])
        self.assertTrue(summary["command_context"]["ok"])
        self.assertTrue(status["integrity"]["settings_context_validation"]["ok"])
        self.assertTrue(status["integrity"]["session_settings_validation"]["ok"])
        self.assertEqual(status["integrity"]["session_settings_sources_count"], settings_surface["all_sources_count"])
        self.assertTrue(status["integrity"]["skill_context_validation"]["ok"])
        self.assertTrue(status["integrity"]["command_context_validation"]["ok"])
        self.assertEqual(resume["resume"]["claude_transcript"]["entries_count"], result["transcript_summary"]["entries_count"])
        self.assertEqual(resume["resume"]["hooks"]["invocations_count"], result["hook_summary"]["invocations_count"])
        self.assertEqual(resume["resume"]["tasks"]["tasks_count"], result["task_summary"]["tasks_count"])
        self.assertEqual(resume["resume"]["tools"]["tools_count"], result["tool_registry_summary"]["tools_count"])
        self.assertEqual(resume["resume"]["runtime_state"]["summary"]["estimated_tokens"], result["token_budget"]["estimated_tokens"])
        self.assertEqual(resume["resume"]["agent_manifest"]["all_agents_count"], len(expected_agents))
        self.assertEqual(resume["resume"]["agent_prompts"]["all_prompts_count"], agent_prompts["all_prompts_count"])
        self.assertEqual(resume["resume"]["settings"]["all_sources_count"], settings_surface["all_sources_count"])
        self.assertEqual(resume["resume"]["skills"]["all_skills_count"], skill_palette["all_skills_count"])
        self.assertEqual(resume["resume"]["handoffs"]["all_handoffs_count"], handoffs["all_handoffs_count"])
        self.assertTrue(resume["resume"]["permission_state"]["ok"])
        self.assertTrue(resume["resume"]["settings_context"]["ok"])
        self.assertTrue(resume["resume"]["skill_context"]["ok"])
        self.assertTrue(resume["resume"]["command_context"]["ok"])
        self.assertTrue(resume["resume"]["integrity"]["permission_state_validation"]["ok"])
        self.assertTrue(status["integrity"]["hook_validation"]["ok"])
        self.assertEqual(status["integrity"]["hook_invocations_count"], result["hook_summary"]["invocations_count"])
        self.assertTrue(status["integrity"]["task_validation"]["ok"])
        self.assertEqual(status["integrity"]["task_states_count"], len(expected_agents))
        self.assertTrue(status["integrity"]["artifact_lineage_validation"]["ok"])
        self.assertEqual(status["integrity"]["artifact_lineage_artifacts_count"], 16)
        self.assertTrue(status["integrity"]["runtime_state_validation"]["ok"])
        self.assertEqual(status["integrity"]["runtime_state_agents_count"], len(expected_agents))
        self.assertTrue(status["integrity"]["agent_manifest_validation"]["ok"])
        self.assertEqual(status["integrity"]["agent_manifest_agents_count"], len(expected_agents))
        self.assertTrue(status["integrity"]["agent_prompts_validation"]["ok"])
        self.assertEqual(status["integrity"]["agent_prompts_count"], agent_prompts["all_prompts_count"])
        self.assertTrue(status["integrity"]["session_skills_validation"]["ok"])
        self.assertEqual(status["integrity"]["session_skills_count"], skill_palette["all_skills_count"])
        self.assertTrue(status["integrity"]["session_handoffs_validation"]["ok"])
        self.assertEqual(status["integrity"]["session_handoffs_count"], handoffs["all_handoffs_count"])
        self.assertTrue(status["integrity"]["tool_validation"]["ok"])
        self.assertEqual(status["integrity"]["tools_count"], result["tool_registry_summary"]["tools_count"])
        self.assertTrue(status["integrity"]["ok"])
        self.assertEqual(artifacts["artifacts_count"], 16)
        self.assertEqual(knowledge["mandate"]["dossier_id"], "D-001")
        self.assertEqual(knowledge["market_evidence"]["comparables_count"], 1)
        self.assertGreater(knowledge["valuation"]["values"]["approche_comparative"], 0)
        self.assertEqual(knowledge["compliance"]["status"], "PRET_REVISION_FINALE")
        self.assertTrue(knowledge["redaction"]["brouillon_rapport_available"])
        self.assertTrue(
            {"search_comparables", "run_calculation", "validate_schema", "format_document", "write_file"}.issubset(
                {event.get("tool") for event in result["events"]}
            )
        )

    def test_start_runtime_can_run_opt_in_claude_live_pipeline_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                payload = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0,
                        "claude_model_provider": {"provider": "fake"},
                    }
                )
                session = payload["session"]
                result = payload["result"]
                model_client = session_model_client(session["session_id"])
                live_replay = session_live_replay(session["session_id"])
                status = session_status(session["session_id"])
                bundle = session_claude_bundle(session["session_id"])
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        expected_agents = ["data-facts", "comps-market", "valuation-draft", "compliance-qa", "redaction"]
        self.assertEqual(session["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0)
        self.assertEqual(result["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0)
        self.assertEqual(result["pipeline_scope"], "multi_agent_live:claude")
        self.assertEqual(result["agents"], expected_agents)
        self.assertEqual(result["live_adapter"]["schema_version"], "claude_live_adapter_v0")
        self.assertTrue(result["live_adapter"]["enabled"])
        self.assertEqual(result["live_adapter"]["agent_type"], "claude-pipeline")
        self.assertEqual(set(result["model_client_by_agent"]), set(expected_agents))
        self.assertEqual(set(result["model_live_loop_by_agent"]), set(expected_agents))
        self.assertTrue(result["model_client"]["enabled"])
        self.assertEqual(result["model_client"]["schema_version"], "claude_pipeline_model_client_summary_v0")
        self.assertEqual(result["model_client"]["requests_count"], 5)
        self.assertEqual(result["model_client"]["responses_count"], 5)
        self.assertEqual(result["model_client"]["live_tool_loop"]["agents_count"], 5)
        self.assertEqual(result["model_client"]["live_tool_loop"]["turns_count"], 5)
        self.assertTrue(model_client["available"])
        self.assertEqual(model_client["runtime_mode"], api.RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0)
        self.assertEqual(model_client["model_client"]["requests_count"], 5)
        self.assertEqual(model_client["live_tool_loop"]["schema_version"], "claude_pipeline_live_tool_loop_v0")
        self.assertTrue(live_replay["available"])
        self.assertEqual(set(live_replay["live_tool_loop_by_agent"]), set(expected_agents))
        self.assertGreater(live_replay["transcript_replay"]["tool_use_count"], 0)
        self.assertTrue(live_replay["transcript_replay"]["validation"]["ok"])
        self.assertTrue(live_replay["permission_replay"]["ok"])
        self.assertTrue(live_replay["ok"], live_replay["validation"])
        self.assertTrue(status["integrity"]["model_client_enabled"])
        self.assertTrue(status["integrity"]["model_client_ok"])
        self.assertTrue(status["integrity"]["ok"], status["integrity"]["errors"])
        self.assertEqual(bundle["counts"]["model_client_requests"], 5)
        self.assertEqual(bundle["counts"]["model_live_turns"], 5)
        self.assertEqual(bundle["counts"]["live_retry_candidates"], 0)
        self.assertTrue(bundle["section_health"]["model_client"])
        self.assertTrue(bundle["section_health"]["live_replay"])

    def test_start_runtime_rejects_unknown_runtime_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                with self.assertRaisesRegex(ValueError, "runtime_mode invalide"):
                    start_runtime({"fixture": "case_nominal.json", "runtime_mode": "missing"})
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

    def test_session_slash_command_executes_and_persists_claude_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                before_result = json.loads(Path(started["session"]["result_path"]).read_text(encoding="utf-8"))
                before_events_count = len(before_result["events"])
                before_messages_count = len(before_result["messages"])
                palette = session_commands(session_id)
                history_before = session_command_history(session_id)

                executed = execute_session_slash_command({"session_id": session_id, "command": "/cost"})
                palette_after = session_commands(session_id)
                history = session_command_history(session_id)
                cost_history = session_command_history(session_id, command="cost", ok="true")
                session = executed["session"]
                result = json.loads(Path(session["result_path"]).read_text(encoding="utf-8"))
                events = [
                    json.loads(line)
                    for line in Path(session["events_path"]).read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                transcript_entries = [
                    json.loads(line)
                    for line in Path(session["claude_transcript_path"]).read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                summary = session_summary(session_id)
                resume = resume_session(session_id)
                status = session_status(session_id)
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(palette["schema_version"], "session_slash_command_palette_v1")
        self.assertIn("cost", palette["executable_command_names"])
        self.assertIn("status", palette["executable_command_names"])
        self.assertIn("analyse-extraction-faits", palette["model_invocable_command_names"])
        self.assertEqual(palette["history"]["commands_count"], 0)
        self.assertEqual(history_before["schema_version"], "session_slash_command_history_browser_v1")
        self.assertFalse(history_before["available"])
        self.assertTrue(history_before["validation"]["ok"], history_before["validation"]["errors"])
        self.assertEqual(executed["schema_version"], "session_slash_command_v1")
        self.assertTrue(executed["command_result"]["ok"], executed["command_result"]["errors"])
        self.assertEqual(executed["command_result"]["command_name"], "cost")
        self.assertEqual(executed["command_result"]["event"]["event"], "slash_command_executed")
        self.assertEqual(executed["command_result"]["event"]["sequence"], before_events_count + 1)
        self.assertEqual(executed["command_result"]["message"]["content_block_types"], ["local_command_output"])
        self.assertEqual(executed["command_summary"]["commands_count"], 1)
        self.assertEqual(session["slash_command_summary"]["latest"]["command_name"], "cost")
        self.assertEqual(len(events), before_events_count + 1)
        self.assertEqual(len(result["messages"]), before_messages_count + 1)
        self.assertEqual(result["messages"][-1]["content"][0]["command"], "/cost")
        self.assertEqual(len(transcript_entries), before_messages_count + 1)
        self.assertEqual(transcript_entries[-1]["block_types"], ["local_command_output"])
        self.assertEqual(summary["slash_commands"]["commands_count"], 1)
        self.assertEqual(summary["command_history"]["all_commands_count"], 1)
        self.assertEqual(resume["resume"]["slash_commands"]["commands_count"], 1)
        self.assertEqual(resume["resume"]["command_history"]["all_commands_count"], 1)
        self.assertEqual(palette_after["history"]["commands_count"], 1)
        self.assertEqual(palette_after["history"]["latest"]["command_name"], "cost")
        self.assertEqual(history["schema_version"], "session_slash_command_history_browser_v1")
        self.assertTrue(history["available"])
        self.assertTrue(history["validation"]["ok"], history["validation"]["errors"])
        self.assertEqual(history["all_commands_count"], 1)
        self.assertEqual(history["commands_count"], 1)
        self.assertEqual(history["latest"]["command_name"], "cost")
        self.assertEqual(history["all_summary"]["ok_count"], 1)
        self.assertEqual(cost_history["filters"]["command"], "cost")
        self.assertEqual(cost_history["filters"]["ok"], True)
        self.assertEqual(cost_history["commands_count"], 1)
        self.assertEqual(cost_history["records"][0]["command_display_name"], "/cost")
        self.assertTrue(status["integrity"]["ok"], status["integrity"]["errors"])
        self.assertEqual(status["integrity"]["slash_command_records_count"], 1)
        self.assertTrue(status["integrity"]["slash_command_history_validation"]["ok"])

    def test_session_slash_command_endpoint_respects_filtered_command_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                        "claude_settings": {"commands": {"disabled": ["cost"]}},
                    }
                )
                session_id = started["session"]["session_id"]
                payload = self.http_json(
                    "POST",
                    host,
                    port,
                    "/session/command",
                    {"session_id": session_id, "command": "/cost"},
                )
                palette = self.http_json("GET", host, port, f"/session/commands?session_id={session_id}")
                history = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/command-history?session_id={session_id}&status=unavailable&ok=false",
                )
                status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertFalse(payload["command_result"]["ok"])
        self.assertEqual(payload["command_result"]["status"], "unavailable")
        self.assertEqual(payload["command_result"]["errors"], ["command_not_available"])
        self.assertEqual(payload["command_result"]["event"]["event"], "slash_command_blocked")
        self.assertEqual(payload["command_summary"]["blocked_count"], 1)
        self.assertNotIn("cost", palette["command_names"])
        self.assertEqual(palette["history"]["blocked_count"], 1)
        self.assertEqual(history["schema_version"], "session_slash_command_history_browser_v1")
        self.assertEqual(history["filters"]["status"], "unavailable")
        self.assertEqual(history["filters"]["ok"], False)
        self.assertEqual(history["commands_count"], 1)
        self.assertEqual(history["records"][0]["command_name"], "cost")
        self.assertFalse(history["records"][0]["ok"])
        self.assertTrue(history["validation"]["ok"], history["validation"]["errors"])
        self.assertIn("status", palette["executable_command_names"])
        self.assertTrue(status["integrity"]["ok"], status["integrity"]["errors"])

    def test_session_hooks_endpoint_exposes_filtered_claude_hook_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                all_hooks = self.http_json("GET", host, port, f"/session/hooks?session_id={session_id}")
                filtered = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/hooks?session_id={session_id}&agent=data-facts&hook_event=PostToolUse",
                )
                summary = session_summary(session_id)
                resume = resume_session(session_id)
                status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(all_hooks["schema_version"], "session_hooks_v1")
        self.assertTrue(all_hooks["available"])
        self.assertTrue(all_hooks["validation"]["ok"], all_hooks["validation"]["errors"])
        self.assertEqual(all_hooks["agents"], ["data-facts"])
        self.assertEqual(all_hooks["summary"]["hook_events"]["SessionStart"], 1)
        self.assertEqual(all_hooks["summary"]["hook_events"]["SessionEnd"], 1)
        self.assertEqual(all_hooks["summary"]["hook_events"]["PreToolUse"], 3)
        self.assertEqual(all_hooks["summary"]["hook_events"]["PostToolUse"], 3)
        self.assertEqual(filtered["filters"]["agent"], "data-facts")
        self.assertEqual(filtered["filters"]["hook_event"], "PostToolUse")
        self.assertEqual(filtered["invocations_count"], 3)
        self.assertEqual(filtered["summary"]["hook_events"], {"PostToolUse": 3})
        self.assertEqual(summary["hooks"]["invocations_count"], all_hooks["all_invocations_count"])
        self.assertEqual(resume["resume"]["hooks"]["invocations_count"], all_hooks["all_invocations_count"])
        self.assertEqual(status["integrity"]["hook_invocations_count"], all_hooks["all_invocations_count"])
        self.assertTrue(status["integrity"]["hook_validation"]["ok"])

    def test_session_tasks_endpoint_exposes_filtered_claude_task_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                all_tasks = self.http_json("GET", host, port, f"/session/tasks?session_id={session_id}")
                completed = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/tasks?session_id={session_id}&agent=data-facts&status=completed",
                )
                summary = session_summary(session_id)
                resume = resume_session(session_id)
                status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(all_tasks["schema_version"], "session_tasks_v1")
        self.assertTrue(all_tasks["available"])
        self.assertTrue(all_tasks["validation"]["ok"], all_tasks["validation"]["errors"])
        self.assertEqual(all_tasks["agents"], ["data-facts"])
        self.assertEqual(all_tasks["statuses"], ["completed"])
        self.assertEqual(all_tasks["all_tasks_count"], 3)
        self.assertEqual(all_tasks["summary"]["tasks_count"], 3)
        self.assertEqual(all_tasks["summary"]["completed_count"], 3)
        self.assertEqual(completed["filters"]["agent"], "data-facts")
        self.assertEqual(completed["filters"]["status"], "completed")
        self.assertEqual(completed["tasks_count"], 3)
        self.assertEqual({task["artifact"] for task in completed["tasks"]}, {"fiche_bien.json", "source_index.json", "timeline_faits.json"})
        self.assertEqual(summary["tasks"]["tasks_count"], all_tasks["all_tasks_count"])
        self.assertEqual(resume["resume"]["tasks"]["tasks_count"], all_tasks["all_tasks_count"])
        self.assertEqual(status["integrity"]["task_states_count"], 1)
        self.assertTrue(status["integrity"]["task_validation"]["ok"])

    def test_session_transcript_endpoint_browses_filtered_claude_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                transcript = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/transcript?session_id={session_id}&limit=2",
                )
                tool_use = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/transcript?session_id={session_id}&agent=data-facts&block_type=tool_use&limit=10",
                )
                paged = session_transcript(session_id, offset=1, limit=1)
                status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(transcript["schema_version"], "session_transcript_v1")
        self.assertTrue(transcript["available"])
        self.assertTrue(transcript["validation"]["ok"], transcript["validation"]["errors"])
        self.assertEqual(transcript["entries_count"], 2)
        self.assertTrue(transcript["has_more"])
        self.assertEqual(transcript["filters"]["limit"], 2)
        self.assertEqual(transcript["agents"], ["data-facts"])
        self.assertIn("assistant", transcript["roles"])
        self.assertIn("tool_use", transcript["block_types"])
        self.assertEqual(tool_use["filters"]["agent"], "data-facts")
        self.assertEqual(tool_use["filters"]["block_type"], "tool_use")
        self.assertGreater(tool_use["entries_count"], 0)
        self.assertGreaterEqual(tool_use["filtered_summary"]["tool_use_count"], tool_use["filtered_entries_count"])
        self.assertTrue(all(entry["agent_type"] == "data-facts" for entry in tool_use["entries"]))
        self.assertTrue(all("tool_use" in entry["block_types"] for entry in tool_use["entries"]))
        self.assertEqual(paged["filters"]["offset"], 1)
        self.assertEqual(paged["entries_count"], 1)
        self.assertEqual(paged["entries"][0]["sequence"], 2)
        self.assertTrue(status["integrity"]["claude_transcript_validation"]["ok"])
        self.assertEqual(status["integrity"]["claude_transcript_entries_count"], transcript["all_entries_count"])

    def test_session_tools_endpoint_exposes_model_facing_tool_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                tools = self.http_json("GET", host, port, f"/session/tools?session_id={session_id}")
                write_tool = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/tools?session_id={session_id}&tool=write_file",
                )
                read_tools = session_tools(session_id, agent="data-facts", permission="runtime_read")
                summary = session_summary(session_id)
                resume = resume_session(session_id)
                status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(tools["schema_version"], "session_tools_v1")
        self.assertTrue(tools["available"])
        self.assertTrue(tools["validation"]["ok"], tools["validation"]["errors"])
        self.assertEqual(tools["agents"], ["data-facts"])
        self.assertIn("read_file", tools["all_tool_names"])
        self.assertIn("write_file", tools["all_tool_names"])
        self.assertEqual(tools["all_summary"]["schema_version"], "claude_tool_registry_summary_v0")
        self.assertTrue(tools["all_summary"]["ok"], tools["all_summary"]["validation_errors"])
        self.assertEqual(len(tools["model_facing_tools"]), tools["tools_count"])
        self.assertTrue(all("input_schema" in item for item in tools["model_facing_tools"]))
        self.assertEqual(write_tool["filters"]["tool"], "write_file")
        self.assertEqual(write_tool["tools_count"], 1)
        self.assertTrue(write_tool["tools"][0]["destructive"])
        self.assertEqual(write_tool["tools"][0]["model_facing_schema"]["name"], "write_file")
        self.assertEqual(read_tools["filters"]["permission"], "runtime_read")
        self.assertGreater(read_tools["tools_count"], 0)
        self.assertTrue(all(tool["permission"] == "runtime_read" for tool in read_tools["tools"]))
        self.assertEqual(summary["tools"]["tools_count"], tools["all_tools_count"])
        self.assertEqual(resume["resume"]["tools"]["tools_count"], tools["all_tools_count"])
        self.assertEqual(status["integrity"]["tools_count"], tools["all_tools_count"])
        self.assertTrue(status["integrity"]["tool_validation"]["ok"])

    def test_session_claude_endpoint_exposes_controller_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                bundle = self.http_json(
                    "GET",
                    host,
                    port,
                    (
                        f"/session/claude?session_id={session_id}"
                        "&agent=data-facts&permission=runtime_read&block_type=tool_use&limit=2"
                    ),
                )
                lineage = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/artifact-lineage?session_id={session_id}&agent=data-facts",
                )
                runtime_state = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/runtime-state?session_id={session_id}&agent=data-facts",
                )
                agents = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/agents?session_id={session_id}&agent=data-facts",
                )
                agent_prompts = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/agent-prompts?session_id={session_id}&agent=data-facts",
                )
                model_client = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/model-client?session_id={session_id}",
                )
                skills = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/skills?session_id={session_id}&agent=data-facts&skill=analyse-extraction-faits",
                )
                settings = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/settings?session_id={session_id}&key=permissions.defaultMode",
                )
                handoffs = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/handoffs?session_id={session_id}&agent=data-facts",
                )
                command_history = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/command-history?session_id={session_id}",
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(bundle["schema_version"], "session_claude_bundle_v1")
        self.assertEqual(bundle["session_id"], session_id)
        self.assertEqual(bundle["routes"]["bundle"], "/session/claude")
        self.assertEqual(bundle["routes"]["action"], "/session/claude/action")
        self.assertEqual(bundle["routes"]["action_snapshot"], "/session/claude/action/snapshot")
        self.assertEqual(bundle["routes"]["artifact_lineage"], "/session/artifact-lineage")
        self.assertEqual(bundle["routes"]["runtime_state"], "/session/runtime-state")
        self.assertEqual(bundle["routes"]["agents"], "/session/agents")
        self.assertEqual(bundle["routes"]["agent_prompts"], "/session/agent-prompts")
        self.assertEqual(bundle["routes"]["model_client"], "/session/model-client")
        self.assertEqual(bundle["routes"]["skills"], "/session/skills")
        self.assertEqual(bundle["routes"]["settings"], "/session/settings")
        self.assertEqual(bundle["routes"]["handoffs"], "/session/handoffs")
        self.assertEqual(bundle["routes"]["command_history"], "/session/command-history")
        self.assertEqual(bundle["filters"]["agent"], "data-facts")
        self.assertEqual(bundle["filters"]["permission"], "runtime_read")
        self.assertEqual(bundle["filters"]["block_type"], "tool_use")
        self.assertEqual(bundle["summary"]["schema_version"], "session_summary_v1")
        self.assertEqual(bundle["commands"]["schema_version"], "session_slash_command_palette_v1")
        self.assertEqual(bundle["permissions"]["schema_version"], "session_claude_permissions_v1")
        self.assertEqual(bundle["actions"]["schema_version"], "session_claude_action_history_v1")
        self.assertEqual(bundle["actions"]["actions_count"], 0)
        self.assertEqual(bundle["hooks"]["schema_version"], "session_hooks_v1")
        self.assertEqual(bundle["tasks"]["schema_version"], "session_tasks_v1")
        self.assertEqual(bundle["tools"]["schema_version"], "session_tools_v1")
        self.assertEqual(bundle["transcript"]["schema_version"], "session_transcript_v1")
        self.assertTrue(bundle["section_health"]["summary"])
        self.assertTrue(bundle["section_health"]["permissions"])
        self.assertTrue(bundle["section_health"]["tools"])
        self.assertTrue(bundle["section_health"]["agents"])
        self.assertTrue(bundle["section_health"]["agent_prompts"])
        self.assertTrue(bundle["section_health"]["skills"])
        self.assertTrue(bundle["section_health"]["settings"])
        self.assertTrue(bundle["section_health"]["handoffs"])
        self.assertTrue(bundle["section_health"]["command_history"])
        self.assertTrue(bundle["section_health"]["artifact_lineage"])
        self.assertTrue(bundle["section_health"]["runtime_state"])
        self.assertTrue(bundle["integrity"]["ok"])
        self.assertTrue(bundle["ok"], bundle["section_health"])
        self.assertEqual(bundle["artifact_lineage"]["schema_version"], "session_artifact_lineage_v1")
        self.assertFalse(bundle["artifact_lineage"]["available"])
        self.assertEqual(bundle["runtime_state"]["schema_version"], "session_claude_runtime_state_v1")
        self.assertTrue(bundle["runtime_state"]["available"])
        self.assertEqual(bundle["agent_manifest"]["schema_version"], "session_claude_agent_manifest_v1")
        self.assertTrue(bundle["agent_manifest"]["available"])
        self.assertEqual(bundle["agent_manifest"]["agents_count"], 1)
        self.assertEqual(bundle["agent_prompts"]["schema_version"], "session_claude_agent_prompts_v1")
        self.assertTrue(bundle["agent_prompts"]["available"])
        self.assertTrue(bundle["agent_prompts"]["validation"]["ok"], bundle["agent_prompts"]["validation"]["errors"])
        self.assertEqual(bundle["agent_prompts"]["prompts_count"], 1)
        self.assertEqual(bundle["skills"]["schema_version"], "session_skills_v1")
        self.assertTrue(bundle["skills"]["available"])
        self.assertEqual(bundle["skills"]["filters"]["agent"], "data-facts")
        self.assertEqual(bundle["settings"]["schema_version"], "session_settings_v1")
        self.assertTrue(bundle["settings"]["available"])
        self.assertEqual(bundle["settings"]["runtime_options"]["permission_mode"], "default")
        self.assertEqual(bundle["handoffs"]["schema_version"], "session_handoffs_v1")
        self.assertFalse(bundle["handoffs"]["available"])
        self.assertTrue(bundle["handoffs"]["validation"]["ok"], bundle["handoffs"]["validation"]["errors"])
        self.assertEqual(bundle["command_history"]["schema_version"], "session_slash_command_history_browser_v1")
        self.assertFalse(bundle["command_history"]["available"])
        self.assertTrue(bundle["command_history"]["validation"]["ok"], bundle["command_history"]["validation"]["errors"])
        self.assertEqual(lineage["schema_version"], "session_artifact_lineage_v1")
        self.assertEqual(lineage["filters"]["agent"], "data-facts")
        self.assertFalse(lineage["available"])
        self.assertEqual(runtime_state["schema_version"], "session_claude_runtime_state_v1")
        self.assertEqual(runtime_state["filters"]["agent"], "data-facts")
        self.assertTrue(runtime_state["available"])
        self.assertTrue(runtime_state["validation"]["ok"], runtime_state["validation"]["errors"])
        self.assertEqual(runtime_state["summary"]["agents_count"], 1)
        self.assertEqual(agents["schema_version"], "session_claude_agent_manifest_v1")
        self.assertEqual(agents["filters"]["agent"], "data-facts")
        self.assertTrue(agents["available"])
        self.assertTrue(agents["validation"]["ok"], agents["validation"]["errors"])
        self.assertEqual(agents["agents_count"], 1)
        self.assertEqual(agents["agents"][0]["agent_type"], "data-facts")
        self.assertEqual(agent_prompts["schema_version"], "session_claude_agent_prompts_v1")
        self.assertEqual(agent_prompts["filters"]["agent"], "data-facts")
        self.assertEqual(agent_prompts["prompts_count"], 1)
        self.assertEqual(agent_prompts["prompts"][0]["sections_count"], 3)
        self.assertIn("Dossier: D-001", agent_prompts["prompts"][0]["rendered_prompt"])
        self.assertEqual(model_client["schema_version"], "session_model_client_v1")
        self.assertFalse(model_client["available"])
        self.assertFalse(model_client["model_client"]["enabled"])
        self.assertEqual(model_client["model_client"]["requests_count"], 0)
        self.assertEqual(skills["schema_version"], "session_skills_v1")
        self.assertEqual(skills["filters"]["agent"], "data-facts")
        self.assertEqual(skills["filters"]["skill"], "analyse-extraction-faits")
        self.assertTrue(skills["available"])
        self.assertTrue(skills["validation"]["ok"], skills["validation"]["errors"])
        self.assertEqual(skills["skills_count"], 1)
        self.assertEqual(skills["skills"][0]["name"], "analyse-extraction-faits")
        self.assertEqual(settings["schema_version"], "session_settings_v1")
        self.assertEqual(settings["filters"]["key"], "permissions.defaultMode")
        self.assertTrue(settings["available"])
        self.assertTrue(settings["validation"]["ok"], settings["validation"]["errors"])
        self.assertEqual(settings["effective_items"][0]["value"], "default")
        self.assertEqual(handoffs["schema_version"], "session_handoffs_v1")
        self.assertEqual(handoffs["filters"]["agent"], "data-facts")
        self.assertFalse(handoffs["available"])
        self.assertTrue(handoffs["validation"]["ok"], handoffs["validation"]["errors"])
        self.assertEqual(command_history["schema_version"], "session_slash_command_history_browser_v1")
        self.assertFalse(command_history["available"])
        self.assertTrue(command_history["validation"]["ok"], command_history["validation"]["errors"])
        self.assertEqual(bundle["tools"]["filters"]["permission"], "runtime_read")
        self.assertTrue(all(tool["permission"] == "runtime_read" for tool in bundle["tools"]["tools"]))
        self.assertEqual(bundle["transcript"]["entries_count"], 2)
        self.assertTrue(all("tool_use" in entry["block_types"] for entry in bundle["transcript"]["entries"]))
        self.assertEqual(bundle["counts"]["tools"], bundle["tools"]["tools_count"])
        self.assertEqual(bundle["counts"]["transcript_entries"], bundle["transcript"]["entries_count"])

    def test_session_claude_action_executes_command_and_updates_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                before = session_claude_bundle(session_id, limit=5)
                command_action = self.http_json(
                    "POST",
                    host,
                    port,
                    "/session/claude/action",
                    {"session_id": session_id, "action": "execute_command", "command": "/cost", "limit": 5},
                )
                permission_action = self.http_json(
                    "POST",
                    host,
                    port,
                    "/session/claude/action",
                    {
                        "session_id": session_id,
                        "action": "update_permissions",
                        "update": {
                            "type": "addDirectories",
                            "destination": "session",
                            "directories": ["C:\\Users\\simon\\claude-code-project"],
                        },
                    },
                )
                refresh = session_claude_action({"session_id": session_id, "action": "refresh", "limit": 5})
                after_permissions = session_permissions(session_id)
                status = session_status(session_id)
                history_records = [
                    json.loads(line)
                    for line in Path(refresh["action_summary"]["path"]).read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                command_snapshot_path = Path(command_action["snapshot"]["path"])
                permission_snapshot_path = Path(permission_action["snapshot"]["path"])
                refresh_snapshot_path = Path(refresh["snapshot"]["path"])
                snapshot_paths_exist = [
                    command_snapshot_path.exists(),
                    permission_snapshot_path.exists(),
                    refresh_snapshot_path.exists(),
                ]
                command_snapshot = json.loads(command_snapshot_path.read_text(encoding="utf-8"))
                permission_snapshot = json.loads(permission_snapshot_path.read_text(encoding="utf-8"))
                refresh_snapshot = json.loads(refresh_snapshot_path.read_text(encoding="utf-8"))
                command_snapshot_http = self.http_json(
                    "GET",
                    host,
                    port,
                    (
                        "/session/claude/action/snapshot"
                        f"?session_id={session_id}&action_id={command_action['action_id']}"
                    ),
                )
                latest_snapshot_http = self.http_json(
                    "GET",
                    host,
                    port,
                    f"/session/claude/action/snapshot?session_id={session_id}",
                )
                action_history_path = Path(refresh["action_summary"]["path"])
                action_history_path.unlink()
                missing_status = session_status(session_id)
                corrupted_records = [dict(record) for record in history_records]
                corrupted_records[0]["schema_version"] = "broken"
                corrupted_records[1]["session_id"] = "wrong-session"
                action_history_path.write_text(
                    "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in corrupted_records),
                    encoding="utf-8",
                )
                corrupt_status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(command_action["schema_version"], "session_claude_action_v1")
        self.assertEqual(command_action["action"], "execute_command")
        self.assertTrue(command_action["mutation_applied"])
        self.assertTrue(command_action["ok"], command_action["bundle"]["section_health"])
        self.assertEqual(command_action["action_result_schema_version"], "session_slash_command_v1")
        self.assertEqual(command_action["snapshot"]["schema_version"], "session_claude_action_snapshot_v1")
        self.assertEqual(command_action["snapshot"]["snapshot_stage"], "completed")
        self.assertEqual(command_action["snapshot"]["action_id"], command_action["action_id"])
        self.assertEqual(command_action["snapshot"]["action"], "execute_command")
        self.assertEqual(command_action["snapshot"]["before"]["actions"]["count"], 0)
        self.assertEqual(command_action["snapshot"]["after"]["actions"]["count"], 1)
        self.assertEqual(command_snapshot["snapshot_stage"], "completed")
        self.assertEqual(command_snapshot_http["schema_version"], "session_claude_action_snapshot_read_v1")
        self.assertEqual(command_snapshot_http["action_id"], command_action["action_id"])
        self.assertEqual(command_snapshot_http["path"], command_action["snapshot"]["path"])
        self.assertEqual(command_snapshot_http["record"]["snapshot_path"], command_action["snapshot"]["path"])
        self.assertEqual(command_snapshot_http["snapshot"], command_snapshot)
        self.assertTrue(command_snapshot_http["validation"]["ok"])
        self.assertEqual(command_action["action_summary"]["schema_version"], "session_claude_action_summary_v1")
        self.assertEqual(command_action["action_summary"]["actions_count"], 1)
        self.assertEqual(command_action["action_summary"]["mutation_count"], 1)
        self.assertEqual(command_action["action_summary"]["snapshots_count"], 1)
        self.assertEqual(command_action["action_summary"]["latest"]["snapshot_path"], command_action["snapshot"]["path"])
        self.assertEqual(command_action["action_summary"]["latest"]["action"], "execute_command")
        self.assertTrue(command_action["action_result"]["command_result"]["ok"])
        self.assertEqual(command_action["action_result"]["command_result"]["command_name"], "cost")
        self.assertEqual(command_action["bundle"]["commands"]["history"]["commands_count"], 1)
        self.assertEqual(command_action["bundle"]["actions"]["actions_count"], 1)
        self.assertEqual(command_action["bundle"]["actions"]["mutation_count"], 1)
        self.assertEqual(command_action["bundle"]["actions"]["snapshots_count"], 1)
        self.assertEqual(command_action["bundle"]["counts"]["controller_snapshots"], 1)
        self.assertEqual(command_action["bundle"]["actions"]["latest"]["command_name"], "cost")
        self.assertEqual(
            command_action["bundle"]["counts"]["all_transcript_entries"],
            before["counts"]["all_transcript_entries"] + 1,
        )
        self.assertEqual(command_action["controller"]["routes"]["action"], "/session/claude/action")
        self.assertEqual(command_action["controller"]["commands"]["count"], command_action["bundle"]["commands"]["commands_count"])
        self.assertEqual(command_action["controller"]["actions"]["count"], 1)
        self.assertEqual(command_action["controller"]["actions"]["snapshots_count"], 1)

        self.assertEqual(permission_action["schema_version"], "session_claude_action_v1")
        self.assertEqual(permission_action["action"], "update_permissions")
        self.assertTrue(permission_action["mutation_applied"])
        self.assertTrue(permission_action["ok"], permission_action["bundle"]["section_health"])
        self.assertEqual(permission_action["snapshot"]["action_id"], permission_action["action_id"])
        self.assertEqual(permission_action["snapshot"]["before"]["actions"]["count"], 1)
        self.assertEqual(permission_action["snapshot"]["after"]["actions"]["count"], 2)
        self.assertEqual(permission_snapshot["action_result"]["permission_update"]["updates_applied_count"], 1)
        self.assertEqual(permission_action["action_result_schema_version"], "session_claude_permission_update_v1")
        self.assertEqual(permission_action["action_result"]["updates_applied_count"], 1)
        self.assertEqual(permission_action["action_result"]["latest_update"]["type"], "addDirectories")
        self.assertEqual(permission_action["action_summary"]["actions_count"], 2)
        self.assertEqual(permission_action["action_summary"]["mutation_count"], 2)
        self.assertEqual(permission_action["action_summary"]["snapshots_count"], 2)
        self.assertEqual(permission_action["action_summary"]["by_action"]["execute_command"], 1)
        self.assertEqual(permission_action["action_summary"]["by_action"]["update_permissions"], 1)
        self.assertEqual(permission_action["bundle"]["actions"]["actions_count"], 2)
        self.assertEqual(permission_action["bundle"]["actions"]["latest"]["permission_latest_update_type"], "addDirectories")
        self.assertEqual(permission_action["bundle"]["counts"]["controller_snapshots"], 2)
        self.assertEqual(permission_action["bundle"]["permissions"]["summary"]["updates_count"], after_permissions["summary"]["updates_count"])
        self.assertEqual(
            permission_action["controller"]["permissions"]["decisions_count"],
            permission_action["bundle"]["permissions"]["permission_summary"]["decisions_count"],
        )
        self.assertEqual(permission_action["controller"]["actions"]["mutation_count"], 2)
        self.assertEqual(permission_action["controller"]["actions"]["snapshots_count"], 2)

        self.assertEqual(refresh["action"], "refresh")
        self.assertFalse(refresh["mutation_applied"])
        self.assertTrue(refresh["ok"], refresh["bundle"]["section_health"])
        self.assertEqual(refresh["snapshot"]["action_id"], refresh["action_id"])
        self.assertEqual(refresh["snapshot"]["before"]["actions"]["count"], 2)
        self.assertEqual(refresh["snapshot"]["after"]["actions"]["count"], 3)
        self.assertEqual(refresh_snapshot["bundle"]["counts"]["controller_snapshots"], 3)
        self.assertEqual(latest_snapshot_http["action_id"], refresh["action_id"])
        self.assertEqual(latest_snapshot_http["snapshot"], refresh_snapshot)
        self.assertEqual(latest_snapshot_http["history"]["actions_count"], 3)
        self.assertEqual(latest_snapshot_http["history"]["snapshots_count"], 3)
        self.assertTrue(latest_snapshot_http["ok"], latest_snapshot_http["validation"]["errors"])
        self.assertEqual(refresh["action_result_schema_version"], "session_claude_refresh_action_v1")
        self.assertEqual(refresh["action_summary"]["actions_count"], 3)
        self.assertEqual(refresh["action_summary"]["mutation_count"], 2)
        self.assertEqual(refresh["action_summary"]["snapshots_count"], 3)
        self.assertEqual(refresh["action_summary"]["by_action"]["refresh"], 1)
        self.assertEqual(refresh["bundle"]["commands"]["history"]["commands_count"], 1)
        self.assertEqual(refresh["bundle"]["actions"]["actions_count"], 3)
        self.assertEqual(refresh["bundle"]["actions"]["failed_count"], 0)
        self.assertEqual(refresh["bundle"]["actions"]["snapshots_count"], 3)
        self.assertEqual(refresh["bundle"]["counts"]["controller_snapshots"], 3)
        self.assertEqual(refresh["bundle"]["permissions"]["summary"]["updates_count"], after_permissions["summary"]["updates_count"])
        self.assertEqual(refresh["controller"]["actions"]["count"], 3)
        self.assertEqual(refresh["controller"]["actions"]["latest"]["action"], "refresh")
        self.assertEqual(refresh["controller"]["actions"]["snapshots_count"], 3)
        self.assertEqual(snapshot_paths_exist, [True, True, True])
        self.assertEqual([record["action"] for record in history_records], ["execute_command", "update_permissions", "refresh"])
        self.assertEqual(
            [record["action_id"] for record in history_records],
            [command_action["action_id"], permission_action["action_id"], refresh["action_id"]],
        )
        self.assertEqual(
            [record["snapshot_path"] for record in history_records],
            [command_action["snapshot"]["path"], permission_action["snapshot"]["path"], refresh["snapshot"]["path"]],
        )
        self.assertTrue(all(record["schema_version"] == "session_claude_action_record_v1" for record in history_records))
        self.assertTrue(status["integrity"]["ok"], status["integrity"]["errors"])
        self.assertEqual(status["integrity"]["claude_action_records_count"], 3)
        self.assertTrue(status["integrity"]["claude_action_history_validation"]["ok"])
        self.assertEqual(status["integrity"]["claude_action_history_validation"]["snapshots_count"], 3)
        self.assertEqual(status["integrity"]["claude_action_history_validation"]["snapshot_files_count"], 3)

        self.assertFalse(missing_status["integrity"]["ok"])
        self.assertIn("claude_action_history_missing", missing_status["integrity"]["errors"])
        self.assertFalse(missing_status["integrity"]["claude_action_history_validation"]["ok"])

        self.assertFalse(corrupt_status["integrity"]["ok"])
        self.assertIn("claude_action_history_schema_invalid:1", corrupt_status["integrity"]["errors"])
        self.assertIn("claude_action_history_session_mismatch:2", corrupt_status["integrity"]["errors"])
        self.assertFalse(corrupt_status["integrity"]["claude_action_history_validation"]["ok"])

    def test_session_permissions_endpoint_updates_claude_permission_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietRuntimeApiHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            host, port = server.server_address
            try:
                started = start_runtime(
                    {
                        "fixture": "case_nominal.json",
                        "runtime_mode": api.RUNTIME_MODE_CLAUDE_DATA_FACTS_V0,
                    }
                )
                session_id = started["session"]["session_id"]
                before = session_permissions(session_id)
                before_updates_count = before["summary"]["updates_count"]
                permission_state_path = Path(before["permission_state_path"])
                before_http = self.http_json("GET", host, port, f"/session/permissions?session_id={session_id}")

                updated = self.http_json(
                    "POST",
                    host,
                    port,
                    "/session/permissions",
                    {
                        "session_id": session_id,
                        "update": {
                            "type": "addDirectories",
                            "destination": "session",
                            "directories": ["C:\\Users\\simon\\claude-code-project"],
                        },
                    },
                )
                after = session_permissions(session_id)
                persisted_state = json.loads(permission_state_path.read_text(encoding="utf-8"))
                result = json.loads(Path(started["session"]["result_path"]).read_text(encoding="utf-8"))
                summary = session_summary(session_id)
                resume = resume_session(session_id)
                status = session_status(session_id)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(before["schema_version"], "session_claude_permissions_v1")
        self.assertTrue(before["available"])
        self.assertTrue(before["validation"]["ok"], before["validation"]["errors"])
        self.assertGreater(before["decisions_count"], 0)
        self.assertEqual(before_http["decisions_count"], before["decisions_count"])
        self.assertEqual(updated["schema_version"], "session_claude_permission_update_v1")
        self.assertTrue(updated["ok"], updated["validation"]["errors"])
        self.assertEqual(updated["updates_applied_count"], 1)
        self.assertEqual(updated["latest_update"]["type"], "addDirectories")
        self.assertEqual(after["summary"]["updates_count"], before_updates_count + 1)
        self.assertEqual(after["summary"]["additional_working_directories_count"], 1)
        self.assertIn(
            {"path": "C:\\Users\\simon\\claude-code-project", "source": "session"},
            persisted_state["additionalWorkingDirectories"],
        )
        self.assertEqual(result["permission_state_summary"]["updates_count"], after["summary"]["updates_count"])
        self.assertEqual(summary["permission_state"]["updates_count"], after["summary"]["updates_count"])
        self.assertEqual(resume["resume"]["permission_state"]["updates_count"], after["summary"]["updates_count"])
        self.assertTrue(status["integrity"]["permission_state_validation"]["ok"])
        self.assertTrue(status["integrity"]["ok"], status["integrity"]["errors"])

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

    def test_beta_readiness_and_anonymized_intake_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            previous_ops_runtime_dir = api.OPS_RUNTIME_DIR
            previous_token = os.environ.get("EVAL_RUNTIME_API_TOKEN")
            previous_hosted_url = os.environ.get("EVAL_IMMO_BETA_HOSTED_URL")
            previous_live_flag = os.environ.get(api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG)
            api.SESSIONS_DIR = Path(tmp)
            os.environ.pop("EVAL_RUNTIME_API_TOKEN", None)
            os.environ.pop("EVAL_IMMO_BETA_HOSTED_URL", None)
            os.environ[api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG] = "false"
            try:
                readiness = beta_ea_readiness()
                os.environ["EVAL_RUNTIME_API_TOKEN"] = "secret-token"
                os.environ["EVAL_IMMO_BETA_HOSTED_URL"] = "http://127.0.0.1:8787"
                http_readiness = beta_ea_readiness()
                os.environ["EVAL_IMMO_BETA_HOSTED_URL"] = "https://beta.eval-immo.example"
                https_readiness = beta_ea_readiness()
                os.environ[api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG] = "true"
                live_enabled_readiness = beta_ea_readiness()
                os.environ[api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG] = "false"
                missing_audit_ops_dir = Path(tmp) / "ops_without_anonymization_audit"
                missing_audit_ops_dir.mkdir()
                api.OPS_RUNTIME_DIR = missing_audit_ops_dir
                missing_audit_readiness = beta_ea_readiness()
                (missing_audit_ops_dir / "anonymisation_audit.json").write_text(
                    json.dumps({"schema_version": "anonymisation_audit_v0", "status": "OK"}),
                    encoding="utf-8",
                )
                temp_ok_audit_readiness = beta_ea_readiness()
                api.OPS_RUNTIME_DIR = previous_ops_runtime_dir
                refused_terms = beta_start_dossier(
                    {
                        "fixture": "case_pilote_residentiel_standard.json",
                        "accepted_beta_terms": False,
                        "anonymization_attestation": True,
                    }
                )
                refused_pii = beta_start_dossier(
                    {
                        "case": {
                            "dossier_id": "D-BETA-PII",
                            "date_reference": "2026-04-28",
                            "client_email": "client@example.com",
                            "comparables": [],
                            "ajustements": [],
                            "confidence": 0.9,
                        },
                        "accepted_beta_terms": True,
                        "anonymization_attestation": True,
                    }
                )
                accepted = beta_start_dossier(
                    {
                        "fixture": "case_pilote_residentiel_standard.json",
                        "accepted_beta_terms": True,
                        "anonymization_attestation": True,
                        "operator": "QA beta",
                        "documents": [{"document_id": "DOC-1", "type": "rapport", "anonymized": True, "sha256": "a" * 64}],
                    }
                )
                session_id = accepted["session"]["session_id"]
                summary = session_summary(session_id)
                records = list_session_records()
            finally:
                api.SESSIONS_DIR = previous_sessions_dir
                api.OPS_RUNTIME_DIR = previous_ops_runtime_dir
                if previous_token is None:
                    os.environ.pop("EVAL_RUNTIME_API_TOKEN", None)
                else:
                    os.environ["EVAL_RUNTIME_API_TOKEN"] = previous_token
                if previous_hosted_url is None:
                    os.environ.pop("EVAL_IMMO_BETA_HOSTED_URL", None)
                else:
                    os.environ["EVAL_IMMO_BETA_HOSTED_URL"] = previous_hosted_url
                if previous_live_flag is None:
                    os.environ.pop(api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG, None)
                else:
                    os.environ[api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG] = previous_live_flag

        self.assertEqual(readiness["schema_version"], "beta_ea_readiness_v1")
        self.assertEqual(readiness["status"], "BETA_LIEN_BLOQUE")
        self.assertIn("hosted_url_configured", readiness["blocking_checks"])
        self.assertIn("token_auth_enabled", readiness["blocking_checks"])
        self.assertEqual(http_readiness["status"], "BETA_LIEN_BLOQUE")
        self.assertIn("hosted_url_configured", http_readiness["blocking_checks"])
        self.assertEqual(https_readiness["status"], "PRET_LIEN_EA")
        self.assertTrue(https_readiness["ready_for_external_ea_link"])
        self.assertIn("live_ai_provider_policy", live_enabled_readiness["blocking_checks"])
        self.assertIn("anonymization_gate", missing_audit_readiness["blocking_checks"])
        self.assertEqual(missing_audit_readiness["evidence"]["anonymization_status"], "ABSENT")
        self.assertNotIn("anonymization_gate", temp_ok_audit_readiness["blocking_checks"])
        self.assertFalse(refused_terms["accepted"])
        self.assertIn("accepted_beta_terms_required", refused_terms["errors"])
        self.assertFalse(refused_pii["accepted"])
        self.assertIn("anonymization_blocking_findings", refused_pii["errors"])
        self.assertEqual(accepted["status"], "ACCEPTE")
        self.assertEqual(accepted["intake"]["audit"]["status"], "OK")
        self.assertEqual(accepted["intake"]["documents_count"], 1)
        self.assertEqual(summary["beta_intake"]["status"], "ACCEPTE")
        self.assertEqual(records[0]["beta_intake_status"], "ACCEPTE")

    def test_beta_ea_operational_scripts_and_procfile_exist(self) -> None:
        readiness_script = PROJECT_ROOT / "outils" / "verifier_beta_ea_readiness_v1.py"
        smoke_script = PROJECT_ROOT / "outils" / "smoke_beta_ea_link_v1.py"
        procfile = PROJECT_ROOT / "Procfile"
        env_example = PROJECT_ROOT / ".env.beta.example"
        runbook = PROJECT_ROOT / "atelier" / "BETA-EA-RUNBOOK-V1.md"

        for path in [readiness_script, smoke_script]:
            py_compile.compile(str(path), doraise=True)

        self.assertIn("beta_ea_readiness_v1", readiness_script.read_text(encoding="utf-8"))
        self.assertIn("beta_ea_smoke_v1", smoke_script.read_text(encoding="utf-8"))
        self.assertIn("outils/lancer_api_v0.py --host 0.0.0.0", procfile.read_text(encoding="utf-8"))
        self.assertIn("EVAL_IMMO_BETA_HOSTED_URL", env_example.read_text(encoding="utf-8"))
        self.assertIn("smoke_beta_ea_link_v1.py", runbook.read_text(encoding="utf-8"))

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
                beta_readiness = self.http_json("GET", host, port, "/beta/readiness")
                beta_terms = self.http_json("GET", host, port, "/beta/terms")
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
        self.assertIn("Beta E.A.", product_ui)
        self.assertIn("betaLaunch", product_ui)
        self.assertIn("/beta/intake", product_ui)
        self.assertIn("external_evaluator_responses_included=false", product_ui)
        self.assertIn("Knowledge", product_ui)
        self.assertIn("knowledgeSnapshot", product_ui)
        self.assertIn("/knowledge/immobilier", product_ui)
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
        self.assertIn("beta", product_summary_payload)
        self.assertEqual(beta_readiness["schema_version"], "beta_ea_readiness_v1")
        self.assertEqual(beta_terms["terms_version"], api.BETA_TERMS_VERSION)

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

    def test_knowledge_immobilier_summary_maps_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous_sessions_dir = api.SESSIONS_DIR
            api.SESSIONS_DIR = Path(tmp)
            try:
                started = start_runtime({"fixture": "case_pilote_residentiel_standard.json"})
                session_id = started["session"]["session_id"]
                knowledge = knowledge_immobilier_summary(session_id)
                summary = session_summary(session_id)
            finally:
                api.SESSIONS_DIR = previous_sessions_dir

        self.assertEqual(knowledge["schema_version"], "knowledge_immobilier_session_v1")
        self.assertEqual(summary["knowledge"]["schema_version"], "knowledge_immobilier_session_v1")
        self.assertEqual(knowledge["subject_property"]["type_bien"], "residentiel_unifamilial")
        self.assertEqual(knowledge["subject_property"]["zone"], "SECTEUR-ANONYMISE-A")
        self.assertEqual(knowledge["sources"]["coverage_status"], "OK")
        self.assertGreaterEqual(knowledge["sources"]["count"], 5)
        self.assertEqual(knowledge["market_evidence"]["comparables_count"], 3)
        self.assertGreater(knowledge["reconciliation"]["conclusion_proposee"]["value"], 0)
        self.assertEqual(knowledge["quality"]["status"], "PRET_ASSISTANCE")
        self.assertTrue(knowledge["human_review"]["required"])
        self.assertFalse(knowledge["human_review"]["external_evaluator_responses_included"])

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
                knowledge_http = self.http_json("GET", host, port, f"/knowledge/immobilier?session_id={session_id}")
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
        self.assertEqual(knowledge_http["schema_version"], "knowledge_immobilier_session_v1")
        self.assertEqual(knowledge_http["reconciliation"]["conclusion_proposee"]["status"], "A_VALIDER_PAR_EVALUATEUR_AGREE")
        self.assertFalse(knowledge_http["limits"]["certification_automatic"])
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
