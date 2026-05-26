from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import re
import uuid

from engine.claude.context import build_context_state
from engine.claude.conversation import summarize_claude_messages
from engine.claude.command_execution import validate_local_command_execution
from engine.claude.transcript import (
    summarize_claude_transcript_entries,
    validate_claude_transcript_entries,
    write_claude_transcript,
)
from engine.claude.permissions import (
    apply_permission_update,
    load_permission_state,
    replay_permission_decisions,
    summarize_permission_state,
    validate_permission_state,
    write_permission_state,
)
from engine.claude.commands import validate_command_context
from engine.claude.handoffs import summarize_handoffs
from engine.claude.hooks import CLAUDE_HOOK_EVENTS, summarize_hook_invocations
from engine.claude.model_client import (
    ModelProviderConfigurationError,
    build_model_client,
    build_model_provider_diagnostics,
    build_model_provider_config,
    summarize_model_provider_config,
)
from engine.claude.settings import load_claude_settings, validate_settings_context
from engine.claude.skills import validate_skill_context
from engine.claude.tasks import summarize_pipeline_task_states, summarize_task_state
from engine.claude.types import CommandSpec
from engine.claude.tools import TOOL_REGISTRY, summarize_tool_registry, validate_tool_registry
from engine.claude_agent import load_agent_runner, load_pipeline_runner
from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml, safe_path_id


ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT / "tests" / "fixtures"
PIPELINE_PATH = ROOT / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
RUNTIME_MODE_PIPELINE_V0 = "pipeline_v0"
RUNTIME_MODE_CLAUDE_PIPELINE_V0 = "claude_pipeline_v0"
RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0 = "claude_live_pipeline_v0"
RUNTIME_MODE_CLAUDE_DATA_FACTS_V0 = "claude_data_facts_v0"
RUNTIME_MODE_CLAUDE_COMPS_MARKET_V0 = "claude_comps_market_v0"
RUNTIME_MODE_CLAUDE_VALUATION_DRAFT_V0 = "claude_valuation_draft_v0"
RUNTIME_MODE_CLAUDE_COMPLIANCE_QA_V0 = "claude_compliance_qa_v0"
RUNTIME_MODE_CLAUDE_REDACTION_V0 = "claude_redaction_v0"
RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0 = "claude_live_data_facts_v0"
RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0 = "claude_live_comps_market_v0"
RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0 = "claude_live_valuation_draft_v0"
RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0 = "claude_live_compliance_qa_v0"
RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0 = "claude_live_redaction_v0"
CLAUDE_SINGLE_AGENT_RUNTIME_MODES = {
    RUNTIME_MODE_CLAUDE_DATA_FACTS_V0: "AGENTCONFIG-DATA-FACTS-V0.yaml",
    RUNTIME_MODE_CLAUDE_COMPS_MARKET_V0: "AGENTCONFIG-COMPS-MARKET-V0.yaml",
    RUNTIME_MODE_CLAUDE_VALUATION_DRAFT_V0: "AGENTCONFIG-VALUATION-DRAFT-V0.yaml",
    RUNTIME_MODE_CLAUDE_COMPLIANCE_QA_V0: "AGENTCONFIG-COMPLIANCE-QA-V0.yaml",
    RUNTIME_MODE_CLAUDE_REDACTION_V0: "AGENTCONFIG-REDACTION-V0.yaml",
}
CLAUDE_LIVE_AGENT_RUNTIME_MODES = {
    RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0: {
        "agent_config": "AGENTCONFIG-DATA-FACTS-V0.yaml",
        "agent_type": "data-facts",
    },
    RUNTIME_MODE_CLAUDE_LIVE_COMPS_MARKET_V0: {
        "agent_config": "AGENTCONFIG-COMPS-MARKET-V0.yaml",
        "agent_type": "comps-market",
    },
    RUNTIME_MODE_CLAUDE_LIVE_VALUATION_DRAFT_V0: {
        "agent_config": "AGENTCONFIG-VALUATION-DRAFT-V0.yaml",
        "agent_type": "valuation-draft",
    },
    RUNTIME_MODE_CLAUDE_LIVE_COMPLIANCE_QA_V0: {
        "agent_config": "AGENTCONFIG-COMPLIANCE-QA-V0.yaml",
        "agent_type": "compliance-qa",
    },
    RUNTIME_MODE_CLAUDE_LIVE_REDACTION_V0: {
        "agent_config": "AGENTCONFIG-REDACTION-V0.yaml",
        "agent_type": "redaction",
    },
}
SUPPORTED_RUNTIME_MODES = {
    RUNTIME_MODE_PIPELINE_V0,
    RUNTIME_MODE_CLAUDE_PIPELINE_V0,
    RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0,
    *CLAUDE_SINGLE_AGENT_RUNTIME_MODES,
    *CLAUDE_LIVE_AGENT_RUNTIME_MODES,
}
SESSIONS_DIR = ROOT / "runtime_sessions"
ATELIER_DIR = ROOT / "atelier"
RUNTIME_DIR = ROOT / "tests" / "runtime"
UI_PATH = ROOT / "ui" / "pilote_api.html"
PRODUCT_UI_PATH = ROOT / "ui" / "product_cockpit.html"
OPS_UI_PATH = ROOT / "ui" / "ops_cockpit.html"
EVALUATOR_UI_PATH = ROOT / "ui" / "evaluateur_review.html"
AUTH_CLIENT_PATH = ROOT / "ui" / "auth_client.js"
OPS_RUNTIME_DIR = ROOT / "runtime_pilotes_reels"
KNOWLEDGE_CONTRACT_PATH = ROOT / "mvp" / "KNOWLEDGE-SCHEMA-IMMOBILIER-V0.yaml"
KNOWLEDGE_API_SCHEMA_PATH = ROOT / "schemas" / "knowledge_immobilier_session_v1.schema.json"
OPS_JSON_REPORTS = {
    "readiness": "readiness_pre_reponses.json",
    "quality": "quality_report.json",
    "manifest": "runtime_manifest.json",
    "knowledge": "knowledge_snapshot.json",
    "registry": "runtime_registry.json",
    "calibration": "calibration_evaluateurs.json",
    "infra_contracts": "infra_contracts_report.json",
    "anonymization": "anonymisation_audit.json",
    "delta": "runtime_delta_report.json",
    "handoff": "ops_handoff_manifest.json",
    "schema_validation": "schema_validation_report.json",
    "package_gate": "paquet_evaluateurs_gate.json",
    "phase_h_gate": "phase_h_campagne_terrain_gate.json",
    "doctor": "ops_doctor_report.json",
}
OPS_CSV_REPORTS = {
    "review_queue": "FILE-REVUE-HUMAINE-V0.csv",
}
ACCESS_AUDIT_FILENAME = "access_audit.jsonl"
ARTIFACT_PREVIEW_MAX_BYTES = 64 * 1024
V1_PACKAGE_DIRNAME = "package_v1"
V1_PACKAGE_MANIFEST_FILENAME = "DEMO-MANIFEST-V1.json"
REVIEW_DECISIONS = {"PRET_REVUE", "A_CORRIGER", "VALIDE", "REJETE"}
REVIEW_NOTES_REQUIRED = {"A_CORRIGER", "VALIDE", "REJETE"}
ROLE_PERMISSIONS = {
    "evaluator": {"runtime_read", "runtime_write", "review_write"},
    "ops": {"runtime_read", "ops_read", "ops_write"},
    "supervisor": {"runtime_read", "runtime_write", "review_write", "ops_read", "ops_write"},
}
ASSISTANT_MESSAGES_FILENAME = "assistant_messages.jsonl"
SLASH_COMMANDS_FILENAME = "slash_commands.jsonl"
CLAUDE_ACTIONS_FILENAME = "claude_actions.jsonl"
CLAUDE_ACTION_SNAPSHOTS_DIRNAME = "claude_action_snapshots"
ANTHROPIC_SDK_RUNTIME_ENV_FLAG = "EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME"
ANTHROPIC_SDK_FACTORY_OVERRIDE: Callable[..., object] | None = None
ASSISTANT_MAX_MESSAGE_CHARS = 4000
APP_DEFAULT_FIXTURE = "case_pilote_residentiel_standard.json"
BETA_TERMS_VERSION = "beta_ea_terms_v1"
BETA_DEFAULT_RETENTION_DAYS = 14
BETA_MAX_RETENTION_DAYS = 30
BETA_SENSITIVE_TEXT_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "postal_code": re.compile(r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d\b", re.IGNORECASE),
    "precise_address": re.compile(r"\b\d{1,6}\s+(rue|avenue|av\.|boulevard|boul\.|chemin|ch\.|route|rang)\b", re.IGNORECASE),
}
BETA_SENSITIVE_KEY_TOKENS = {
    "client",
    "courriel",
    "email",
    "nom",
    "owner",
    "phone",
    "proprietaire",
    "telephone",
}
BETA_SAFE_KEY_TOKENS = {"anonym", "id", "source", "fixture", "zone"}
BETA_RAW_DOCUMENT_KEYS = {"base64", "binary", "content", "file_bytes", "pdf_base64", "raw_text"}
ASSISTANT_AGENT_PROFILES = {
    "superviseur-evaluateur-ai": {
        "label": "Superviseur evaluateur AI",
        "agent_config": "SUPERVISOR-ASTON-IMMOBILIER",
        "focus": "orchestration, synthese dossier, prochaines actions",
    },
    "data-facts": {
        "label": "Agent Dossier",
        "agent_config": "AGENTCONFIG-DATA-FACTS-V0.yaml",
        "focus": "faits, sources, documents, donnees extraites",
    },
    "comps-market": {
        "label": "Agent Marche",
        "agent_config": "AGENTCONFIG-COMPS-MARKET-V0.yaml",
        "focus": "comparables, marche, ventes, justification des comparables",
    },
    "valuation-draft": {
        "label": "Agent Analyse",
        "agent_config": "AGENTCONFIG-VALUATION-DRAFT-V0.yaml",
        "focus": "valeurs, approches, calculs, ajustements",
    },
    "compliance-qa": {
        "label": "Agent Conformite",
        "agent_config": "AGENTCONFIG-COMPLIANCE-QA-V0.yaml",
        "focus": "warnings, blocages, gates, limites, conformite",
    },
    "redaction": {
        "label": "Agent Rapport",
        "agent_config": "AGENTCONFIG-REDACTION-V0.yaml",
        "focus": "rapport, synthese, formulation, annexes",
    },
}


def create_session(strict_mode: bool = True) -> dict:
    session_id = uuid.uuid4().hex[:12]
    run_id = f"run_{utc_now_compact()}_{session_id}"
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=False)
    session = {
        "schema_version": "runtime_session_v1",
        "session_id": session_id,
        "run_id": run_id,
        "strict_mode": strict_mode,
        "status": "CREATED",
        "created_at_utc": utc_now_iso(),
        "updated_at_utc": utc_now_iso(),
        "session_dir": str(session_dir),
        "events_url": f"/stream?session_id={session_id}",
        "status_url": f"/status?session_id={session_id}",
        "artifacts_url": f"/artifacts?session_id={session_id}",
    }
    write_json(session_dir / "session.json", session)
    return session


def load_session(session_id: str) -> dict | None:
    session_path = SESSIONS_DIR / safe_path_id(session_id) / "session.json"
    if not session_path.exists():
        return None
    return json.loads(session_path.read_text(encoding="utf-8"))


def save_session(session: dict) -> None:
    session["updated_at_utc"] = utc_now_iso()
    write_json(Path(session["session_dir"]) / "session.json", session)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_case_from_body(body: dict) -> tuple[dict, str]:
    if "case" in body:
        return body["case"], body.get("source_fixture", "inline")

    fixture_name = body.get("fixture", "case_nominal.json")
    if Path(fixture_name).name != fixture_name:
        raise ValueError("fixture invalide")

    fixture_path = FIXTURES_DIR / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(f"fixture introuvable: {fixture_name}")

    return json.loads(fixture_path.read_text(encoding="utf-8")), fixture_name


def runtime_mode_from_body(body: dict, session: dict) -> str:
    runtime_mode = str(body.get("runtime_mode") or session.get("runtime_mode") or RUNTIME_MODE_PIPELINE_V0)
    if runtime_mode not in SUPPORTED_RUNTIME_MODES:
        raise ValueError(f"runtime_mode invalide: {runtime_mode}")
    return runtime_mode


def is_claude_runtime_mode(runtime_mode: str) -> bool:
    return (
        runtime_mode == RUNTIME_MODE_CLAUDE_PIPELINE_V0
        or runtime_mode == RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0
        or runtime_mode in CLAUDE_SINGLE_AGENT_RUNTIME_MODES
        or runtime_mode in CLAUDE_LIVE_AGENT_RUNTIME_MODES
    )


def is_claude_live_runtime_mode(runtime_mode: str) -> bool:
    return runtime_mode == RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0 or runtime_mode in CLAUDE_LIVE_AGENT_RUNTIME_MODES


def run_case_runtime_mode(
    runtime_mode: str,
    case: dict,
    session_dir: Path,
    *,
    source_fixture: str,
    case_key: str,
    strict_mode: bool,
    settings_context: dict[str, object] | None = None,
    model_provider_options: dict[str, object] | None = None,
) -> dict:
    if runtime_mode == RUNTIME_MODE_PIPELINE_V0:
        steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
        engine = RuntimeEngine(steps=steps, strict_mode=strict_mode)
        return engine.run_case_data(
            case,
            session_dir / "artifacts",
            source_fixture=source_fixture,
            case_stem=case_key,
            case_subdir=True,
        )

    if runtime_mode == RUNTIME_MODE_CLAUDE_PIPELINE_V0:
        result = load_pipeline_runner(project_root=ROOT, settings_context=settings_context).run_case_data(
            case,
            session_dir / "artifacts",
            source_fixture=source_fixture,
            case_stem=case_key,
            case_subdir=True,
        )
        result["runtime_mode"] = runtime_mode
        result["pipeline_scope"] = "multi_agent:claude"
        return result

    if runtime_mode == RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0:
        sdk_factory = ANTHROPIC_SDK_FACTORY_OVERRIDE
        provider_config = build_model_provider_config(
            model_provider_options,
            env=os.environ,
            sdk_available=True if sdk_factory is not None else None,
        )
        allow_sdk_runtime = truthy_query(os.environ.get(ANTHROPIC_SDK_RUNTIME_ENV_FLAG))
        use_sdk_runtime = provider_config.provider == "anthropic" and allow_sdk_runtime
        provider_summary = summarize_model_provider_config(
            provider_config,
            require_executable=not use_sdk_runtime,
            require_network_for_non_fake=True,
            require_sdk_for_network=use_sdk_runtime,
        )
        if not provider_summary["ok"]:
            errors = provider_summary.get("errors", [])
            raise ValueError(f"claude_model_provider invalide: {', '.join(str(error) for error in errors)}")
        try:
            model_client = build_model_client(
                provider_config,
                enable_experimental_adapters=use_sdk_runtime,
                enable_sdk_execution=use_sdk_runtime,
                sdk_factory=sdk_factory,
                env=os.environ,
            )
        except ModelProviderConfigurationError as exc:
            raise ValueError(f"claude_model_provider invalide: {exc}") from exc
        result = load_pipeline_runner(
            project_root=ROOT,
            settings_context=settings_context,
            model_client=model_client,
            runtime_mode=runtime_mode,
        ).run_case_data(
            case,
            session_dir / "artifacts",
            source_fixture=source_fixture,
            case_stem=case_key,
            case_subdir=True,
        )
        result["runtime_mode"] = runtime_mode
        result["pipeline_scope"] = "multi_agent_live:claude"
        result["live_adapter"] = {
            "schema_version": "claude_live_adapter_v0",
            "enabled": True,
            "agent_type": "claude-pipeline",
            "provider": result.get("model_client", {}).get("provider", "fake")
            if isinstance(result.get("model_client"), dict)
            else "fake",
            "provider_config": provider_summary,
            "provider_diagnostics": build_model_provider_diagnostics(
                model_provider_options,
                env=os.environ,
                sdk_available=True if sdk_factory is not None else None,
            ),
            "model_client": result.get("model_client", {}),
            "model_client_by_agent": result.get("model_client_by_agent", {}),
            "ok": bool(result.get("model_client", {}).get("ok", False))
            if isinstance(result.get("model_client"), dict)
            else False,
        }
        return result

    live_agent_config = CLAUDE_LIVE_AGENT_RUNTIME_MODES.get(runtime_mode)
    if live_agent_config:
        agent_config_name = str(live_agent_config["agent_config"])
        agent_type = str(live_agent_config["agent_type"])
        sdk_factory = ANTHROPIC_SDK_FACTORY_OVERRIDE
        provider_config = build_model_provider_config(
            model_provider_options,
            env=os.environ,
            sdk_available=True if sdk_factory is not None else None,
        )
        allow_sdk_runtime = truthy_query(os.environ.get(ANTHROPIC_SDK_RUNTIME_ENV_FLAG))
        use_sdk_runtime = provider_config.provider == "anthropic" and allow_sdk_runtime
        provider_summary = summarize_model_provider_config(
            provider_config,
            require_executable=not use_sdk_runtime,
            require_network_for_non_fake=True,
            require_sdk_for_network=use_sdk_runtime,
        )
        if not provider_summary["ok"]:
            errors = provider_summary.get("errors", [])
            raise ValueError(f"claude_model_provider invalide: {', '.join(str(error) for error in errors)}")
        try:
            model_client = build_model_client(
                provider_config,
                enable_experimental_adapters=use_sdk_runtime,
                enable_sdk_execution=use_sdk_runtime,
                sdk_factory=sdk_factory,
                env=os.environ,
            )
        except ModelProviderConfigurationError as exc:
            raise ValueError(f"claude_model_provider invalide: {exc}") from exc
        runner = load_agent_runner(
            agent_config_name,
            project_root=ROOT,
            settings_context=settings_context,
            model_client=model_client,
            runtime_mode=runtime_mode,
        )
        result = runner.run_case_data(
            case,
            session_dir / "artifacts",
            source_fixture=source_fixture,
            case_stem=case_key,
            case_subdir=True,
        )
        result["runtime_mode"] = runtime_mode
        result["pipeline_scope"] = f"single_agent_live:{agent_type}"
        result["live_adapter"] = {
            "schema_version": "claude_live_adapter_v0",
            "enabled": True,
            "agent_type": agent_type,
            "provider": result.get("model_client", {}).get("provider", "fake")
            if isinstance(result.get("model_client"), dict)
            else "fake",
            "provider_config": provider_summary,
            "provider_diagnostics": build_model_provider_diagnostics(
                model_provider_options,
                env=os.environ,
                sdk_available=True if sdk_factory is not None else None,
            ),
            "model_client": result.get("model_client", {}),
            "ok": bool(result.get("model_client", {}).get("ok", False))
            if isinstance(result.get("model_client"), dict)
            else False,
        }
        return result

    agent_config_name = CLAUDE_SINGLE_AGENT_RUNTIME_MODES.get(runtime_mode)
    if agent_config_name:
        runner = load_agent_runner(agent_config_name, project_root=ROOT, settings_context=settings_context)
        result = runner.run_case_data(
            case,
            session_dir / "artifacts",
            source_fixture=source_fixture,
            case_stem=case_key,
            case_subdir=True,
        )
        result["runtime_mode"] = runtime_mode
        result["pipeline_scope"] = f"single_agent:{result['agent_type']}"
        return result

    raise ValueError(f"runtime_mode invalide: {runtime_mode}")


def list_fixtures() -> list[dict[str, object]]:
    fixtures = []
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        if path.name.startswith("template_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        fixtures.append(
            {
                "name": path.name,
                "dossier_id": data.get("dossier_id", ""),
                "date_reference": data.get("date_reference", ""),
                "comparables_count": len(data.get("comparables", [])),
                "ajustements_count": len(data.get("ajustements", [])),
                "confidence": data.get("confidence", ""),
            }
        )
    return fixtures


def read_json_dict(path: Path) -> dict:
    if not path.exists() or not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_json_list(path: Path) -> list:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else []


def bounded_limit(value: str, default: int = 50, maximum: int = 100) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return min(max(limit, 0), maximum)


def _optional_int(value: object, *, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truthy_query(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "oui", "on"}


def recent_sessions(limit: int = 8) -> list[dict]:
    return list_session_records(limit=limit)


def list_session_records(limit: int = 50) -> list[dict]:
    if not SESSIONS_DIR.exists():
        return []
    sessions: list[dict] = []
    for path in sorted(SESSIONS_DIR.glob("*/session.json")):
        try:
            session = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(session, dict):
            continue
        sessions.append(session_workbench_record(session))
    sessions.sort(key=lambda item: str(item.get("updated_at_utc") or ""), reverse=True)
    return sessions[: max(0, limit)]


def session_workbench_record(session: dict) -> dict:
    session_id = str(session.get("session_id") or "")
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    review = read_json_dict(Path(str(session.get("review_path") or "")))
    artifacts = read_json_dict(Path(str(session.get("artifact_index_path") or "")))
    package = read_session_package_manifest(session)
    try:
        integrity = validate_session_integrity(session) if session_id else {"ok": False, "errors": ["session_id_missing"]}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        integrity = {"ok": False, "errors": [f"integrity_unreadable:{type(exc).__name__}"]}

    blocking_failures = result.get("blocking_failures", [])
    warnings = result.get("warnings", [])
    if not isinstance(blocking_failures, list):
        blocking_failures = []
    if not isinstance(warnings, list):
        warnings = []
    review_decision = str(review.get("decision") or session.get("review_decision") or "A_SAISIR")
    beta_intake = beta_intake_summary_from_session(session)
    next_action = review_next_action(
        has_result=bool(result),
        integrity_ok=bool(integrity.get("ok")),
        blocking_failures_count=len(blocking_failures),
        review_decision=review_decision,
    )
    return {
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "dossier_id": result.get("dossier_id") or session.get("dossier_id", ""),
        "status": result.get("status") or session.get("status", "CREATED"),
        "created_at_utc": session.get("created_at_utc", ""),
        "updated_at_utc": session.get("updated_at_utc", ""),
        "review_decision": review_decision,
        "reviewer": review.get("reviewer", ""),
        "reviewed_at_utc": review.get("created_at_utc", ""),
        "integrity_ok": bool(integrity.get("ok")),
        "integrity_errors_count": len(integrity.get("errors", [])) if isinstance(integrity.get("errors"), list) else 0,
        "artifacts_count": int(artifacts.get("artifacts_count", 0) or 0),
        "warnings_count": len(warnings),
        "blocking_failures_count": len(blocking_failures),
        "claude_transcript_entries_count": int(
            session.get("claude_transcript_summary", {}).get("entries_count", 0)
            if isinstance(session.get("claude_transcript_summary"), dict)
            else 0
        ),
        "next_action": next_action,
        "session_summary_url": f"/session/summary?session_id={session_id}",
        "dossier_review_url": f"/review/dossier?session_id={session_id}",
        "package_status": package.get("status", "ABSENT"),
        "package_origin": package.get("package_origin", ""),
        "package_generated": bool(package),
        "package_url": f"/review/package?session_id={session_id}",
        "beta_intake_status": beta_intake.get("status", ""),
        "beta_delete_after_utc": beta_intake.get("delete_after_utc", ""),
        "beta_terms_version": beta_intake.get("terms_version", ""),
        "app_display_name": session.get("app_display_name", ""),
        "app_property_type": session.get("app_property_type", ""),
        "app_neighborhood": session.get("app_neighborhood", ""),
    }


def review_next_action(*, has_result: bool, integrity_ok: bool, blocking_failures_count: int, review_decision: str) -> str:
    if not has_result:
        return "EXECUTER_RUNTIME"
    if not integrity_ok:
        return "VERIFIER_INTEGRITE"
    if blocking_failures_count:
        return "CORRIGER_BLOCAGES"
    if review_decision == "A_SAISIR":
        return "SAISIR_DECISION"
    if review_decision == "PRET_REVUE":
        return "POURSUIVRE_REVUE"
    if review_decision == "A_CORRIGER":
        return "APPLIQUER_CORRECTIONS"
    if review_decision == "VALIDE":
        return "DOSSIER_VALIDE"
    if review_decision == "REJETE":
        return "DOSSIER_REJETE"
    return "POURSUIVRE_REVUE"


def review_workbench_summary(limit: int = 50) -> dict:
    sessions = list_session_records(limit=limit)
    decision_counts: dict[str, int] = {}
    for item in sessions:
        decision = str(item.get("review_decision") or "A_SAISIR")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    integrity_blocked = [item for item in sessions if not item.get("integrity_ok")]
    blocking_runtime = [item for item in sessions if int(item.get("blocking_failures_count", 0) or 0) > 0]
    queue = load_ops_csv("review_queue")
    return {
        "schema_version": "review_workbench_summary_v1",
        "sessions_count": len(sessions),
        "pending_count": decision_counts.get("A_SAISIR", 0) + decision_counts.get("PRET_REVUE", 0),
        "validated_count": decision_counts.get("VALIDE", 0),
        "correction_count": decision_counts.get("A_CORRIGER", 0),
        "rejected_count": decision_counts.get("REJETE", 0),
        "integrity_blocked_count": len(integrity_blocked),
        "runtime_blocked_count": len(blocking_runtime),
        "decision_counts": decision_counts,
        "sessions": sessions,
        "review_queue": {
            "status": queue.get("status", "ABSENT"),
            "items_count": queue.get("rows_count", 0),
        },
        "decisions_allowed": sorted(REVIEW_DECISIONS),
        "routes": {
            "sessions": "/sessions",
            "session_summary": "/session/summary",
            "dossier_review": "/review/dossier",
            "save_review": "/review",
            "session_package": "/review/package",
            "resume": "/resume",
        },
    }


def review_campaign_summary(limit: int = 100) -> dict:
    sessions = list_session_records(limit=limit)
    decision_counts: dict[str, int] = {}
    rows: list[dict] = []
    for item in sessions:
        decision = str(item.get("review_decision") or "A_SAISIR")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        rows.append(
            {
                "session_id": item.get("session_id", ""),
                "run_id": item.get("run_id", ""),
                "dossier_id": item.get("dossier_id", ""),
                "runtime_status": item.get("status", "UNKNOWN"),
                "decision": decision,
                "reviewer": item.get("reviewer", ""),
                "reviewed_at_utc": item.get("reviewed_at_utc", ""),
                "integrity_ok": bool(item.get("integrity_ok")),
                "blocking_failures_count": int(item.get("blocking_failures_count", 0) or 0),
                "warnings_count": int(item.get("warnings_count", 0) or 0),
                "artifacts_count": int(item.get("artifacts_count", 0) or 0),
                "next_action": item.get("next_action", ""),
                "package_status": item.get("package_status", "ABSENT"),
                "package_url": item.get("package_url", ""),
            }
        )

    reviewed = [row for row in rows if row["decision"] != "A_SAISIR"]
    ready_rows = [
        row
        for row in rows
        if row["decision"] == "VALIDE" and row["integrity_ok"] and row["blocking_failures_count"] == 0
    ]
    blocked_rows = [
        row
        for row in rows
        if not row["integrity_ok"] or row["blocking_failures_count"] > 0 or row["decision"] in {"A_CORRIGER", "REJETE"}
    ]
    package_rows = [row for row in rows if row["package_status"] != "ABSENT"]
    return {
        "schema_version": "review_campaign_v1",
        "scope": "REVUE_INTERNE_PRE_EVALUATEUR",
        "external_evaluator_responses_included": False,
        "sessions_count": len(rows),
        "reviews_count": len(reviewed),
        "pending_count": decision_counts.get("A_SAISIR", 0) + decision_counts.get("PRET_REVUE", 0),
        "validated_count": decision_counts.get("VALIDE", 0),
        "correction_count": decision_counts.get("A_CORRIGER", 0),
        "rejected_count": decision_counts.get("REJETE", 0),
        "ready_for_package_count": len(ready_rows),
        "package_generated_count": len(package_rows),
        "blocked_count": len(blocked_rows),
        "decision_counts": decision_counts,
        "rows": rows,
        "ready_session_ids": [row["session_id"] for row in ready_rows],
        "package_session_ids": [row["session_id"] for row in package_rows],
        "blocked_session_ids": [row["session_id"] for row in blocked_rows],
        "source": {
            "sessions_dir": str(SESSIONS_DIR),
            "review_files": "runtime_sessions/*/review.json",
            "generated_from": "local_runtime_sessions",
        },
    }


def beta_retention_days() -> int:
    raw = os.environ.get("EVAL_IMMO_BETA_RETENTION_DAYS", "")
    try:
        days = int(raw) if raw else BETA_DEFAULT_RETENTION_DAYS
    except ValueError:
        days = BETA_DEFAULT_RETENTION_DAYS
    return min(max(days, 1), BETA_MAX_RETENTION_DAYS)


def beta_terms() -> dict:
    return {
        "schema_version": "beta_terms_v1",
        "terms_version": BETA_TERMS_VERSION,
        "audience": "evaluateur_agree_beta_fermee",
        "requires_anonymized_inputs": True,
        "requires_human_validation": True,
        "certification_automatic": False,
        "external_evaluator_responses_included": False,
        "retention_days": beta_retention_days(),
        "accepted_input_modes": ["fixture_synthetique", "dossier_json_anonymise"],
        "raw_document_storage": "refuse_par_defaut_avant_contrat",
    }


def beta_check(label: str, ok: bool, severity: str, detail: str, action: str = "") -> dict:
    return {
        "label": label,
        "status": "OK" if ok else severity,
        "ok": ok,
        "severity": severity if not ok else "info",
        "detail": detail,
        "action": action,
    }


def beta_ea_readiness() -> dict:
    status_report = read_json_dict(ATELIER_DIR / "STATUT-PHASES-PROJET-V1.json")
    release_report = read_json_dict(RUNTIME_DIR / "release_candidate_report.json")
    homologation_report = read_json_dict(RUNTIME_DIR / "homologation_metier_report.json")
    live_smoke = read_json_dict(OPS_RUNTIME_DIR / "claude_live_provider_smoke_v0.json")
    anonymization_report = load_ops_json("anonymization")
    ops = ops_summary()

    auth_enabled = bool(os.environ.get("EVAL_RUNTIME_API_TOKEN"))
    hosted_url = os.environ.get("EVAL_IMMO_BETA_HOSTED_URL", "").strip()
    hosted_url_ok = hosted_url.startswith("https://")
    live_provider_env = truthy_query(os.environ.get(ANTHROPIC_SDK_RUNTIME_ENV_FLAG))
    live_operator_enabled = os.environ.get("EVAL_IMMO_RUN_LIVE_SMOKE", "").lower() == "true"
    release_ok = bool(release_report.get("ok")) and release_report.get("decision") == "PRET_GO_LIVE_CONTROLE"
    product_ok = "PROD_BLOQUEE" in str(status_report.get("decision") or "") and release_ok
    anonymization_ok = anonymization_report.get("status") == "OK"
    live_policy_ok = not live_provider_env and not live_operator_enabled

    checks = [
        beta_check(
            "hosted_url_configured",
            hosted_url_ok,
            "BLOCANT",
            hosted_url or "aucune URL beta HTTPS configuree dans EVAL_IMMO_BETA_HOSTED_URL",
            "deployer le serveur beta derriere HTTPS et definir EVAL_IMMO_BETA_HOSTED_URL",
        ),
        beta_check(
            "token_auth_enabled",
            auth_enabled,
            "BLOCANT",
            "EVAL_RUNTIME_API_TOKEN actif" if auth_enabled else "auth locale desactivee",
            "definir un token par environnement avant de partager le lien",
        ),
        beta_check(
            "release_candidate_gate",
            release_ok,
            "BLOCANT",
            str(release_report.get("decision") or "ABSENT"),
            "regenerer les preuves et corriger le gate release candidate",
        ),
        beta_check(
            "product_review_package_workflow",
            product_ok,
            "BLOCANT",
            str(status_report.get("decision") or "ABSENT"),
            "conserver la V1 bloquee production mais prete controle avant terrain reel",
        ),
        beta_check(
            "anonymization_gate",
            anonymization_ok,
            "BLOCANT",
            str(anonymization_report.get("status") or "ABSENT"),
            "corriger les findings d'anonymisation avant tout dossier externe",
        ),
        beta_check(
            "live_ai_provider_policy",
            live_policy_ok,
            "BLOCANT",
            "runtime live Anthropic desactive par defaut" if live_policy_ok else "runtime live Anthropic active dans l'environnement",
            "laisser le runtime live desactive pour la beta sans contrat ou documenter le mode operateur",
        ),
        beta_check(
            "phase_h_real_terrain_inputs",
            not bool(ops.get("waiting_for_real_inputs")),
            "INFO",
            str(ops.get("phase_h_gate_status") or "ABSENT"),
            "non bloquant pour une beta fermee sur dossiers anonymises",
        ),
    ]
    blocking = [item for item in checks if item["status"] == "BLOCANT"]
    warnings = [item for item in checks if item["status"] not in {"OK", "BLOCANT"}]
    return {
        "schema_version": "beta_ea_readiness_v1",
        "status": "PRET_LIEN_EA" if not blocking else "BETA_LIEN_BLOQUE",
        "ready_for_external_ea_link": not blocking,
        "ready_for_local_anonymized_beta": release_ok and anonymization_ok and live_policy_ok,
        "generated_at_utc": utc_now_iso(),
        "hosted_url": hosted_url,
        "terms": beta_terms(),
        "checks": checks,
        "blocking_count": len(blocking),
        "warning_count": len(warnings),
        "blocking_checks": [item["label"] for item in blocking],
        "warning_checks": [item["label"] for item in warnings],
        "evidence": {
            "project_status_decision": status_report.get("decision", "ABSENT"),
            "release_candidate_decision": release_report.get("decision", "ABSENT"),
            "homologation_decision": homologation_report.get("production_decision", "ABSENT"),
            "ops_doctor_status": ops.get("doctor_status", "ABSENT"),
            "phase_h_gate_status": ops.get("phase_h_gate_status", "ABSENT"),
            "anonymization_status": anonymization_report.get("status", "ABSENT"),
            "live_smoke_ok": bool(live_smoke.get("ok", False)),
            "live_smoke_missing_guardrails": live_smoke.get("missing_guardrails", []),
        },
        "routes": {
            "readiness": "/beta/readiness",
            "terms": "/beta/terms",
            "intake": "/beta/intake",
            "product": "/product",
            "review": "/review/ui",
        },
    }


def beta_redact(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "***" + value[-2:]


def beta_path_is_safe_key(path: str) -> bool:
    lower = path.lower()
    return any(token in lower for token in BETA_SAFE_KEY_TOKENS)


def beta_path_is_sensitive_key(path: str) -> bool:
    lower = path.lower()
    return any(token in lower for token in BETA_SENSITIVE_KEY_TOKENS) and not beta_path_is_safe_key(path)


def beta_scan_anonymization(value: object, path: str = "$") -> list[dict]:
    findings: list[dict] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            key_text = str(key)
            if key_text.lower() in BETA_RAW_DOCUMENT_KEYS and item not in (None, "", [], {}):
                findings.append(
                    {
                        "path": child_path,
                        "type": "raw_document_payload",
                        "severity": "blocker",
                        "excerpt": "[contenu brut refuse]",
                    }
                )
            if beta_path_is_sensitive_key(child_path) and item not in (None, "", [], {}):
                findings.append(
                    {
                        "path": child_path,
                        "type": "sensitive_field_name",
                        "severity": "blocker",
                        "excerpt": beta_redact(str(item)),
                    }
                )
            findings.extend(beta_scan_anonymization(item, child_path))
        return findings
    if isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(beta_scan_anonymization(item, f"{path}[{index}]"))
        return findings
    if isinstance(value, str) and value.strip():
        if beta_path_is_safe_key(path):
            return findings
        for name, pattern in BETA_SENSITIVE_TEXT_PATTERNS.items():
            for match in pattern.finditer(value):
                findings.append(
                    {
                        "path": path,
                        "type": name,
                        "severity": "blocker",
                        "excerpt": beta_redact(match.group(0)),
                    }
                )
    return findings


def beta_anonymization_audit_payload(payload: dict) -> dict:
    findings = beta_scan_anonymization(payload)
    blocking = [item for item in findings if item.get("severity") == "blocker"]
    return {
        "schema_version": "beta_anonymization_audit_v1",
        "status": "OK" if not blocking else "REFUS_DONNEES_IDENTIFIANTES",
        "findings_count": len(findings),
        "blocking_findings_count": len(blocking),
        "findings": findings[:50],
    }


def beta_intake_summary_from_session(session: dict) -> dict:
    summary = session.get("beta_intake_summary", {})
    return summary if isinstance(summary, dict) else {}


def beta_start_dossier(body: dict) -> dict:
    accepted_terms = bool(body.get("accepted_beta_terms") or body.get("terms_accepted"))
    anonymization_attestation = bool(body.get("anonymization_attestation") or body.get("documents_anonymized"))
    operator = str(body.get("operator") or body.get("reviewer") or "").strip()
    case, source_fixture = load_case_from_body(body)
    document_manifest = body.get("documents", [])
    if not isinstance(document_manifest, list):
        document_manifest = []
    audit = beta_anonymization_audit_payload({"case": case, "documents": document_manifest})
    errors = []
    if not accepted_terms:
        errors.append("accepted_beta_terms_required")
    if not anonymization_attestation:
        errors.append("anonymization_attestation_required")
    if audit["blocking_findings_count"]:
        errors.append("anonymization_blocking_findings")
    if errors:
        return {
            "schema_version": "beta_intake_v1",
            "accepted": False,
            "status": "REFUSE",
            "errors": errors,
            "audit": audit,
            "terms": beta_terms(),
        }

    started = start_runtime(
        {
            "case": case,
            "source_fixture": f"beta:{source_fixture}",
            "strict_mode": True,
            "runtime_mode": body.get("runtime_mode") or RUNTIME_MODE_PIPELINE_V0,
        }
    )
    session_id = str(started.get("session", {}).get("session_id") or "")
    session = require_session(session_id)
    retention_days = beta_retention_days()
    beta_intake = {
        "schema_version": "beta_intake_v1",
        "accepted": True,
        "status": "ACCEPTE",
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "created_at_utc": utc_now_iso(),
        "operator": operator,
        "terms_version": BETA_TERMS_VERSION,
        "accepted_beta_terms": accepted_terms,
        "anonymization_attestation": anonymization_attestation,
        "retention_days": retention_days,
        "delete_after_utc": beta_delete_after_utc(retention_days),
        "source_fixture": source_fixture,
        "documents_count": len(document_manifest),
        "document_manifest": beta_document_manifest_summary(document_manifest),
        "audit": audit,
        "limits": {
            "certification_automatic": False,
            "external_evaluator_responses_included": False,
            "requires_human_validation": True,
            "raw_document_storage": "refuse_par_defaut_avant_contrat",
        },
    }
    intake_path = Path(str(session["session_dir"])) / "beta_intake.json"
    write_json(intake_path, beta_intake)
    session["beta_intake_path"] = str(intake_path)
    session["beta_intake_summary"] = {
        "status": beta_intake["status"],
        "terms_version": BETA_TERMS_VERSION,
        "retention_days": retention_days,
        "delete_after_utc": beta_intake["delete_after_utc"],
        "documents_count": len(document_manifest),
        "anonymization_status": audit["status"],
    }
    if body.get("display_name") or case.get("dossier_id"):
        session["app_display_name"] = str(body.get("display_name") or case.get("dossier_id") or "").strip()
    if body.get("property_type") or case.get("type_bien"):
        session["app_property_type"] = str(body.get("property_type") or case.get("type_bien") or "").strip()
    if body.get("neighborhood") or case.get("zone"):
        session["app_neighborhood"] = str(body.get("neighborhood") or case.get("zone") or "").strip()
    save_session(session)
    started["session"] = session
    return {
        "schema_version": "beta_intake_v1",
        "accepted": True,
        "status": "ACCEPTE",
        "session": session,
        "started": started,
        "intake": beta_intake,
        "state": app_state(session_id),
    }


def beta_delete_after_utc(retention_days: int) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return (now + timedelta(days=retention_days)).isoformat()


def beta_document_manifest_summary(documents: list) -> list[dict]:
    summary = []
    for index, item in enumerate(documents[:25], start=1):
        if isinstance(item, dict):
            summary.append(
                {
                    "index": index,
                    "document_id": str(item.get("document_id") or item.get("id") or f"document_{index}"),
                    "type": str(item.get("type") or item.get("kind") or ""),
                    "anonymized": bool(item.get("anonymized", True)),
                    "sha256": str(item.get("sha256") or "")[:64],
                }
            )
        else:
            summary.append({"index": index, "document_id": f"document_{index}", "type": str(type(item).__name__), "anonymized": False, "sha256": ""})
    return summary


def product_summary() -> dict:
    status_report = read_json_dict(ATELIER_DIR / "STATUT-PHASES-PROJET-V1.json")
    release_report = read_json_dict(RUNTIME_DIR / "release_candidate_report.json")
    homologation_report = read_json_dict(RUNTIME_DIR / "homologation_metier_report.json")
    runtime_summary = read_json_list(RUNTIME_DIR / "runtime_summary.json")
    fixtures = list_fixtures()
    status_counts: dict[str, int] = {}
    for item in runtime_summary:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    package_manifest = read_json_dict(ATELIER_DIR / "PAQUET-V1-PRE-EVALUATEUR" / "DEMO-MANIFEST-V1.json")
    handoff_manifest = read_json_dict(ATELIER_DIR / "HANDOFF-REVUE-EVALUATEUR-V1.json")
    ops = ops_summary()
    ops_snapshot = ops_observability_snapshot()
    review_campaign = review_campaign_summary(limit=25)
    session_packages = latest_session_packages_summary(limit=25)
    beta = beta_ea_readiness()
    decision = str(status_report.get("decision") or "UNKNOWN")
    return {
        "schema_version": "product_cockpit_summary_v1",
        "status": decision,
        "ok": bool(status_report.get("ok")),
        "target": status_report.get("target", "UNKNOWN"),
        "production_blocked": "PROD_BLOQUEE" in decision or homologation_report.get("production_real_decision") == "NO_GO_PROD_TERRAIN_REEL",
        "phase_h_decision": status_report.get("phase_h_decision", "UNKNOWN"),
        "release_candidate_decision": release_report.get("decision", "UNKNOWN"),
        "homologation_decision": homologation_report.get("production_decision", "UNKNOWN"),
        "runtime": {
            "cases_count": len(runtime_summary),
            "status_counts": status_counts,
            "ready_cases": status_counts.get("PRET_REVISION_FINALE", 0),
            "review_cases": status_counts.get("A_REVOIR", 0),
            "draft_cases": status_counts.get("BROUILLON", 0),
        },
        "fixtures": {
            "count": len(fixtures),
            "items": fixtures,
        },
        "sessions": {
            "recent": recent_sessions(),
        },
        "review_campaign": review_campaign,
        "session_packages": session_packages,
        "beta": beta,
        "ops": ops,
        "ops_snapshot": ops_snapshot,
        "terrain": {
            "status": ops.get("phase_h_gate_status", "ABSENT"),
            "mode": ops.get("phase_h_mode", ""),
            "active_cases_count": ops.get("phase_h_active_cases_count", 0),
            "waiting_for_real_inputs": ops.get("waiting_for_real_inputs", False),
            "blocking_counts": ops.get("blocking_counts", {}),
        },
        "package": {
            "status": package_manifest.get("status", "UNKNOWN"),
            "dossier_id": package_manifest.get("dossier_id", ""),
            "runtime_status": package_manifest.get("runtime_status", "UNKNOWN"),
            "artifacts_count": package_manifest.get("artifacts_count", 0),
            "session_generated_count": session_packages["generated_count"],
            "latest_session_id": session_packages.get("latest_session_id", ""),
        },
        "handoff": {
            "status": handoff_manifest.get("status", "UNKNOWN"),
            "stop_point": handoff_manifest.get("stop_point", ""),
        },
        "routes": {
            "product": "/product",
            "runtime": "/ui",
            "ops": "/ops/ui",
            "review": "/review/ui",
            "summary": "/product/summary",
            "demo": "/product/demo",
            "sessions": "/sessions",
            "review_workbench": "/review/workbench",
            "review_campaign": "/review/campaign",
            "review_package": "/review/package",
            "knowledge_immobilier": "/knowledge/immobilier",
            "assistant_workbench": "/assistant/workbench",
            "assistant_message": "/assistant/message",
            "session_claude": "/session/claude",
            "session_claude_action": "/session/claude/action",
            "session_claude_action_snapshot": "/session/claude/action/snapshot",
            "session_artifact_lineage": "/session/artifact-lineage",
            "session_runtime_state": "/session/runtime-state",
            "session_agents": "/session/agents",
            "session_agent_prompts": "/session/agent-prompts",
            "session_model_client": "/session/model-client",
            "session_live_replay": "/session/live-replay",
            "session_provider_diagnostics": "/session/provider-diagnostics",
            "beta_readiness": "/beta/readiness",
            "beta_terms": "/beta/terms",
            "beta_intake": "/beta/intake",
            "session_skills": "/session/skills",
            "session_settings": "/session/settings",
            "session_handoffs": "/session/handoffs",
            "session_command": "/session/command",
            "session_command_history": "/session/command-history",
            "session_hooks": "/session/hooks",
            "session_permissions": "/session/permissions",
            "session_tasks": "/session/tasks",
            "session_tools": "/session/tools",
            "session_transcript": "/session/transcript",
            "app_state": "/app/state",
            "app_demo": "/app/demo",
            "app_message": "/app/message",
            "app_validate_review": "/app/review/validate",
            "app_package": "/app/package",
            "session_summary": "/session/summary",
            "session_commands": "/session/commands",
            "artifact_content": "/artifact",
            "dossier_review": "/review/dossier",
            "ops_snapshot": "/ops/snapshot",
        },
    }


def app_money(value: object) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{amount:,.0f} $".replace(",", " ")


def app_date_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.date().isoformat()


def app_surface_label(surface: object) -> str:
    if not isinstance(surface, dict):
        return "-"
    value = surface.get("value")
    unit = surface.get("unit") or ""
    if value in (None, ""):
        return "-"
    return f"{value} {unit}".strip()


def app_title_from_session(session_id: str, dossier: dict, knowledge: dict) -> str:
    subject = knowledge.get("subject_property", {}) if isinstance(knowledge.get("subject_property"), dict) else {}
    address = str(subject.get("adresse_anonymisee") or "").strip()
    if address and address != "NON_FOURNIE":
        return address
    dossier_id = str(knowledge.get("dossier_id") or dossier.get("dossier_id") or session_id)
    return f"Dossier {dossier_id}"


def app_property_type_label(raw: object) -> str:
    value = str(raw or "").strip()
    labels = {
        "residentiel_unifamilial": "Residentiel unifamilial",
        "residentiel": "Residentiel",
        "commercial": "Commercial",
        "multilogement": "Multilogement",
    }
    return labels.get(value, value.replace("_", " ").title() if value else "Type a confirmer")


def app_status_label(record: dict) -> str:
    if record.get("package_status") == "PRET_REVUE_EVALUATEUR_AGREE":
        return "complet"
    status = str(record.get("status") or "")
    if status in {"PRET_REVISION_FINALE", "A_REVOIR"}:
        return "en-cours"
    return "brouillon"


def app_dossier_card_from_record(record: dict) -> dict:
    session_id = str(record.get("session_id") or "")
    title = str(record.get("app_display_name") or f"Dossier {record.get('dossier_id') or session_id}")
    return {
        "id": session_id,
        "slug": session_id,
        "session_id": session_id,
        "address": title,
        "property_type": str(record.get("app_property_type") or "Runtime immobilier"),
        "neighborhood": str(record.get("app_neighborhood") or record.get("status") or "Session"),
        "status": app_status_label(record),
        "updatedAt": app_date_label(record.get("updated_at_utc")) or "Session locale",
        "pinned": record.get("package_status") == "PRET_REVUE_EVALUATEUR_AGREE",
        "runtime_status": record.get("status", "UNKNOWN"),
        "review_decision": record.get("review_decision", "A_SAISIR"),
        "package_status": record.get("package_status", "ABSENT"),
        "next_action": record.get("next_action", ""),
    }


def app_source_documents(knowledge: dict) -> list[dict]:
    sources = knowledge.get("sources", {}) if isinstance(knowledge.get("sources"), dict) else {}
    items = sources.get("items", []) if isinstance(sources.get("items"), list) else []
    documents: list[dict] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("source_id") or f"SRC-{index}")
        documents.append(
            {
                "id": source_id,
                "name": f"Source {source_id}",
                "filename": str(item.get("source_type") or "runtime_fixture"),
                "sizeLabel": str(item.get("reliability_level") or "A_VALIDER"),
                "producer_steps": item.get("producer_steps", []),
            }
        )
    return documents


def app_fact_chips(knowledge: dict, dossier: dict) -> list[dict]:
    subject = knowledge.get("subject_property", {}) if isinstance(knowledge.get("subject_property"), dict) else {}
    mandate = knowledge.get("mandate", {}) if isinstance(knowledge.get("mandate"), dict) else {}
    facts = dossier.get("facts", {}) if isinstance(dossier.get("facts"), dict) else {}
    chips = [
        {"label": f"Type: {app_property_type_label(subject.get('type_bien'))}", "highlight": True},
        {"label": f"Surface: {app_surface_label(subject.get('surface') or facts.get('surface'))}", "highlight": True},
        {"label": f"Zone: {subject.get('zone') or 'A confirmer'}", "highlight": True},
        {"label": f"Date: {mandate.get('date_reference') or facts.get('date_reference') or '-'}", "highlight": True},
        {"label": f"Confiance: {subject.get('confidence') or facts.get('confidence') or '-'}", "highlight": False},
        {"label": f"Sources: {len(subject.get('source_ids', [])) if isinstance(subject.get('source_ids'), list) else facts.get('source_ids_count', 0)}", "highlight": False},
    ]
    return [chip for chip in chips if not chip["label"].endswith(": -")]


def app_comparable_rows(knowledge: dict) -> list[dict]:
    market = knowledge.get("market_evidence", {}) if isinstance(knowledge.get("market_evidence"), dict) else {}
    comparables = market.get("comparables", []) if isinstance(market.get("comparables"), list) else []
    rows: list[dict] = []
    for index, item in enumerate(comparables, start=1):
        if not isinstance(item, dict):
            continue
        price = float(item.get("prix_vente") or 0)
        score = item.get("score")
        source_id = str(item.get("source_id") or "")
        score_label = f"score {score}" if score not in (None, "") else "score a confirmer"
        rows.append(
            {
                "id": str(item.get("comparable_id") or f"C{index}"),
                "rank": f"C{index}",
                "address": str(item.get("comparable_id") or f"Comparable {index}"),
                "hab_m2": None,
                "terrain_m2": None,
                "year_built": None,
                "renovated_year": None,
                "garage_type": None,
                "sale_price": price,
                "sale_date": str(item.get("date_vente") or ""),
                "meta": " | ".join(part for part in [source_id, score_label] if part),
                "price": app_money(price),
                "date": app_date_label(item.get("date_vente")),
                "score": score,
                "source_id": source_id,
            }
        )
    return rows


def app_fixture_adjustments(source_fixture: str) -> list[dict]:
    if not source_fixture or Path(source_fixture).name != source_fixture:
        return []
    payload = read_json_dict(FIXTURES_DIR / source_fixture)
    adjustments = payload.get("ajustements", []) if isinstance(payload.get("ajustements"), list) else []
    return [item for item in adjustments if isinstance(item, dict)]


def app_adjustment_rows(knowledge: dict, dossier: dict) -> list[dict]:
    comparables = app_comparable_rows(knowledge)
    fixture_adjustments = app_fixture_adjustments(str(dossier.get("source_fixture") or ""))
    source_ids = {str(row.get("source_id") or "") for row in comparables}
    global_amount = sum(
        float(item.get("montant") or 0)
        for item in fixture_adjustments
        if str(item.get("source_id") or "") not in source_ids and item.get("validation_humaine") is True
    )
    global_share = round(global_amount / len(comparables), 2) if comparables else 0
    rows: list[dict] = []
    for row in comparables:
        source_id = str(row.get("source_id") or "")
        direct = sum(
            float(item.get("montant") or 0)
            for item in fixture_adjustments
            if str(item.get("source_id") or "") == source_id and item.get("validation_humaine") is True
        )
        sale_price = float(row.get("sale_price") or 0)
        adjusted = sale_price + direct + global_share
        rows.append(
            {
                "id": f"adj-{row['id']}",
                "comparable_id": row["id"],
                "comparableLabel": f"{row['rank']} - {row['address']}",
                "salePrice": sale_price,
                "surface_adj": direct,
                "year_adj": 0,
                "condition_adj": global_share,
                "garage_adj": 0,
                "adjusted": adjusted,
                "source_id": source_id,
                "basis": "ajustements valides de la fixture runtime; non certifiant",
            }
        )
    return rows


def app_workflow(summary: dict, dossier: dict, package: dict, assistant: dict) -> dict:
    result = summary.get("result", {}) if isinstance(summary.get("result"), dict) else {}
    review = summary.get("review", {}) if isinstance(summary.get("review"), dict) else {}
    integrity = summary.get("integrity", {}) if isinstance(summary.get("integrity"), dict) else {}
    blocking = result.get("blocking_failures", []) if isinstance(result.get("blocking_failures"), list) else []
    review_decision = str(review.get("decision") or "A_SAISIR")
    package_status = str(package.get("status") or "ABSENT")
    steps = [
        {
            "id": "runtime",
            "label": "Lancer dossier",
            "status": result.get("status", "UNKNOWN"),
            "complete": bool(result) and bool(integrity.get("ok")) and not blocking,
        },
        {
            "id": "inspect",
            "label": "Inspecter",
            "status": "PRET" if dossier.get("coverage", {}).get("missing_count", 1) == 0 else "A_COMPLETER",
            "complete": dossier.get("coverage", {}).get("missing_count", 1) == 0,
        },
        {
            "id": "review",
            "label": "Revue interne",
            "status": review_decision,
            "complete": review_decision == "VALIDE",
        },
        {
            "id": "package",
            "label": "Paquet V1",
            "status": package_status,
            "complete": package_status == "PRET_REVUE_EVALUATEUR_AGREE",
        },
    ]
    return {
        "status": assistant.get("status", "ASSISTANCE_DOSSIER_ACTIVE"),
        "steps": steps,
        "next_actions": assistant.get("next_actions", []),
        "can_validate_review": bool(integrity.get("ok")) and not blocking,
        "can_generate_package": review_decision == "VALIDE",
        "limits": {
            "certification_automatic": False,
            "external_evaluator_responses_included": False,
            "requires_human_validation": True,
        },
    }


def app_claude_controller_state(session_id: str, *, session: dict | None = None) -> dict:
    session = session if isinstance(session, dict) else require_session(session_id)
    runtime_mode = str(session.get("runtime_mode") or "")
    routes = {
        "bundle": "/session/claude",
        "action": "/session/claude/action",
        "action_snapshot": "/session/claude/action/snapshot",
        "artifact_lineage": "/session/artifact-lineage",
        "runtime_state": "/session/runtime-state",
        "agents": "/session/agents",
        "agent_prompts": "/session/agent-prompts",
        "model_client": "/session/model-client",
        "live_replay": "/session/live-replay",
        "provider_diagnostics": "/session/provider-diagnostics",
        "skills": "/session/skills",
        "settings": "/session/settings",
        "handoffs": "/session/handoffs",
        "commands": "/session/commands",
        "command": "/session/command",
        "command_history": "/session/command-history",
        "permissions": "/session/permissions",
        "hooks": "/session/hooks",
        "tasks": "/session/tasks",
        "tools": "/session/tools",
        "transcript": "/session/transcript",
    }
    if not is_claude_runtime_mode(runtime_mode):
        return {
            "schema_version": "app_claude_controller_v1",
            "available": False,
            "status": "NON_CLAUDE_RUNTIME",
            "reason": "runtime_mode_not_claude",
            "session_id": session_id,
            "run_id": session.get("run_id", ""),
            "runtime_mode": runtime_mode,
            "routes": routes,
            "agents": [],
            "counts": {},
            "section_health": {},
            "commands": {},
            "permissions": {},
            "hooks": {},
            "tasks": {},
            "tools": {},
            "transcript": {},
            "artifact_lineage": {},
            "runtime_state": {},
            "agent_manifest": {},
            "agent_prompts": {},
            "model_client": {},
            "live_replay": {},
            "provider_diagnostics": {},
            "skills": {},
            "settings": {},
            "handoffs": {},
            "command_history": {},
            "integrity": {},
            "ok": False,
        }

    bundle = session_claude_bundle(session_id, limit=10)
    commands = bundle.get("commands", {}) if isinstance(bundle.get("commands"), dict) else {}
    permissions = bundle.get("permissions", {}) if isinstance(bundle.get("permissions"), dict) else {}
    actions = bundle.get("actions", {}) if isinstance(bundle.get("actions"), dict) else {}
    hooks = bundle.get("hooks", {}) if isinstance(bundle.get("hooks"), dict) else {}
    tasks = bundle.get("tasks", {}) if isinstance(bundle.get("tasks"), dict) else {}
    tools = bundle.get("tools", {}) if isinstance(bundle.get("tools"), dict) else {}
    transcript = bundle.get("transcript", {}) if isinstance(bundle.get("transcript"), dict) else {}
    artifact_lineage = bundle.get("artifact_lineage", {}) if isinstance(bundle.get("artifact_lineage"), dict) else {}
    runtime_state = bundle.get("runtime_state", {}) if isinstance(bundle.get("runtime_state"), dict) else {}
    agent_manifest = bundle.get("agent_manifest", {}) if isinstance(bundle.get("agent_manifest"), dict) else {}
    agent_prompts = bundle.get("agent_prompts", {}) if isinstance(bundle.get("agent_prompts"), dict) else {}
    model_client = bundle.get("model_client", {}) if isinstance(bundle.get("model_client"), dict) else {}
    model_client_summary = (
        model_client.get("model_client", {})
        if isinstance(model_client.get("model_client"), dict)
        else {}
    )
    model_live_loop = (
        model_client.get("live_tool_loop", {})
        if isinstance(model_client.get("live_tool_loop"), dict)
        else model_client_summary.get("live_tool_loop", {})
        if isinstance(model_client_summary.get("live_tool_loop"), dict)
        else {}
    )
    provider_diagnostics = (
        bundle.get("provider_diagnostics", {}) if isinstance(bundle.get("provider_diagnostics"), dict) else {}
    )
    live_replay = bundle.get("live_replay", {}) if isinstance(bundle.get("live_replay"), dict) else {}
    skills = bundle.get("skills", {}) if isinstance(bundle.get("skills"), dict) else {}
    settings = bundle.get("settings", {}) if isinstance(bundle.get("settings"), dict) else {}
    handoffs = bundle.get("handoffs", {}) if isinstance(bundle.get("handoffs"), dict) else {}
    command_history = bundle.get("command_history", {}) if isinstance(bundle.get("command_history"), dict) else {}
    integrity = bundle.get("integrity", {}) if isinstance(bundle.get("integrity"), dict) else {}

    agents: set[str] = set()
    for source in (hooks, tasks, tools, transcript, artifact_lineage, runtime_state, agent_manifest, agent_prompts, skills, handoffs):
        agents.update(agent for agent in source.get("agents", []) if isinstance(agent, str) and agent)
        agents.update(str(agent) for agent in source.get("agent_types", []) if str(agent))
    for command in commands.get("commands", []) if isinstance(commands.get("commands"), list) else []:
        if isinstance(command, dict):
            agents.update(str(agent) for agent in command.get("agents", []) if str(agent))

    permission_summary = permissions.get("permission_summary", {}) if isinstance(permissions.get("permission_summary"), dict) else {}
    permission_state_summary = permissions.get("summary", {}) if isinstance(permissions.get("summary"), dict) else {}
    tool_summary = tools.get("all_summary", {}) if isinstance(tools.get("all_summary"), dict) else {}
    task_summary = tasks.get("all_summary", {}) if isinstance(tasks.get("all_summary"), dict) else {}

    return {
        "schema_version": "app_claude_controller_v1",
        "available": True,
        "status": "CLAUDE_CONTROLLER_READY" if bundle.get("ok") else "CLAUDE_CONTROLLER_ATTENTION",
        "session_id": bundle.get("session_id", session_id),
        "run_id": bundle.get("run_id", session.get("run_id", "")),
        "runtime_mode": runtime_mode,
        "bundle_schema_version": bundle.get("schema_version", ""),
        "routes": routes,
        "agents": sorted(agents),
        "agents_count": len(agents),
        "counts": bundle.get("counts", {}),
        "section_health": bundle.get("section_health", {}),
        "commands": {
            "count": commands.get("commands_count", 0),
            "executable_count": commands.get("executable_commands_count", 0),
            "model_invocable_count": commands.get("model_invocable_commands_count", 0),
            "names": commands.get("command_names", []),
            "model_invocable_names": commands.get("model_invocable_command_names", []),
        },
        "permissions": {
            "available": permissions.get("available", False),
            "mode": permission_state_summary.get("mode", ""),
            "decisions_count": permission_summary.get("decisions_count", permissions.get("decisions_count", 0)),
            "allowed_count": permission_summary.get("allowed_count", 0),
            "denied_count": permission_summary.get("denied_count", 0),
            "update_route": permissions.get("update_route", "/session/permissions"),
        },
        "actions": {
            "count": actions.get("actions_count", 0),
            "mutation_count": actions.get("mutation_count", 0),
            "snapshots_count": actions.get("snapshots_count", 0),
            "ok_count": actions.get("ok_count", 0),
            "failed_count": actions.get("failed_count", 0),
            "by_action": actions.get("by_action", {}),
            "latest": actions.get("latest", {}),
            "path": actions.get("path", ""),
        },
        "hooks": {
            "count": hooks.get("all_invocations_count", 0),
            "filtered_count": hooks.get("invocations_count", 0),
            "events": hooks.get("hook_events", []),
        },
        "tasks": {
            "count": tasks.get("all_tasks_count", 0),
            "filtered_count": tasks.get("tasks_count", 0),
            "statuses": tasks.get("statuses", []),
            "completed_count": task_summary.get("completed_count", 0),
        },
        "tools": {
            "count": tools.get("all_tools_count", 0),
            "filtered_count": tools.get("tools_count", 0),
            "names": tools.get("all_tool_names", []),
            "permissions": tools.get("permissions", []),
            "destructive_tools": tool_summary.get("destructive_tools", []),
            "model_facing_count": len(tools.get("model_facing_tools", []))
            if isinstance(tools.get("model_facing_tools"), list)
            else 0,
        },
        "transcript": {
            "entries_count": transcript.get("all_entries_count", 0),
            "page_entries_count": transcript.get("entries_count", 0),
            "roles": transcript.get("roles", []),
            "block_types": transcript.get("block_types", []),
            "has_more": transcript.get("has_more", False),
            "path": transcript.get("transcript_path", ""),
        },
        "artifact_lineage": {
            "available": artifact_lineage.get("available", False),
            "artifacts_count": artifact_lineage.get("all_artifacts_count", 0),
            "filtered_artifacts_count": artifact_lineage.get("artifacts_count", 0),
            "handoff_edges_count": artifact_lineage.get("all_handoff_edges_count", 0),
            "terminal_artifacts_count": len(artifact_lineage.get("all_terminal_artifact_keys", []))
            if isinstance(artifact_lineage.get("all_terminal_artifact_keys"), list)
            else 0,
            "ok": artifact_lineage.get("ok", False),
        },
        "runtime_state": {
            "available": runtime_state.get("available", False),
            "agents_count": runtime_state.get("agents_count", 0),
            "messages_count": runtime_state.get("summary", {}).get("messages_count", 0)
            if isinstance(runtime_state.get("summary"), dict)
            else 0,
            "estimated_tokens": runtime_state.get("summary", {}).get("estimated_tokens", 0)
            if isinstance(runtime_state.get("summary"), dict)
            else 0,
            "needs_compaction_count": runtime_state.get("summary", {}).get("needs_compaction_count", 0)
            if isinstance(runtime_state.get("summary"), dict)
            else 0,
            "total_cost_usd": runtime_state.get("summary", {}).get("total_cost_usd", 0.0)
            if isinstance(runtime_state.get("summary"), dict)
            else 0.0,
            "ok": runtime_state.get("ok", False),
        },
        "agent_manifest": {
            "available": agent_manifest.get("available", False),
            "agents_count": agent_manifest.get("all_agents_count", agent_manifest.get("agents_count", 0)),
            "filtered_agents_count": agent_manifest.get("agents_count", 0),
            "tools_count": agent_manifest.get("all_summary", {}).get("tools_count", 0)
            if isinstance(agent_manifest.get("all_summary"), dict)
            else 0,
            "skills_count": agent_manifest.get("all_summary", {}).get("skills_count", 0)
            if isinstance(agent_manifest.get("all_summary"), dict)
            else 0,
            "commands_count": agent_manifest.get("all_summary", {}).get("commands_count", 0)
            if isinstance(agent_manifest.get("all_summary"), dict)
            else 0,
            "ok": agent_manifest.get("ok", False),
        },
        "agent_prompts": {
            "available": agent_prompts.get("available", False),
            "prompts_count": agent_prompts.get("all_prompts_count", agent_prompts.get("prompts_count", 0)),
            "filtered_prompts_count": agent_prompts.get("prompts_count", 0),
            "sections_count": agent_prompts.get("all_summary", {}).get("sections_count", 0)
            if isinstance(agent_prompts.get("all_summary"), dict)
            else 0,
            "rendered_chars": agent_prompts.get("all_summary", {}).get("rendered_chars", 0)
            if isinstance(agent_prompts.get("all_summary"), dict)
            else 0,
            "ok": agent_prompts.get("ok", False),
        },
        "model_client": {
            "available": model_client.get("available", False),
            "enabled": model_client_summary.get("enabled", False),
            "provider": model_client_summary.get("provider", ""),
            "requests_count": model_client_summary.get("requests_count", 0),
            "responses_count": model_client_summary.get("responses_count", 0),
            "input_tokens": model_client_summary.get("input_tokens", 0),
            "output_tokens": model_client_summary.get("output_tokens", 0),
            "live_stop_reason": model_live_loop.get("stop_reason", ""),
            "live_turns_count": model_live_loop.get("turns_count", 0),
            "live_tool_calls_count": model_live_loop.get("tool_calls_count", 0),
            "live_tool_results_count": model_live_loop.get("tool_results_count", 0),
            "ok": model_client.get("ok", False),
        },
        "live_replay": {
            "available": live_replay.get("available", False),
            "retry_candidates_count": live_replay.get("retry_candidates_count", 0),
            "permission_requests_count": live_replay.get("permission_requests_count", 0),
            "transcript_ok": live_replay.get("transcript_replay", {}).get("validation", {}).get("ok", False)
            if isinstance(live_replay.get("transcript_replay"), dict)
            and isinstance(live_replay.get("transcript_replay", {}).get("validation"), dict)
            else False,
            "permission_replay_ok": live_replay.get("permission_replay", {}).get("ok", False)
            if isinstance(live_replay.get("permission_replay"), dict)
            else False,
            "ok": live_replay.get("ok", False),
        },
        "provider_diagnostics": {
            "available": provider_diagnostics.get("available", False),
            "provider": provider_diagnostics.get("provider", ""),
            "sdk_transport_ready": provider_diagnostics.get("sdk_transport", {}).get("ready", False)
            if isinstance(provider_diagnostics.get("sdk_transport"), dict)
            else False,
            "api_runtime_ready": provider_diagnostics.get("api_runtime", {}).get("ready", False)
            if isinstance(provider_diagnostics.get("api_runtime"), dict)
            else False,
            "missing_guardrails": provider_diagnostics.get("missing_guardrails", []),
            "ok": provider_diagnostics.get("ok", True),
        },
        "skills": {
            "available": skills.get("available", False),
            "skills_count": skills.get("all_skills_count", skills.get("skills_count", 0)),
            "filtered_skills_count": skills.get("skills_count", 0),
            "agents_count": skills.get("all_summary", {}).get("agents_count", 0)
            if isinstance(skills.get("all_summary"), dict)
            else 0,
            "loaded_from": skills.get("loaded_from", []),
            "plugins_count": skills.get("all_summary", {}).get("plugins_count", 0)
            if isinstance(skills.get("all_summary"), dict)
            else 0,
            "ok": skills.get("ok", False),
        },
        "settings": {
            "available": settings.get("available", False),
            "sources_count": settings.get("all_sources_count", settings.get("sources_count", 0)),
            "filtered_sources_count": settings.get("sources_count", 0),
            "effective_keys_count": settings.get("summary", {}).get("effective_keys_count", 0)
            if isinstance(settings.get("summary"), dict)
            else 0,
            "permission_mode": settings.get("runtime_options", {}).get("permission_mode", "")
            if isinstance(settings.get("runtime_options"), dict)
            else "",
            "include_builtin_commands": settings.get("runtime_options", {}).get("include_builtin_commands", True)
            if isinstance(settings.get("runtime_options"), dict)
            else True,
            "active_sources": settings.get("active_sources", []),
            "ok": settings.get("ok", False),
        },
        "handoffs": {
            "available": handoffs.get("available", False),
            "handoffs_count": handoffs.get("all_handoffs_count", handoffs.get("handoffs_count", 0)),
            "filtered_handoffs_count": handoffs.get("handoffs_count", 0),
            "created_count": handoffs.get("all_created_handoffs_count", 0),
            "received_count": handoffs.get("all_received_handoffs_count", 0),
            "artifacts_count": handoffs.get("all_summary", {}).get("artifacts_count", 0)
            if isinstance(handoffs.get("all_summary"), dict)
            else 0,
            "ok": handoffs.get("ok", False),
        },
        "command_history": {
            "available": command_history.get("available", False),
            "commands_count": command_history.get("all_commands_count", command_history.get("commands_count", 0)),
            "filtered_commands_count": command_history.get("filtered_commands_count", command_history.get("commands_count", 0)),
            "ok_count": command_history.get("all_summary", {}).get("ok_count", 0)
            if isinstance(command_history.get("all_summary"), dict)
            else 0,
            "blocked_count": command_history.get("all_summary", {}).get("blocked_count", 0)
            if isinstance(command_history.get("all_summary"), dict)
            else 0,
            "latest": command_history.get("latest", {}),
            "ok": command_history.get("ok", False),
        },
        "integrity": {
            "ok": integrity.get("ok", False),
            "errors_count": len(integrity.get("errors", [])) if isinstance(integrity.get("errors"), list) else 0,
            "errors": integrity.get("errors", [])[:20] if isinstance(integrity.get("errors"), list) else [],
        },
        "ok": bool(bundle.get("ok")),
    }


def app_session_view(session_id: str) -> dict:
    summary = session_summary(session_id)
    dossier = dossier_review_summary(session_id)
    knowledge = knowledge_immobilier_summary(session_id)
    assistant = assistant_workbench(session_id)
    package = session_package_summary(session_id)
    session = summary.get("session", {}) if isinstance(summary.get("session"), dict) else {}
    subject = knowledge.get("subject_property", {}) if isinstance(knowledge.get("subject_property"), dict) else {}
    reconciliation = knowledge.get("reconciliation", {}) if isinstance(knowledge.get("reconciliation"), dict) else {}
    conclusion = reconciliation.get("conclusion_proposee", {}) if isinstance(reconciliation.get("conclusion_proposee"), dict) else {}
    title = app_title_from_session(session_id, dossier, knowledge)
    card = {
        "id": session_id,
        "slug": session_id,
        "session_id": session_id,
        "address": str(session.get("app_display_name") or title),
        "property_type": str(session.get("app_property_type") or app_property_type_label(subject.get("type_bien"))),
        "neighborhood": str(session.get("app_neighborhood") or subject.get("zone") or "Zone anonymisee"),
        "status": app_status_label(
            {
                "status": dossier.get("status"),
                "package_status": package.get("status", "ABSENT"),
            }
        ),
        "updatedAt": app_date_label(session.get("updated_at_utc")) or "Session locale",
        "pinned": package.get("status") == "PRET_REVUE_EVALUATEUR_AGREE",
        "runtime_status": dossier.get("status", "UNKNOWN"),
        "review_decision": summary.get("review", {}).get("decision", "A_SAISIR") if isinstance(summary.get("review"), dict) else "A_SAISIR",
        "package_status": package.get("status", "ABSENT"),
    }
    return {
        "session": session,
        "dossier": card,
        "documents": app_source_documents(knowledge),
        "fact_chips": app_fact_chips(knowledge, dossier),
        "comparables": app_comparable_rows(knowledge),
        "adjustments": app_adjustment_rows(knowledge, dossier),
        "valuation": {
            "values": dossier.get("valuation", {}).get("values", {}) if isinstance(dossier.get("valuation"), dict) else {},
            "conclusion": conclusion,
            "conclusion_label": app_money(conclusion.get("value")),
            "status": conclusion.get("status", "A_VALIDER_PAR_EVALUATEUR_AGREE"),
        },
        "compliance": dossier.get("compliance", {}),
        "report": {
            "available": dossier.get("report", {}).get("available", False) if isinstance(dossier.get("report"), dict) else False,
            "preview": dossier.get("report", {}).get("preview", "") if isinstance(dossier.get("report"), dict) else "",
            "title": "Brouillon de rapport",
            "subtitle": "Non certifie - validation evaluateur agree requise",
        },
        "knowledge": knowledge,
        "assistant": assistant,
        "claude": app_claude_controller_state(session_id, session=session),
        "package": package,
        "workflow": app_workflow(summary, dossier, package, assistant),
    }


def app_state(session_id: str = "") -> dict:
    product = product_summary()
    session_records = list_session_records(limit=50)
    active_session_id = safe_path_id(session_id) if session_id else ""
    if not active_session_id and session_records:
        active_session_id = str(session_records[0].get("session_id") or "")
    active = app_session_view(active_session_id) if active_session_id else None
    dossiers = [app_dossier_card_from_record(record) for record in session_records]
    if active and isinstance(active, dict):
        active_card = active.get("dossier", {})
        for index, item in enumerate(dossiers):
            if item.get("session_id") == active_session_id:
                dossiers[index] = {**item, **active_card}
                break
    return {
        "schema_version": "evaluateur_ai_app_state_v1",
        "status": "PRET_APP_PRODUIT" if active else "AUCUNE_SESSION",
        "active_session_id": active_session_id,
        "dossiers_count": len(dossiers),
        "dossiers": dossiers,
        "active": active,
        "product": product,
        "routes": {
            "state": "/app/state",
            "demo": "/app/demo",
            "message": "/app/message",
            "claude": "/session/claude",
            "claude_action": "/session/claude/action",
            "claude_action_snapshot": "/session/claude/action/snapshot",
            "artifact_lineage": "/session/artifact-lineage",
            "runtime_state": "/session/runtime-state",
            "agents": "/session/agents",
            "agent_prompts": "/session/agent-prompts",
            "model_client": "/session/model-client",
            "live_replay": "/session/live-replay",
            "provider_diagnostics": "/session/provider-diagnostics",
            "beta_readiness": "/beta/readiness",
            "beta_terms": "/beta/terms",
            "beta_intake": "/beta/intake",
            "skills": "/session/skills",
            "settings": "/session/settings",
            "handoffs": "/session/handoffs",
            "command": "/session/command",
            "commands": "/session/commands",
            "command_history": "/session/command-history",
            "hooks": "/session/hooks",
            "permissions": "/session/permissions",
            "tasks": "/session/tasks",
            "tools": "/session/tools",
            "transcript": "/session/transcript",
            "validate_review": "/app/review/validate",
            "package": "/app/package",
        },
        "limits": {
            "certification_automatic": False,
            "external_evaluator_responses_included": False,
            "requires_human_validation": True,
            "beta_terms_version": BETA_TERMS_VERSION,
            "beta_retention_days": beta_retention_days(),
        },
    }


def app_start_demo(body: dict) -> dict:
    fixture = str(body.get("fixture") or APP_DEFAULT_FIXTURE)
    started = start_runtime({"fixture": fixture, "strict_mode": True})
    session_id = str(started.get("session", {}).get("session_id") or "")
    if session_id and any(body.get(key) for key in ("display_name", "property_type", "neighborhood")):
        session = require_session(session_id)
        session["app_display_name"] = str(body.get("display_name") or "").strip()
        session["app_property_type"] = str(body.get("property_type") or "").strip()
        session["app_neighborhood"] = str(body.get("neighborhood") or "").strip()
        save_session(session)
    state = app_state(session_id)
    return {"schema_version": "evaluateur_ai_app_demo_v1", "started": started, "state": state}


def app_validate_review(body: dict) -> dict:
    session_id = str(body.get("session_id") or "")
    reviewer = str(body.get("reviewer") or "Revue interne locale")
    notes = str(
        body.get("notes")
        or "Validation interne locale pour generer le paquet V1. Valeur non certifiee; validation d'un evaluateur agree requise."
    )
    review = save_review({"session_id": session_id, "decision": "VALIDE", "reviewer": reviewer, "notes": notes})
    return {"schema_version": "evaluateur_ai_app_review_v1", "review": review, "state": app_state(session_id)}


def app_generate_package(body: dict) -> dict:
    session_id = str(body.get("session_id") or "")
    package = generate_v1_package_for_session(session_id)
    return {"schema_version": "evaluateur_ai_app_package_v1", "package": package, "state": app_state(session_id)}


def app_send_message(body: dict) -> dict:
    response = assistant_message(body)
    return {
        "schema_version": "evaluateur_ai_app_message_v1",
        "message": response,
        "state": app_state(str(body.get("session_id") or "")),
    }


def load_ops_json(name: str, runtime_dir: Path | None = None) -> dict:
    filename = OPS_JSON_REPORTS.get(name)
    if not filename:
        raise KeyError(name)
    runtime_dir = runtime_dir or OPS_RUNTIME_DIR
    path = runtime_dir / filename
    if not path.exists():
        return {"status": "ABSENT", "path": str(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"payload": payload}


def load_ops_csv(name: str, runtime_dir: Path | None = None) -> dict:
    filename = OPS_CSV_REPORTS.get(name)
    if not filename:
        raise KeyError(name)
    runtime_dir = runtime_dir or OPS_RUNTIME_DIR
    path = runtime_dir / filename
    if not path.exists():
        return {"status": "ABSENT", "path": str(path), "rows": []}
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    return {"status": "OK", "path": str(path), "rows_count": len(rows), "rows": rows}


def ops_summary(runtime_dir: Path | None = None) -> dict:
    runtime_dir = runtime_dir or OPS_RUNTIME_DIR
    readiness = load_ops_json("readiness", runtime_dir)
    quality = load_ops_json("quality", runtime_dir)
    registry = load_ops_json("registry", runtime_dir)
    delta = load_ops_json("delta", runtime_dir)
    handoff = load_ops_json("handoff", runtime_dir)
    infra = load_ops_json("infra_contracts", runtime_dir)
    schemas = load_ops_json("schema_validation", runtime_dir)
    package_gate = load_ops_json("package_gate", runtime_dir)
    phase_h_gate = load_ops_json("phase_h_gate", runtime_dir)
    doctor = load_ops_json("doctor", runtime_dir)
    review_queue = load_ops_csv("review_queue", runtime_dir)
    phase_h_status = phase_h_gate.get("decision") or phase_h_gate.get("status", "ABSENT")
    waiting_for_real_inputs = "EN_ATTENTE_ENTREES_TERRAIN_REELLES" in {
        str(readiness.get("status", "")),
        str(handoff.get("status", "")),
        str(schemas.get("status", "")),
        str(package_gate.get("status", "")),
        str(phase_h_status),
        str(doctor.get("status", "")),
    }
    return {
        "readiness_status": readiness.get("status", "ABSENT"),
        "delta_status": delta.get("status", "ABSENT"),
        "handoff_status": handoff.get("status", "ABSENT"),
        "infra_contracts_status": infra_status(infra),
        "schema_validation_status": schemas.get("status", "ABSENT"),
        "package_gate_status": package_gate.get("status", "ABSENT"),
        "phase_h_gate_status": phase_h_status,
        "phase_h_mode": phase_h_gate.get("mode", ""),
        "phase_h_active_cases_count": phase_h_gate.get("active_cases_count", 0),
        "doctor_status": doctor.get("status", "ABSENT"),
        "quality_cases_count": quality.get("cases_count", 0),
        "runtime_fingerprint_sha256": readiness.get("runtime_fingerprint_sha256", ""),
        "registry_runs_count": registry.get("runs_count", 0),
        "review_queue_items": review_queue.get("rows_count", 0),
        "waiting_for_real_inputs": waiting_for_real_inputs,
        "blocking_counts": {
            "handoff_missing": len(handoff.get("required_missing_blocking", [])) if isinstance(handoff.get("required_missing_blocking"), list) else 0,
            "infra_invalid": int(infra_invalid_blocking(infra)),
            "schemas_invalid": int(schemas.get("files_invalid_blocking", 0) or 0),
            "package_issues": int(package_gate.get("blocking_issues_count", 0) or 0),
            "phase_h_errors": len(phase_h_gate.get("errors", [])) if isinstance(phase_h_gate.get("errors"), list) else 0,
            "doctor_issues": len(doctor.get("issues", [])) if isinstance(doctor.get("issues"), list) else 0,
        },
        "reports": {
            key: str(runtime_dir / filename)
            for key, filename in {**OPS_JSON_REPORTS, **OPS_CSV_REPORTS}.items()
        },
    }


def infra_invalid_blocking(report: dict) -> int:
    if "files_invalid_blocking" in report:
        return int(report.get("files_invalid_blocking", 0) or 0)
    return 0 if report.get("ok") is True else int(report.get("files_invalid", 0) or 0)


def infra_status(report: dict) -> str:
    if report.get("status"):
        return str(report.get("status"))
    if report.get("ok") is True:
        return "OK"
    if report.get("ok") is False:
        return "A_CORRIGER"
    return str(report.get("status", "ABSENT"))


def file_observability_record(name: str, path: Path) -> dict:
    exists = path.exists() and path.is_file()
    record = {
        "name": name,
        "path": str(path),
        "exists": exists,
        "status": "PRESENT" if exists else "ABSENT",
        "bytes": 0,
        "updated_at_utc": "",
    }
    if exists:
        stat = path.stat()
        record["bytes"] = stat.st_size
        record["updated_at_utc"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat()
    return record


def ops_observability_snapshot(runtime_dir: Path | None = None) -> dict:
    runtime_dir = runtime_dir or OPS_RUNTIME_DIR
    expected = {**OPS_JSON_REPORTS, **OPS_CSV_REPORTS}
    reports = [file_observability_record(name, runtime_dir / filename) for name, filename in expected.items()]
    present = [item for item in reports if item["exists"]]
    missing = [item["name"] for item in reports if not item["exists"]]
    run_report_path = runtime_dir / "pre_reponses_run.json"
    run_report = read_json_dict(run_report_path)
    lock_report = read_json_dict(runtime_dir / "pre_reponses.lock")
    if len(present) == len(reports):
        status = "OBSERVABILITE_COMPLETE"
        next_action = "AUCUNE"
    elif present:
        status = "OBSERVABILITE_PARTIELLE"
        next_action = "EXECUTER_PRE_REPONSES"
    else:
        status = "OBSERVABILITE_A_GENERER"
        next_action = "EXECUTER_PRE_REPONSES"
    return {
        "schema_version": "ops_observability_snapshot_v1",
        "status": status,
        "runtime_dir": str(runtime_dir),
        "expected_reports_count": len(reports),
        "present_reports_count": len(present),
        "missing_reports_count": len(missing),
        "missing_reports": missing,
        "reports": reports,
        "last_run": {
            "exists": bool(run_report),
            "path": str(run_report_path),
            "ok": run_report.get("ok"),
            "started_at_utc": run_report.get("started_at_utc", ""),
            "ended_at_utc": run_report.get("ended_at_utc", ""),
            "duration_seconds": run_report.get("duration_seconds", 0),
            "steps_count": run_report.get("steps_count", 0),
            "failed_step": run_report.get("failed_step", ""),
        },
        "lock": {
            "active": bool(lock_report),
            "status": lock_report.get("status", "ABSENT") if lock_report else "ABSENT",
            "acquired_at_utc": lock_report.get("acquired_at_utc", "") if lock_report else "",
            "ttl_seconds": lock_report.get("ttl_seconds", 0) if lock_report else 0,
        },
        "next_action": next_action,
        "actions": {
            "dry_run": "/ops/pre-response-run {dry_run:true}",
            "run": "/ops/pre-response-run {dry_run:false}",
        },
    }


def run_pre_response_ops(dry_run: bool = False) -> dict:
    from outils.executer_pre_reponses_v0 import execute_pre_response_chain

    return execute_pre_response_chain(
        report_out=OPS_RUNTIME_DIR / "pre_reponses_run.json",
        lock_file=OPS_RUNTIME_DIR / "pre_reponses.lock",
        dry_run=dry_run,
    )


def start_runtime(body: dict) -> dict:
    session = None
    if body.get("session_id"):
        session = load_session(body["session_id"])
        if session is None:
            raise ValueError(f"session introuvable: {body['session_id']}")
    else:
        session = create_session(strict_mode=bool(body.get("strict_mode", True)))

    case, source_fixture = load_case_from_body(body)
    session_dir = Path(session["session_dir"])
    case_key = safe_path_id(str(case.get("dossier_id") or source_fixture.replace(".json", "")))
    case_input_path = session_dir / f"{case_key}.input.json"
    write_json(case_input_path, case)

    runtime_mode = runtime_mode_from_body(body, session)
    settings_context = load_claude_settings(
        project_root=ROOT,
        session_settings=body.get("claude_settings") if isinstance(body.get("claude_settings"), dict) else {},
    )
    result = run_case_runtime_mode(
        runtime_mode,
        case,
        session_dir,
        source_fixture=source_fixture,
        case_key=case_key,
        strict_mode=bool(session.get("strict_mode", True)),
        settings_context=settings_context,
        model_provider_options=body.get("claude_model_provider")
        if isinstance(body.get("claude_model_provider"), dict)
        else None,
    )

    result_path = session_dir / "result.json"
    events_path = session_dir / "events.jsonl"
    artifact_index_path = session_dir / "artifact_index.json"
    knowledge_snapshot_path = session_dir / "knowledge_snapshot.json"

    enriched_events = enrich_events(result["events"], session)
    result["events"] = enriched_events
    claude_transcript_summary = persist_claude_transcript_for_session(result, session)
    permission_state_summary = persist_permission_state_for_session(result, session)
    settings_context = (
        result.get("settings_context", settings_context)
        if isinstance(result.get("settings_context", settings_context), dict)
        else settings_context
    )
    skill_context = result.get("skill_context", {}) if isinstance(result.get("skill_context"), dict) else {}
    command_context = result.get("command_context", {}) if isinstance(result.get("command_context"), dict) else {}
    artifact_index = build_artifact_index(enriched_events)
    knowledge_snapshot = build_knowledge_snapshot(session, result, artifact_index)

    write_json(result_path, result)
    events_path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in enriched_events), encoding="utf-8")
    write_json(artifact_index_path, artifact_index)
    write_json(knowledge_snapshot_path, knowledge_snapshot)

    session.update(
        {
            "status": result["status"],
            "dossier_id": result["dossier_id"],
            "runtime_mode": runtime_mode,
            "source_fixture": source_fixture,
            "case_input_path": str(case_input_path),
            "result_path": str(result_path),
            "events_path": str(events_path),
            "artifact_dir": result["artifact_dir"],
            "artifact_index_path": str(artifact_index_path),
            "knowledge_snapshot_path": str(knowledge_snapshot_path),
            **(
                {
                    "claude_transcript_path": str(result.get("transcript_path") or ""),
                    "claude_transcript_summary": claude_transcript_summary,
                }
                if claude_transcript_summary
                else {}
            ),
            **(
                {
                    "permission_state_path": str(result.get("permission_state_path") or ""),
                    "permission_state_summary": permission_state_summary,
                }
                if permission_state_summary
                else {}
            ),
            "settings_context": settings_context,
            **({"model_client": result.get("model_client", {})} if isinstance(result.get("model_client"), dict) else {}),
            **({"live_adapter": result.get("live_adapter", {})} if isinstance(result.get("live_adapter"), dict) else {}),
            **({"skill_context": skill_context} if skill_context else {}),
            **({"command_context": command_context} if command_context else {}),
        }
    )
    save_session(session)
    return {"session": session, "result": result}


def enrich_events(events: list[dict], session: dict) -> list[dict]:
    enriched: list[dict] = []
    for sequence, event in enumerate(events, start=1):
        enriched.append(enrich_event(event, session, sequence))
    return enriched


def enrich_event(event: dict, session: dict, sequence: int) -> dict:
    session_id = str(session["session_id"])
    run_id = str(session["run_id"])
    item = dict(event)
    item["event_id"] = item.get("event_id") or f"{run_id}_{sequence:04d}"
    item["sequence"] = sequence
    item["session_id"] = session_id
    item["run_id"] = run_id
    item.setdefault("step", "session")
    item.setdefault("artifact", "")
    if item.get("path"):
        item.setdefault("artifact_path", item["path"])
    return item


def build_artifact_index(events: list[dict]) -> dict:
    artifacts: list[dict] = []
    for event in events:
        if event.get("event") != "artifact_written":
            continue
        artifact_path = Path(str(event.get("artifact_path") or event.get("path") or ""))
        record = {
            "event_id": event.get("event_id", ""),
            "step": event.get("step", ""),
            "artifact": event.get("artifact", ""),
            "path": artifact_path.as_posix(),
            "exists": artifact_path.exists(),
            "bytes": artifact_path.stat().st_size if artifact_path.exists() else 0,
            "sha256": sha256_file(artifact_path) if artifact_path.exists() else "",
        }
        artifacts.append(record)
    return {
        "schema_version": "artifact_index_v1",
        "artifacts_count": len(artifacts),
        "artifacts": artifacts,
    }


def persist_claude_transcript_for_session(result: dict, session: dict) -> dict:
    transcript_path_value = str(result.get("transcript_path") or "")
    if not transcript_path_value:
        return {}
    transcript_path = Path(transcript_path_value)
    entries = load_jsonl(transcript_path)
    if not entries:
        return {}

    session_id = str(session["session_id"])
    run_id = str(session["run_id"])
    enriched: list[dict] = []
    for sequence, entry in enumerate(entries, start=1):
        item = dict(entry)
        item["schema_version"] = str(item.get("schema_version") or "claude_transcript_entry_v0")
        item["kind"] = str(item.get("kind") or "message")
        item["sequence"] = sequence
        item["session_id"] = session_id
        item["run_id"] = run_id
        enriched.append(item)

    transcript_path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in enriched),
        encoding="utf-8",
    )
    summary = summarize_claude_transcript_for_session(enriched, transcript_path, result, session)
    result["transcript_summary"] = summary
    return summary


def summarize_claude_transcript_for_session(
    entries: list[dict],
    transcript_path: Path,
    result: dict,
    session: dict,
) -> dict:
    base = result.get("transcript_summary", {})
    summary = dict(base) if isinstance(base, dict) else {}
    roles: dict[str, int] = {}
    agents: list[str] = []
    tool_use_count = 0
    tool_result_count = 0
    handoff_messages_count = 0
    for entry in entries:
        role = str(entry.get("role") or "unknown")
        roles[role] = roles.get(role, 0) + 1
        agent_type = str(entry.get("agent_type") or "")
        if agent_type and agent_type not in agents:
            agents.append(agent_type)
        block_types = entry.get("block_types", [])
        if isinstance(block_types, list):
            tool_use_count += sum(1 for block_type in block_types if block_type == "tool_use")
            tool_result_count += sum(1 for block_type in block_types if block_type == "tool_result")
            handoff_messages_count += sum(1 for block_type in block_types if block_type == "handoff")
    validation = validate_claude_transcript_entries(
        entries,
        agent_type=str(result.get("agent_type") or summary.get("agent_type") or ""),
        session_id=str(session.get("session_id") or ""),
        run_id=str(session.get("run_id") or ""),
    )
    summary.update(
        {
            "schema_version": "claude_transcript_summary_v0",
            "session_id": session.get("session_id", ""),
            "run_id": session.get("run_id", ""),
            "agent_type": result.get("agent_type", summary.get("agent_type", "")),
            "path": transcript_path.as_posix(),
            "entries_count": len(entries),
            "messages_count": len(entries),
            "agents": agents,
            "agents_count": len(agents),
            "roles": roles,
            "tool_use_count": tool_use_count,
            "tool_result_count": tool_result_count,
            "handoff_messages_count": handoff_messages_count,
            "validation": validation,
            "ok": bool(entries) and validation["ok"],
        }
    )
    return summary


def persist_permission_state_for_session(result: dict, session: dict) -> dict:
    permission_state_path_value = str(result.get("permission_state_path") or "")
    if not permission_state_path_value:
        return {}
    permission_state_path = Path(permission_state_path_value)
    state = load_permission_state(permission_state_path)
    if not state:
        return {}

    state["session_id"] = str(session["session_id"])
    state["run_id"] = str(session["run_id"])
    state["path"] = permission_state_path.as_posix()
    state = write_permission_state(permission_state_path, state)
    summary = summarize_permission_state_for_session(state, permission_state_path, result, session)
    result["permission_state"] = state
    result["permission_state_summary"] = summary
    return summary


def settings_context_from_session(session: dict, result: dict) -> dict[str, object]:
    for container in (session, result):
        context = container.get("settings_context", {}) if isinstance(container, dict) else {}
        if isinstance(context, dict) and context:
            return dict(context)
    return {}


def lookup_setting_value(settings: dict[str, object], key: str) -> tuple[bool, object]:
    current: object = settings
    for part in str(key or "").split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def setting_value_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def setting_items_from_payload(
    settings: dict[str, object],
    keys: list[str],
    *,
    key_filter: str = "",
    source: str = "",
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for key in sorted({str(item) for item in keys if str(item)}):
        if key_filter and key != key_filter:
            continue
        found, value = lookup_setting_value(settings, key)
        if not found:
            continue
        items.append(
            {
                "schema_version": "session_settings_item_v1",
                "source": source,
                "key": key,
                "value": value,
                "value_type": setting_value_type(value),
                "redacted": key.startswith("env."),
            }
        )
    return items


def setting_source_items(
    context: dict[str, object],
    *,
    source: str = "",
    key: str = "",
) -> list[dict[str, object]]:
    source_filter = str(source or "").strip()
    key_filter = str(key or "").strip()
    raw_sources = context.get("sources", []) if isinstance(context, dict) else []
    items: list[dict[str, object]] = []
    for raw_source in raw_sources if isinstance(raw_sources, list) else []:
        if not isinstance(raw_source, dict):
            continue
        source_name = str(raw_source.get("source") or "")
        if source_filter and source_name != source_filter:
            continue
        settings = raw_source.get("settings", {}) if isinstance(raw_source.get("settings"), dict) else {}
        raw_keys = raw_source.get("keys", [])
        keys = [str(item) for item in raw_keys if str(item)] if isinstance(raw_keys, list) else []
        setting_items = setting_items_from_payload(settings, keys, key_filter=key_filter, source=source_name)
        if key_filter and not setting_items:
            continue
        item = {
            "schema_version": "session_settings_source_v1",
            "source": source_name,
            "display_name": str(raw_source.get("display_name") or source_name),
            "path": str(raw_source.get("path") or ""),
            "exists": bool(raw_source.get("exists", False)),
            "editable": bool(raw_source.get("editable", False)),
            "keys": [str(entry.get("key") or "") for entry in setting_items if entry.get("key")],
            "keys_count": len(setting_items),
            "settings_items": setting_items,
            "settings": settings if not key_filter else {entry["key"]: entry["value"] for entry in setting_items},
        }
        items.append(item)
    return items


def summarize_session_settings(
    context: dict[str, object],
    sources: list[dict[str, object]],
    effective_items: list[dict[str, object]],
) -> dict[str, object]:
    runtime_options = context.get("runtime_options", {}) if isinstance(context.get("runtime_options"), dict) else {}
    validation = context.get("validation", {}) if isinstance(context.get("validation"), dict) else {}
    return {
        "schema_version": "session_settings_summary_v1",
        "sources_count": len(sources),
        "active_sources": [str(source.get("source") or "") for source in sources if source.get("source")],
        "editable_sources": [str(source.get("source") or "") for source in sources if source.get("editable")],
        "effective_items_count": len(effective_items),
        "effective_keys_count": len(context.get("effective_keys", [])) if isinstance(context.get("effective_keys"), list) else 0,
        "permission_mode": str(runtime_options.get("permission_mode") or ""),
        "include_builtin_commands": bool(runtime_options.get("include_builtin_commands", True)),
        "disabled_commands_count": len(runtime_options.get("disabled_commands", []))
        if isinstance(runtime_options.get("disabled_commands"), list)
        else 0,
        "enabled_commands_count": len(runtime_options.get("enabled_commands", []))
        if isinstance(runtime_options.get("enabled_commands"), list)
        else 0,
        "env_keys_count": len(runtime_options.get("env_keys", []))
        if isinstance(runtime_options.get("env_keys"), list)
        else 0,
        "warnings_count": len(validation.get("warnings", []))
        if isinstance(validation.get("warnings"), list)
        else 0,
        "errors_count": len(validation.get("errors", []))
        if isinstance(validation.get("errors"), list)
        else 0,
        "ok": bool(context.get("ok", False)),
    }


def validate_session_settings_context(context: dict[str, object]) -> dict[str, object]:
    validation = validate_settings_context(context) if isinstance(context, dict) and context else {
        "schema_version": "claude_settings_validation_v0",
        "errors": ["settings_context_missing"],
        "ok": False,
    }
    errors = [str(error) for error in validation.get("errors", []) if str(error)]
    if not isinstance(context, dict) or not context:
        return {
            "schema_version": "session_settings_validation_v1",
            "errors": sorted(set(errors)),
            "ok": False,
        }
    if context.get("schema_version") != "claude_settings_context_v0":
        errors.append("settings_context_schema_invalid")
    raw_sources = context.get("sources", [])
    sources = raw_sources if isinstance(raw_sources, list) else []
    if not isinstance(raw_sources, list):
        errors.append("settings_sources_not_list")
    if int(context.get("sources_count", 0) or 0) != len(sources):
        errors.append("settings_sources_count_mismatch")
    source_names: list[str] = []
    source_order = context.get("source_order", []) if isinstance(context.get("source_order"), list) else []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"settings_source_not_object:{index}")
            continue
        source_name = str(source.get("source") or "")
        if not source_name:
            errors.append(f"settings_source_missing_name:{index}")
        else:
            source_names.append(source_name)
            if source_order and source_name not in source_order:
                errors.append(f"settings_source_unknown:{source_name}")
        if not isinstance(source.get("keys", []), list):
            errors.append(f"settings_source_keys_not_list:{source_name or index}")
        if not isinstance(source.get("settings", {}), dict):
            errors.append(f"settings_source_settings_not_object:{source_name or index}")
        path = str(source.get("path") or "")
        if path and source.get("exists") and not Path(path).exists():
            errors.append(f"settings_source_path_missing:{source_name or index}")
    active_sources = [str(item) for item in context.get("active_sources", [])] if isinstance(context.get("active_sources"), list) else []
    if active_sources != source_names:
        errors.append("settings_active_sources_mismatch")
    runtime_options = context.get("runtime_options", {})
    if not isinstance(runtime_options, dict) or runtime_options.get("schema_version") != "claude_runtime_settings_v0":
        errors.append("settings_runtime_options_invalid")
    return {
        "schema_version": "session_settings_validation_v1",
        "sources_count": len(sources),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_settings(session_id: str, *, source: str = "", key: str = "") -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    context = settings_context_from_session(session, result)
    source_filter = str(source or "").strip()
    key_filter = str(key or "").strip()
    all_sources = setting_source_items(context)
    sources = setting_source_items(context, source=source_filter, key=key_filter)
    effective = context.get("effective", {}) if isinstance(context.get("effective"), dict) else {}
    raw_effective_keys = context.get("effective_keys", [])
    effective_keys = [str(item) for item in raw_effective_keys if str(item)] if isinstance(raw_effective_keys, list) else []
    effective_items = setting_items_from_payload(effective, effective_keys, key_filter=key_filter, source="effective")
    validation = validate_session_settings_context(context)
    return {
        "schema_version": "session_settings_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(context),
        "filters": {
            "source": source_filter,
            "key": key_filter,
        },
        "source_order": context.get("source_order", []) if isinstance(context.get("source_order"), list) else [],
        "enabled_sources": context.get("enabled_sources", []) if isinstance(context.get("enabled_sources"), list) else [],
        "active_sources": context.get("active_sources", []) if isinstance(context.get("active_sources"), list) else [],
        "sources_count": len(sources),
        "all_sources_count": len(all_sources),
        "sources": sources,
        "effective_keys": [str(item.get("key") or "") for item in effective_items if item.get("key")],
        "all_effective_keys": effective_keys,
        "effective_items": effective_items,
        "effective": effective if not key_filter else {item["key"]: item["value"] for item in effective_items},
        "runtime_options": context.get("runtime_options", {}) if isinstance(context.get("runtime_options"), dict) else {},
        "summary": summarize_session_settings(context, sources, effective_items),
        "all_summary": summarize_session_settings(context, all_sources, setting_items_from_payload(effective, effective_keys, source="effective")),
        "validation": validation,
        "ok": bool(context) and bool(validation.get("ok")),
    }


def skill_contexts_by_agent_from_session(session: dict, result: dict) -> dict[str, dict[str, object]]:
    for container in (result, session):
        raw = container.get("skill_context_by_agent", {}) if isinstance(container, dict) else {}
        if isinstance(raw, dict) and raw:
            return {
                str(agent): dict(context)
                for agent, context in raw.items()
                if str(agent) and isinstance(context, dict)
            }

    for container in (result, session):
        context = container.get("skill_context", {}) if isinstance(container, dict) else {}
        if not isinstance(context, dict) or not context:
            continue
        contexts_by_agent = context.get("contexts_by_agent", {})
        if isinstance(contexts_by_agent, dict) and contexts_by_agent:
            return {
                str(agent): dict(agent_context)
                for agent, agent_context in contexts_by_agent.items()
                if str(agent) and isinstance(agent_context, dict)
            }
        agent_type = str(context.get("agent_type") or result.get("agent_type") or "")
        if agent_type and agent_type != "claude-pipeline":
            return {agent_type: dict(context)}
    return {}


def merge_skill_palette_item(skills_by_name: dict[str, dict[str, object]], skill: object, agent: str) -> None:
    if not isinstance(skill, dict):
        return
    name = str(skill.get("name") or "")
    if not name:
        return
    current = skills_by_name.get(name)
    if current is None:
        current = dict(skill)
        current["declared_agents"] = (
            list(skill.get("agents", []))
            if isinstance(skill.get("agents"), list)
            else []
        )
        current["agents"] = []
        skills_by_name[name] = current
    if agent and agent not in current["agents"]:
        current["agents"].append(agent)
    for field in ("allowed_tools", "paths", "hooks", "context", "errors"):
        existing = current.get(field, [])
        incoming = skill.get(field, []) if isinstance(skill, dict) else []
        if isinstance(existing, list) and isinstance(incoming, list):
            current[field] = list(dict.fromkeys([*existing, *incoming]))
    current["ok"] = bool(current.get("ok", True)) and bool(skill.get("ok", True))


def skill_palette_items(
    contexts_by_agent: dict[str, dict[str, object]],
    *,
    agent: str = "",
    skill: str = "",
    loaded_from: str = "",
) -> list[dict[str, object]]:
    agent_filter = str(agent or "").strip()
    skill_filter = str(skill or "").strip()
    loaded_from_filter = str(loaded_from or "").strip()
    skills_by_name: dict[str, dict[str, object]] = {}
    for agent_name, context in contexts_by_agent.items():
        if agent_filter and agent_name != agent_filter:
            continue
        skills = context.get("skills", []) if isinstance(context, dict) else []
        for item in skills if isinstance(skills, list) else []:
            merge_skill_palette_item(skills_by_name, item, agent_name)

    items: list[dict[str, object]] = []
    for item in skills_by_name.values():
        name = str(item.get("name") or "")
        if skill_filter and name != skill_filter:
            continue
        if loaded_from_filter and str(item.get("loaded_from") or "") != loaded_from_filter:
            continue
        items.append(item)
    return sorted(items, key=lambda item: str(item.get("name") or ""))


def summarize_session_skill_palette(
    items: list[dict[str, object]],
    contexts_by_agent: dict[str, dict[str, object]],
) -> dict[str, object]:
    skill_names = [str(item.get("name") or "") for item in items if item.get("name")]
    loaded_from = sorted({str(item.get("loaded_from") or "") for item in items if item.get("loaded_from")})
    sources = sorted({str(item.get("source") or "") for item in items if item.get("source")})
    plugins = sorted({str(item.get("plugin") or "") for item in items if item.get("plugin")})
    allowed_tools = sorted(
        {
            str(tool)
            for item in items
            for tool in item.get("allowed_tools", []) if isinstance(item.get("allowed_tools"), list)
            if str(tool)
        }
    )
    return {
        "schema_version": "session_skills_summary_v1",
        "agents": sorted(contexts_by_agent),
        "agents_count": len(contexts_by_agent),
        "skills_count": len(items),
        "unique_skills_count": len(set(skill_names)),
        "assigned_skills_count": sum(int(context.get("skills_count", 0) or 0) for context in contexts_by_agent.values()),
        "skill_names": sorted(set(skill_names)),
        "loaded_from": loaded_from,
        "sources": sources,
        "plugins": plugins,
        "plugins_count": len(plugins),
        "allowed_tools": allowed_tools,
        "total_frontmatter_tokens": sum(int(item.get("frontmatter_tokens", 0) or 0) for item in items),
        "total_content_length": sum(int(item.get("content_length", 0) or 0) for item in items),
        "user_invocable_count": sum(1 for item in items if item.get("user_invocable") is True),
        "disable_model_invocation_count": sum(1 for item in items if item.get("disable_model_invocation") is True),
        "path_scoped_count": sum(1 for item in items if isinstance(item.get("paths"), list) and item.get("paths")),
        "analysis_backed_count": sum(1 for item in items if item.get("has_analysis") is True),
        "ok": all(bool(item.get("ok", True)) for item in items),
    }


def validate_session_skill_contexts(contexts_by_agent: dict[str, dict[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    if not contexts_by_agent:
        errors.append("skill_context_missing")
    for agent, context in contexts_by_agent.items():
        validation = validate_skill_context(context)
        errors.extend(f"{agent}:{error}" for error in validation.get("errors", []))
        skills = context.get("skills", []) if isinstance(context, dict) else []
        if not isinstance(skills, list):
            errors.append(f"{agent}:skills_not_list")
            continue
        if int(context.get("skills_count", 0) or 0) != len(skills):
            errors.append(f"{agent}:skills_count_mismatch")
        for index, skill in enumerate(skills, start=1):
            if not isinstance(skill, dict):
                errors.append(f"{agent}:skill_not_object:{index}")
                continue
            name = str(skill.get("name") or "")
            if skill.get("schema_version") != "claude_skill_spec_v0":
                errors.append(f"{agent}:skill_schema_invalid:{name or index}")
            path = str(skill.get("path") or "")
            if not path:
                errors.append(f"{agent}:skill_missing_path:{name or index}")
            elif not (ROOT / path).exists():
                errors.append(f"{agent}:skill_file_missing:{path}")
            if not skill.get("ok", True):
                errors.append(f"{agent}:skill_not_ok:{name or index}")
    return {
        "schema_version": "session_skills_validation_v1",
        "agents_count": len(contexts_by_agent),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_skills(session_id: str, *, agent: str = "", skill: str = "", loaded_from: str = "") -> dict:
    session = require_session(session_id)
    runtime_mode = str(session.get("runtime_mode") or "")
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    agent_filter = str(agent or "").strip()
    skill_filter = str(skill or "").strip()
    loaded_from_filter = str(loaded_from or "").strip()
    contexts_by_agent = skill_contexts_by_agent_from_session(session, result)
    filtered_contexts = {
        name: context
        for name, context in contexts_by_agent.items()
        if not agent_filter or name == agent_filter
    }
    all_items = skill_palette_items(contexts_by_agent)
    items = skill_palette_items(
        contexts_by_agent,
        agent=agent_filter,
        skill=skill_filter,
        loaded_from=loaded_from_filter,
    )
    validation = validate_session_skill_contexts(contexts_by_agent) if is_claude_runtime_mode(runtime_mode) else {
        "schema_version": "session_skills_validation_v1",
        "agents_count": 0,
        "errors": [],
        "ok": False,
    }
    return {
        "schema_version": "session_skills_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": runtime_mode,
        "available": bool(contexts_by_agent),
        "filters": {
            "agent": agent_filter,
            "skill": skill_filter,
            "loaded_from": loaded_from_filter,
        },
        "agents": sorted(contexts_by_agent),
        "loaded_from": sorted({str(item.get("loaded_from") or "") for item in all_items if item.get("loaded_from")}),
        "all_skills_count": len(all_items),
        "skills_count": len(items),
        "skill_names": [str(item.get("name") or "") for item in items if item.get("name")],
        "all_skill_names": [str(item.get("name") or "") for item in all_items if item.get("name")],
        "summary": summarize_session_skill_palette(items, filtered_contexts),
        "all_summary": summarize_session_skill_palette(all_items, contexts_by_agent),
        "contexts_by_agent": filtered_contexts,
        "skills": items,
        "validation": validation,
        "ok": bool(contexts_by_agent) and bool(validation.get("ok")),
    }


def execute_session_slash_command(body: dict) -> dict:
    session = require_session(str(body.get("session_id") or ""))
    command_name = str(body.get("command") or body.get("command_name") or "").strip()
    if not command_name:
        raise ValueError("command requis")
    args = str(body.get("args") or "")
    result_path = Path(str(session.get("result_path") or ""))
    result = read_json_dict(result_path)
    if not result:
        raise ValueError("resultat session introuvable")

    runner = load_claude_runner_for_session(session)
    command_result = runner.execute_slash_command(command_name, args=args, runtime_result=result)
    command_summary = persist_session_slash_command(session, result, command_result)
    write_json(result_path, result)
    save_session(session)
    return {
        "schema_version": "session_slash_command_v1",
        "session": session,
        "command_result": command_result,
        "command_summary": command_summary,
        "result": {
            "status": result.get("status", session.get("status", "UNKNOWN")),
            "events_count": len(result.get("events", [])) if isinstance(result.get("events"), list) else 0,
            "messages_count": len(result.get("messages", [])) if isinstance(result.get("messages"), list) else 0,
            "conversation_state": result.get("conversation_state", {}),
            "context_state": result.get("context_state", {}),
            "transcript_summary": result.get("transcript_summary", {}),
        },
    }


def session_commands(session_id: str) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    command_context = session.get("command_context", result.get("command_context", {}))
    if not isinstance(command_context, dict) or not command_context:
        return {
            "schema_version": "session_slash_command_palette_v1",
            "session_id": session["session_id"],
            "run_id": session.get("run_id", ""),
            "runtime_mode": session.get("runtime_mode", ""),
            "commands_count": 0,
            "executable_commands_count": 0,
            "command_names": [],
            "executable_command_names": [],
            "model_invocable_command_names": [],
            "commands": [],
            "history": read_slash_command_history(session),
        }

    commands = command_palette_items(command_context)
    command_names = [str(command.get("name") or "") for command in commands if command.get("name")]
    executable = [command for command in commands if command.get("executable") is True]
    model_invocable = [command for command in commands if command.get("model_invocable") is True]
    return {
        "schema_version": "session_slash_command_palette_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "command_context_schema_version": command_context.get("schema_version", ""),
        "commands_count": len(commands),
        "executable_commands_count": len(executable),
        "model_invocable_commands_count": len(model_invocable),
        "command_names": command_names,
        "executable_command_names": [str(command["name"]) for command in executable],
        "model_invocable_command_names": [str(command["name"]) for command in model_invocable],
        "settings_filtered_command_names": command_context.get("settings_filtered_command_names", []),
        "commands": commands,
        "history": read_slash_command_history(session),
        "execution_route": "/session/command",
        "ok": bool(command_context.get("ok", True)),
    }


def command_palette_items(command_context: dict) -> list[dict[str, object]]:
    raw_items = flatten_command_context_commands(command_context)
    model_invocable_names = set(
        str(name)
        for name in command_context.get("model_invocable_command_names", [])
        if str(name)
    )
    if not model_invocable_names:
        contexts_by_agent = command_context.get("contexts_by_agent", {})
        if isinstance(contexts_by_agent, dict):
            for context in contexts_by_agent.values():
                if not isinstance(context, dict):
                    continue
                model_invocable_names.update(
                    str(name)
                    for name in context.get("model_invocable_command_names", [])
                    if str(name)
                )
    items: list[dict[str, object]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        spec = command_spec_from_context(raw)
        execution_error = validate_local_command_execution(spec)
        name = str(raw.get("name") or "")
        items.append(
            {
                "name": name,
                "slash_name": f"/{name}" if name else "",
                "description": str(raw.get("description") or ""),
                "type": str(raw.get("type") or ""),
                "source": str(raw.get("source") or ""),
                "loaded_from": str(raw.get("loaded_from") or ""),
                "agents": list(raw.get("agents", [])) if isinstance(raw.get("agents"), list) else [],
                "aliases": list(raw.get("aliases", [])) if isinstance(raw.get("aliases"), list) else [],
                "argument_hint": str(raw.get("argument_hint") or ""),
                "user_invocable": bool(raw.get("user_invocable", True)),
                "model_invocable": name in model_invocable_names,
                "supports_non_interactive": bool(raw.get("supports_non_interactive", False)),
                "bridge_safe": bool(raw.get("bridge_safe", False)),
                "remote_safe": bool(raw.get("remote_safe", False)),
                "executable": not execution_error,
                "execution_error": execution_error,
                "execution_route": "/session/command" if not execution_error else "",
            }
        )
    return sorted(items, key=lambda item: str(item.get("name") or ""))


def flatten_command_context_commands(command_context: dict) -> list[dict[str, object]]:
    commands_by_name: dict[str, dict[str, object]] = {}
    commands = command_context.get("commands", [])
    if isinstance(commands, list):
        for command in commands:
            merge_command_palette_item(commands_by_name, command, str(command_context.get("agent_type") or ""))

    contexts_by_agent = command_context.get("contexts_by_agent", {})
    if isinstance(contexts_by_agent, dict):
        for agent, context in contexts_by_agent.items():
            if not isinstance(context, dict):
                continue
            for command in context.get("commands", []) if isinstance(context.get("commands"), list) else []:
                merge_command_palette_item(commands_by_name, command, str(agent))

    return list(commands_by_name.values())


def merge_command_palette_item(
    commands_by_name: dict[str, dict[str, object]],
    command: object,
    agent: str,
) -> None:
    if not isinstance(command, dict):
        return
    name = str(command.get("name") or "")
    if not name:
        return
    current = commands_by_name.get(name)
    if current is None:
        current = dict(command)
        current["agents"] = []
        commands_by_name[name] = current
    if agent and agent not in current["agents"]:
        current["agents"].append(agent)


def command_spec_from_context(command: dict[str, object]) -> CommandSpec:
    return CommandSpec(
        name=str(command.get("name") or ""),
        type=str(command.get("type") or ""),
        description=str(command.get("description") or ""),
        source=str(command.get("source") or ""),
        loaded_from=str(command.get("loaded_from") or "builtin"),
        aliases=[str(item) for item in command.get("aliases", [])] if isinstance(command.get("aliases"), list) else [],
        argument_hint=str(command.get("argument_hint") or ""),
        supports_non_interactive=bool(command.get("supports_non_interactive", False)),
        immediate=bool(command.get("immediate", False)),
        is_hidden=bool(command.get("is_hidden", False)),
        is_sensitive=bool(command.get("is_sensitive", False)),
        has_user_specified_description=bool(command.get("has_user_specified_description", True)),
        disable_model_invocation=bool(command.get("disable_model_invocation", False)),
        user_invocable=bool(command.get("user_invocable", True)),
        bridge_safe=bool(command.get("bridge_safe", False)),
        remote_safe=bool(command.get("remote_safe", False)),
        ok=bool(command.get("ok", True)),
        errors=[str(item) for item in command.get("errors", [])] if isinstance(command.get("errors"), list) else [],
    )


def read_slash_command_history(session: dict) -> dict:
    path_value = str(session.get("slash_command_history_path") or "")
    path = Path(path_value) if path_value else Path(str(session.get("session_dir") or "")) / SLASH_COMMANDS_FILENAME
    records, errors = load_jsonl_lenient(path)
    if path_value and (not path.exists() or not path.is_file()):
        errors.append("missing")
    return {
        "schema_version": "session_slash_command_history_v1",
        "available": bool(records),
        "path": path.as_posix() if path_value or path.exists() else "",
        "commands_count": len(records),
        "ok_count": sum(1 for item in records if item.get("ok") is True),
        "blocked_count": sum(1 for item in records if item.get("ok") is not True),
        "latest": records[-1] if records else {},
        "records": records,
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def summarize_session_command_history(records: list[dict[str, object]]) -> dict[str, object]:
    statuses = sorted({str(record.get("status") or "") for record in records if record.get("status")})
    command_names = sorted({str(record.get("command_name") or "") for record in records if record.get("command_name")})
    command_types = sorted({str(record.get("command_type") or "") for record in records if record.get("command_type")})
    return {
        "schema_version": "session_slash_command_history_summary_v1",
        "commands_count": len(records),
        "ok_count": sum(1 for record in records if record.get("ok") is True),
        "blocked_count": sum(1 for record in records if record.get("ok") is not True),
        "command_names": command_names,
        "command_names_count": len(command_names),
        "command_types": command_types,
        "statuses": statuses,
        "latest": records[-1] if records else {},
    }


def validate_slash_command_history(session: dict, summary: dict | None = None) -> tuple[dict[str, object], list[dict[str, object]]]:
    summary = summary if isinstance(summary, dict) else {}
    path_value = str(summary.get("path") or session.get("slash_command_history_path") or "")
    path = Path(path_value) if path_value else Path(str(session.get("session_dir") or "")) / SLASH_COMMANDS_FILENAME
    records, load_errors = load_jsonl_lenient(path)
    errors = [str(error) for error in load_errors if str(error)]
    if path_value and (not path.exists() or not path.is_file()):
        errors.append("missing")
    if path.exists() and path.is_file():
        try:
            path.resolve().relative_to(Path(str(session["session_dir"])).resolve())
        except ValueError:
            errors.append("outside_session")
    if summary and int(summary.get("commands_count", 0) or 0) != len(records):
        errors.append("count_mismatch")
    for index, record in enumerate(records, start=1):
        if record.get("schema_version") != "session_slash_command_record_v1":
            errors.append(f"schema_invalid:{index}")
        if record.get("session_id") != session.get("session_id"):
            errors.append(f"session_mismatch:{index}")
        if record.get("run_id") != session.get("run_id"):
            errors.append(f"run_mismatch:{index}")
        if not record.get("command_name"):
            errors.append(f"missing_command_name:{index}")
        if not record.get("status"):
            errors.append(f"missing_status:{index}")
        if not isinstance(record.get("ok"), bool):
            errors.append(f"ok_not_boolean:{index}")
        if not isinstance(record.get("errors", []), list):
            errors.append(f"errors_not_list:{index}")
    return (
        {
            "schema_version": "session_slash_command_history_validation_v1",
            "available": bool(records),
            "path": path.as_posix() if path_value or path.exists() else "",
            "records_count": len(records),
            "errors": sorted(set(errors)),
            "ok": not errors,
        },
        records,
    )


def session_command_history(
    session_id: str,
    *,
    command: str = "",
    status: str = "",
    ok: str = "",
    offset: int = 0,
    limit: int = 20,
) -> dict:
    session = require_session(session_id)
    command_filter = str(command or "").strip().lstrip("/")
    status_filter = str(status or "").strip()
    ok_filter_raw = str(ok or "").strip().lower()
    ok_filter: bool | None = None
    if ok_filter_raw in {"true", "1", "yes", "ok", "success"}:
        ok_filter = True
    elif ok_filter_raw in {"false", "0", "no", "blocked", "failed"}:
        ok_filter = False
    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 20), 0), 100)
    summary = session.get("slash_command_summary", {}) if isinstance(session.get("slash_command_summary"), dict) else {}
    validation, all_records = validate_slash_command_history(session, summary)
    filtered_records = [
        record
        for record in all_records
        if (not command_filter or record.get("command_name") == command_filter)
        and (not status_filter or record.get("status") == status_filter)
        and (ok_filter is None or record.get("ok") is ok_filter)
    ]
    records = filtered_records[safe_offset : safe_offset + safe_limit] if safe_limit else []
    return {
        "schema_version": "session_slash_command_history_browser_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(all_records),
        "path": validation.get("path", ""),
        "filters": {
            "command": command_filter,
            "status": status_filter,
            "ok": "" if ok_filter is None else ok_filter,
            "offset": safe_offset,
            "limit": safe_limit,
        },
        "all_commands_count": len(all_records),
        "filtered_commands_count": len(filtered_records),
        "commands_count": len(records),
        "has_more": safe_offset + safe_limit < len(filtered_records) if safe_limit else bool(filtered_records),
        "command_names": summarize_session_command_history(all_records)["command_names"],
        "statuses": summarize_session_command_history(all_records)["statuses"],
        "summary": summarize_session_command_history(records),
        "filtered_summary": summarize_session_command_history(filtered_records),
        "all_summary": summarize_session_command_history(all_records),
        "latest": all_records[-1] if all_records else {},
        "records": records,
        "validation": validation,
        "ok": (not all_records) or bool(validation.get("ok")),
    }


def read_claude_action_history(session: dict) -> dict:
    path_value = str(session.get("claude_action_history_path") or "")
    path = Path(path_value) if path_value else Path(str(session.get("session_dir") or "")) / CLAUDE_ACTIONS_FILENAME
    records, errors = load_jsonl_lenient(path)
    if path_value and (not path.exists() or not path.is_file()):
        errors.append("missing")
    by_action: dict[str, int] = {}
    for record in records:
        action = str(record.get("action") or "")
        if action:
            by_action[action] = by_action.get(action, 0) + 1
    return {
        "schema_version": "session_claude_action_history_v1",
        "path": path.as_posix() if path_value or path.exists() else "",
        "actions_count": len(records),
        "mutation_count": sum(1 for item in records if item.get("mutation_applied") is True),
        "snapshots_count": sum(1 for item in records if item.get("snapshot_path")),
        "ok_count": sum(1 for item in records if item.get("ok") is True),
        "failed_count": sum(1 for item in records if item.get("ok") is not True),
        "by_action": by_action,
        "latest": records[-1] if records else {},
        "records": records,
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def validate_claude_action_history(session: dict, summary: dict | None = None) -> tuple[dict[str, object], list[dict]]:
    summary = summary if isinstance(summary, dict) else {}
    path_value = str(summary.get("path") or session.get("claude_action_history_path") or "")
    errors: list[str] = []
    records: list[dict] = []
    if not path_value:
        return {
            "schema_version": "session_claude_action_history_validation_v1",
            "available": False,
            "records_count": 0,
            "errors": [],
            "ok": True,
        }, []

    path = Path(path_value)
    if not path.exists() or not path.is_file():
        errors.append("missing")
    else:
        try:
            path.resolve().relative_to(Path(str(session["session_dir"])).resolve())
        except ValueError:
            errors.append("outside_session")
        records, load_errors = load_jsonl_lenient(path)
        errors.extend(load_errors)

    by_action: dict[str, int] = {}
    snapshot_paths_count = 0
    snapshot_files_count = 0
    supported_actions = {"execute_command", "update_permissions", "live_replay", "refresh"}
    for index, record in enumerate(records, start=1):
        for field in (
            "schema_version",
            "created_at_utc",
            "action_id",
            "session_id",
            "run_id",
            "action",
            "requested_action",
            "mutation_applied",
            "status",
            "ok",
            "action_result_schema_version",
            "snapshot_path",
        ):
            if field not in record:
                errors.append(f"missing_{field}:{index}")
        if record.get("schema_version") != "session_claude_action_record_v1":
            errors.append(f"schema_invalid:{index}")
        if record.get("session_id") != session.get("session_id"):
            errors.append(f"session_mismatch:{index}")
        if record.get("run_id") != session.get("run_id"):
            errors.append(f"run_mismatch:{index}")
        action_name = str(record.get("action") or "")
        if action_name not in supported_actions:
            errors.append(f"action_invalid:{index}")
        else:
            by_action[action_name] = by_action.get(action_name, 0) + 1
        if not isinstance(record.get("mutation_applied"), bool):
            errors.append(f"mutation_applied_invalid:{index}")
        if not isinstance(record.get("ok"), bool):
            errors.append(f"ok_invalid:{index}")
        action_id = str(record.get("action_id") or "")
        snapshot_path_value = str(record.get("snapshot_path") or "")
        if snapshot_path_value:
            snapshot_paths_count += 1
            snapshot_path = Path(snapshot_path_value)
            snapshot_inside_session = True
            try:
                snapshot_path.resolve().relative_to(Path(str(session["session_dir"])).resolve())
            except ValueError:
                snapshot_inside_session = False
                errors.append(f"snapshot_outside_session:{index}")
            if not snapshot_path.exists() or not snapshot_path.is_file():
                errors.append(f"snapshot_missing:{index}")
            elif snapshot_inside_session:
                try:
                    snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    errors.append(f"snapshot_json_invalid:{index}")
                    snapshot_payload = {}
                if not isinstance(snapshot_payload, dict):
                    errors.append(f"snapshot_not_object:{index}")
                    snapshot_payload = {}
                if snapshot_payload:
                    snapshot_files_count += 1
                    if snapshot_payload.get("schema_version") != "session_claude_action_snapshot_v1":
                        errors.append(f"snapshot_schema_invalid:{index}")
                    if action_id and snapshot_payload.get("action_id") != action_id:
                        errors.append(f"snapshot_action_id_mismatch:{index}")
                    if snapshot_payload.get("session_id") != session.get("session_id"):
                        errors.append(f"snapshot_session_mismatch:{index}")
                    if snapshot_payload.get("run_id") != session.get("run_id"):
                        errors.append(f"snapshot_run_mismatch:{index}")
                    if action_name and snapshot_payload.get("action") != action_name:
                        errors.append(f"snapshot_action_mismatch:{index}")
                    if snapshot_payload.get("requested_action") != record.get("requested_action"):
                        errors.append(f"snapshot_requested_action_mismatch:{index}")

    if summary:
        if len(records) != int(summary.get("actions_count", 0) or 0):
            errors.append("count_mismatch")
        if sum(1 for item in records if item.get("mutation_applied") is True) != int(summary.get("mutation_count", 0) or 0):
            errors.append("mutation_count_mismatch")
        if snapshot_paths_count != int(summary.get("snapshots_count", 0) or 0):
            errors.append("snapshots_count_mismatch")
        if sum(1 for item in records if item.get("ok") is True) != int(summary.get("ok_count", 0) or 0):
            errors.append("ok_count_mismatch")
        if sum(1 for item in records if item.get("ok") is not True) != int(summary.get("failed_count", 0) or 0):
            errors.append("failed_count_mismatch")
        summary_by_action = summary.get("by_action", {}) if isinstance(summary.get("by_action"), dict) else {}
        if {str(key): int(value) for key, value in summary_by_action.items()} != by_action:
            errors.append("by_action_mismatch")

    return {
        "schema_version": "session_claude_action_history_validation_v1",
        "available": True,
        "path": path_value,
        "records_count": len(records),
        "summary_actions_count": int(summary.get("actions_count", 0) or 0) if summary else 0,
        "mutation_count": sum(1 for item in records if item.get("mutation_applied") is True),
        "snapshots_count": snapshot_paths_count,
        "snapshot_files_count": snapshot_files_count,
        "ok_count": sum(1 for item in records if item.get("ok") is True),
        "failed_count": sum(1 for item in records if item.get("ok") is not True),
        "by_action": by_action,
        "errors": sorted(set(errors)),
        "ok": not errors,
    }, records


def new_claude_action_id(action: str) -> str:
    return safe_path_id(f"{utc_now_compact()}-{action}-{uuid.uuid4().hex[:8]}")


def claude_action_snapshot_path(session: dict, action_id: str) -> Path:
    return Path(str(session["session_dir"])) / CLAUDE_ACTION_SNAPSHOTS_DIRNAME / f"{safe_path_id(action_id)}.json"


def compact_claude_action_result(action_result: dict) -> dict:
    command_result = action_result.get("command_result", {}) if isinstance(action_result.get("command_result"), dict) else {}
    latest_update = action_result.get("latest_update", {}) if isinstance(action_result.get("latest_update"), dict) else {}
    event = command_result.get("event", {}) if isinstance(command_result.get("event"), dict) else {}
    ok_value = action_result.get("ok")
    if ok_value is None and command_result:
        ok_value = command_result.get("ok")
    compact = {
        "schema_version": action_result.get("schema_version", ""),
        "ok": bool(ok_value),
    }
    if command_result:
        compact["command"] = {
            "command_name": command_result.get("command_name", ""),
            "command_display_name": command_result.get("command_display_name", ""),
            "status": command_result.get("status", ""),
            "ok": bool(command_result.get("ok")),
            "event_id": event.get("event_id", ""),
        }
    if latest_update or "updates_applied_count" in action_result:
        compact["permission_update"] = {
            "updates_applied_count": action_result.get("updates_applied_count", 0),
            "latest_update": latest_update,
        }
    return compact


def compact_claude_bundle_for_snapshot(bundle: dict | None) -> dict:
    if not isinstance(bundle, dict) or not bundle:
        return {}
    return {
        "schema_version": bundle.get("schema_version", ""),
        "session_id": bundle.get("session_id", ""),
        "run_id": bundle.get("run_id", ""),
        "runtime_mode": bundle.get("runtime_mode", ""),
        "filters": bundle.get("filters", {}),
        "counts": bundle.get("counts", {}),
        "section_health": bundle.get("section_health", {}),
        "ok": bool(bundle.get("ok")),
    }


def write_claude_action_snapshot(
    session: dict,
    *,
    action_id: str,
    action: str,
    requested_action: str,
    mutation_applied: bool,
    action_result: dict,
    action_summary: dict,
    ok: bool,
    before_controller: dict,
    after_controller: dict | None = None,
    bundle: dict | None = None,
    snapshot_path: Path | None = None,
    stage: str = "completed",
) -> dict:
    path = snapshot_path or claude_action_snapshot_path(session, action_id)
    latest = action_summary.get("latest", {}) if isinstance(action_summary.get("latest"), dict) else {}
    payload = {
        "schema_version": "session_claude_action_snapshot_v1",
        "snapshot_stage": stage,
        "created_at_utc": utc_now_iso(),
        "action_id": action_id,
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "action": action,
        "requested_action": requested_action,
        "mutation_applied": bool(mutation_applied),
        "status": latest.get("status", "ok" if ok else "failed"),
        "ok": bool(ok),
        "path": path.as_posix(),
        "action_result": compact_claude_action_result(action_result),
        "action_summary": {
            "schema_version": action_summary.get("schema_version", ""),
            "path": action_summary.get("path", ""),
            "actions_count": action_summary.get("actions_count", 0),
            "mutation_count": action_summary.get("mutation_count", 0),
            "snapshots_count": action_summary.get("snapshots_count", 0),
            "ok_count": action_summary.get("ok_count", 0),
            "failed_count": action_summary.get("failed_count", 0),
            "by_action": action_summary.get("by_action", {}),
            "latest": latest,
        },
        "before": before_controller if isinstance(before_controller, dict) else {},
        "after": after_controller if isinstance(after_controller, dict) else {},
        "bundle": compact_claude_bundle_for_snapshot(bundle),
    }
    write_json(path, payload)
    session["claude_action_snapshots_dir"] = path.parent.as_posix()
    session["claude_action_snapshot_summary"] = {
        "schema_version": "session_claude_action_snapshot_summary_v1",
        "dir": path.parent.as_posix(),
        "snapshots_count": action_summary.get("snapshots_count", 0),
        "latest": {
            "action_id": action_id,
            "action": action,
            "path": path.as_posix(),
            "snapshot_stage": stage,
            "ok": bool(ok),
        },
    }
    save_session(session)
    return payload


def session_claude_action_snapshot(session_id: str, *, action_id: str = "", snapshot_path: str = "") -> dict:
    session = require_session(session_id)
    history = read_claude_action_history(session)
    records = history.get("records", []) if isinstance(history.get("records"), list) else []
    requested_action_id = str(action_id or "").strip()
    requested_snapshot_path = str(snapshot_path or "").strip()
    record: dict = {}

    if requested_action_id:
        record = next(
            (item for item in records if isinstance(item, dict) and str(item.get("action_id") or "") == requested_action_id),
            {},
        )
    elif requested_snapshot_path:
        requested_path = Path(requested_snapshot_path)
        for item in records:
            if not isinstance(item, dict):
                continue
            item_path_value = str(item.get("snapshot_path") or "")
            if item_path_value == requested_snapshot_path:
                record = item
                break
            try:
                if item_path_value and Path(item_path_value).resolve() == requested_path.resolve():
                    record = item
                    break
            except OSError:
                continue
    else:
        latest = history.get("latest", {})
        record = latest if isinstance(latest, dict) else {}

    if not record:
        raise FileNotFoundError("snapshot action introuvable")

    path_value = str(record.get("snapshot_path") or "")
    if not path_value:
        raise FileNotFoundError("snapshot introuvable")
    path = Path(path_value)
    try:
        path.resolve().relative_to(Path(str(session["session_dir"])).resolve())
    except ValueError:
        raise ValueError("snapshot hors session") from None
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"snapshot introuvable: {path.as_posix()}")

    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"snapshot JSON invalide: {exc}") from exc
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot invalide")

    validation_errors: list[str] = []
    if snapshot.get("schema_version") != "session_claude_action_snapshot_v1":
        validation_errors.append("snapshot_schema_invalid")
    if snapshot.get("action_id") != record.get("action_id"):
        validation_errors.append("snapshot_action_id_mismatch")
    if snapshot.get("session_id") != session.get("session_id"):
        validation_errors.append("snapshot_session_mismatch")
    if snapshot.get("run_id") != session.get("run_id"):
        validation_errors.append("snapshot_run_mismatch")
    if snapshot.get("action") != record.get("action"):
        validation_errors.append("snapshot_action_mismatch")
    if snapshot.get("requested_action") != record.get("requested_action"):
        validation_errors.append("snapshot_requested_action_mismatch")

    return {
        "schema_version": "session_claude_action_snapshot_read_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "action_id": record.get("action_id", ""),
        "action": record.get("action", ""),
        "requested_action": record.get("requested_action", ""),
        "path": path.as_posix(),
        "record": record,
        "snapshot": snapshot,
        "history": {
            "path": history.get("path", ""),
            "actions_count": history.get("actions_count", 0),
            "snapshots_count": history.get("snapshots_count", 0),
        },
        "validation": {
            "schema_version": "session_claude_action_snapshot_read_validation_v1",
            "errors": validation_errors,
            "ok": not validation_errors,
        },
        "ok": not validation_errors,
    }


def load_session_permission_state(session: dict, result: dict | None = None) -> tuple[dict, Path | None]:
    path_value = str(session.get("permission_state_path") or "")
    path = Path(path_value) if path_value else None
    state = load_permission_state(path) if path else {}
    if not state and isinstance(result, dict) and isinstance(result.get("permission_state"), dict):
        state = dict(result["permission_state"])
    return state, path


def session_permissions(session_id: str) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    state, path = load_session_permission_state(session, result)
    if not state:
        return {
            "schema_version": "session_claude_permissions_v1",
            "session_id": session["session_id"],
            "run_id": session.get("run_id", ""),
            "runtime_mode": session.get("runtime_mode", ""),
            "available": False,
            "permission_state_path": "",
            "state": {},
            "summary": {},
            "decisions": [],
            "permission_summary": {},
            "validation": {
                "schema_version": "claude_permission_state_validation_v0",
                "errors": ["permission_state_missing"],
                "ok": False,
            },
            "update_route": "/session/permissions",
            "ok": False,
        }

    validation_errors = validate_permission_state(state)
    decisions = result.get("permission_decisions", []) if isinstance(result.get("permission_decisions"), list) else []
    permission_summary = result.get("permission_summary", {}) if isinstance(result.get("permission_summary"), dict) else {}
    summary = (
        summarize_permission_state_for_session(state, path, result, session)
        if path is not None
        else summarize_permission_state(state)
    )
    return {
        "schema_version": "session_claude_permissions_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": True,
        "permission_state_path": path.as_posix() if path is not None else "",
        "state": state,
        "summary": summary,
        "decisions_count": len(decisions),
        "decisions": decisions,
        "permission_summary": permission_summary,
        "validation": {
            "schema_version": "claude_permission_state_validation_v0",
            "errors": validation_errors,
            "ok": not validation_errors,
        },
        "update_route": "/session/permissions",
        "ok": not validation_errors,
    }


def update_session_permissions(body: dict) -> dict:
    session = require_session(str(body.get("session_id") or ""))
    updates_value = body.get("updates")
    if updates_value is None and "update" in body:
        updates_value = [body.get("update")]
    if not isinstance(updates_value, list) or not updates_value:
        raise ValueError("permission update requis")

    updates = []
    for update in updates_value:
        if not isinstance(update, dict):
            raise ValueError("permission update invalide")
        updates.append(update)

    result_path = Path(str(session.get("result_path") or ""))
    result = read_json_dict(result_path)
    state, permission_state_path = load_session_permission_state(session, result)
    if permission_state_path is None or not state:
        raise ValueError("permission_state non disponible pour cette session")

    next_state = state
    for update in updates:
        next_state = apply_permission_update(next_state, update)

    next_state["session_id"] = str(session["session_id"])
    next_state["run_id"] = str(session.get("run_id") or "")
    next_state["path"] = permission_state_path.as_posix()
    permission_decisions = (
        result.get("permission_decisions", [])
        if isinstance(result.get("permission_decisions"), list)
        else []
    )
    if permission_decisions:
        next_state["replay"] = replay_permission_decisions(
            next_state,
            permission_decisions,
            allowed_tools=[
                str(tool)
                for tool in next_state.get("allowed_tools", [])
                if isinstance(tool, str) and tool
            ],
        )

    next_state = write_permission_state(permission_state_path, next_state)
    summary = summarize_permission_state_for_session(next_state, permission_state_path, result, session)
    result["permission_state"] = next_state
    result["permission_state_summary"] = summary
    result["permission_replay_summary"] = next_state.get("replay", {})
    session["permission_state_summary"] = summary
    if result_path:
        write_json(result_path, result)
    save_session(session)

    validation_errors = validate_permission_state(next_state)
    return {
        "schema_version": "session_claude_permission_update_v1",
        "session": session,
        "updates_applied_count": len(updates),
        "latest_update": next_state.get("updates", [])[-1] if next_state.get("updates") else {},
        "permission_state": next_state,
        "summary": summary,
        "validation": {
            "schema_version": "claude_permission_state_validation_v0",
            "errors": validation_errors,
            "ok": not validation_errors,
        },
        "permissions": session_permissions(str(session["session_id"])),
        "ok": not validation_errors,
    }


def hook_invocations_from_result(result: dict) -> list[dict[str, object]]:
    invocations = result.get("hook_invocations", []) if isinstance(result, dict) else []
    if not isinstance(invocations, list):
        return []
    return [dict(item) for item in invocations if isinstance(item, dict)]


def validate_hook_telemetry(
    invocations: list[dict[str, object]],
    summary: dict[str, object] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    sequence_by_agent: dict[str, int] = {}
    for index, invocation in enumerate(invocations, start=1):
        for field in ("schema_version", "hook_event", "sequence", "agent_type", "status"):
            if not invocation.get(field):
                errors.append(f"hook_missing_{field}:{index}")
        if invocation.get("schema_version") != "claude_hook_invocation_v0":
            errors.append(f"hook_schema_invalid:{index}")
        hook_event = str(invocation.get("hook_event") or "")
        if hook_event not in CLAUDE_HOOK_EVENTS:
            errors.append(f"hook_event_invalid:{index}")
        agent_type = str(invocation.get("agent_type") or "unknown")
        try:
            sequence = int(invocation.get("sequence") or 0)
        except (TypeError, ValueError):
            sequence = 0
        if sequence <= 0:
            errors.append(f"hook_sequence_invalid:{index}")
        previous = sequence_by_agent.get(agent_type, 0)
        if sequence and sequence != previous + 1:
            errors.append(f"hook_sequence_gap:{agent_type}:{sequence}")
        if sequence:
            sequence_by_agent[agent_type] = sequence

    if isinstance(summary, dict) and summary:
        expected_count = int(summary.get("invocations_count", 0) or 0)
        if expected_count != len(invocations):
            errors.append("hook_summary_count_mismatch")
        expected_blocking = int(summary.get("blocking_count", 0) or 0)
        actual_blocking = sum(1 for invocation in invocations if invocation.get("blocking") is True)
        if expected_blocking != actual_blocking:
            errors.append("hook_summary_blocking_count_mismatch")

    return {
        "schema_version": "claude_hook_telemetry_validation_v0",
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_hook_summary_from_result(result: dict) -> dict:
    invocations = hook_invocations_from_result(result)
    summary = result.get("hook_summary", {}) if isinstance(result.get("hook_summary"), dict) else {}
    if not summary and invocations:
        summary = summarize_hook_invocations(
            invocations,
            agent_type=str(result.get("agent_type") or "claude-runtime"),
        )
    return {
        "schema_version": "session_hooks_summary_v1",
        "available": bool(invocations),
        "invocations_count": len(invocations),
        "summary": summary,
        "summary_by_agent": result.get("hook_summary_by_agent", {})
        if isinstance(result.get("hook_summary_by_agent"), dict)
        else {},
        "validation": validate_hook_telemetry(invocations, summary),
    }


def session_hooks(session_id: str, *, agent: str = "", hook_event: str = "") -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    all_invocations = hook_invocations_from_result(result)
    all_summary = result.get("hook_summary", {}) if isinstance(result.get("hook_summary"), dict) else {}
    if not all_summary and all_invocations:
        all_summary = summarize_hook_invocations(
            all_invocations,
            agent_type=str(result.get("agent_type") or "claude-runtime"),
        )

    agent_filter = str(agent or "").strip()
    hook_event_filter = str(hook_event or "").strip()
    invocations = [
        invocation
        for invocation in all_invocations
        if (not agent_filter or invocation.get("agent_type") == agent_filter)
        and (not hook_event_filter or invocation.get("hook_event") == hook_event_filter)
    ]
    summary_agent_type = agent_filter or str(result.get("agent_type") or "claude-runtime")
    filtered_summary = summarize_hook_invocations(invocations, agent_type=summary_agent_type)
    summaries_by_agent = (
        result.get("hook_summary_by_agent", {})
        if isinstance(result.get("hook_summary_by_agent"), dict)
        else {}
    )
    if agent_filter and isinstance(summaries_by_agent, dict):
        summaries_by_agent = {
            name: summary
            for name, summary in summaries_by_agent.items()
            if name == agent_filter
        }
    validation = validate_hook_telemetry(all_invocations, all_summary)
    return {
        "schema_version": "session_hooks_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(all_invocations),
        "filters": {
            "agent": agent_filter,
            "hook_event": hook_event_filter,
        },
        "agents": sorted({str(invocation.get("agent_type") or "") for invocation in all_invocations if invocation.get("agent_type")}),
        "hook_events": sorted({str(invocation.get("hook_event") or "") for invocation in all_invocations if invocation.get("hook_event")}),
        "all_invocations_count": len(all_invocations),
        "invocations_count": len(invocations),
        "summary": filtered_summary,
        "all_summary": all_summary,
        "summary_by_agent": summaries_by_agent,
        "invocations": invocations,
        "validation": validation,
        "ok": bool(all_invocations) and bool(validation.get("ok")),
    }


def handoff_string_items(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def handoffs_created_from_result(result: dict) -> list[dict[str, object]]:
    raw = result.get("handoffs", []) if isinstance(result, dict) else []
    return [dict(handoff) for handoff in raw if isinstance(handoff, dict)] if isinstance(raw, list) else []


def handoffs_received_by_agent_from_result(result: dict) -> dict[str, list[dict[str, object]]]:
    if not isinstance(result, dict):
        return {}
    raw = result.get("handoffs_by_agent", {})
    if isinstance(raw, dict) and raw:
        return {
            str(agent): [dict(handoff) for handoff in handoffs if isinstance(handoff, dict)]
            for agent, handoffs in raw.items()
            if str(agent) and isinstance(handoffs, list)
        }
    received = result.get("handoffs_received", [])
    agent_type = str(result.get("agent_type") or "")
    if agent_type and isinstance(received, list):
        return {
            agent_type: [dict(handoff) for handoff in received if isinstance(handoff, dict)]
        }
    return {}


def handoff_record(
    handoff: dict[str, object],
    *,
    direction: str,
    index: int,
    receiver_agent: str = "",
) -> dict[str, object]:
    from_agent = str(handoff.get("from_agent") or "")
    to_agent = str(handoff.get("to_agent") or "")
    artifacts = handoff.get("artifacts", []) if isinstance(handoff.get("artifacts"), list) else []
    blocking = handoff_string_items(handoff.get("blocking_failures"))
    warnings = handoff_string_items(handoff.get("warnings"))
    return {
        "schema_version": "session_handoff_record_v1",
        "handoff_id": f"{direction}:{index}:{from_agent}>{to_agent}",
        "direction": direction,
        "receiver_agent": receiver_agent,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "status": str(handoff.get("status") or "UNKNOWN"),
        "artifact_dir": str(handoff.get("artifact_dir") or ""),
        "artifacts_count": int(handoff.get("artifacts_count", len(artifacts)) or 0),
        "artifacts": [dict(artifact) for artifact in artifacts if isinstance(artifact, dict)],
        "blocking_failures": blocking,
        "warnings": warnings,
        "task_summary": dict(handoff.get("task_summary", {})) if isinstance(handoff.get("task_summary"), dict) else {},
        "permission_summary": dict(handoff.get("permission_summary", {})) if isinstance(handoff.get("permission_summary"), dict) else {},
        "context_summary": dict(handoff.get("context_summary", {})) if isinstance(handoff.get("context_summary"), dict) else {},
        "ok": not blocking,
    }


def all_handoff_records_from_result(result: dict) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index, handoff in enumerate(handoffs_created_from_result(result), start=1):
        records.append(handoff_record(handoff, direction="created", index=index))
    received_by_agent = handoffs_received_by_agent_from_result(result)
    received_index = 0
    for receiver_agent, handoffs in received_by_agent.items():
        for handoff in handoffs:
            received_index += 1
            records.append(
                handoff_record(
                    handoff,
                    direction="received",
                    index=received_index,
                    receiver_agent=receiver_agent,
                )
            )
    return records


def summarize_session_handoff_records(records: list[dict[str, object]]) -> dict[str, object]:
    agents = sorted(
        {
            str(value)
            for record in records
            for value in (record.get("from_agent"), record.get("to_agent"), record.get("receiver_agent"))
            if str(value)
        }
    )
    statuses = sorted({str(record.get("status") or "") for record in records if record.get("status")})
    return {
        "schema_version": "session_handoffs_summary_v1",
        "handoffs_count": len(records),
        "created_handoffs_count": sum(1 for record in records if record.get("direction") == "created"),
        "received_handoffs_count": sum(1 for record in records if record.get("direction") == "received"),
        "agents": agents,
        "agents_count": len(agents),
        "from_agents": sorted({str(record.get("from_agent") or "") for record in records if record.get("from_agent")}),
        "to_agents": sorted({str(record.get("to_agent") or "") for record in records if record.get("to_agent")}),
        "receiver_agents": sorted(
            {str(record.get("receiver_agent") or "") for record in records if record.get("receiver_agent")}
        ),
        "statuses": statuses,
        "artifacts_count": sum(int(record.get("artifacts_count", 0) or 0) for record in records),
        "blocking_count": sum(len(record.get("blocking_failures", [])) for record in records if isinstance(record.get("blocking_failures"), list)),
        "warning_count": sum(len(record.get("warnings", [])) for record in records if isinstance(record.get("warnings"), list)),
        "ok": all(bool(record.get("ok", True)) for record in records),
    }


def validate_handoff_payload(handoff: dict[str, object], *, index: str) -> list[str]:
    errors: list[str] = []
    if handoff.get("schema_version") != "claude_agent_handoff_v0":
        errors.append(f"handoff_schema_invalid:{index}")
    for field in ("from_agent", "to_agent", "status"):
        if not handoff.get(field):
            errors.append(f"handoff_missing_{field}:{index}")
    artifacts = handoff.get("artifacts", [])
    if not isinstance(artifacts, list):
        errors.append(f"handoff_artifacts_not_list:{index}")
        artifacts = []
    if int(handoff.get("artifacts_count", 0) or 0) != len(artifacts):
        errors.append(f"handoff_artifacts_count_mismatch:{index}")
    for artifact_index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            errors.append(f"handoff_artifact_not_object:{index}:{artifact_index}")
            continue
        if not artifact.get("artifact"):
            errors.append(f"handoff_artifact_missing_name:{index}:{artifact_index}")
        if not artifact.get("path"):
            errors.append(f"handoff_artifact_missing_path:{index}:{artifact_index}")
    return errors


def validate_session_handoffs(result: dict) -> dict[str, object]:
    created = handoffs_created_from_result(result)
    received_by_agent = handoffs_received_by_agent_from_result(result)
    errors: list[str] = []
    for index, handoff in enumerate(created, start=1):
        errors.extend(validate_handoff_payload(handoff, index=f"created:{index}"))
    received_count = 0
    for agent, handoffs in received_by_agent.items():
        for index, handoff in enumerate(handoffs, start=1):
            received_count += 1
            errors.extend(validate_handoff_payload(handoff, index=f"received:{agent}:{index}"))
            to_agent = str(handoff.get("to_agent") or "")
            if to_agent and to_agent != agent:
                errors.append(f"handoff_receiver_mismatch:{agent}:{index}")

    summary = result.get("handoff_summary", {}) if isinstance(result.get("handoff_summary"), dict) else {}
    if summary:
        expected_count = len(created) if created else received_count
        if int(summary.get("handoffs_count", 0) or 0) != expected_count:
            errors.append("handoff_summary_count_mismatch")
        expected_blocking = sum(
            len(handoff_string_items(handoff.get("blocking_failures")))
            for handoff in (created if created else [handoff for handoffs in received_by_agent.values() for handoff in handoffs])
        )
        if int(summary.get("blocking_count", 0) or 0) != expected_blocking:
            errors.append("handoff_summary_blocking_count_mismatch")

    summary_by_agent = result.get("handoff_summary_by_agent", {}) if isinstance(result.get("handoff_summary_by_agent"), dict) else {}
    for agent, handoffs in received_by_agent.items():
        agent_summary = summary_by_agent.get(agent, {}) if isinstance(summary_by_agent, dict) else {}
        if isinstance(agent_summary, dict) and agent_summary:
            if int(agent_summary.get("handoffs_count", 0) or 0) != len(handoffs):
                errors.append(f"handoff_agent_summary_count_mismatch:{agent}")

    return {
        "schema_version": "session_handoffs_validation_v1",
        "created_handoffs_count": len(created),
        "received_handoffs_count": received_count,
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_handoff_summary_from_result(result: dict) -> dict:
    records = all_handoff_records_from_result(result)
    validation = validate_session_handoffs(result)
    return {
        "schema_version": "session_handoffs_summary_wrapper_v1",
        "available": bool(records),
        "handoffs_count": len(records),
        "summary": summarize_session_handoff_records(records),
        "runtime_summary": result.get("handoff_summary", {}) if isinstance(result.get("handoff_summary"), dict) else {},
        "summary_by_agent": result.get("handoff_summary_by_agent", {})
        if isinstance(result.get("handoff_summary_by_agent"), dict)
        else {},
        "validation": validation,
        "ok": (not records) or bool(validation.get("ok")),
    }


def session_handoffs(
    session_id: str,
    *,
    agent: str = "",
    from_agent: str = "",
    to_agent: str = "",
    direction: str = "",
    status: str = "",
) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    agent_filter = str(agent or "").strip()
    from_filter = str(from_agent or "").strip()
    to_filter = str(to_agent or "").strip()
    direction_filter = str(direction or "").strip()
    status_filter = str(status or "").strip()
    if direction_filter not in {"", "created", "received"}:
        direction_filter = ""

    all_records = all_handoff_records_from_result(result)

    def record_matches_agent(record: dict[str, object]) -> bool:
        if not agent_filter:
            return True
        if record.get("direction") == "created":
            return record.get("from_agent") == agent_filter
        return record.get("receiver_agent") == agent_filter or record.get("to_agent") == agent_filter

    records = [
        record
        for record in all_records
        if record_matches_agent(record)
        and (not from_filter or record.get("from_agent") == from_filter)
        and (not to_filter or record.get("to_agent") == to_filter)
        and (not direction_filter or record.get("direction") == direction_filter)
        and (not status_filter or record.get("status") == status_filter)
    ]
    validation = validate_session_handoffs(result)
    received_by_agent: dict[str, list[dict[str, object]]] = {}
    for record in records:
        if record.get("direction") != "received":
            continue
        receiver = str(record.get("receiver_agent") or record.get("to_agent") or "")
        if receiver:
            received_by_agent.setdefault(receiver, []).append(record)
    summary_by_agent = (
        result.get("handoff_summary_by_agent", {})
        if isinstance(result.get("handoff_summary_by_agent"), dict)
        else {}
    )
    if agent_filter and isinstance(summary_by_agent, dict):
        summary_by_agent = {
            name: summary
            for name, summary in summary_by_agent.items()
            if name == agent_filter
        }
    return {
        "schema_version": "session_handoffs_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(all_records),
        "filters": {
            "agent": agent_filter,
            "from_agent": from_filter,
            "to_agent": to_filter,
            "direction": direction_filter,
            "status": status_filter,
        },
        "agents": summarize_session_handoff_records(all_records)["agents"],
        "directions": sorted({str(record.get("direction") or "") for record in all_records if record.get("direction")}),
        "statuses": sorted({str(record.get("status") or "") for record in all_records if record.get("status")}),
        "all_handoffs_count": len(all_records),
        "handoffs_count": len(records),
        "all_created_handoffs_count": sum(1 for record in all_records if record.get("direction") == "created"),
        "created_handoffs_count": sum(1 for record in records if record.get("direction") == "created"),
        "all_received_handoffs_count": sum(1 for record in all_records if record.get("direction") == "received"),
        "received_handoffs_count": sum(1 for record in records if record.get("direction") == "received"),
        "summary": summarize_session_handoff_records(records),
        "all_summary": summarize_session_handoff_records(all_records),
        "runtime_summary": result.get("handoff_summary", {}) if isinstance(result.get("handoff_summary"), dict) else {},
        "summary_by_agent": summary_by_agent,
        "handoffs": records,
        "created_handoffs": [record for record in records if record.get("direction") == "created"],
        "received_handoffs": [record for record in records if record.get("direction") == "received"],
        "received_handoffs_by_agent": received_by_agent,
        "validation": validation,
        "ok": (not all_records) or bool(validation.get("ok")),
    }


def task_states_from_result(result: dict) -> dict[str, dict[str, object]]:
    if not isinstance(result, dict):
        return {}
    by_agent = result.get("task_state_by_agent", {})
    if isinstance(by_agent, dict) and by_agent:
        return {
            str(agent): dict(state)
            for agent, state in by_agent.items()
            if str(agent) and isinstance(state, dict)
        }
    task_state = result.get("task_state", {})
    if isinstance(task_state, dict) and task_state:
        agent_type = str(task_state.get("agent_type") or result.get("agent_type") or "")
        if agent_type:
            return {agent_type: dict(task_state)}
    return {}


def task_items_from_states(task_states: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for agent, state in task_states.items():
        tasks = state.get("tasks", []) if isinstance(state, dict) else []
        if not isinstance(tasks, list):
            continue
        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                continue
            item = dict(task)
            item["agent_type"] = str(item.get("agent_type") or agent)
            item["sequence"] = int(item.get("order") or index)
            items.append(item)
    return sorted(items, key=lambda item: (str(item.get("agent_type") or ""), int(item.get("sequence") or 0)))


def summarize_task_states_for_session(task_states: dict[str, dict[str, object]], result: dict) -> dict[str, object]:
    if not task_states:
        return {}
    if len(task_states) == 1:
        state = dict(next(iter(task_states.values())))
        return summarize_task_state(state)
    summary = result.get("task_summary", {}) if isinstance(result.get("task_summary"), dict) else {}
    if summary:
        return dict(summary)
    return summarize_pipeline_task_states({agent: dict(state) for agent, state in task_states.items()})


def validate_task_telemetry(
    task_states: dict[str, dict[str, object]],
    summary: dict[str, object] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    valid_statuses = {"pending", "in_progress", "completed", "blocked"}
    tasks = task_items_from_states(task_states)
    for index, task in enumerate(tasks, start=1):
        for field in ("id", "agent_type", "artifact", "title", "status"):
            if not task.get(field):
                errors.append(f"task_missing_{field}:{index}")
        if str(task.get("status") or "") not in valid_statuses:
            errors.append(f"task_status_invalid:{index}")

    status_counts = {
        "pending_count": sum(1 for task in tasks if task.get("status") == "pending"),
        "in_progress_count": sum(1 for task in tasks if task.get("status") == "in_progress"),
        "completed_count": sum(1 for task in tasks if task.get("status") == "completed"),
        "blocked_count": sum(1 for task in tasks if task.get("status") == "blocked"),
    }
    if isinstance(summary, dict) and summary:
        if int(summary.get("tasks_count", 0) or 0) != len(tasks):
            errors.append("task_summary_count_mismatch")
        for field_name, count in status_counts.items():
            if int(summary.get(field_name, 0) or 0) != count:
                errors.append(f"task_summary_{field_name}_mismatch")

    return {
        "schema_version": "claude_task_telemetry_validation_v0",
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_task_summary_from_result(result: dict) -> dict:
    task_states = task_states_from_result(result)
    tasks = task_items_from_states(task_states)
    summary = summarize_task_states_for_session(task_states, result)
    validation = validate_task_telemetry(task_states, summary)
    return {
        "schema_version": "session_tasks_summary_v1",
        "available": bool(tasks),
        "agents_count": len(task_states),
        "tasks_count": len(tasks),
        "summary": summary,
        "validation": validation,
        "ok": bool(tasks) and bool(validation.get("ok")),
    }


def session_tasks(session_id: str, *, agent: str = "", status: str = "") -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    task_states = task_states_from_result(result)
    all_tasks = task_items_from_states(task_states)
    summary = summarize_task_states_for_session(task_states, result)
    agent_filter = str(agent or "").strip()
    status_filter = str(status or "").strip()
    tasks = [
        task
        for task in all_tasks
        if (not agent_filter or task.get("agent_type") == agent_filter)
        and (not status_filter or task.get("status") == status_filter)
    ]
    filtered_states: dict[str, dict[str, object]] = {}
    for task in tasks:
        agent_type = str(task.get("agent_type") or "")
        if not agent_type:
            continue
        state = filtered_states.setdefault(
            agent_type,
            {
                "schema_version": "claude_agent_task_state_v0",
                "agent_type": agent_type,
                "tasks": [],
                "current_task_id": "",
            },
        )
        state["tasks"].append(task)
    if not filtered_states:
        filtered_summary = {}
    elif len(filtered_states) == 1:
        filtered_summary = summarize_task_state(dict(next(iter(filtered_states.values()))))
    else:
        filtered_summary = summarize_pipeline_task_states(
            {agent_name: summarize_task_state(dict(state)) for agent_name, state in filtered_states.items()}
        )
    validation = validate_task_telemetry(task_states, summary)
    return {
        "schema_version": "session_tasks_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(all_tasks),
        "filters": {
            "agent": agent_filter,
            "status": status_filter,
        },
        "agents": sorted(task_states),
        "statuses": sorted({str(task.get("status") or "") for task in all_tasks if task.get("status")}),
        "all_tasks_count": len(all_tasks),
        "tasks_count": len(tasks),
        "summary": filtered_summary,
        "all_summary": summary,
        "task_state_by_agent": {
            agent_name: dict(task_state)
            for agent_name, task_state in task_states.items()
        },
        "tasks": tasks,
        "validation": validation,
        "ok": bool(all_tasks) and bool(validation.get("ok")),
    }


def validate_artifact_lineage(
    lineage: dict[str, object],
    *,
    artifact_index: dict | None = None,
    task_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    if not isinstance(lineage, dict) or not lineage:
        return {
            "schema_version": "claude_artifact_lineage_validation_v1",
            "available": False,
            "errors": [],
            "ok": True,
        }

    errors: list[str] = []
    artifacts = lineage.get("artifacts", [])
    handoff_edges = lineage.get("handoff_edges", [])
    terminal_artifact_keys = lineage.get("terminal_artifact_keys", [])
    if not isinstance(artifacts, list):
        errors.append("lineage_artifacts_not_list")
        artifacts = []
    if not isinstance(handoff_edges, list):
        errors.append("lineage_handoff_edges_not_list")
        handoff_edges = []
    if not isinstance(terminal_artifact_keys, list):
        errors.append("lineage_terminal_keys_not_list")
        terminal_artifact_keys = []

    if lineage.get("schema_version") != "claude_pipeline_artifact_lineage_v1":
        errors.append("lineage_schema_invalid")
    if int(lineage.get("artifacts_count", 0) or 0) != len(artifacts):
        errors.append("lineage_artifacts_count_mismatch")
    if int(lineage.get("handoff_edges_count", 0) or 0) != len(handoff_edges):
        errors.append("lineage_handoff_edges_count_mismatch")
    if lineage.get("ok") is False:
        errors.append("lineage_reported_not_ok")

    indexed_records = (
        artifact_index.get("artifacts", [])
        if isinstance(artifact_index, dict) and isinstance(artifact_index.get("artifacts", []), list)
        else []
    )
    indexed_paths = {
        str(record.get("path") or "")
        for record in indexed_records
        if isinstance(record, dict) and record.get("path")
    }
    indexed_keys = {
        f"{record.get('step', '')}.{record.get('artifact', '')}"
        for record in indexed_records
        if isinstance(record, dict) and record.get("step") and record.get("artifact")
    }
    artifact_keys: set[str] = set()
    consumed_keys: set[str] = set()
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            errors.append(f"lineage_artifact_not_object:{index}")
            continue
        for field in ("artifact_key", "agent_type", "step", "artifact", "path"):
            if not artifact.get(field):
                errors.append(f"lineage_artifact_missing_{field}:{index}")
        artifact_key = str(artifact.get("artifact_key") or "")
        if artifact_key in artifact_keys:
            errors.append(f"lineage_artifact_duplicate:{artifact_key}")
        if artifact_key:
            artifact_keys.add(artifact_key)
        path = str(artifact.get("path") or "")
        if indexed_paths and path and path not in indexed_paths:
            errors.append(f"lineage_artifact_not_indexed:{artifact_key}")
        if indexed_keys and artifact_key and artifact_key not in indexed_keys:
            errors.append(f"lineage_artifact_key_not_indexed:{artifact_key}")
        if not artifact.get("exists"):
            errors.append(f"lineage_artifact_missing_file:{artifact_key}")
        consumed_by = artifact.get("consumed_by", [])
        if consumed_by and not isinstance(consumed_by, list):
            errors.append(f"lineage_artifact_consumers_invalid:{artifact_key}")
        if artifact.get("terminal") and consumed_by:
            errors.append(f"lineage_terminal_has_consumers:{artifact_key}")

    for index, edge in enumerate(handoff_edges, start=1):
        if not isinstance(edge, dict):
            errors.append(f"lineage_handoff_not_object:{index}")
            continue
        for field in ("from_agent", "to_agent", "status"):
            if not edge.get(field):
                errors.append(f"lineage_handoff_missing_{field}:{index}")
        edge_artifacts = edge.get("artifacts", [])
        if not isinstance(edge_artifacts, list):
            errors.append(f"lineage_handoff_artifacts_not_list:{index}")
            edge_artifacts = []
        if int(edge.get("artifacts_count", 0) or 0) != len(edge_artifacts):
            errors.append(f"lineage_handoff_artifacts_count_mismatch:{index}")
        for artifact in edge_artifacts:
            if not isinstance(artifact, dict):
                continue
            artifact_key = str(artifact.get("artifact_key") or "")
            if artifact_key:
                consumed_keys.add(artifact_key)
                if artifact_key not in artifact_keys:
                    errors.append(f"lineage_handoff_unknown_artifact:{artifact_key}")

    terminal_keys = {str(key) for key in terminal_artifact_keys if str(key)}
    expected_terminal_keys = {
        str(artifact.get("artifact_key") or "")
        for artifact in artifacts
        if isinstance(artifact, dict) and artifact.get("terminal")
    }
    expected_terminal_keys.discard("")
    if terminal_keys != expected_terminal_keys:
        errors.append("lineage_terminal_keys_mismatch")
    if consumed_keys & terminal_keys:
        errors.append("lineage_consumed_terminal_key")

    if isinstance(task_summary, dict) and task_summary:
        completed_count = int(task_summary.get("completed_count", 0) or 0)
        if completed_count and completed_count != len(artifacts):
            errors.append("lineage_task_completed_count_mismatch")

    return {
        "schema_version": "claude_artifact_lineage_validation_v1",
        "available": True,
        "artifacts_count": len(artifacts),
        "handoff_edges_count": len(handoff_edges),
        "terminal_artifacts_count": len(terminal_keys),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_artifact_lineage(session_id: str, *, agent: str = "", terminal_only: bool = False) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    lineage = result.get("artifact_lineage", {}) if isinstance(result.get("artifact_lineage"), dict) else {}
    artifact_index = session_artifacts(session_id) if session.get("artifact_index_path") else {}
    task_summary = summarize_task_states_for_session(task_states_from_result(result), result)
    validation = validate_artifact_lineage(lineage, artifact_index=artifact_index, task_summary=task_summary)
    all_artifacts = lineage.get("artifacts", []) if isinstance(lineage.get("artifacts"), list) else []
    all_handoff_edges = lineage.get("handoff_edges", []) if isinstance(lineage.get("handoff_edges"), list) else []
    agent_filter = str(agent or "").strip()
    artifacts = [
        artifact
        for artifact in all_artifacts
        if isinstance(artifact, dict)
        and (not agent_filter or artifact.get("agent_type") == agent_filter)
        and (not terminal_only or bool(artifact.get("terminal")))
    ]
    handoff_edges = [
        edge
        for edge in all_handoff_edges
        if isinstance(edge, dict)
        and (
            not agent_filter
            or edge.get("from_agent") == agent_filter
            or edge.get("to_agent") == agent_filter
        )
    ]
    terminal_keys = [
        str(artifact.get("artifact_key") or "")
        for artifact in artifacts
        if isinstance(artifact, dict) and artifact.get("terminal") and artifact.get("artifact_key")
    ]
    all_terminal_keys = [
        str(artifact.get("artifact_key") or "")
        for artifact in all_artifacts
        if isinstance(artifact, dict) and artifact.get("terminal") and artifact.get("artifact_key")
    ]
    agents = sorted(
        {
            str(artifact.get("agent_type") or "")
            for artifact in all_artifacts
            if isinstance(artifact, dict) and artifact.get("agent_type")
        }
    )
    all_summary = {
        "schema_version": "session_artifact_lineage_summary_v1",
        "available": bool(lineage),
        "agents_count": len(agents),
        "artifacts_count": len(all_artifacts),
        "handoff_edges_count": len(all_handoff_edges),
        "terminal_artifacts_count": len(all_terminal_keys),
        "ok": bool(validation.get("ok")),
    }
    summary = {
        "schema_version": "session_artifact_lineage_summary_v1",
        "available": bool(lineage),
        "agents_count": len({str(item.get("agent_type") or "") for item in artifacts if item.get("agent_type")}),
        "artifacts_count": len(artifacts),
        "handoff_edges_count": len(handoff_edges),
        "terminal_artifacts_count": len(terminal_keys),
        "ok": bool(validation.get("ok")),
    }
    return {
        "schema_version": "session_artifact_lineage_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(lineage),
        "filters": {
            "agent": agent_filter,
            "terminal_only": bool(terminal_only),
        },
        "agents": agents,
        "all_artifacts_count": len(all_artifacts),
        "artifacts_count": len(artifacts),
        "all_handoff_edges_count": len(all_handoff_edges),
        "handoff_edges_count": len(handoff_edges),
        "terminal_artifact_keys": terminal_keys,
        "all_terminal_artifact_keys": all_terminal_keys,
        "summary": summary,
        "all_summary": all_summary,
        "artifacts": artifacts,
        "handoff_edges": handoff_edges,
        "validation": validation,
        "ok": (not lineage) or bool(validation.get("ok")),
    }


def runtime_state_by_agent(result: dict, by_agent_key: str, state_key: str) -> dict[str, dict[str, object]]:
    if not isinstance(result, dict):
        return {}
    by_agent = result.get(by_agent_key, {})
    if isinstance(by_agent, dict) and by_agent:
        return {
            str(agent): dict(state)
            for agent, state in by_agent.items()
            if str(agent) and isinstance(state, dict)
        }
    state = result.get(state_key, {})
    if isinstance(state, dict) and state:
        agent_type = str(state.get("agent_type") or result.get("agent_type") or "")
        if agent_type:
            return {agent_type: dict(state)}
    return {}


def summarize_runtime_state_sections(
    conversation_states: dict[str, dict[str, object]],
    context_states: dict[str, dict[str, object]],
    token_budgets: dict[str, dict[str, object]],
    usage_accounting: dict[str, dict[str, object]],
) -> dict[str, object]:
    agents = sorted(set(conversation_states) | set(context_states) | set(token_budgets) | set(usage_accounting))
    estimated_tokens = sum(int(state.get("estimated_tokens", 0) or 0) for state in context_states.values())
    usage_tokens = 0
    input_tokens = 0
    output_tokens = 0
    total_cost_usd = 0.0
    for usage in usage_accounting.values():
        usage_payload = usage.get("usage", {}) if isinstance(usage.get("usage"), dict) else {}
        input_tokens += int(usage_payload.get("input_tokens", usage.get("input_tokens", 0)) or 0)
        output_tokens += int(usage_payload.get("output_tokens", usage.get("output_tokens", 0)) or 0)
        usage_tokens += int(usage_payload.get("total_tokens", usage.get("total_tokens", 0)) or 0)
        total_cost_usd += float(usage.get("cost_usd", usage.get("total_cost_usd", 0.0)) or 0.0)
    warnings_count = sum(len(state.get("warnings", [])) for state in token_budgets.values() if isinstance(state.get("warnings", []), list))
    return {
        "schema_version": "session_claude_runtime_state_summary_v1",
        "agents_count": len(agents),
        "agents": agents,
        "messages_count": sum(int(state.get("messages_count", 0) or 0) for state in conversation_states.values()),
        "tool_use_count": sum(int(state.get("tool_use_count", 0) or 0) for state in conversation_states.values()),
        "tool_result_count": sum(int(state.get("tool_result_count", 0) or 0) for state in conversation_states.values()),
        "estimated_tokens": estimated_tokens,
        "usage_total_tokens": usage_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_cost_usd": round(total_cost_usd, 8),
        "needs_compaction_count": sum(1 for state in context_states.values() if state.get("needs_compaction")),
        "token_budget_warnings_count": warnings_count,
        "ok": all(
            bool(state.get("ok", True))
            for states in (conversation_states, token_budgets, usage_accounting)
            for state in states.values()
        ),
    }


def validate_runtime_state(
    conversation_states: dict[str, dict[str, object]],
    context_states: dict[str, dict[str, object]],
    token_budgets: dict[str, dict[str, object]],
    usage_accounting: dict[str, dict[str, object]],
) -> dict[str, object]:
    errors: list[str] = []
    agents = sorted(set(conversation_states) | set(context_states) | set(token_budgets) | set(usage_accounting))
    for agent in agents:
        conversation = conversation_states.get(agent, {})
        context = context_states.get(agent, {})
        token_budget = token_budgets.get(agent, {})
        usage = usage_accounting.get(agent, {})
        if not conversation:
            errors.append(f"runtime_state_conversation_missing:{agent}")
        elif conversation.get("schema_version") != "claude_conversation_state_v0":
            errors.append(f"runtime_state_conversation_schema_invalid:{agent}")
        elif not conversation.get("ok", False):
            errors.append(f"runtime_state_conversation_not_ok:{agent}")
        if not context:
            errors.append(f"runtime_state_context_missing:{agent}")
        elif context.get("schema_version") != "claude_context_state_v0":
            errors.append(f"runtime_state_context_schema_invalid:{agent}")
        if conversation and context and int(conversation.get("messages_count", 0) or 0) != int(context.get("messages_count", 0) or 0):
            errors.append(f"runtime_state_messages_count_mismatch:{agent}")
        if not token_budget:
            errors.append(f"runtime_state_token_budget_missing:{agent}")
        elif token_budget.get("schema_version") != "claude_token_budget_v0":
            errors.append(f"runtime_state_token_budget_schema_invalid:{agent}")
        elif not token_budget.get("ok", False):
            errors.append(f"runtime_state_token_budget_not_ok:{agent}")
        if not usage:
            errors.append(f"runtime_state_usage_missing:{agent}")
        elif usage.get("schema_version") != "claude_usage_accounting_v0":
            errors.append(f"runtime_state_usage_schema_invalid:{agent}")
        elif not usage.get("ok", False):
            errors.append(f"runtime_state_usage_not_ok:{agent}")

    return {
        "schema_version": "session_claude_runtime_state_validation_v1",
        "available": bool(agents),
        "agents_count": len(agents),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_runtime_state(session_id: str, *, agent: str = "") -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    all_conversation_states = runtime_state_by_agent(result, "conversation_state_by_agent", "conversation_state")
    all_context_states = runtime_state_by_agent(result, "context_state_by_agent", "context_state")
    all_token_budgets = runtime_state_by_agent(result, "token_budget_by_agent", "token_budget")
    all_usage_accounting = runtime_state_by_agent(result, "usage_accounting_by_agent", "usage_accounting")
    agent_filter = str(agent or "").strip()

    def filtered(states: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
        if not agent_filter:
            return {name: dict(state) for name, state in states.items()}
        return {name: dict(state) for name, state in states.items() if name == agent_filter}

    conversation_states = filtered(all_conversation_states)
    context_states = filtered(all_context_states)
    token_budgets = filtered(all_token_budgets)
    usage_states = filtered(all_usage_accounting)
    validation = validate_runtime_state(all_conversation_states, all_context_states, all_token_budgets, all_usage_accounting)
    summary = summarize_runtime_state_sections(conversation_states, context_states, token_budgets, usage_states)
    all_summary = summarize_runtime_state_sections(all_conversation_states, all_context_states, all_token_budgets, all_usage_accounting)
    agents = sorted(set(all_conversation_states) | set(all_context_states) | set(all_token_budgets) | set(all_usage_accounting))
    return {
        "schema_version": "session_claude_runtime_state_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(agents),
        "filters": {"agent": agent_filter},
        "agents": agents,
        "agents_count": len(agents),
        "conversation_state": result.get("conversation_state", {}) if isinstance(result.get("conversation_state"), dict) else {},
        "context_state": result.get("context_state", {}) if isinstance(result.get("context_state"), dict) else {},
        "token_budget": result.get("token_budget", {}) if isinstance(result.get("token_budget"), dict) else {},
        "usage_accounting": result.get("usage_accounting", {}) if isinstance(result.get("usage_accounting"), dict) else {},
        "conversation_state_by_agent": conversation_states,
        "context_state_by_agent": context_states,
        "token_budget_by_agent": token_budgets,
        "usage_accounting_by_agent": usage_states,
        "summary": summary,
        "all_summary": all_summary,
        "validation": validation,
        "ok": (not agents) or bool(validation.get("ok")),
    }


def agent_definition_manifest_item(definition: object) -> dict[str, object]:
    agent_type = str(getattr(definition, "agent_type", "") or "")
    model_profile = getattr(definition, "model_profile", None)
    model_profile_payload = model_profile.as_dict() if hasattr(model_profile, "as_dict") else {}
    budgets = getattr(definition, "budgets", None)
    flags = getattr(definition, "flags", None)
    tool_registry_summary = getattr(definition, "tool_registry_summary", {})
    skill_context = getattr(definition, "skill_context", {})
    command_context = getattr(definition, "command_context", {})
    tools_allowed = list(getattr(definition, "tools", []) or [])
    skills_allowed = list(getattr(definition, "skills", []) or [])
    command_names = (
        list(command_context.get("command_names", []))
        if isinstance(command_context, dict) and isinstance(command_context.get("command_names", []), list)
        else []
    )
    model_invocable_command_names = (
        list(command_context.get("model_invocable_command_names", []))
        if isinstance(command_context, dict) and isinstance(command_context.get("model_invocable_command_names", []), list)
        else []
    )
    item = {
        "schema_version": "session_claude_agent_manifest_item_v1",
        "agent_type": agent_type,
        "config_path": str(getattr(definition, "config_path", "") or ""),
        "model": str(getattr(definition, "model", "") or ""),
        "model_profile": model_profile_payload,
        "inputs": list(getattr(definition, "inputs", []) or []),
        "outputs": list(getattr(definition, "outputs", []) or []),
        "tools_allowed": tools_allowed,
        "tools_count": len(tools_allowed),
        "tool_registry_summary": dict(tool_registry_summary) if isinstance(tool_registry_summary, dict) else {},
        "skills_allowed": skills_allowed,
        "skills_count": len(skills_allowed),
        "skill_context": dict(skill_context) if isinstance(skill_context, dict) else {},
        "command_names": command_names,
        "commands_count": len(command_names),
        "model_invocable_command_names": model_invocable_command_names,
        "model_invocable_commands_count": len(model_invocable_command_names),
        "command_context": dict(command_context) if isinstance(command_context, dict) else {},
        "budgets": {
            "max_iterations": int(getattr(budgets, "max_iterations", 0) or 0),
            "max_tokens": int(getattr(budgets, "max_tokens", 0) or 0),
            "max_total_tokens": int(getattr(budgets, "max_total_tokens", 0) or 0),
            "window_size": int(getattr(budgets, "window_size", 0) or 0),
            "max_wall_clock_seconds": getattr(budgets, "max_wall_clock_seconds", None),
        },
        "flags": {
            "thinking_enabled": bool(getattr(flags, "thinking_enabled", False)),
            "long_cache": bool(getattr(flags, "long_cache", False)),
            "verification_checklist": getattr(flags, "verification_checklist", None),
        },
        "quality_gates": dict(getattr(definition, "quality_gates", {}) or {}),
        "human_validation": dict(getattr(definition, "human_validation", {}) or {}),
    }
    item["ok"] = all(
        bool(section.get("ok", True))
        for section in (
            item["tool_registry_summary"],
            item["skill_context"],
            item["command_context"],
        )
        if isinstance(section, dict)
    ) and bool(agent_type) and bool(item["config_path"])
    return item


def summarize_agent_manifest_items(items: list[dict[str, object]]) -> dict[str, object]:
    models = sorted(
        {
            str((item.get("model_profile") if isinstance(item.get("model_profile"), dict) else {}).get("canonical_model") or item.get("model") or "")
            for item in items
            if item.get("model_profile") or item.get("model")
        }
    )
    tools = sorted({str(tool) for item in items for tool in item.get("tools_allowed", []) if str(tool)})
    skills = sorted({str(skill) for item in items for skill in item.get("skills_allowed", []) if str(skill)})
    commands = sorted({str(command) for item in items for command in item.get("command_names", []) if str(command)})
    return {
        "schema_version": "session_claude_agent_manifest_summary_v1",
        "agents_count": len(items),
        "tools_count": len(tools),
        "skills_count": len(skills),
        "commands_count": len(commands),
        "models": models,
        "tool_names": tools,
        "skill_names": skills,
        "command_names": commands,
        "human_validation_required_count": sum(
            1
            for item in items
            if isinstance(item.get("human_validation"), dict) and item["human_validation"].get("required")
        ),
        "ok": all(bool(item.get("ok")) for item in items),
    }


def validate_agent_manifest(items: list[dict[str, object]], result: dict | None = None) -> dict[str, object]:
    errors: list[str] = []
    agent_types: set[str] = set()
    for index, item in enumerate(items, start=1):
        if item.get("schema_version") != "session_claude_agent_manifest_item_v1":
            errors.append(f"agent_manifest_schema_invalid:{index}")
        agent_type = str(item.get("agent_type") or "")
        if not agent_type:
            errors.append(f"agent_manifest_missing_agent_type:{index}")
        if agent_type in agent_types:
            errors.append(f"agent_manifest_duplicate_agent:{agent_type}")
        if agent_type:
            agent_types.add(agent_type)
        config_path = str(item.get("config_path") or "")
        if not config_path:
            errors.append(f"agent_manifest_missing_config_path:{agent_type or index}")
        elif not (ROOT / config_path).exists():
            errors.append(f"agent_manifest_config_missing:{config_path}")
        model_profile = item.get("model_profile", {})
        if not isinstance(model_profile, dict) or model_profile.get("schema_version") != "claude_model_profile_v0":
            errors.append(f"agent_manifest_model_profile_invalid:{agent_type or index}")
        if int(item.get("tools_count", 0) or 0) != len(item.get("tools_allowed", []) if isinstance(item.get("tools_allowed"), list) else []):
            errors.append(f"agent_manifest_tools_count_mismatch:{agent_type or index}")
        if int(item.get("skills_count", 0) or 0) != len(item.get("skills_allowed", []) if isinstance(item.get("skills_allowed"), list) else []):
            errors.append(f"agent_manifest_skills_count_mismatch:{agent_type or index}")
        for section_name in ("tool_registry_summary", "skill_context", "command_context"):
            section = item.get(section_name, {})
            if isinstance(section, dict) and section and not section.get("ok", True):
                errors.append(f"agent_manifest_{section_name}_not_ok:{agent_type or index}")
        if not item.get("ok"):
            errors.append(f"agent_manifest_item_not_ok:{agent_type or index}")

    if isinstance(result, dict) and result:
        expected_agents = result.get("agents", [])
        if not isinstance(expected_agents, list):
            result_agent_type = str(result.get("agent_type") or "")
            expected_agents = [result_agent_type] if result_agent_type and result_agent_type != "claude-pipeline" else []
        expected_set = {str(agent) for agent in expected_agents if str(agent)}
        if expected_set and expected_set != agent_types:
            errors.append("agent_manifest_result_agents_mismatch")

    return {
        "schema_version": "session_claude_agent_manifest_validation_v1",
        "agents_count": len(items),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_agents(session_id: str, *, agent: str = "") -> dict:
    session = require_session(session_id)
    runtime_mode = str(session.get("runtime_mode") or "")
    agent_filter = str(agent or "").strip()
    if not is_claude_runtime_mode(runtime_mode):
        return {
            "schema_version": "session_claude_agent_manifest_v1",
            "session_id": session["session_id"],
            "run_id": session.get("run_id", ""),
            "runtime_mode": runtime_mode,
            "available": False,
            "filters": {"agent": agent_filter},
            "agents": [],
            "agent_types": [],
            "agents_count": 0,
            "all_agents_count": 0,
            "summary": summarize_agent_manifest_items([]),
            "all_summary": summarize_agent_manifest_items([]),
            "validation": validate_agent_manifest([]),
            "ok": False,
        }

    result = read_json_dict(Path(str(session.get("result_path") or "")))
    try:
        runner = load_claude_runner_for_session(session)
        definitions = [subrunner.definition for subrunner in runner.runners] if hasattr(runner, "runners") else [runner.definition]
        all_items = [agent_definition_manifest_item(definition) for definition in definitions]
        load_error = ""
    except Exception as exc:
        all_items = []
        load_error = f"{type(exc).__name__}: {exc}"

    filtered_items = [
        item for item in all_items if not agent_filter or item.get("agent_type") == agent_filter
    ]
    validation = validate_agent_manifest(all_items, result)
    if load_error:
        validation = {
            **validation,
            "errors": sorted({*validation.get("errors", []), f"agent_manifest_load_error:{load_error}"}),
            "ok": False,
        }
    return {
        "schema_version": "session_claude_agent_manifest_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": runtime_mode,
        "available": bool(all_items),
        "filters": {"agent": agent_filter},
        "agents": filtered_items,
        "agent_types": [str(item.get("agent_type") or "") for item in filtered_items if item.get("agent_type")],
        "all_agent_types": [str(item.get("agent_type") or "") for item in all_items if item.get("agent_type")],
        "agents_count": len(filtered_items),
        "all_agents_count": len(all_items),
        "models": summarize_agent_manifest_items(all_items)["models"],
        "summary": summarize_agent_manifest_items(filtered_items),
        "all_summary": summarize_agent_manifest_items(all_items),
        "validation": validation,
        "ok": bool(all_items) and bool(validation.get("ok")),
    }


def load_session_case_input(session: dict) -> dict[str, object]:
    path_value = str(session.get("case_input_path") or "")
    candidates: list[Path] = []
    if path_value:
        candidates.append(Path(path_value))
    dossier_id = str(session.get("dossier_id") or "")
    session_dir = Path(str(session.get("session_dir") or ""))
    if dossier_id and session_dir:
        candidates.append(session_dir / f"{safe_path_id(dossier_id)}.input.json")
    if session_dir.exists():
        candidates.extend(sorted(session_dir.glob("*.input.json")))
    for path in candidates:
        payload = read_json_dict(path)
        if payload:
            return payload
    return {}


def agent_prompt_item(runner: object, case: dict[str, object], source_fixture: str, received_handoffs: list[dict[str, object]]) -> dict[str, object]:
    definition = getattr(runner, "definition")
    context = runner.build_context(case, source_fixture, received_handoffs) if hasattr(runner, "build_context") else {}
    sections = definition.build_system_prompt(context) if hasattr(definition, "build_system_prompt") else []
    section_names = ["static", "dynamic", "contract"]
    rendered_sections = [
        {
            "schema_version": "session_claude_agent_prompt_section_v1",
            "name": section_names[index] if index < len(section_names) else f"section_{index + 1}",
            "text": str(section or ""),
            "chars": len(str(section or "")),
        }
        for index, section in enumerate(sections)
    ]
    return {
        "schema_version": "session_claude_agent_prompt_v1",
        "agent_type": str(getattr(definition, "agent_type", "") or ""),
        "config_path": str(getattr(definition, "config_path", "") or ""),
        "model": str(getattr(definition, "model", "") or ""),
        "context": context,
        "source_fixture": source_fixture,
        "handoffs_received_count": len(received_handoffs),
        "system_prompt_static": str(getattr(definition, "system_prompt_static", "") or ""),
        "system_prompt_dynamic_template": str(getattr(definition, "system_prompt_dynamic_template", "") or ""),
        "sections_count": len(rendered_sections),
        "rendered_sections": rendered_sections,
        "rendered_prompt": "\n\n".join(str(section or "") for section in sections),
        "rendered_chars": sum(len(str(section or "")) for section in sections),
        "tools_allowed": list(getattr(definition, "tools", []) or []),
        "skills_allowed": list(getattr(definition, "skills", []) or []),
        "command_names": (
            list(getattr(definition, "command_context", {}).get("command_names", []))
            if isinstance(getattr(definition, "command_context", {}), dict)
            else []
        ),
        "quality_gates": dict(getattr(definition, "quality_gates", {}) or {}),
        "human_validation": dict(getattr(definition, "human_validation", {}) or {}),
        "ok": bool(getattr(definition, "agent_type", "")) and len(rendered_sections) == 3,
    }


def summarize_agent_prompt_items(items: list[dict[str, object]]) -> dict[str, object]:
    agents = [str(item.get("agent_type") or "") for item in items if item.get("agent_type")]
    tools = sorted({str(tool) for item in items for tool in item.get("tools_allowed", []) if str(tool)})
    skills = sorted({str(skill) for item in items for skill in item.get("skills_allowed", []) if str(skill)})
    commands = sorted({str(command) for item in items for command in item.get("command_names", []) if str(command)})
    return {
        "schema_version": "session_claude_agent_prompts_summary_v1",
        "prompts_count": len(items),
        "agents": agents,
        "agents_count": len(agents),
        "sections_count": sum(int(item.get("sections_count", 0) or 0) for item in items),
        "rendered_chars": sum(int(item.get("rendered_chars", 0) or 0) for item in items),
        "tools_count": len(tools),
        "skills_count": len(skills),
        "commands_count": len(commands),
        "tool_names": tools,
        "skill_names": skills,
        "command_names": commands,
        "human_validation_required_count": sum(
            1
            for item in items
            if isinstance(item.get("human_validation"), dict) and item["human_validation"].get("required")
        ),
        "ok": all(bool(item.get("ok")) for item in items),
    }


def validate_agent_prompts(items: list[dict[str, object]], result: dict | None = None) -> dict[str, object]:
    errors: list[str] = []
    agent_types: set[str] = set()
    for index, item in enumerate(items, start=1):
        if item.get("schema_version") != "session_claude_agent_prompt_v1":
            errors.append(f"agent_prompt_schema_invalid:{index}")
        agent_type = str(item.get("agent_type") or "")
        if not agent_type:
            errors.append(f"agent_prompt_missing_agent_type:{index}")
        else:
            agent_types.add(agent_type)
        config_path = str(item.get("config_path") or "")
        if not config_path:
            errors.append(f"agent_prompt_missing_config_path:{agent_type or index}")
        elif not (ROOT / config_path).exists():
            errors.append(f"agent_prompt_config_missing:{config_path}")
        if not str(item.get("system_prompt_static") or "").strip():
            errors.append(f"agent_prompt_static_missing:{agent_type or index}")
        if not str(item.get("system_prompt_dynamic_template") or "").strip():
            errors.append(f"agent_prompt_dynamic_template_missing:{agent_type or index}")
        sections = item.get("rendered_sections", [])
        if not isinstance(sections, list) or len(sections) != 3:
            errors.append(f"agent_prompt_sections_count_invalid:{agent_type or index}")
        else:
            for section in sections:
                if not isinstance(section, dict) or not str(section.get("text") or "").strip():
                    errors.append(f"agent_prompt_section_empty:{agent_type or index}")
        if "{{" in str(item.get("rendered_prompt") or ""):
            errors.append(f"agent_prompt_unresolved_template:{agent_type or index}")
        if not item.get("ok"):
            errors.append(f"agent_prompt_not_ok:{agent_type or index}")

    if isinstance(result, dict) and result:
        expected_agents = result.get("agents", [])
        if not isinstance(expected_agents, list):
            result_agent_type = str(result.get("agent_type") or "")
            expected_agents = [result_agent_type] if result_agent_type and result_agent_type != "claude-pipeline" else []
        expected_set = {str(agent) for agent in expected_agents if str(agent)}
        if expected_set and expected_set != agent_types:
            errors.append("agent_prompt_result_agents_mismatch")

    return {
        "schema_version": "session_claude_agent_prompts_validation_v1",
        "prompts_count": len(items),
        "errors": sorted(set(errors)),
        "ok": not errors,
    }


def session_agent_prompts(session_id: str, *, agent: str = "") -> dict:
    session = require_session(session_id)
    runtime_mode = str(session.get("runtime_mode") or "")
    agent_filter = str(agent or "").strip()
    if not is_claude_runtime_mode(runtime_mode):
        return {
            "schema_version": "session_claude_agent_prompts_v1",
            "session_id": session["session_id"],
            "run_id": session.get("run_id", ""),
            "runtime_mode": runtime_mode,
            "available": False,
            "filters": {"agent": agent_filter},
            "prompts": [],
            "agents": [],
            "prompts_count": 0,
            "all_prompts_count": 0,
            "summary": summarize_agent_prompt_items([]),
            "all_summary": summarize_agent_prompt_items([]),
            "validation": validate_agent_prompts([]),
            "ok": False,
        }

    result = read_json_dict(Path(str(session.get("result_path") or "")))
    case = load_session_case_input(session)
    source_fixture = str(session.get("source_fixture") or result.get("source_fixture") or "inline")
    received_by_agent = handoffs_received_by_agent_from_result(result)
    try:
        runtime_runner = load_claude_runner_for_session(session)
        runners = list(runtime_runner.runners) if hasattr(runtime_runner, "runners") else [runtime_runner]
        all_items = [
            agent_prompt_item(
                runner,
                case,
                source_fixture,
                received_by_agent.get(str(runner.definition.agent_type), []),
            )
            for runner in runners
        ]
        load_error = ""
    except Exception as exc:
        all_items = []
        load_error = f"{type(exc).__name__}: {exc}"
    filtered_items = [
        item for item in all_items if not agent_filter or item.get("agent_type") == agent_filter
    ]
    validation = validate_agent_prompts(all_items, result)
    if load_error:
        validation = {
            **validation,
            "errors": sorted({*validation.get("errors", []), f"agent_prompt_load_error:{load_error}"}),
            "ok": False,
        }
    return {
        "schema_version": "session_claude_agent_prompts_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": runtime_mode,
        "available": bool(all_items),
        "filters": {"agent": agent_filter},
        "source_fixture": source_fixture,
        "case_available": bool(case),
        "prompts": filtered_items,
        "agents": [str(item.get("agent_type") or "") for item in filtered_items if item.get("agent_type")],
        "all_agents": [str(item.get("agent_type") or "") for item in all_items if item.get("agent_type")],
        "prompts_count": len(filtered_items),
        "all_prompts_count": len(all_items),
        "summary": summarize_agent_prompt_items(filtered_items),
        "all_summary": summarize_agent_prompt_items(all_items),
        "validation": validation,
        "ok": bool(all_items) and bool(validation.get("ok")),
    }


def load_session_transcript_entries(session: dict, result: dict | None = None) -> tuple[list[dict], Path | None]:
    path_value = str(session.get("claude_transcript_path") or "")
    if not path_value and isinstance(result, dict):
        path_value = str(result.get("transcript_path") or "")
    if not path_value:
        return [], None
    path = Path(path_value)
    return load_jsonl(path), path


def transcript_browser_summary(entries: list[dict]) -> dict[str, object]:
    roles: dict[str, int] = {}
    block_types: dict[str, int] = {}
    agents: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        role = str(entry.get("role") or "unknown")
        roles[role] = roles.get(role, 0) + 1
        agent = str(entry.get("agent_type") or "")
        if agent and agent not in agents:
            agents.append(agent)
        for block_type in entry.get("block_types", []) if isinstance(entry.get("block_types"), list) else []:
            block_type_name = str(block_type or "")
            if block_type_name:
                block_types[block_type_name] = block_types.get(block_type_name, 0) + 1
    return {
        "schema_version": "session_transcript_browser_summary_v1",
        "entries_count": len(entries),
        "agents": agents,
        "agents_count": len(agents),
        "roles": roles,
        "block_types": block_types,
        "tool_use_count": block_types.get("tool_use", 0),
        "tool_result_count": block_types.get("tool_result", 0),
        "handoff_messages_count": block_types.get("handoff", 0),
    }


def session_transcript(
    session_id: str,
    *,
    agent: str = "",
    role: str = "",
    block_type: str = "",
    offset: int = 0,
    limit: int = 50,
) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    entries, transcript_path = load_session_transcript_entries(session, result)
    agent_filter = str(agent or "").strip()
    role_filter = str(role or "").strip()
    block_type_filter = str(block_type or "").strip()
    safe_offset = max(int(offset or 0), 0)
    safe_limit = min(max(int(limit or 50), 0), 100)
    filtered_entries = [
        entry
        for entry in entries
        if (not agent_filter or entry.get("agent_type") == agent_filter)
        and (not role_filter or entry.get("role") == role_filter)
        and (
            not block_type_filter
            or (
                isinstance(entry.get("block_types"), list)
                and block_type_filter in entry.get("block_types", [])
            )
        )
    ]
    page_entries = filtered_entries[safe_offset : safe_offset + safe_limit] if safe_limit else []
    transcript_agent_type = str(
        result.get("agent_type")
        or session.get("claude_transcript_summary", {}).get("agent_type")
        or ""
    )
    all_summary = (
        summarize_claude_transcript_entries(
            entries,
            agent_type=transcript_agent_type,
            path=transcript_path.as_posix() if transcript_path is not None else "",
        )
        if entries
        else {}
    )
    validation = (
        validate_claude_transcript_entries(
            entries,
            agent_type=transcript_agent_type,
            session_id=str(session.get("session_id") or ""),
            run_id=str(session.get("run_id") or ""),
        )
        if entries
        else {
            "schema_version": "claude_transcript_validation_v0",
            "agent_type": transcript_agent_type,
            "entries_count": 0,
            "errors_count": 1,
            "errors": ["transcript_empty"],
            "ok": False,
        }
    )
    return {
        "schema_version": "session_transcript_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(entries),
        "transcript_path": transcript_path.as_posix() if transcript_path is not None else "",
        "filters": {
            "agent": agent_filter,
            "role": role_filter,
            "block_type": block_type_filter,
            "offset": safe_offset,
            "limit": safe_limit,
        },
        "agents": sorted({str(entry.get("agent_type") or "") for entry in entries if entry.get("agent_type")}),
        "roles": sorted({str(entry.get("role") or "") for entry in entries if entry.get("role")}),
        "block_types": sorted(
            {
                str(block_type_name)
                for entry in entries
                if isinstance(entry.get("block_types"), list)
                for block_type_name in entry.get("block_types", [])
                if str(block_type_name)
            }
        ),
        "all_entries_count": len(entries),
        "filtered_entries_count": len(filtered_entries),
        "entries_count": len(page_entries),
        "has_more": safe_offset + len(page_entries) < len(filtered_entries),
        "summary": transcript_browser_summary(page_entries),
        "filtered_summary": transcript_browser_summary(filtered_entries),
        "all_summary": all_summary,
        "entries": page_entries,
        "validation": validation,
        "ok": bool(entries) and bool(validation.get("ok")),
    }


def tools_by_agent_from_result(result: dict) -> dict[str, list[str]]:
    if not isinstance(result, dict):
        return {}
    raw = result.get("tools_by_agent", {})
    if isinstance(raw, dict) and raw:
        return {
            str(agent): [
                str(tool)
                for tool in tools
                if isinstance(tool, str) and tool
            ]
            for agent, tools in raw.items()
            if str(agent) and isinstance(tools, list)
        }
    summary = result.get("tool_registry_summary", {}) if isinstance(result.get("tool_registry_summary"), dict) else {}
    tool_names = summary.get("tool_names", []) if isinstance(summary.get("tool_names"), list) else []
    agent_type = str(result.get("agent_type") or "")
    if agent_type and tool_names:
        return {agent_type: [str(tool) for tool in tool_names if isinstance(tool, str) and tool]}
    return {}


def unique_session_tool_names(tools_by_agent: dict[str, list[str]]) -> list[str]:
    return sorted(
        {
            str(tool)
            for tools in tools_by_agent.values()
            for tool in tools
            if str(tool)
        }
    )


def validate_session_tool_registry(tools_by_agent: dict[str, list[str]]) -> dict[str, object]:
    registry_errors = validate_tool_registry()
    session_errors: list[str] = []
    for agent, tools in tools_by_agent.items():
        for tool_name in tools:
            if tool_name not in TOOL_REGISTRY:
                session_errors.append(f"{agent}:{tool_name}:missing_from_registry")
    errors = sorted(set([*registry_errors, *session_errors]))
    return {
        "schema_version": "session_tool_registry_validation_v1",
        "registry_errors": registry_errors,
        "session_errors": sorted(set(session_errors)),
        "errors": errors,
        "ok": not errors,
    }


def tool_palette_items(
    tools_by_agent: dict[str, list[str]],
    *,
    agent: str = "",
    permission: str = "",
    tool: str = "",
) -> list[dict[str, object]]:
    agent_filter = str(agent or "").strip()
    permission_filter = str(permission or "").strip()
    tool_filter = str(tool or "").strip()
    agents_by_tool: dict[str, list[str]] = {}
    for agent_name, tool_names in tools_by_agent.items():
        if agent_filter and agent_name != agent_filter:
            continue
        for tool_name in tool_names:
            agents_by_tool.setdefault(tool_name, [])
            if agent_name not in agents_by_tool[tool_name]:
                agents_by_tool[tool_name].append(agent_name)

    items: list[dict[str, object]] = []
    for tool_name in sorted(agents_by_tool):
        if tool_filter and tool_name != tool_filter:
            continue
        spec = TOOL_REGISTRY.get(tool_name)
        if spec is None:
            item = {
                "name": tool_name,
                "agents": sorted(agents_by_tool[tool_name]),
                "schema_version": "",
                "description": "",
                "permission": "",
                "read_only": False,
                "destructive": False,
                "strict": False,
                "model_facing_schema": {},
                "ok": False,
                "errors": ["missing_from_registry"],
            }
        else:
            if permission_filter and spec.permission != permission_filter:
                continue
            spec_dict = spec.as_dict()
            item = {
                **spec_dict,
                "agents": sorted(agents_by_tool[tool_name]),
                "model_facing_schema": spec.model_facing_schema(),
                "ok": True,
                "errors": [],
            }
        items.append(item)
    return items


def session_tool_summary_from_result(result: dict) -> dict:
    tools_by_agent = tools_by_agent_from_result(result)
    tool_names = unique_session_tool_names(tools_by_agent)
    summary = (
        result.get("tool_registry_summary", {})
        if isinstance(result.get("tool_registry_summary"), dict)
        else {}
    )
    if not summary and tool_names:
        summary = summarize_tool_registry(tool_names)
    validation = validate_session_tool_registry(tools_by_agent)
    return {
        "schema_version": "session_tools_summary_v1",
        "available": bool(tool_names),
        "agents_count": len(tools_by_agent),
        "tools_count": len(tool_names),
        "tool_names": tool_names,
        "summary": summary,
        "summary_by_agent": result.get("tool_registry_summary_by_agent", {})
        if isinstance(result.get("tool_registry_summary_by_agent"), dict)
        else {},
        "validation": validation,
        "ok": bool(tool_names) and bool(validation.get("ok")) and bool(summary.get("ok", True)),
    }


def session_tools(session_id: str, *, agent: str = "", permission: str = "", tool: str = "") -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    tools_by_agent = tools_by_agent_from_result(result)
    all_tool_names = unique_session_tool_names(tools_by_agent)
    agent_filter = str(agent or "").strip()
    permission_filter = str(permission or "").strip()
    tool_filter = str(tool or "").strip()
    items = tool_palette_items(
        tools_by_agent,
        agent=agent_filter,
        permission=permission_filter,
        tool=tool_filter,
    )
    filtered_tool_names = [str(item.get("name") or "") for item in items if item.get("name")]
    all_summary = (
        result.get("tool_registry_summary", {})
        if isinstance(result.get("tool_registry_summary"), dict)
        else {}
    )
    if not all_summary and all_tool_names:
        all_summary = summarize_tool_registry(all_tool_names)
    filtered_summary = summarize_tool_registry(filtered_tool_names) if filtered_tool_names else {}
    summary_by_agent = (
        result.get("tool_registry_summary_by_agent", {})
        if isinstance(result.get("tool_registry_summary_by_agent"), dict)
        else {}
    )
    if agent_filter and isinstance(summary_by_agent, dict):
        summary_by_agent = {
            agent_name: summary
            for agent_name, summary in summary_by_agent.items()
            if agent_name == agent_filter
        }
    validation = validate_session_tool_registry(tools_by_agent)
    return {
        "schema_version": "session_tools_v1",
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "available": bool(all_tool_names),
        "filters": {
            "agent": agent_filter,
            "permission": permission_filter,
            "tool": tool_filter,
        },
        "agents": sorted(tools_by_agent),
        "permissions": sorted(
            {
                TOOL_REGISTRY[tool_name].permission
                for tool_name in all_tool_names
                if tool_name in TOOL_REGISTRY
            }
        ),
        "all_tools_count": len(all_tool_names),
        "tools_count": len(items),
        "tool_names": filtered_tool_names,
        "all_tool_names": all_tool_names,
        "summary": filtered_summary,
        "all_summary": all_summary,
        "summary_by_agent": summary_by_agent,
        "tools_by_agent": tools_by_agent,
        "tools": items,
        "model_facing_tools": [
            item.get("model_facing_schema", {})
            for item in items
            if isinstance(item.get("model_facing_schema"), dict) and item.get("model_facing_schema")
        ],
        "validation": validation,
        "ok": bool(all_tool_names) and bool(validation.get("ok")),
    }


def session_claude_bundle(
    session_id: str,
    *,
    agent: str = "",
    hook_event: str = "",
    task_status: str = "",
    permission: str = "",
    tool: str = "",
    skill: str = "",
    loaded_from: str = "",
    settings_source: str = "",
    settings_key: str = "",
    handoff_direction: str = "",
    handoff_from_agent: str = "",
    handoff_to_agent: str = "",
    handoff_status: str = "",
    command_history_command: str = "",
    command_history_status: str = "",
    command_history_ok: str = "",
    command_history_offset: int = 0,
    command_history_limit: int = 10,
    role: str = "",
    block_type: str = "",
    offset: int = 0,
    limit: int = 20,
    lineage_terminal_only: bool = False,
) -> dict:
    summary = session_summary(session_id)
    session = summary.get("session", {}) if isinstance(summary.get("session"), dict) else require_session(session_id)
    commands = session_commands(session_id)
    command_history = session_command_history(
        session_id,
        command=command_history_command,
        status=command_history_status,
        ok=command_history_ok,
        offset=command_history_offset,
        limit=command_history_limit,
    )
    permissions = session_permissions(session_id)
    actions = read_claude_action_history(session)
    hooks = session_hooks(session_id, agent=agent, hook_event=hook_event)
    tasks = session_tasks(session_id, agent=agent, status=task_status)
    tools = session_tools(session_id, agent=agent, permission=permission, tool=tool)
    transcript = session_transcript(
        session_id,
        agent=agent,
        role=role,
        block_type=block_type,
        offset=offset,
        limit=limit,
    )
    artifact_lineage = session_artifact_lineage(
        session_id,
        agent=agent,
        terminal_only=lineage_terminal_only,
    )
    runtime_state = session_runtime_state(session_id, agent=agent)
    agent_manifest = session_agents(session_id, agent=agent)
    agent_prompts = session_agent_prompts(session_id, agent=agent)
    model_client = session_model_client(session_id)
    model_client_summary = (
        model_client.get("model_client", {})
        if isinstance(model_client.get("model_client"), dict)
        else {}
    )
    model_live_loop = (
        model_client.get("live_tool_loop", {})
        if isinstance(model_client.get("live_tool_loop"), dict)
        else model_client_summary.get("live_tool_loop", {})
        if isinstance(model_client_summary.get("live_tool_loop"), dict)
        else {}
    )
    live_replay = session_live_replay(session_id)
    provider_diagnostics = session_provider_diagnostics(session_id)
    skills = session_skills(session_id, agent=agent, skill=skill, loaded_from=loaded_from)
    settings = session_settings(session_id, source=settings_source, key=settings_key)
    handoffs = session_handoffs(
        session_id,
        agent=agent,
        from_agent=handoff_from_agent,
        to_agent=handoff_to_agent,
        direction=handoff_direction,
        status=handoff_status,
    )
    section_health = {
        "summary": bool(summary.get("integrity", {}).get("ok")) if isinstance(summary.get("integrity"), dict) else False,
        "agents": bool(agent_manifest.get("ok")),
        "skills": bool(skills.get("ok")),
        "settings": bool(settings.get("ok")),
        "commands": bool(commands.get("ok", commands.get("commands_count", 0) > 0)),
        "command_history": (not command_history.get("available")) or bool(command_history.get("ok")),
        "permissions": bool(permissions.get("ok")),
        "actions": bool(actions.get("ok", True)),
        "hooks": bool(hooks.get("ok")),
        "tasks": bool(tasks.get("ok")),
        "tools": bool(tools.get("ok")),
        "transcript": bool(transcript.get("ok")),
        "artifact_lineage": (not artifact_lineage.get("available")) or bool(artifact_lineage.get("ok")),
        "runtime_state": (not runtime_state.get("available")) or bool(runtime_state.get("ok")),
        "agent_prompts": (not agent_prompts.get("available")) or bool(agent_prompts.get("ok")),
        "model_client": (not model_client.get("available")) or bool(model_client.get("ok")),
        "live_replay": (not live_replay.get("available")) or bool(live_replay.get("ok")),
        "provider_diagnostics": bool(provider_diagnostics.get("ok")),
        "handoffs": (not handoffs.get("available")) or bool(handoffs.get("ok")),
    }
    return {
        "schema_version": "session_claude_bundle_v1",
        "session_id": session.get("session_id", session_id),
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "filters": {
            "agent": str(agent or "").strip(),
            "hook_event": str(hook_event or "").strip(),
            "task_status": str(task_status or "").strip(),
            "permission": str(permission or "").strip(),
            "tool": str(tool or "").strip(),
            "skill": str(skill or "").strip(),
            "loaded_from": str(loaded_from or "").strip(),
            "settings_source": str(settings_source or "").strip(),
            "settings_key": str(settings_key or "").strip(),
            "handoff_direction": str(handoff_direction or "").strip(),
            "handoff_from_agent": str(handoff_from_agent or "").strip(),
            "handoff_to_agent": str(handoff_to_agent or "").strip(),
            "handoff_status": str(handoff_status or "").strip(),
            "command_history_command": str(command_history_command or "").strip().lstrip("/"),
            "command_history_status": str(command_history_status or "").strip(),
            "command_history_ok": str(command_history_ok or "").strip(),
            "command_history_offset": max(int(command_history_offset or 0), 0),
            "command_history_limit": min(max(int(command_history_limit or 10), 0), 100),
            "role": str(role or "").strip(),
            "block_type": str(block_type or "").strip(),
            "offset": max(int(offset or 0), 0),
            "limit": min(max(int(limit or 20), 0), 100),
            "lineage_terminal_only": bool(lineage_terminal_only),
        },
        "routes": {
            "bundle": "/session/claude",
            "action": "/session/claude/action",
            "action_snapshot": "/session/claude/action/snapshot",
            "summary": "/session/summary",
            "artifact_lineage": "/session/artifact-lineage",
            "runtime_state": "/session/runtime-state",
            "agents": "/session/agents",
            "agent_prompts": "/session/agent-prompts",
            "model_client": "/session/model-client",
            "live_replay": "/session/live-replay",
            "provider_diagnostics": "/session/provider-diagnostics",
            "skills": "/session/skills",
            "settings": "/session/settings",
            "handoffs": "/session/handoffs",
            "commands": "/session/commands",
            "command": "/session/command",
            "command_history": "/session/command-history",
            "permissions": "/session/permissions",
            "hooks": "/session/hooks",
            "tasks": "/session/tasks",
            "tools": "/session/tools",
            "transcript": "/session/transcript",
            "artifact": "/artifact",
        },
        "counts": {
            "commands": commands.get("commands_count", 0),
            "executable_commands": commands.get("executable_commands_count", 0),
            "permission_decisions": permissions.get("decisions_count", 0),
            "controller_actions": actions.get("actions_count", 0),
            "controller_mutations": actions.get("mutation_count", 0),
            "controller_snapshots": actions.get("snapshots_count", 0),
            "hooks": hooks.get("invocations_count", 0),
            "all_hooks": hooks.get("all_invocations_count", 0),
            "tasks": tasks.get("tasks_count", 0),
            "all_tasks": tasks.get("all_tasks_count", 0),
            "tools": tools.get("tools_count", 0),
            "all_tools": tools.get("all_tools_count", 0),
            "transcript_entries": transcript.get("entries_count", 0),
            "all_transcript_entries": transcript.get("all_entries_count", 0),
            "artifacts": summary.get("artifacts", {}).get("artifacts_count", 0)
            if isinstance(summary.get("artifacts"), dict)
            else 0,
            "artifact_lineage": artifact_lineage.get("artifacts_count", 0),
            "all_artifact_lineage": artifact_lineage.get("all_artifacts_count", 0),
            "terminal_artifact_lineage": len(artifact_lineage.get("terminal_artifact_keys", []))
            if isinstance(artifact_lineage.get("terminal_artifact_keys"), list)
            else 0,
            "runtime_agents": runtime_state.get("agents_count", 0),
            "runtime_estimated_tokens": runtime_state.get("summary", {}).get("estimated_tokens", 0)
            if isinstance(runtime_state.get("summary"), dict)
            else 0,
            "runtime_needs_compaction": runtime_state.get("summary", {}).get("needs_compaction_count", 0)
            if isinstance(runtime_state.get("summary"), dict)
            else 0,
            "agents": agent_manifest.get("agents_count", 0),
            "all_agents": agent_manifest.get("all_agents_count", 0),
            "agent_prompts": agent_prompts.get("prompts_count", 0),
            "all_agent_prompts": agent_prompts.get("all_prompts_count", 0),
            "model_client_requests": model_client.get("model_client", {}).get("requests_count", 0)
            if isinstance(model_client.get("model_client"), dict)
            else 0,
            "model_client_responses": model_client.get("model_client", {}).get("responses_count", 0)
            if isinstance(model_client.get("model_client"), dict)
            else 0,
            "model_live_turns": model_live_loop.get("turns_count", 0),
            "model_live_tool_calls": model_live_loop.get("tool_calls_count", 0),
            "model_live_tool_results": model_live_loop.get("tool_results_count", 0),
            "live_retry_candidates": live_replay.get("retry_candidates_count", 0),
            "live_permission_requests": live_replay.get("permission_requests_count", 0),
            "provider_missing_guardrails": len(provider_diagnostics.get("missing_guardrails", []))
            if isinstance(provider_diagnostics.get("missing_guardrails"), list)
            else 0,
            "skills": skills.get("skills_count", 0),
            "all_skills": skills.get("all_skills_count", 0),
            "settings_sources": settings.get("sources_count", 0),
            "all_settings_sources": settings.get("all_sources_count", 0),
            "settings_effective_keys": len(settings.get("effective_keys", []))
            if isinstance(settings.get("effective_keys"), list)
            else 0,
            "handoffs": handoffs.get("handoffs_count", 0),
            "all_handoffs": handoffs.get("all_handoffs_count", 0),
            "created_handoffs": handoffs.get("created_handoffs_count", 0),
            "received_handoffs": handoffs.get("received_handoffs_count", 0),
            "command_history": command_history.get("commands_count", 0),
            "all_command_history": command_history.get("all_commands_count", 0),
        },
        "section_health": section_health,
        "summary": summary,
        "agent_manifest": agent_manifest,
        "agent_prompts": agent_prompts,
        "model_client": model_client,
        "live_replay": live_replay,
        "provider_diagnostics": provider_diagnostics,
        "skills": skills,
        "settings": settings,
        "handoffs": handoffs,
        "commands": commands,
        "command_history": command_history,
        "permissions": permissions,
        "actions": actions,
        "hooks": hooks,
        "tasks": tasks,
        "tools": tools,
        "transcript": transcript,
        "artifact_lineage": artifact_lineage,
        "runtime_state": runtime_state,
        "integrity": summary.get("integrity", {}),
        "ok": all(section_health.values()),
    }


def session_claude_action(body: dict) -> dict:
    session_id = str(body.get("session_id") or "").strip()
    if not session_id:
        raise ValueError("session_id requis")
    action = str(body.get("action") or body.get("type") or "").strip()
    if not action:
        raise ValueError("action requise")

    normalized_action = {
        "command": "execute_command",
        "slash_command": "execute_command",
        "execute_command": "execute_command",
        "permission_update": "update_permissions",
        "permissions": "update_permissions",
        "update_permissions": "update_permissions",
        "live_replay": "live_replay",
        "replay_live_loop": "live_replay",
        "retry_candidates": "live_replay",
        "refresh": "refresh",
    }.get(action)
    if normalized_action is None:
        raise ValueError(f"action claude non supportee: {action}")

    session = require_session(session_id)
    action_id = new_claude_action_id(normalized_action)
    snapshot_path = claude_action_snapshot_path(session, action_id)
    before_controller = app_claude_controller_state(session_id, session=session)

    action_result: dict[str, object]
    mutation_applied = False
    if normalized_action == "execute_command":
        command_body = {
            "session_id": session_id,
            "command": body.get("command") or body.get("command_name") or "",
            "args": body.get("args") or "",
        }
        action_result = execute_session_slash_command(command_body)
        mutation_applied = True
        result_ok = bool(
            isinstance(action_result.get("command_result"), dict)
            and action_result["command_result"].get("ok")
        )
    elif normalized_action == "update_permissions":
        permission_body = {
            "session_id": session_id,
            "updates": body.get("updates"),
        }
        if permission_body["updates"] is None and "update" in body:
            permission_body["update"] = body.get("update")
        action_result = update_session_permissions(permission_body)
        mutation_applied = True
        result_ok = bool(action_result.get("ok"))
    elif normalized_action == "live_replay":
        action_result = session_live_replay(session_id)
        result_ok = bool(action_result.get("ok"))
    else:
        action_result = {
            "schema_version": "session_claude_refresh_action_v1",
            "session_id": session_id,
            "ok": True,
        }
        result_ok = True

    session = require_session(session_id)
    action_summary = append_claude_action_history(
        session,
        action_id=action_id,
        action=normalized_action,
        requested_action=action,
        mutation_applied=mutation_applied,
        action_result=action_result,
        snapshot_path=snapshot_path.as_posix(),
        ok=bool(result_ok),
    )
    write_claude_action_snapshot(
        session,
        action_id=action_id,
        action=normalized_action,
        requested_action=action,
        mutation_applied=mutation_applied,
        action_result=action_result,
        action_summary=action_summary,
        ok=bool(result_ok),
        before_controller=before_controller,
        snapshot_path=snapshot_path,
        stage="recorded",
    )
    bundle = session_claude_bundle(
        session_id,
        agent=str(body.get("agent") or ""),
        hook_event=str(body.get("hook_event") or ""),
        task_status=str(body.get("task_status") or body.get("status") or ""),
        permission=str(body.get("permission") or ""),
        tool=str(body.get("tool") or ""),
        role=str(body.get("role") or ""),
        block_type=str(body.get("block_type") or ""),
        offset=_optional_int(body.get("offset", 0), default=0) or 0,
        limit=bounded_limit(body.get("limit", 20)),
    )
    controller = app_claude_controller_state(session_id)
    snapshot = write_claude_action_snapshot(
        require_session(session_id),
        action_id=action_id,
        action=normalized_action,
        requested_action=action,
        mutation_applied=mutation_applied,
        action_result=action_result,
        action_summary=action_summary,
        ok=bool(result_ok),
        before_controller=before_controller,
        after_controller=controller,
        bundle=bundle,
        snapshot_path=snapshot_path,
    )
    return {
        "schema_version": "session_claude_action_v1",
        "session_id": session_id,
        "run_id": bundle.get("run_id", ""),
        "runtime_mode": bundle.get("runtime_mode", ""),
        "action_id": action_id,
        "action": normalized_action,
        "requested_action": action,
        "mutation_applied": mutation_applied,
        "action_result": action_result,
        "action_result_schema_version": action_result.get("schema_version", ""),
        "action_summary": action_summary,
        "snapshot": snapshot,
        "bundle": bundle,
        "controller": controller,
        "ok": bool(result_ok) and bool(bundle.get("ok")),
    }


def append_claude_action_history(
    session: dict,
    *,
    action_id: str,
    action: str,
    requested_action: str,
    mutation_applied: bool,
    action_result: dict,
    snapshot_path: str,
    ok: bool,
) -> dict:
    path = Path(str(session["session_dir"])) / CLAUDE_ACTIONS_FILENAME
    command_result = action_result.get("command_result", {}) if isinstance(action_result.get("command_result"), dict) else {}
    latest_update = action_result.get("latest_update", {}) if isinstance(action_result.get("latest_update"), dict) else {}
    event = command_result.get("event", {}) if isinstance(command_result.get("event"), dict) else {}
    record = {
        "schema_version": "session_claude_action_record_v1",
        "created_at_utc": utc_now_iso(),
        "action_id": action_id,
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "action": action,
        "requested_action": requested_action,
        "mutation_applied": bool(mutation_applied),
        "status": command_result.get("status", "ok" if ok else "failed"),
        "ok": bool(ok),
        "action_result_schema_version": action_result.get("schema_version", ""),
        "command_name": command_result.get("command_name", ""),
        "command_display_name": command_result.get("command_display_name", ""),
        "command_status": command_result.get("status", ""),
        "command_event_id": event.get("event_id", ""),
        "permission_updates_applied_count": action_result.get("updates_applied_count", 0),
        "permission_latest_update_type": latest_update.get("type", ""),
        "permission_latest_update_destination": latest_update.get("destination", ""),
        "snapshot_path": snapshot_path,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    records = load_jsonl(path)
    by_action: dict[str, int] = {}
    for item in records:
        action_name = str(item.get("action") or "")
        if action_name:
            by_action[action_name] = by_action.get(action_name, 0) + 1
    summary = {
        "schema_version": "session_claude_action_summary_v1",
        "path": path.as_posix(),
        "actions_count": len(records),
        "mutation_count": sum(1 for item in records if item.get("mutation_applied") is True),
        "snapshots_count": sum(1 for item in records if item.get("snapshot_path")),
        "ok_count": sum(1 for item in records if item.get("ok") is True),
        "failed_count": sum(1 for item in records if item.get("ok") is not True),
        "by_action": by_action,
        "latest": record,
        "ok": True,
    }
    session["claude_action_history_path"] = path.as_posix()
    session["claude_action_summary"] = summary
    save_session(session)
    return summary


def load_claude_runner_for_session(session: dict):
    runtime_mode = str(session.get("runtime_mode") or "")
    settings_context = session.get("settings_context") if isinstance(session.get("settings_context"), dict) else None
    if runtime_mode in {RUNTIME_MODE_CLAUDE_PIPELINE_V0, RUNTIME_MODE_CLAUDE_LIVE_PIPELINE_V0}:
        return load_pipeline_runner(project_root=ROOT, settings_context=settings_context)
    agent_config_name = CLAUDE_SINGLE_AGENT_RUNTIME_MODES.get(runtime_mode)
    if not agent_config_name and runtime_mode in CLAUDE_LIVE_AGENT_RUNTIME_MODES:
        agent_config_name = str(CLAUDE_LIVE_AGENT_RUNTIME_MODES[runtime_mode]["agent_config"])
    if agent_config_name:
        return load_agent_runner(agent_config_name, project_root=ROOT, settings_context=settings_context)
    raise ValueError(f"slash commands non disponibles pour runtime_mode: {runtime_mode}")


def persist_session_slash_command(session: dict, result: dict, command_result: dict) -> dict:
    append_slash_command_event(session, result, command_result)
    append_slash_command_message(session, result, command_result)
    return append_slash_command_history(session, command_result)


def append_slash_command_event(session: dict, result: dict, command_result: dict) -> None:
    event = command_result.get("event")
    if not isinstance(event, dict):
        return
    events_path = Path(str(session.get("events_path") or ""))
    events = load_jsonl(events_path)
    if not events and isinstance(result.get("events"), list):
        events = [dict(item) for item in result["events"] if isinstance(item, dict)]
    enriched = enrich_event(event, session, len(events) + 1)
    events.append(enriched)
    result["events"] = events
    command_result["event"] = enriched
    if events_path:
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in events), encoding="utf-8")


def append_slash_command_message(session: dict, result: dict, command_result: dict) -> None:
    message = command_result.get("message")
    if not isinstance(message, dict):
        return
    messages = result.get("messages", [])
    if not isinstance(messages, list):
        messages = []
    messages.append(message)
    result["messages"] = messages
    agent_type = str(result.get("agent_type") or command_result.get("agent_type") or "claude-runtime")
    runtime_options = (
        session.get("settings_context", {}).get("runtime_options", {})
        if isinstance(session.get("settings_context"), dict)
        else {}
    )
    result["conversation_state"] = summarize_claude_messages(
        messages,
        agent_type=agent_type,
        strict_tool_result_pairing=bool(runtime_options.get("strict_tool_result_pairing", True)),
    )
    previous_context_state = result.get("context_state", {}) if isinstance(result.get("context_state"), dict) else {}
    context_state = build_context_state(
        messages,
        agent_type=agent_type,
        threshold_tokens=_optional_int(
            previous_context_state.get("threshold_tokens"),
            default=_optional_int(runtime_options.get("context_compaction_threshold_tokens")),
        ),
        preserve_recent_tool_results=_optional_int(
            previous_context_state.get("preserve_recent_tool_results"),
            default=_optional_int(runtime_options.get("preserve_recent_tool_results"), default=3) or 3,
        ) or 3,
    )
    if previous_context_state.get("compact_summary_artifact"):
        context_state["compact_summary_artifact"] = previous_context_state["compact_summary_artifact"]
    result["context_state"] = context_state

    transcript_path_value = str(session.get("claude_transcript_path") or result.get("transcript_path") or "")
    if transcript_path_value:
        transcript_path = Path(transcript_path_value)
        result["transcript_path"] = transcript_path.as_posix()
        write_claude_transcript(
            transcript_path,
            messages,
            agent_type=agent_type,
            session_id=str(session.get("session_id") or ""),
            run_id=str(session.get("run_id") or ""),
        )
        summary = persist_claude_transcript_for_session(result, session)
        if summary:
            session["claude_transcript_summary"] = summary


def append_slash_command_history(session: dict, command_result: dict) -> dict:
    path = Path(str(session["session_dir"])) / SLASH_COMMANDS_FILENAME
    output = command_result.get("output", {}) if isinstance(command_result.get("output"), dict) else {}
    record = {
        "schema_version": "session_slash_command_record_v1",
        "created_at_utc": utc_now_iso(),
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "command_name": command_result.get("command_name", ""),
        "command_display_name": command_result.get("command_display_name", ""),
        "command_type": command_result.get("command_type", ""),
        "status": command_result.get("status", ""),
        "ok": bool(command_result.get("ok")),
        "errors": command_result.get("errors", []),
        "event_id": command_result.get("event", {}).get("event_id", "")
        if isinstance(command_result.get("event"), dict)
        else "",
        "message_sequence": command_result.get("message", {}).get("message_sequence", 0)
        if isinstance(command_result.get("message"), dict)
        else 0,
        "display_text": str(output.get("display_text") or ""),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    records = load_jsonl(path)
    summary = {
        "schema_version": "session_slash_command_summary_v1",
        "path": path.as_posix(),
        "commands_count": len(records),
        "latest": record,
        "ok_count": sum(1 for item in records if item.get("ok") is True),
        "blocked_count": sum(1 for item in records if item.get("ok") is not True),
    }
    session["slash_command_history_path"] = path.as_posix()
    session["slash_command_summary"] = summary
    return summary


def summarize_permission_state_for_session(
    state: dict,
    permission_state_path: Path,
    result: dict,
    session: dict,
) -> dict:
    summary = summarize_permission_state(state)
    summary.update(
        {
            "schema_version": "claude_permission_state_summary_v0",
            "session_id": session.get("session_id", ""),
            "run_id": session.get("run_id", ""),
            "agent_type": result.get("agent_type", summary.get("agent_type", "")),
            "path": permission_state_path.as_posix(),
            "replay": state.get("replay", {}),
            "ok": bool(summary.get("ok")) and bool(state.get("replay", {}).get("ok", True)),
        }
    )
    return summary


def build_knowledge_snapshot(session: dict, result: dict, artifact_index: dict) -> dict:
    facts = read_artifact_json_from_index(session, artifact_index, "data-facts", "fiche_bien.json")
    timeline = read_artifact_json_from_index(session, artifact_index, "data-facts", "timeline_faits.json")
    comparables_payload = read_artifact_json_from_index(session, artifact_index, "comps-market", "comparables_proposes.json")
    justifications_payload = read_artifact_json_from_index(session, artifact_index, "comps-market", "justifications_comparables.json")
    comparative = read_artifact_json_from_index(session, artifact_index, "valuation-draft", "calculs_approche_comparative.json")
    cost = read_artifact_json_from_index(session, artifact_index, "valuation-draft", "calculs_approche_cout.json")
    income = read_artifact_json_from_index(session, artifact_index, "valuation-draft", "calculs_approche_revenu.json")
    hypotheses = read_artifact_json_from_index(session, artifact_index, "valuation-draft", "hypotheses_explicites.json")
    non_conformites = read_artifact_json_from_index(session, artifact_index, "compliance-qa", "rapport_non_conformites.json")
    compliance = read_artifact_json_from_index(session, artifact_index, "compliance-qa", "statut_sortie.json")
    recommendations = read_artifact_text_from_index(session, artifact_index, "compliance-qa", "recommandations_corrections.md")
    report = read_artifact_text_from_index(session, artifact_index, "redaction", "brouillon_rapport.md")
    annexe = read_artifact_text_from_index(session, artifact_index, "redaction", "annexe_sources.md")

    comparables = comparables_payload.get("comparables", []) if isinstance(comparables_payload.get("comparables"), list) else []
    justifications = justifications_payload.get("justifications", []) if isinstance(justifications_payload.get("justifications"), list) else []
    values = compliance.get("valuation_values", {}) if isinstance(compliance.get("valuation_values"), dict) else {}
    source_items = knowledge_source_items(session, artifact_index)
    source_ids = {str(item.get("source_id") or "") for item in source_items if item.get("source_id")}
    expected_source_ids = {str(item) for item in facts.get("source_ids", []) if item} if isinstance(facts.get("source_ids"), list) else set()
    missing_source_ids = sorted(expected_source_ids - source_ids)
    blocking = compliance.get("blocking_failures", result.get("blocking_failures", []))
    warnings = compliance.get("warnings", result.get("warnings", []))
    if not isinstance(blocking, list):
        blocking = []
    if not isinstance(warnings, list):
        warnings = []
    valuation_approaches = {
        "approche_comparative": comparative,
        "approche_cout": cost,
        "approche_revenu": income,
    }
    valuation_values = {key: value.get("value") for key, value in valuation_approaches.items() if isinstance(value.get("value"), (int, float))}
    if not values:
        values = valuation_values
    quality = knowledge_quality(
        facts=facts,
        comparables=comparables,
        values=values,
        blocking=blocking,
        missing_source_ids=missing_source_ids,
        report=report,
    )
    return {
        "schema_version": "knowledge_immobilier_session_v1",
        "contract": {
            "source": "mvp/KNOWLEDGE-SCHEMA-IMMOBILIER-V0.yaml",
            "api_schema": "schemas/knowledge_immobilier_session_v1.schema.json",
        },
        "session_id": session["session_id"],
        "run_id": session["run_id"],
        "dossier_id": result.get("dossier_id", ""),
        "status": result.get("status", "UNKNOWN"),
        "mandate": {
            "dossier_id": result.get("dossier_id", ""),
            "type_rapport": "evaluation_residentielle_v0",
            "date_reference": facts.get("date_reference", ""),
            "droits_evalues": "valeur marchande",
            "finalite": "assistance pre-revue evaluateur agree",
            "portee": "runtime local source par artefacts de session",
            "limites": [
                "aucune certification automatique",
                "aucune reponse evaluateur agree inventee",
                "dossiers reels et donnees sensibles exclus du runtime demo",
            ],
        },
        "subject_property": {
            "type_bien": facts.get("type_bien", ""),
            "zone": facts.get("zone", ""),
            "adresse_anonymisee": facts.get("adresse_anonymisee", "NON_FOURNIE"),
            "surface": facts.get("surface"),
            "confidence": facts.get("confidence"),
            "source_ids": sorted(expected_source_ids),
            "timeline": timeline.get("events", []) if isinstance(timeline.get("events"), list) else [],
        },
        "sources": {
            "count": len(source_items),
            "items": source_items,
            "missing_source_ids": missing_source_ids,
            "coverage_status": "OK" if not missing_source_ids else "A_COMPLETER",
        },
        "market_evidence": {
            "comparables_count": len(comparables),
            "comparables": comparables,
            "justifications": justifications,
        },
        "valuation": {
            "approaches": valuation_approaches,
            "values": values,
            "hypotheses": hypotheses.get("hypotheses", []) if isinstance(hypotheses.get("hypotheses"), list) else [],
        },
        "reconciliation": build_knowledge_reconciliation(values),
        "compliance": {
            "status": compliance.get("status", result.get("status", "UNKNOWN")),
            "blocking_failures": blocking,
            "warnings": warnings,
            "non_conformites": non_conformites,
            "recommendations": recommendations,
        },
        "redaction": {
            "brouillon_rapport_available": bool(report),
            "annexe_sources_available": bool(annexe),
            "sections_manquantes": [] if report and annexe else [name for name, available in {"brouillon_rapport": bool(report), "annexe_sources": bool(annexe)}.items() if not available],
            "brouillon_rapport_preview": report[:1200],
        },
        "human_review": {
            "required": True,
            "decision_source": "review interne + evaluateur agree",
            "external_evaluator_responses_included": False,
        },
        "audit": {
            "events_count": len(result.get("events", [])),
            "artifacts_count": artifact_index.get("artifacts_count", 0),
            "latest_event_id": result.get("events", [{}])[-1].get("event_id", "") if result.get("events") else "",
            "audit_log": result.get("audit_log", ""),
            "artifact_dir": result.get("artifact_dir", ""),
            "source_artifacts": knowledge_source_artifacts(artifact_index),
        },
        "quality": quality,
        "limits": {
            "certification_automatic": False,
            "external_evaluator_responses_included": False,
            "requires_human_validation": True,
        },
    }


def knowledge_immobilier_summary(session_id: str) -> dict:
    session = require_session(session_id)
    snapshot = read_json_dict(Path(str(session.get("knowledge_snapshot_path") or "")))
    if snapshot.get("schema_version") == "knowledge_immobilier_session_v1":
        return snapshot
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    artifact_index = session_artifacts(session_id)
    return build_knowledge_snapshot(session, result, artifact_index)


def artifact_records_from_index(artifact_index: dict, step: str = "", artifact: str = "") -> list[dict]:
    records = artifact_index.get("artifacts", []) if isinstance(artifact_index, dict) else []
    result: list[dict] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if step and record.get("step") != step:
            continue
        if artifact and record.get("artifact") != artifact:
            continue
        result.append(record)
    return result


def resolve_index_artifact_path(session: dict, record: dict) -> Path | None:
    raw = Path(str(record.get("path") or ""))
    if not raw:
        return None
    try:
        resolved = raw.resolve()
        resolved.relative_to(Path(str(session["session_dir"])).resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.exists() and resolved.is_file() else None


def read_artifact_json_from_index(session: dict, artifact_index: dict, step: str, artifact: str) -> dict:
    for record in artifact_records_from_index(artifact_index, step, artifact):
        path = resolve_index_artifact_path(session, record)
        if not path:
            continue
        return read_json_dict(path)
    return {}


def read_artifact_text_from_index(session: dict, artifact_index: dict, step: str, artifact: str, limit: int = 16 * 1024) -> str:
    for record in artifact_records_from_index(artifact_index, step, artifact):
        path = resolve_index_artifact_path(session, record)
        if not path:
            continue
        return path.read_text(encoding="utf-8")[:limit]
    return ""


def knowledge_source_items(session: dict, artifact_index: dict) -> list[dict]:
    dedup: dict[str, dict] = {}
    for record in artifact_records_from_index(artifact_index, artifact="source_index.json"):
        path = resolve_index_artifact_path(session, record)
        payload = read_json_dict(path) if path else {}
        for source in payload.get("sources", []):
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("source_id") or "")
            if not source_id:
                continue
            item = dedup.setdefault(
                source_id,
                {
                    "source_id": source_id,
                    "source_type": source.get("source_type", "runtime_fixture"),
                    "reliability_level": source.get("reliability_level", "A_VALIDER"),
                    "producer_steps": [],
                },
            )
            step = str(record.get("step") or "")
            if step and step not in item["producer_steps"]:
                item["producer_steps"].append(step)
    return sorted(dedup.values(), key=lambda item: item["source_id"])


def build_knowledge_reconciliation(values: dict) -> dict:
    numeric_values = {key: float(value) for key, value in values.items() if isinstance(value, (int, float))}
    if numeric_values:
        spread = round(max(numeric_values.values()) - min(numeric_values.values()), 2)
        proposed = numeric_values.get("approche_comparative", next(iter(numeric_values.values())))
    else:
        spread = 0.0
        proposed = None
    return {
        "valeurs_par_approche": numeric_values,
        "ecart_inter_approches": spread,
        "poids_recommandes": {
            "approche_comparative": 1.0 if "approche_comparative" in numeric_values else 0.0,
            "approche_cout": 0.0,
            "approche_revenu": 0.0,
        },
        "conclusion_proposee": {
            "value": proposed,
            "status": "A_VALIDER_PAR_EVALUATEUR_AGREE" if proposed is not None else "ABSENTE",
            "policy": "proxy_v0_non_certifiant",
        },
        "points_validation_humaine": [
            "confirmer les sources et les comparables retenus",
            "valider les ajustements sensibles",
            "signer la conclusion de valeur hors systeme automatique",
        ],
    }


def knowledge_quality(*, facts: dict, comparables: list, values: dict, blocking: list, missing_source_ids: list, report: str) -> dict:
    missing_sections = []
    if not facts:
        missing_sections.append("subject_property")
    if not comparables:
        missing_sections.append("market_evidence")
    if not values:
        missing_sections.append("valuation")
    if not report:
        missing_sections.append("redaction")
    if blocking:
        status = "BLOQUE"
    elif missing_source_ids or missing_sections:
        status = "A_COMPLETER"
    else:
        status = "PRET_ASSISTANCE"
    return {
        "status": status,
        "missing_sections": missing_sections,
        "missing_source_ids_count": len(missing_source_ids),
        "blocking_failures_count": len(blocking),
        "knowledge_ready": status == "PRET_ASSISTANCE",
    }


def knowledge_source_artifacts(artifact_index: dict) -> list[dict]:
    return [
        {
            "step": record.get("step", ""),
            "artifact": record.get("artifact", ""),
            "event_id": record.get("event_id", ""),
            "sha256": record.get("sha256", ""),
        }
        for record in artifact_index.get("artifacts", [])
        if isinstance(record, dict)
    ]


def session_status(session_id: str) -> dict:
    session = require_session(session_id)
    validation = validate_session_integrity(session)
    return {"session": session, "integrity": validation}


def session_artifacts(session_id: str) -> dict:
    session = require_session(session_id)
    artifact_index_path = session.get("artifact_index_path")
    if not artifact_index_path:
        return {"schema_version": "artifact_index_v1", "artifacts_count": 0, "artifacts": []}
    path = Path(str(artifact_index_path))
    if not path.exists():
        return {"schema_version": "artifact_index_v1", "artifacts_count": 0, "artifacts": []}
    return json.loads(path.read_text(encoding="utf-8"))


def session_model_client(session_id: str) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    model_client = (
        session.get("model_client")
        if isinstance(session.get("model_client"), dict)
        else result.get("model_client", {})
        if isinstance(result.get("model_client"), dict)
        else {}
    )
    live_adapter = (
        session.get("live_adapter")
        if isinstance(session.get("live_adapter"), dict)
        else result.get("live_adapter", {})
        if isinstance(result.get("live_adapter"), dict)
        else {}
    )
    if not model_client:
        model_client = {
            "schema_version": "claude_model_client_summary_v0",
            "enabled": False,
            "provider": "",
            "requests_count": 0,
            "responses_count": 0,
            "tool_calls_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "ok": True,
        }
    live_tool_loop = (
        model_client.get("live_tool_loop", {})
        if isinstance(model_client.get("live_tool_loop"), dict)
        else result.get("model_live_loop", {})
        if isinstance(result.get("model_live_loop"), dict)
        else {}
    )
    model_requests = (
        result.get("model_requests", [])
        if isinstance(result.get("model_requests"), list)
        else model_client.get("requests", [])
        if isinstance(model_client.get("requests"), list)
        else []
    )
    model_responses = (
        result.get("model_responses", [])
        if isinstance(result.get("model_responses"), list)
        else model_client.get("responses", [])
        if isinstance(model_client.get("responses"), list)
        else []
    )
    return {
        "schema_version": "session_model_client_v1",
        "available": bool(model_client.get("enabled")),
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "model_client": model_client,
        "live_adapter": live_adapter,
        "live_tool_loop": live_tool_loop,
        "request": result.get("model_request", {}) if isinstance(result.get("model_request"), dict) else {},
        "response": result.get("model_response", {}) if isinstance(result.get("model_response"), dict) else {},
        "requests": model_requests,
        "responses": model_responses,
        "ok": bool(model_client.get("ok", True)),
    }


def live_loop_from_model_client_surface(model_client_surface: dict, result: dict) -> dict:
    model_client = (
        model_client_surface.get("model_client", {})
        if isinstance(model_client_surface.get("model_client"), dict)
        else {}
    )
    live_loop = (
        model_client_surface.get("live_tool_loop", {})
        if isinstance(model_client_surface.get("live_tool_loop"), dict)
        else model_client.get("live_tool_loop", {})
        if isinstance(model_client.get("live_tool_loop"), dict)
        else result.get("model_live_loop", {})
        if isinstance(result.get("model_live_loop"), dict)
        else {}
    )
    return live_loop if isinstance(live_loop, dict) else {}


def live_loop_by_agent_from_result(result: dict) -> dict[str, dict]:
    loops = result.get("model_live_loop_by_agent", {})
    if not isinstance(loops, dict):
        return {}
    return {
        str(agent): loop
        for agent, loop in loops.items()
        if str(agent) and isinstance(loop, dict)
    }


def transcript_tool_replay(entries: list[dict]) -> dict:
    tool_uses: dict[str, dict] = {}
    tool_results: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        agent_type = str(entry.get("agent_type") or "")
        sequence = int(entry.get("sequence") or 0)
        content = entry.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type == "tool_use":
                tool_call_id = str(block.get("id") or "")
                if not tool_call_id:
                    continue
                tool_uses[tool_call_id] = {
                    "tool_call_id": tool_call_id,
                    "tool": str(block.get("name") or ""),
                    "input": block.get("input", {}) if isinstance(block.get("input"), dict) else {},
                    "agent_type": agent_type,
                    "transcript_sequence": sequence,
                }
            elif block_type == "tool_result":
                tool_call_id = str(block.get("tool_use_id") or "")
                if not tool_call_id:
                    continue
                tool_results.append(
                    {
                        "tool_call_id": tool_call_id,
                        "tool": str(block.get("name") or ""),
                        "ok": bool(block.get("ok", False)),
                        "error": str(block.get("error") or ""),
                        "permission": str(block.get("permission") or ""),
                        "agent_type": agent_type,
                        "transcript_sequence": sequence,
                    }
                )

    retry_candidates: list[dict] = []
    for result in tool_results:
        if result.get("ok"):
            continue
        tool_use = tool_uses.get(str(result.get("tool_call_id") or ""), {})
        retry_candidates.append(
            {
                "source": "transcript_tool_result",
                "tool_call_id": result.get("tool_call_id", ""),
                "tool": result.get("tool") or tool_use.get("tool", ""),
                "agent_type": result.get("agent_type") or tool_use.get("agent_type", ""),
                "input": tool_use.get("input", {}),
                "error": result.get("error", ""),
                "permission": result.get("permission", ""),
                "retryable": True,
                "transcript_sequence": result.get("transcript_sequence", 0),
            }
        )

    return {
        "schema_version": "session_live_transcript_tool_replay_v1",
        "tool_use_count": len(tool_uses),
        "tool_result_count": len(tool_results),
        "failed_tool_result_count": len(retry_candidates),
        "retry_candidates": retry_candidates,
    }


def dedupe_replay_records(records: list[dict], *, default_key_prefix: str) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        key = "|".join(
            [
                str(record.get("agent_type") or ""),
                str(record.get("tool_call_id") or ""),
                str(record.get("tool") or ""),
                str(record.get("error") or record.get("reason") or ""),
            ]
        )
        if key == "|||":
            key = f"{default_key_prefix}:{index}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def live_loop_failure_records(live_loop: dict, live_loop_by_agent: dict[str, dict]) -> list[dict]:
    failures: list[dict] = []
    for loop in [live_loop, *live_loop_by_agent.values()]:
        if not isinstance(loop, dict):
            continue
        for failure in loop.get("failed_tool_calls", []) if isinstance(loop.get("failed_tool_calls"), list) else []:
            if not isinstance(failure, dict):
                continue
            failures.append(
                {
                    "source": "live_tool_loop",
                    "tool_call_id": str(failure.get("tool_call_id") or ""),
                    "tool": str(failure.get("tool") or ""),
                    "agent_type": str(failure.get("agent_type") or loop.get("agent_type") or ""),
                    "input": failure.get("input", {}) if isinstance(failure.get("input"), dict) else {},
                    "artifact": str(failure.get("artifact") or ""),
                    "path": str(failure.get("path") or ""),
                    "turn": int(failure.get("turn") or 0),
                    "stop_reason": str(failure.get("stop_reason") or ""),
                    "error": str(failure.get("error") or ""),
                    "retryable": bool(failure.get("retryable", True)),
                }
            )
    return failures


def live_loop_permission_requests(live_loop: dict, live_loop_by_agent: dict[str, dict], result: dict) -> list[dict]:
    requests: list[dict] = []
    for loop in [live_loop, *live_loop_by_agent.values()]:
        if not isinstance(loop, dict):
            continue
        for item in loop.get("permission_requests", []) if isinstance(loop.get("permission_requests"), list) else []:
            if not isinstance(item, dict):
                continue
            requests.append(
                {
                    "source": "live_tool_loop",
                    "tool_call_id": str(item.get("tool_call_id") or ""),
                    "tool": str(item.get("tool") or ""),
                    "agent_type": str(item.get("agent_type") or loop.get("agent_type") or ""),
                    "permission": str(item.get("permission") or ""),
                    "reason": str(item.get("reason") or "permission_state_ask_rule"),
                    "recommended_update": item.get("recommended_update", {})
                    if isinstance(item.get("recommended_update"), dict)
                    else {},
                }
            )
    decisions = result.get("permission_decisions", [])
    if isinstance(decisions, list):
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            if decision.get("reason") != "permission_state_ask_rule":
                continue
            tool_name = str(decision.get("tool") or "")
            requests.append(
                {
                    "source": "permission_decision",
                    "tool_call_id": str(decision.get("tool_call_id") or ""),
                    "tool": tool_name,
                    "agent_type": str(decision.get("agent_type") or ""),
                    "permission": str(decision.get("permission") or ""),
                    "reason": "permission_state_ask_rule",
                    "recommended_update": {
                        "behavior": "allow",
                        "scope": "project",
                        "rules": [{"toolName": tool_name}] if tool_name else [],
                    },
                }
            )
    return dedupe_replay_records(requests, default_key_prefix="permission_request")


def permission_replay_surface_from_result(result: dict) -> dict:
    summary = result.get("permission_replay_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    by_agent = result.get("permission_replay_summary_by_agent", {})
    by_agent = by_agent if isinstance(by_agent, dict) else {}
    errors: list[str] = []
    if summary and not summary.get("ok"):
        errors.extend(str(error) for error in summary.get("errors", []) if str(error))
    for agent, replay in by_agent.items():
        if not isinstance(replay, dict) or replay.get("ok"):
            continue
        errors.extend(f"{agent}:{error}" for error in replay.get("errors", []) if str(error))
    return {
        "schema_version": "session_live_permission_replay_v1",
        "available": bool(summary or by_agent),
        "summary": summary,
        "by_agent": by_agent,
        "errors": errors,
        "ok": not errors,
    }


def session_live_replay(session_id: str) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    model_client = session_model_client(session_id)
    live_loop = live_loop_from_model_client_surface(model_client, result)
    live_loop_by_agent = live_loop_by_agent_from_result(result)
    has_live_loop = bool(live_loop.get("enabled") or live_loop_by_agent)
    entries, transcript_path = load_session_transcript_entries(session, result)
    transcript_agent_type = str(
        result.get("agent_type")
        or session.get("claude_transcript_summary", {}).get("agent_type")
        or ("claude-pipeline" if live_loop_by_agent else "")
    )
    transcript_validation = (
        validate_claude_transcript_entries(
            entries,
            agent_type=transcript_agent_type,
            session_id=str(session.get("session_id") or ""),
            run_id=str(session.get("run_id") or ""),
        )
        if entries
        else {
            "schema_version": "claude_transcript_validation_v0",
            "agent_type": transcript_agent_type,
            "entries_count": 0,
            "errors_count": 1 if has_live_loop else 0,
            "errors": ["transcript_empty"] if has_live_loop else [],
            "ok": not has_live_loop,
        }
    )
    tool_replay = transcript_tool_replay(entries)
    retry_candidates = dedupe_replay_records(
        [
            *live_loop_failure_records(live_loop, live_loop_by_agent),
            *tool_replay.get("retry_candidates", []),
        ],
        default_key_prefix="retry_candidate",
    )
    permission_requests = live_loop_permission_requests(live_loop, live_loop_by_agent, result)
    permission_replay = permission_replay_surface_from_result(result)
    replay_validation = {
        "schema_version": "session_live_replay_validation_v1",
        "has_live_loop": has_live_loop,
        "transcript_ok": bool(transcript_validation.get("ok")),
        "permission_replay_ok": bool(permission_replay.get("ok")),
        "failed_tool_calls_count": len(retry_candidates),
        "permission_requests_count": len(permission_requests),
        "retry_candidates_count": len(retry_candidates),
        "ok": (not has_live_loop)
        or (bool(transcript_validation.get("ok")) and bool(permission_replay.get("ok"))),
    }
    return {
        "schema_version": "session_live_replay_v1",
        "available": has_live_loop,
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "live_tool_loop": live_loop,
        "live_tool_loop_by_agent": live_loop_by_agent,
        "permission_requests": permission_requests,
        "permission_requests_count": len(permission_requests),
        "retry_candidates": retry_candidates,
        "retry_candidates_count": len(retry_candidates),
        "transcript_replay": {
            "schema_version": "session_live_transcript_replay_v1",
            "available": bool(entries),
            "transcript_path": transcript_path.as_posix() if transcript_path is not None else "",
            "entries_count": len(entries),
            "tool_use_count": tool_replay.get("tool_use_count", 0),
            "tool_result_count": tool_replay.get("tool_result_count", 0),
            "failed_tool_result_count": tool_replay.get("failed_tool_result_count", 0),
            "validation": transcript_validation,
        },
        "permission_replay": permission_replay,
        "validation": replay_validation,
        "ok": bool(replay_validation.get("ok")),
    }


def model_provider_options_from_summary(summary: dict) -> dict[str, object]:
    options: dict[str, object] = {}
    raw_options = summary.get("options", {}) if isinstance(summary.get("options"), dict) else {}
    for key, value in raw_options.items():
        if value != "[REDACTED]":
            options[str(key)] = value
    for key in ("provider", "model", "api_key_env", "timeout_seconds", "max_retries", "allow_network"):
        if key in summary:
            options[key] = summary.get(key)
    if "sdk_execution_enabled" in summary:
        options["enable_sdk_execution"] = summary.get("sdk_execution_enabled")
    return options


def model_provider_options_from_query(query: dict[str, list[str]]) -> dict[str, object]:
    options: dict[str, object] = {}
    for key in ("provider", "model", "api_key_env", "endpoint", "timeout_seconds", "max_retries", "max_tokens"):
        if key in query:
            options[key] = query.get(key, [""])[0]
    for key in ("allow_network", "enable_sdk_execution"):
        if key in query:
            options[key] = query.get(key, ["false"])[0]
    return options


def session_provider_diagnostics(
    session_id: str,
    *,
    provider_options: dict[str, object] | None = None,
    env: dict[str, str] | None = None,
    sdk_available: bool | None = None,
) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    model_client = session_model_client(session_id)
    live_adapter = (
        session.get("live_adapter")
        if isinstance(session.get("live_adapter"), dict)
        else result.get("live_adapter", {})
        if isinstance(result.get("live_adapter"), dict)
        else {}
    )
    provider_summary = (
        live_adapter.get("provider_config", {})
        if isinstance(live_adapter.get("provider_config"), dict)
        else {}
    )
    if provider_options is not None:
        source = "request"
        options = dict(provider_options)
    elif provider_summary:
        source = "session_live_adapter"
        options = model_provider_options_from_summary(provider_summary)
    else:
        source = "default"
        options = {}
    effective_sdk_available = sdk_available if sdk_available is not None else (
        True if ANTHROPIC_SDK_FACTORY_OVERRIDE is not None else None
    )
    diagnostics = build_model_provider_diagnostics(
        options,
        env=os.environ if env is None else env,
        sdk_available=effective_sdk_available,
    )
    return {
        "schema_version": "session_provider_diagnostics_v1",
        "available": is_claude_runtime_mode(str(session.get("runtime_mode") or "")),
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "runtime_mode": session.get("runtime_mode", ""),
        "source": source,
        "provider": diagnostics.get("provider", ""),
        "diagnostics": diagnostics,
        "provider_config": diagnostics.get("config", {}),
        "default_runtime": diagnostics.get("default_runtime", {}),
        "sdk_transport": diagnostics.get("sdk_transport", {}),
        "api_runtime": diagnostics.get("api_runtime", {}),
        "guardrails": diagnostics.get("guardrails", []),
        "missing_guardrails": diagnostics.get("missing_guardrails", []),
        "model_client": model_client.get("model_client", {}) if isinstance(model_client, dict) else {},
        "redacted": True,
        "routes": {
            "self": "/session/provider-diagnostics",
            "model_client": "/session/model-client",
            "bundle": "/session/claude",
        },
        "ok": bool(diagnostics.get("ok", False)),
    }


def session_summary(session_id: str) -> dict:
    session = require_session(session_id)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    knowledge = read_json_dict(Path(str(session.get("knowledge_snapshot_path") or "")))
    review = read_json_dict(Path(str(session.get("review_path") or "")))
    artifacts = session_artifacts(session_id)
    integrity = validate_session_integrity(session)
    return {
        "schema_version": "session_summary_v1",
        "session": session,
        "result": {
            "dossier_id": result.get("dossier_id", session.get("dossier_id", "")),
            "status": result.get("status", session.get("status", "UNKNOWN")),
            "blocking_failures": result.get("blocking_failures", []),
            "warnings": result.get("warnings", []),
            "events_count": len(result.get("events", [])) if isinstance(result.get("events"), list) else 0,
        },
        "knowledge": knowledge,
        "review": review,
        "beta_intake": beta_intake_summary_from_session(session),
        "claude_transcript": session.get("claude_transcript_summary", {}),
        "permission_state": session.get("permission_state_summary", {}),
        "settings_context": session.get("settings_context", result.get("settings_context", {})),
        "model_client": session_model_client(session_id),
        "live_adapter": session.get("live_adapter", result.get("live_adapter", {})),
        "settings": session_settings(session_id),
        "skill_context": session.get("skill_context", result.get("skill_context", {})),
        "command_context": session.get("command_context", result.get("command_context", {})),
        "slash_commands": session.get("slash_command_summary", {}),
        "command_history": session_command_history(session_id),
        "agent_manifest": session_agents(session_id),
        "agent_prompts": session_agent_prompts(session_id),
        "skills": session_skills(session_id),
        "handoffs": session_handoffs(session_id),
        "hooks": session_hook_summary_from_result(result),
        "tasks": session_task_summary_from_result(result),
        "tools": session_tool_summary_from_result(result),
        "artifact_lineage": result.get("artifact_lineage", {}),
        "runtime_state": session_runtime_state(session_id),
        "integrity": integrity,
        "artifacts": artifacts,
    }


def resolve_session_artifact(session: dict, *, event_id: str = "", artifact_path: str = "") -> tuple[dict, Path]:
    artifact_index = session_artifacts(str(session["session_id"]))
    artifacts = artifact_index.get("artifacts", []) if isinstance(artifact_index, dict) else []
    selected: dict | None = None
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        if event_id and artifact.get("event_id") == event_id:
            selected = artifact
            break
        if artifact_path and artifact.get("path") == artifact_path:
            selected = artifact
            break

    if selected is None:
        raise FileNotFoundError("artefact introuvable dans l'index de session")

    raw_path = Path(str(selected.get("path") or ""))
    resolved_path = raw_path.resolve()
    session_dir = Path(str(session["session_dir"])).resolve()
    try:
        resolved_path.relative_to(session_dir)
    except ValueError as exc:
        raise ValueError("artefact hors session refuse") from exc

    if not resolved_path.exists():
        raise FileNotFoundError(f"artefact introuvable sur disque: {selected.get('path', '')}")
    return selected, resolved_path


def session_artifact_content(session_id: str, *, event_id: str = "", artifact_path: str = "") -> dict:
    session = require_session(session_id)
    artifact, path = resolve_session_artifact(session, event_id=event_id, artifact_path=artifact_path)
    size = path.stat().st_size
    raw = path.read_bytes()[:ARTIFACT_PREVIEW_MAX_BYTES]
    text = raw.decode("utf-8", errors="replace")
    suffix = path.suffix.lower()
    payload = {
        "schema_version": "session_artifact_content_v1",
        "session_id": session_id,
        "artifact": artifact,
        "path": artifact.get("path", ""),
        "bytes": size,
        "truncated": size > ARTIFACT_PREVIEW_MAX_BYTES,
        "content_type": "application/json" if suffix == ".json" else "text/markdown" if suffix == ".md" else "text/plain",
        "text": text,
    }
    if suffix == ".json" and not payload["truncated"]:
        try:
            payload["json"] = json.loads(text)
        except json.JSONDecodeError:
            payload["json_error"] = "JSONDecodeError"
    return payload


def find_artifact_record(session: dict, step: str, artifact_name: str) -> dict | None:
    artifact_index = session_artifacts(str(session["session_id"]))
    for artifact in artifact_index.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        if artifact.get("step") == step and artifact.get("artifact") == artifact_name:
            return artifact
    return None


def read_indexed_artifact_json(session: dict, step: str, artifact_name: str) -> dict:
    artifact = find_artifact_record(session, step, artifact_name)
    if not artifact:
        return {}
    _, path = resolve_session_artifact(session, event_id=str(artifact.get("event_id") or ""))
    return read_json_dict(path)


def read_indexed_artifact_text(session: dict, step: str, artifact_name: str, limit: int = 16 * 1024) -> str:
    artifact = find_artifact_record(session, step, artifact_name)
    if not artifact:
        return ""
    _, path = resolve_session_artifact(session, event_id=str(artifact.get("event_id") or ""))
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def dossier_review_summary(session_id: str) -> dict:
    session = require_session(session_id)
    facts = read_indexed_artifact_json(session, "data-facts", "fiche_bien.json")
    comparables_payload = read_indexed_artifact_json(session, "comps-market", "comparables_proposes.json")
    compliance = read_indexed_artifact_json(session, "compliance-qa", "statut_sortie.json")
    report_preview = read_indexed_artifact_text(session, "redaction", "brouillon_rapport.md")
    approaches = []
    for artifact_name in [
        "calculs_approche_comparative.json",
        "calculs_approche_cout.json",
        "calculs_approche_revenu.json",
    ]:
        payload = read_indexed_artifact_json(session, "valuation-draft", artifact_name)
        if not payload:
            continue
        approaches.append(
            {
                "approach": payload.get("approach", artifact_name.replace("calculs_", "").replace(".json", "")),
                "method": payload.get("method", ""),
                "value": payload.get("value"),
                "input_count": payload.get("input_count", 0),
            }
        )

    comparables = comparables_payload.get("comparables", [])
    if not isinstance(comparables, list):
        comparables = []
    comparable_rows = [
        {
            "comparable_id": item.get("comparable_id", ""),
            "prix_vente": item.get("prix_vente"),
            "score": item.get("score"),
            "source_id": item.get("source_id", ""),
            "date_vente": item.get("date_vente", ""),
        }
        for item in comparables
        if isinstance(item, dict)
    ]
    required = [
        ("data-facts", "fiche_bien.json"),
        ("comps-market", "comparables_proposes.json"),
        ("valuation-draft", "calculs_approche_comparative.json"),
        ("valuation-draft", "calculs_approche_cout.json"),
        ("valuation-draft", "calculs_approche_revenu.json"),
        ("compliance-qa", "statut_sortie.json"),
        ("redaction", "brouillon_rapport.md"),
    ]
    missing = [f"{step}.{artifact}" for step, artifact in required if not find_artifact_record(session, step, artifact)]
    valuation_values = compliance.get("valuation_values", {}) if isinstance(compliance, dict) else {}
    return {
        "schema_version": "dossier_review_summary_v1",
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "dossier_id": facts.get("dossier_id") or compliance.get("dossier_id") or session.get("dossier_id", ""),
        "status": compliance.get("status", session.get("status", "UNKNOWN")),
        "source_fixture": facts.get("source_fixture") or compliance.get("source_fixture", ""),
        "facts": {
            "date_reference": facts.get("date_reference", ""),
            "surface": facts.get("surface"),
            "confidence": facts.get("confidence"),
            "source_ids": facts.get("source_ids", []),
            "source_ids_count": len(facts.get("source_ids", [])) if isinstance(facts.get("source_ids"), list) else 0,
        },
        "comparables": {
            "count": len(comparable_rows),
            "items": comparable_rows,
        },
        "valuation": {
            "approaches": approaches,
            "values": valuation_values,
        },
        "compliance": {
            "status": compliance.get("status", session.get("status", "UNKNOWN")),
            "blocking_failures": compliance.get("blocking_failures", []),
            "warnings": compliance.get("warnings", []),
        },
        "report": {
            "available": bool(report_preview),
            "preview": report_preview,
        },
        "coverage": {
            "required_count": len(required),
            "missing_count": len(missing),
            "missing": missing,
        },
    }


def session_package_dir(session: dict) -> Path:
    raw = str(session.get("session_dir") or "").strip()
    base = Path(raw) if raw else ROOT / ".missing-session"
    return base / V1_PACKAGE_DIRNAME


def session_package_manifest_path(session: dict) -> Path:
    return session_package_dir(session) / V1_PACKAGE_MANIFEST_FILENAME


def read_session_package_manifest(session: dict) -> dict:
    return read_json_dict(session_package_manifest_path(session))


def session_review_payload(session: dict) -> dict:
    session_dir = Path(str(session.get("session_dir") or ""))
    review_path = Path(str(session.get("review_path") or ""))
    if review_path.exists():
        try:
            review_path.resolve().relative_to(session_dir.resolve())
        except (OSError, ValueError):
            review_path = session_dir / "review.json"
    else:
        review_path = session_dir / "review.json"
    return read_json_dict(review_path)


def validate_v1_package_source(session: dict) -> dict:
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    review = session_review_payload(session)
    integrity = validate_session_integrity(session)
    errors: list[str] = []

    if not result:
        errors.append("runtime_result_missing")
    if review.get("decision") != "VALIDE":
        errors.append("internal_review_valide_required")
    if not integrity.get("ok"):
        errors.append("session_integrity_invalid")

    blocking_failures = result.get("blocking_failures", [])
    if not isinstance(blocking_failures, list):
        blocking_failures = ["blocking_failures_invalid"]
    if blocking_failures:
        errors.append("runtime_blocking_failures_present")

    artifact_dir = Path(str(result.get("artifact_dir") or ""))
    if not artifact_dir.exists() or not artifact_dir.is_dir():
        errors.append("artifact_dir_missing")
    else:
        session_dir = Path(str(session.get("session_dir") or "")).resolve()
        try:
            artifact_dir.resolve().relative_to(session_dir)
        except (OSError, ValueError):
            errors.append("artifact_dir_outside_session")

    return {
        "schema_version": "v1_package_source_gate_v1",
        "ok": not errors,
        "session_id": session.get("session_id", ""),
        "run_id": session.get("run_id", ""),
        "required_review_decision": "VALIDE",
        "actual_review_decision": review.get("decision", "A_SAISIR"),
        "integrity_ok": bool(integrity.get("ok")),
        "blocking_failures_count": len(blocking_failures),
        "artifact_dir": str(artifact_dir) if str(artifact_dir) != "." else "",
        "blocking_errors_count": len(errors),
        "blocking_errors": errors,
        "external_evaluator_responses_included": False,
    }


def session_package_summary(session_id: str) -> dict:
    session = require_session(session_id)
    manifest = read_session_package_manifest(session)
    package_dir = session_package_dir(session)
    package_files = manifest.get("package_files", {}) if manifest else {}
    files = {}
    if isinstance(package_files, dict):
        files = {
            key: {
                "path": str(package_dir / str(filename)),
                "exists": (package_dir / str(filename)).exists(),
            }
            for key, filename in package_files.items()
        }
    return {
        "schema_version": "session_package_v1",
        "status": manifest.get("status", "ABSENT"),
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "dossier_id": manifest.get("dossier_id", session.get("dossier_id", "")),
        "out_dir": str(package_dir),
        "manifest_path": str(session_package_manifest_path(session)),
        "manifest": manifest,
        "files": files,
        "gate": validate_v1_package_source(session),
        "external_evaluator_responses_included": False,
    }


def latest_session_packages_summary(limit: int = 25) -> dict:
    rows = [
        {
            "session_id": item.get("session_id", ""),
            "dossier_id": item.get("dossier_id", ""),
            "package_status": item.get("package_status", "ABSENT"),
            "package_url": item.get("package_url", ""),
        }
        for item in list_session_records(limit=limit)
        if item.get("package_generated")
    ]
    return {
        "schema_version": "session_packages_summary_v1",
        "generated_count": len(rows),
        "latest_session_id": rows[0]["session_id"] if rows else "",
        "rows": rows,
    }


def generate_v1_package_for_session(session_id: str) -> dict:
    from outils.generer_paquet_v1_pre_evaluateur import PACKAGE_FILES, generate_package_from_case

    session = require_session(session_id)
    gate = validate_v1_package_source(session)
    if not gate["ok"]:
        raise ValueError("paquet V1 refuse: " + "; ".join(gate["blocking_errors"]))

    result = read_json_dict(Path(str(session.get("result_path") or "")))
    review = session_review_payload(session)
    integrity = validate_session_integrity(session)
    out_dir = session_package_dir(session)
    outputs = generate_package_from_case(
        case=result,
        out_dir=out_dir,
        session=session,
        review=review,
        integrity=integrity,
        package_origin="validated_runtime_session",
    )
    manifest_path = out_dir / PACKAGE_FILES["manifest"]
    manifest = read_json_dict(manifest_path)
    session["v1_package_path"] = str(out_dir)
    session["v1_package_manifest_path"] = str(manifest_path)
    session["v1_package_status"] = outputs["status"]
    save_session(session)
    return {
        "schema_version": "session_package_v1",
        "status": outputs["status"],
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "dossier_id": outputs["dossier_id"],
        "out_dir": outputs["out_dir"],
        "manifest_path": str(manifest_path),
        "manifest": manifest,
        "files": outputs["files"],
        "gate": gate,
        "external_evaluator_responses_included": False,
        "package_url": f"/review/package?session_id={session_id}",
    }


def assistant_message(body: dict) -> dict:
    session = require_session(str(body.get("session_id", "")))
    message = normalize_assistant_message(str(body.get("message") or ""))
    requested_agent = str(body.get("agent") or "auto").strip() or "auto"
    context = assistant_context(session)
    agent = select_assistant_agent(message, requested_agent)
    profile = assistant_agent_profile(agent)
    response = {
        "schema_version": "assistant_message_v1",
        "message_id": uuid.uuid4().hex[:12],
        "created_at_utc": utc_now_iso(),
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "dossier_id": context["dossier_id"],
        "requested_agent": requested_agent,
        "agent": agent,
        "agent_label": profile["label"],
        "agent_config": profile["agent_config"],
        "answer": render_assistant_answer(message, agent, context),
        "context_summary": {
            "runtime_status": context["runtime_status"],
            "review_decision": context["review_decision"],
            "package_status": context["package_status"],
            "integrity_ok": context["integrity_ok"],
            "facts_count": context["facts_count"],
            "comparables_count": context["comparables_count"],
            "valuation_approaches_count": context["valuation_approaches_count"],
            "warnings_count": len(context["warnings"]),
            "blocking_failures_count": len(context["blocking_failures"]),
            "artifacts_count": context["artifacts_count"],
        },
        "citations": assistant_citations(context),
        "limits": {
            "certification_automatic": False,
            "external_evaluator_responses_included": False,
            "requires_human_validation": True,
        },
    }
    append_assistant_exchange(session, message, response)
    return response


def assistant_workbench(session_id: str) -> dict:
    session = require_session(session_id)
    context = assistant_context(session)
    transcript = assistant_transcript_summary(session)
    agents = assistant_agent_workbench_items(context)
    next_actions = assistant_next_actions(context, agents, transcript)
    return {
        "schema_version": "assistant_workbench_v1",
        "session_id": context["session_id"],
        "run_id": context["run_id"],
        "dossier_id": context["dossier_id"],
        "status": assistant_workbench_status(context),
        "runtime_status": context["runtime_status"],
        "review_decision": context["review_decision"],
        "package_status": context["package_status"],
        "integrity_ok": context["integrity_ok"],
        "supervisor": {
            "agent": "superviseur-evaluateur-ai",
            "label": ASSISTANT_AGENT_PROFILES["superviseur-evaluateur-ai"]["label"],
            "agent_config": ASSISTANT_AGENT_PROFILES["superviseur-evaluateur-ai"]["agent_config"],
            "mode": "orchestration_session_runtime",
        },
        "agents_count": len(agents),
        "agents": agents,
        "next_actions_count": len(next_actions),
        "next_actions": next_actions,
        "transcript": transcript,
        "routes": {
            "assistant_message": "/assistant/message",
            "session_summary": context["session_summary_url"],
            "dossier_review": context["dossier_review_url"],
            "package": context["package_url"],
        },
        "limits": {
            "certification_automatic": False,
            "external_evaluator_responses_included": False,
            "requires_human_validation": True,
            "llm_native_agent_loop_connected": False,
        },
    }


def normalize_assistant_message(message: str) -> str:
    value = message.strip()
    if not value:
        raise ValueError("message assistant requis")
    if len(value) > ASSISTANT_MAX_MESSAGE_CHARS:
        raise ValueError(f"message assistant trop long: max {ASSISTANT_MAX_MESSAGE_CHARS} caracteres")
    return value


def assistant_agent_profile(agent: str) -> dict:
    return ASSISTANT_AGENT_PROFILES.get(agent, ASSISTANT_AGENT_PROFILES["superviseur-evaluateur-ai"])


def assistant_context(session: dict) -> dict:
    session_id = str(session["session_id"])
    summary = session_summary(session_id)
    dossier = dossier_review_summary(session_id)
    package = session_package_summary(session_id)
    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
    agent_configs = {
        step.name: {
            "agent_config": step.agent_config,
            "skills_allowed": step.skills,
            "reads": step.reads,
            "writes": step.writes,
        }
        for step in steps
    }
    facts = dossier.get("facts", {}) if isinstance(dossier.get("facts"), dict) else {}
    comparables = dossier.get("comparables", {}) if isinstance(dossier.get("comparables"), dict) else {}
    valuation = dossier.get("valuation", {}) if isinstance(dossier.get("valuation"), dict) else {}
    compliance = dossier.get("compliance", {}) if isinstance(dossier.get("compliance"), dict) else {}
    artifacts = summary.get("artifacts", {}) if isinstance(summary.get("artifacts"), dict) else {}
    review = summary.get("review", {}) if isinstance(summary.get("review"), dict) else {}
    result = summary.get("result", {}) if isinstance(summary.get("result"), dict) else {}
    integrity = summary.get("integrity", {}) if isinstance(summary.get("integrity"), dict) else {}
    return {
        "session_id": session_id,
        "run_id": session.get("run_id", ""),
        "dossier_id": dossier.get("dossier_id") or result.get("dossier_id") or session.get("dossier_id", ""),
        "runtime_status": result.get("status", session.get("status", "UNKNOWN")),
        "review_decision": review.get("decision", session.get("review_decision", "A_SAISIR")),
        "package_status": package.get("status", "ABSENT"),
        "integrity_ok": bool(integrity.get("ok")),
        "integrity_errors": integrity.get("errors", []) if isinstance(integrity.get("errors"), list) else [],
        "facts": facts,
        "facts_count": len([key for key, value in facts.items() if value not in (None, "", [])]),
        "comparables": comparables.get("items", []) if isinstance(comparables.get("items"), list) else [],
        "comparables_count": int(comparables.get("count", 0) or 0),
        "valuation_approaches": valuation.get("approaches", []) if isinstance(valuation.get("approaches"), list) else [],
        "valuation_values": valuation.get("values", {}) if isinstance(valuation.get("values"), dict) else {},
        "valuation_approaches_count": len(valuation.get("approaches", [])) if isinstance(valuation.get("approaches"), list) else 0,
        "warnings": compliance.get("warnings", result.get("warnings", [])) if isinstance(compliance.get("warnings", []), list) else [],
        "blocking_failures": compliance.get("blocking_failures", result.get("blocking_failures", [])) if isinstance(compliance.get("blocking_failures", []), list) else [],
        "coverage": dossier.get("coverage", {}) if isinstance(dossier.get("coverage"), dict) else {},
        "report": dossier.get("report", {}) if isinstance(dossier.get("report"), dict) else {},
        "artifacts_count": int(artifacts.get("artifacts_count", 0) or 0),
        "agent_configs": agent_configs,
        "session_summary_url": f"/session/summary?session_id={session_id}",
        "dossier_review_url": f"/review/dossier?session_id={session_id}",
        "package_url": f"/review/package?session_id={session_id}",
    }


def assistant_transcript_summary(session: dict) -> dict:
    path = Path(str(session["session_dir"])) / ASSISTANT_MESSAGES_FILENAME
    messages = load_jsonl(path)
    latest = messages[-1] if messages else {}
    assistant = latest.get("assistant", {}) if isinstance(latest.get("assistant"), dict) else {}
    return {
        "schema_version": "assistant_transcript_summary_v1",
        "messages_count": len(messages),
        "path": str(path) if path.exists() else "",
        "latest_at_utc": latest.get("created_at_utc", ""),
        "latest_agent": assistant.get("agent", ""),
        "latest_agent_label": assistant.get("agent_label", ""),
    }


def assistant_agent_workbench_items(context: dict) -> list[dict]:
    artifact_index = session_artifacts(context["session_id"])
    artifacts = artifact_index.get("artifacts", []) if isinstance(artifact_index, dict) else []
    artifacts_by_step: dict[str, list[dict]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifacts_by_step.setdefault(str(artifact.get("step") or ""), []).append(artifact)

    items: list[dict] = []
    for order, step in enumerate(load_steps_from_pipeline_yaml(PIPELINE_PATH), start=1):
        profile = assistant_agent_profile(step.name)
        produced = sorted({str(item.get("artifact") or "") for item in artifacts_by_step.get(step.name, []) if item.get("artifact")})
        missing = [artifact for artifact in step.writes if artifact not in produced]
        if not produced:
            status = "A_EXECUTER"
        elif missing:
            status = "PARTIEL"
        else:
            status = "TERMINE"
        gate_status = assistant_agent_gate_status(step.name, status, context)
        items.append(
            {
                "order": order,
                "agent": step.name,
                "label": profile["label"],
                "agent_config": profile["agent_config"],
                "focus": profile["focus"],
                "status": status,
                "gate_status": gate_status,
                "reads": step.reads,
                "writes": step.writes,
                "skills_allowed": step.skills,
                "artifacts_count": len(produced),
                "produced_artifacts": produced,
                "missing_artifacts": missing,
            }
        )
    return items


def assistant_agent_gate_status(agent: str, status: str, context: dict) -> str:
    if status in {"A_EXECUTER", "PARTIEL"}:
        return "ARTEFACTS_INCOMPLETS"
    if agent == "compliance-qa" and context["blocking_failures"]:
        return "BLOCAGE_RUNTIME"
    if agent == "redaction" and context["review_decision"] not in {"PRET_REVUE", "VALIDE"}:
        return "REVUE_INTERNE_A_SAISIR"
    return "OK"


def assistant_workbench_status(context: dict) -> str:
    if not context["integrity_ok"]:
        return "INTEGRITE_A_VERIFIER"
    if context["blocking_failures"]:
        return "BLOCAGE_RUNTIME"
    if context["package_status"] == "PRET_REVUE_EVALUATEUR_AGREE":
        return "PRET_REVUE_EVALUATEUR_AGREE"
    if context["review_decision"] == "VALIDE":
        return "PRET_PAQUET_V1"
    return "ASSISTANCE_DOSSIER_ACTIVE"


def assistant_next_actions(context: dict, agents: list[dict], transcript: dict) -> list[dict]:
    actions: list[dict] = []
    if not context["integrity_ok"]:
        actions.append(
            {
                "priority": "P0",
                "agent": "compliance-qa",
                "action": "VERIFIER_INTEGRITE_SESSION",
                "reason": "; ".join(context["integrity_errors"]) or "integrite session non confirmee",
                "route": context["session_summary_url"],
            }
        )
    if context["blocking_failures"]:
        actions.append(
            {
                "priority": "P0",
                "agent": "compliance-qa",
                "action": "TRAITER_BLOCAGES_RUNTIME",
                "reason": ", ".join(context["blocking_failures"]),
                "route": context["dossier_review_url"],
            }
        )
    if int(transcript.get("messages_count", 0) or 0) == 0:
        actions.append(
            {
                "priority": "P1",
                "agent": "superviseur-evaluateur-ai",
                "action": "QUESTIONNER_DOSSIER",
                "reason": "aucune conversation assistant sur cette session",
                "route": "/assistant/message",
            }
        )
    incomplete_agents = [item for item in agents if item["status"] != "TERMINE"]
    if incomplete_agents:
        first = incomplete_agents[0]
        actions.append(
            {
                "priority": "P1",
                "agent": first["agent"],
                "action": "COMPLETER_ARTEFACTS_AGENT",
                "reason": ", ".join(first["missing_artifacts"][:4]),
                "route": context["session_summary_url"],
            }
        )
    if context["integrity_ok"] and not context["blocking_failures"]:
        if context["review_decision"] == "A_SAISIR":
            actions.append(
                {
                    "priority": "P1",
                    "agent": "superviseur-evaluateur-ai",
                    "action": "SAISIR_REVUE_INTERNE",
                    "reason": "la revue interne est requise avant le paquet V1",
                    "route": context["dossier_review_url"],
                }
            )
        elif context["review_decision"] == "VALIDE" and context["package_status"] != "PRET_REVUE_EVALUATEUR_AGREE":
            actions.append(
                {
                    "priority": "P1",
                    "agent": "redaction",
                    "action": "GENERER_PAQUET_V1",
                    "reason": "revue interne validee et paquet absent",
                    "route": context["package_url"],
                }
            )
        elif context["package_status"] == "PRET_REVUE_EVALUATEUR_AGREE":
            actions.append(
                {
                    "priority": "P2",
                    "agent": "superviseur-evaluateur-ai",
                    "action": "PREPARER_REVUE_EVALUATEUR_AGREE",
                    "reason": "paquet V1 pret sans reponses externes inventees",
                    "route": context["package_url"],
                }
            )
    return actions


def select_assistant_agent(message: str, requested_agent: str) -> str:
    if requested_agent in ASSISTANT_AGENT_PROFILES:
        return requested_agent
    if requested_agent != "auto":
        return "superviseur-evaluateur-ai"
    text = message.lower()
    if any(token in text for token in ["comparable", "comparables", "marche", "vente", "prix"]):
        return "comps-market"
    if any(token in text for token in ["valeur", "evaluation", "approche", "calcul", "ajustement", "revenu", "cout"]):
        return "valuation-draft"
    if any(token in text for token in ["conformite", "blocage", "warning", "risque", "gate", "limite", "integrite"]):
        return "compliance-qa"
    if any(token in text for token in ["rapport", "redige", "redaction", "annexe", "synthese"]):
        return "redaction"
    if any(token in text for token in ["fait", "faits", "source", "document", "surface", "date", "dossier"]):
        return "data-facts"
    return "superviseur-evaluateur-ai"


def render_assistant_answer(message: str, agent: str, context: dict) -> str:
    profile = assistant_agent_profile(agent)
    lines = [
        f"{profile['label']} - lecture du dossier {context['dossier_id'] or '-'}",
        f"Statut runtime: {context['runtime_status']} | revue interne: {context['review_decision']} | paquet: {context['package_status']}.",
    ]
    if agent == "data-facts":
        facts = context["facts"]
        lines.extend(
            [
                f"Faits disponibles: date_reference={facts.get('date_reference', '-')}, surface={facts.get('surface', '-')}, confiance={facts.get('confidence', '-')}.",
                f"Sources referencees: {facts.get('source_ids_count', 0)}.",
            ]
        )
    elif agent == "comps-market":
        comparables = context["comparables"][:4]
        lines.append(f"Comparables disponibles: {context['comparables_count']}.")
        for item in comparables:
            lines.append(
                f"- {item.get('comparable_id', '-')}: prix={item.get('prix_vente', '-')}, score={item.get('score', '-')}, source={item.get('source_id', '-')}, date={item.get('date_vente', '-')}"
            )
    elif agent == "valuation-draft":
        values = context["valuation_values"]
        if values:
            lines.append("Valeurs par approche: " + ", ".join(f"{key}={value}" for key, value in values.items()))
        for approach in context["valuation_approaches"]:
            lines.append(
                f"- {approach.get('approach', '-')}: methode={approach.get('method', '-')}, valeur={approach.get('value', '-')}, inputs={approach.get('input_count', 0)}"
            )
    elif agent == "compliance-qa":
        lines.extend(
            [
                f"Warnings: {len(context['warnings'])}; blocages: {len(context['blocking_failures'])}.",
                "Blocages: " + (", ".join(context["blocking_failures"]) if context["blocking_failures"] else "aucun"),
                "Warnings: " + (", ".join(context["warnings"]) if context["warnings"] else "aucun"),
                f"Couverture artefacts: {context['coverage'].get('required_count', 0) - context['coverage'].get('missing_count', 0)} / {context['coverage'].get('required_count', 0)}.",
            ]
        )
    elif agent == "redaction":
        report = context["report"]
        preview = str(report.get("preview") or "Rapport non disponible pour cette session.")
        lines.extend(
            [
                f"Rapport disponible: {bool(report.get('available'))}.",
                "Apercu rapport:",
                preview[:1200],
            ]
        )
    else:
        lines.extend(
            [
                f"J'ai acces a {context['artifacts_count']} artefacts, {context['comparables_count']} comparables et {context['valuation_approaches_count']} approches de valeur.",
                f"Warnings: {len(context['warnings'])}; blocages: {len(context['blocking_failures'])}.",
                "Je peux router la suite vers Agent Dossier, Agent Marche, Agent Analyse, Agent Conformite ou Agent Rapport selon ta question.",
            ]
        )
    lines.extend(
        [
            f"Question recue: {message}",
            "Limite: cette reponse est une assistance AI sourcee par les artefacts runtime; elle ne certifie pas la valeur et ne remplace pas la validation d'un evaluateur agree.",
        ]
    )
    return "\n".join(lines)


def assistant_citations(context: dict) -> list[dict]:
    return [
        {"label": "Session summary", "route": context["session_summary_url"]},
        {"label": "Dossier review", "route": context["dossier_review_url"]},
        {"label": "Package V1", "route": context["package_url"]},
        {"label": "Agent configs", "source": "integration/AGENTCONFIG-*-V0.yaml"},
    ]


def append_assistant_exchange(session: dict, message: str, response: dict) -> None:
    path = Path(str(session["session_dir"])) / ASSISTANT_MESSAGES_FILENAME
    record = {
        "schema_version": "assistant_exchange_v1",
        "created_at_utc": response["created_at_utc"],
        "session_id": session["session_id"],
        "run_id": session.get("run_id", ""),
        "user_message": message,
        "assistant": {
            "message_id": response["message_id"],
            "agent": response["agent"],
            "agent_label": response["agent_label"],
            "answer": response["answer"],
            "citations": response["citations"],
            "limits": response["limits"],
        },
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    session["assistant_messages_path"] = str(path)
    session["assistant_messages_count"] = len(load_jsonl(path))
    save_session(session)


def validate_review_payload(session: dict, body: dict) -> dict:
    decision = str(body.get("decision") or "PENDING").strip()
    reviewer = str(body.get("reviewer") or "").strip()
    notes = str(body.get("notes") or "").strip()

    if decision not in REVIEW_DECISIONS:
        raise ValueError(f"decision invalide: {decision}")
    if not reviewer:
        raise ValueError("reviewer requis")
    if decision in REVIEW_NOTES_REQUIRED and not notes:
        raise ValueError(f"notes requises pour decision {decision}")

    if decision == "VALIDE":
        integrity = validate_session_integrity(session)
        result = read_json_dict(Path(str(session.get("result_path") or "")))
        blocking_failures = result.get("blocking_failures", [])
        if not integrity["ok"]:
            raise ValueError("validation refusee: integrite session invalide")
        if blocking_failures:
            raise ValueError("validation refusee: blocages runtime presents")

    return {"decision": decision, "reviewer": reviewer, "notes": notes}


def save_review(body: dict) -> dict:
    session = require_session(str(body.get("session_id", "")))
    validated = validate_review_payload(session, body)
    review = {
        "schema_version": "session_review_v1",
        "session_id": session["session_id"],
        "run_id": session["run_id"],
        "decision": validated["decision"],
        "reviewer": validated["reviewer"],
        "notes": validated["notes"],
        "created_at_utc": utc_now_iso(),
    }
    review_path = Path(session["session_dir"]) / "review.json"
    write_json(review_path, review)
    session["review_path"] = str(review_path)
    session["review_decision"] = review["decision"]
    save_session(session)
    return {"session": session, "review": review}


def resume_session(session_id: str) -> dict:
    session = require_session(session_id)
    validation = validate_session_integrity(session)
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    resume = {
        "schema_version": "session_resume_v1",
        "session_id": session["session_id"],
        "run_id": session["run_id"],
        "status": "RESUME_READY" if validation["ok"] else "RESUME_BLOCKED",
        "claude_transcript_path": session.get("claude_transcript_path", ""),
        "claude_transcript": session.get("claude_transcript_summary", {}),
        "permission_state_path": session.get("permission_state_path", ""),
        "permission_state": session.get("permission_state_summary", {}),
        "settings_context": session.get("settings_context", {}),
        "model_client": session_model_client(str(session["session_id"])),
        "live_replay": session_live_replay(str(session["session_id"])),
        "live_adapter": session.get("live_adapter", result.get("live_adapter", {})),
        "settings": session_settings(str(session["session_id"])),
        "skill_context": session.get("skill_context", {}),
        "command_context": session.get("command_context", {}),
        "slash_commands": session.get("slash_command_summary", {}),
        "command_history": session_command_history(str(session["session_id"])),
        "agent_manifest": session_agents(str(session["session_id"])),
        "agent_prompts": session_agent_prompts(str(session["session_id"])),
        "skills": session_skills(str(session["session_id"])),
        "handoffs": session_handoffs(str(session["session_id"])),
        "hooks": session_hook_summary_from_result(result),
        "tasks": session_task_summary_from_result(result),
        "tools": session_tool_summary_from_result(result),
        "artifact_lineage": result.get("artifact_lineage", {}) if isinstance(result.get("artifact_lineage"), dict) else {},
        "runtime_state": session_runtime_state(str(session["session_id"])),
        "integrity": validation,
        "resumed_at_utc": utc_now_iso(),
    }
    resume_path = Path(session["session_dir"]) / "resume.json"
    write_json(resume_path, resume)
    session["resume_path"] = str(resume_path)
    session["resume_status"] = resume["status"]
    save_session(session)
    return {"session": session, "resume": resume}


def validate_session_integrity(session: dict) -> dict:
    errors: list[str] = []
    result = read_json_dict(Path(str(session.get("result_path") or "")))
    events = load_jsonl(Path(session.get("events_path", "")))
    event_ids: set[str] = set()
    artifact_events = 0
    hook_invocations = hook_invocations_from_result(result)
    hook_summary = result.get("hook_summary", {}) if isinstance(result.get("hook_summary"), dict) else {}
    hook_validation: dict[str, object] = {}
    task_states = task_states_from_result(result)
    task_summary = summarize_task_states_for_session(task_states, result)
    task_validation: dict[str, object] = {}
    artifact_lineage = result.get("artifact_lineage", {}) if isinstance(result.get("artifact_lineage"), dict) else {}
    artifact_lineage_validation: dict[str, object] = {}
    runtime_conversation_states = runtime_state_by_agent(result, "conversation_state_by_agent", "conversation_state")
    runtime_context_states = runtime_state_by_agent(result, "context_state_by_agent", "context_state")
    runtime_token_budgets = runtime_state_by_agent(result, "token_budget_by_agent", "token_budget")
    runtime_usage_accounting = runtime_state_by_agent(result, "usage_accounting_by_agent", "usage_accounting")
    runtime_state_validation: dict[str, object] = {}
    agent_manifest_validation: dict[str, object] = {}
    agent_manifest: dict[str, object] = {}
    agent_prompts_surface: dict[str, object] = {}
    agent_prompts_validation: dict[str, object] = {}
    model_client_surface: dict[str, object] = {}
    skills_surface: dict[str, object] = {}
    skills_validation: dict[str, object] = {}
    tools_by_agent = tools_by_agent_from_result(result)
    tool_validation: dict[str, object] = {}
    claude_transcript_path_value = str(session.get("claude_transcript_path") or "")
    claude_transcript_entries = load_jsonl(Path(claude_transcript_path_value)) if claude_transcript_path_value else []
    claude_transcript_validation: dict[str, object] = {}
    permission_state_path_value = str(session.get("permission_state_path") or "")
    permission_state = load_permission_state(Path(permission_state_path_value)) if permission_state_path_value else {}
    permission_state_validation: dict[str, object] = {}
    settings_context = session.get("settings_context", {})
    settings_context_validation: dict[str, object] = {}
    settings_surface: dict[str, object] = {}
    session_settings_validation: dict[str, object] = {}
    skill_context = session.get("skill_context", {})
    skill_context_validation: dict[str, object] = {}
    handoffs_surface: dict[str, object] = {}
    handoffs_validation: dict[str, object] = {}
    command_context = session.get("command_context", {})
    command_context_validation: dict[str, object] = {}
    slash_command_summary = session.get("slash_command_summary", {})
    slash_command_records: list[dict] = []
    slash_command_history_validation: dict[str, object] = {}
    claude_action_summary = session.get("claude_action_summary", {})
    claude_action_history_validation: dict[str, object] = {}
    claude_action_records: list[dict] = []

    if not events:
        errors.append("events_missing")

    for event in events:
        for field in ("event_id", "session_id", "run_id", "sequence", "event"):
            if not event.get(field):
                errors.append(f"event_missing_{field}")
        if event.get("session_id") != session.get("session_id"):
            errors.append(f"event_session_mismatch:{event.get('event_id', '')}")
        if event.get("run_id") != session.get("run_id"):
            errors.append(f"event_run_mismatch:{event.get('event_id', '')}")
        event_id = str(event.get("event_id", ""))
        if event_id in event_ids:
            errors.append(f"event_duplicate:{event_id}")
        event_ids.add(event_id)
        if event.get("event") == "artifact_written":
            artifact_events += 1
            artifact_path = Path(str(event.get("artifact_path") or event.get("path") or ""))
            if not artifact_path.exists():
                errors.append(f"artifact_missing:{artifact_path.as_posix()}")

    artifact_index = session_artifacts(str(session["session_id"])) if session.get("artifact_index_path") else {}
    indexed_artifacts = artifact_index.get("artifacts", []) if isinstance(artifact_index, dict) else []
    for artifact in indexed_artifacts:
        if artifact.get("event_id") not in event_ids:
            errors.append(f"artifact_event_missing:{artifact.get('path', '')}")
        if not artifact.get("exists"):
            errors.append(f"artifact_index_missing:{artifact.get('path', '')}")

    artifact_lineage_validation = validate_artifact_lineage(
        artifact_lineage,
        artifact_index=artifact_index,
        task_summary=task_summary,
    )
    if artifact_lineage:
        errors.extend(
            f"artifact_lineage_{error}"
            for error in artifact_lineage_validation.get("errors", [])
        )

    if claude_transcript_path_value:
        claude_transcript_path = Path(claude_transcript_path_value)
        if not claude_transcript_path.exists() or not claude_transcript_path.is_file():
            errors.append("claude_transcript_missing")
        else:
            try:
                claude_transcript_path.resolve().relative_to(Path(str(session["session_dir"])).resolve())
            except ValueError:
                errors.append("claude_transcript_outside_session")
        if not claude_transcript_entries:
            errors.append("claude_transcript_empty")
        for expected_sequence, entry in enumerate(claude_transcript_entries, start=1):
            for field in ("schema_version", "kind", "sequence", "session_id", "run_id", "agent_type", "role"):
                if not entry.get(field):
                    errors.append(f"claude_transcript_missing_{field}")
            if entry.get("schema_version") != "claude_transcript_entry_v0":
                errors.append(f"claude_transcript_schema_invalid:{expected_sequence}")
            if entry.get("kind") != "message":
                errors.append(f"claude_transcript_kind_invalid:{expected_sequence}")
            if entry.get("sequence") != expected_sequence:
                errors.append(f"claude_transcript_sequence_invalid:{expected_sequence}")
            if entry.get("session_id") != session.get("session_id"):
                errors.append(f"claude_transcript_session_mismatch:{expected_sequence}")
            if entry.get("run_id") != session.get("run_id"):
                errors.append(f"claude_transcript_run_mismatch:{expected_sequence}")
        claude_transcript_validation = validate_claude_transcript_entries(
            claude_transcript_entries,
            agent_type=str(session.get("result", {}).get("agent_type") or session.get("claude_transcript_summary", {}).get("agent_type") or ""),
            session_id=str(session.get("session_id") or ""),
            run_id=str(session.get("run_id") or ""),
        )
        errors.extend(f"claude_transcript_{error}" for error in claude_transcript_validation.get("errors", []))

    if permission_state_path_value:
        permission_state_path = Path(permission_state_path_value)
        if not permission_state_path.exists() or not permission_state_path.is_file():
            errors.append("permission_state_missing")
        else:
            try:
                permission_state_path.resolve().relative_to(Path(str(session["session_dir"])).resolve())
            except ValueError:
                errors.append("permission_state_outside_session")
        if not permission_state:
            errors.append("permission_state_empty")
        else:
            validation_errors = validate_permission_state(permission_state)
            permission_state_validation = {
                "schema_version": "claude_permission_state_validation_v0",
                "errors": validation_errors,
                "ok": not validation_errors,
            }
            errors.extend(f"permission_state_{error}" for error in validation_errors)
            if permission_state.get("session_id") != session.get("session_id"):
                errors.append("permission_state_session_mismatch")
            if permission_state.get("run_id") != session.get("run_id"):
                errors.append("permission_state_run_mismatch")

    if isinstance(settings_context, dict) and settings_context:
        settings_context_validation = validate_settings_context(settings_context)
        errors.extend(f"settings_context_{error}" for error in settings_context_validation.get("errors", []))
        settings_surface = session_settings(str(session["session_id"]))
        session_settings_validation = (
            settings_surface.get("validation", {})
            if isinstance(settings_surface.get("validation"), dict)
            else {}
        )
        errors.extend(f"session_settings_{error}" for error in session_settings_validation.get("errors", []))

    if isinstance(skill_context, dict) and skill_context:
        skill_context_validation = validate_skill_context(skill_context)
        errors.extend(f"skill_context_{error}" for error in skill_context_validation.get("errors", []))

    if isinstance(command_context, dict) and command_context:
        command_context_validation = validate_command_context(command_context)
        errors.extend(f"command_context_{error}" for error in command_context_validation.get("errors", []))

    if hook_invocations:
        hook_validation = validate_hook_telemetry(hook_invocations, hook_summary)
        errors.extend(f"hook_telemetry_{error}" for error in hook_validation.get("errors", []))

    if task_states:
        task_validation = validate_task_telemetry(task_states, task_summary)
        errors.extend(f"task_telemetry_{error}" for error in task_validation.get("errors", []))

    if runtime_conversation_states or runtime_context_states or runtime_token_budgets or runtime_usage_accounting:
        runtime_state_validation = validate_runtime_state(
            runtime_conversation_states,
            runtime_context_states,
            runtime_token_budgets,
            runtime_usage_accounting,
        )
        errors.extend(f"runtime_state_{error}" for error in runtime_state_validation.get("errors", []))

    if is_claude_runtime_mode(str(session.get("runtime_mode") or "")):
        agent_manifest = session_agents(str(session["session_id"]))
        agent_manifest_validation = (
            agent_manifest.get("validation", {})
            if isinstance(agent_manifest.get("validation"), dict)
            else {}
        )
        errors.extend(f"agent_manifest_{error}" for error in agent_manifest_validation.get("errors", []))
        agent_prompts_surface = session_agent_prompts(str(session["session_id"]))
        agent_prompts_validation = (
            agent_prompts_surface.get("validation", {})
            if isinstance(agent_prompts_surface.get("validation"), dict)
            else {}
        )
        errors.extend(f"agent_prompts_{error}" for error in agent_prompts_validation.get("errors", []))
        model_client_surface = session_model_client(str(session["session_id"]))
        if is_claude_live_runtime_mode(str(session.get("runtime_mode") or "")):
            if not model_client_surface.get("available"):
                errors.append("model_client_missing")
            if not model_client_surface.get("ok"):
                errors.append("model_client_not_ok")
        skills_surface = session_skills(str(session["session_id"]))
        skills_validation = (
            skills_surface.get("validation", {})
            if isinstance(skills_surface.get("validation"), dict)
            else {}
        )
        errors.extend(f"session_skills_{error}" for error in skills_validation.get("errors", []))
        handoffs_surface = session_handoffs(str(session["session_id"]))
        handoffs_validation = (
            handoffs_surface.get("validation", {})
            if isinstance(handoffs_surface.get("validation"), dict)
            else {}
        )
        errors.extend(f"session_handoffs_{error}" for error in handoffs_validation.get("errors", []))

    if tools_by_agent:
        tool_validation = validate_session_tool_registry(tools_by_agent)
        errors.extend(f"tool_registry_{error}" for error in tool_validation.get("errors", []))

    if (isinstance(slash_command_summary, dict) and slash_command_summary) or session.get("slash_command_history_path"):
        slash_command_history_validation, slash_command_records = validate_slash_command_history(
            session,
            slash_command_summary if isinstance(slash_command_summary, dict) else {},
        )
        errors.extend(
            f"slash_command_history_{error}"
            for error in slash_command_history_validation.get("errors", [])
        )

    if (isinstance(claude_action_summary, dict) and claude_action_summary) or session.get("claude_action_history_path"):
        claude_action_history_validation, claude_action_records = validate_claude_action_history(
            session,
            claude_action_summary if isinstance(claude_action_summary, dict) else {},
        )
        errors.extend(
            f"claude_action_history_{error}"
            for error in claude_action_history_validation.get("errors", [])
        )

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "events_count": len(events),
        "artifact_events_count": artifact_events,
        "indexed_artifacts_count": len(indexed_artifacts),
        "claude_transcript_entries_count": len(claude_transcript_entries),
        "claude_transcript_validation": claude_transcript_validation,
        "permission_state_validation": permission_state_validation,
        "settings_context_validation": settings_context_validation,
        "session_settings_sources_count": int(settings_surface.get("all_sources_count", 0) or 0)
        if settings_surface
        else 0,
        "session_settings_validation": session_settings_validation,
        "skill_context_validation": skill_context_validation,
        "command_context_validation": command_context_validation,
        "hook_invocations_count": len(hook_invocations),
        "hook_validation": hook_validation,
        "task_states_count": len(task_states),
        "task_validation": task_validation,
        "artifact_lineage_artifacts_count": int(artifact_lineage.get("artifacts_count", 0) or 0)
        if artifact_lineage
        else 0,
        "artifact_lineage_validation": artifact_lineage_validation,
        "runtime_state_agents_count": len(
            set(runtime_conversation_states)
            | set(runtime_context_states)
            | set(runtime_token_budgets)
            | set(runtime_usage_accounting)
        ),
        "runtime_state_validation": runtime_state_validation,
        "agent_manifest_agents_count": int(agent_manifest.get("all_agents_count", 0) or 0)
        if agent_manifest
        else 0,
        "agent_manifest_validation": agent_manifest_validation,
        "agent_prompts_count": int(agent_prompts_surface.get("all_prompts_count", 0) or 0)
        if agent_prompts_surface
        else 0,
        "agent_prompts_validation": agent_prompts_validation,
        "model_client_enabled": bool(
            model_client_surface.get("model_client", {}).get("enabled", False)
        )
        if model_client_surface and isinstance(model_client_surface.get("model_client"), dict)
        else False,
        "model_client_ok": bool(model_client_surface.get("ok", True)) if model_client_surface else True,
        "session_skills_count": int(skills_surface.get("all_skills_count", 0) or 0)
        if skills_surface
        else 0,
        "session_skills_validation": skills_validation,
        "session_handoffs_count": int(handoffs_surface.get("all_handoffs_count", 0) or 0)
        if handoffs_surface
        else 0,
        "session_handoffs_validation": handoffs_validation,
        "tools_count": len(unique_session_tool_names(tools_by_agent)),
        "tool_validation": tool_validation,
        "slash_command_records_count": len(slash_command_records),
        "slash_command_history_validation": slash_command_history_validation,
        "claude_action_records_count": len(claude_action_records),
        "claude_action_history_validation": claude_action_history_validation,
    }


def require_session(session_id: str) -> dict:
    if not session_id:
        raise ValueError("session_id requis")
    session = load_session(session_id)
    if session is None:
        raise ValueError(f"session introuvable: {session_id}")
    return session


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists() or not path.is_file():
        return []
    items: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def load_jsonl_lenient(path: Path) -> tuple[list[dict], list[str]]:
    if not path.exists() or not path.is_file():
        return [], []
    items: list[dict] = []
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"json_invalid:{line_number}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"record_not_object:{line_number}")
            continue
        items.append(payload)
    return items, errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def access_audit_path() -> Path:
    return SESSIONS_DIR / ACCESS_AUDIT_FILENAME


def append_access_audit(entry: dict) -> None:
    path = access_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = dict(entry)
    record["timestamp_utc"] = utc_now_iso()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class RuntimeApiHandler(BaseHTTPRequestHandler):
    server_version = "EvaluationImmobiliereRuntime/0.1"

    def do_GET(self) -> None:
        try:
            self._handle_get()
        except FileNotFoundError as exc:
            self._send_json(404, {"error": str(exc)})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self._send_json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def _handle_get(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_file(PRODUCT_UI_PATH, "text/html; charset=utf-8")
            return
        if parsed.path in {"/product", "/product/ui", "/app"}:
            self._send_file(PRODUCT_UI_PATH, "text/html; charset=utf-8")
            return
        if parsed.path == "/ui":
            self._send_file(UI_PATH, "text/html; charset=utf-8")
            return
        if parsed.path == "/product/summary":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, product_summary())
            return
        if parsed.path == "/beta/readiness":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, beta_ea_readiness())
            return
        if parsed.path == "/beta/terms":
            self._send_json(200, beta_terms())
            return
        if parsed.path == "/app/state":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, app_state(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path in {"/ops/ui", "/ops/cockpit"}:
            self._send_file(OPS_UI_PATH, "text/html; charset=utf-8")
            return
        if parsed.path in {"/review/ui", "/evaluateur", "/evaluateur/revue"}:
            self._send_file(EVALUATOR_UI_PATH, "text/html; charset=utf-8")
            return
        if parsed.path == "/auth/client.js":
            self._send_file(AUTH_CLIENT_PATH, "text/javascript; charset=utf-8")
            return
        if parsed.path == "/auth/status":
            context = self._auth_context()
            role = str(context["role"])
            self._send_json(
                200,
                {
                    "schema_version": "runtime_auth_status_v1",
                    "enabled": bool(context["enabled"]),
                    "authorized": bool(context["authorized"]),
                    "role": role,
                    "reason": context["reason"],
                    "permissions": sorted(ROLE_PERMISSIONS.get(role, set())),
                    "roles": sorted(ROLE_PERMISSIONS),
                },
            )
            return
        if parsed.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if parsed.path == "/fixtures":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, {"fixtures": list_fixtures()})
            return
        if parsed.path == "/sessions":
            if not self._require_permission("runtime_read"):
                return
            limit = bounded_limit(parse_qs(parsed.query).get("limit", ["50"])[0])
            sessions = list_session_records(limit=limit)
            self._send_json(200, {"schema_version": "runtime_sessions_v1", "sessions_count": len(sessions), "sessions": sessions})
            return
        if parsed.path == "/session":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, require_session(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/session/summary":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, session_summary(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/session/claude":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_claude_bundle(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    hook_event=query.get("hook_event", [""])[0],
                    task_status=query.get("task_status", query.get("status", [""]))[0],
                    permission=query.get("permission", [""])[0],
                    tool=query.get("tool", [""])[0],
                    skill=query.get("skill", [""])[0],
                    loaded_from=query.get("loaded_from", [""])[0],
                    settings_source=query.get("settings_source", query.get("source", [""]))[0],
                    settings_key=query.get("settings_key", query.get("key", [""]))[0],
                    handoff_direction=query.get("handoff_direction", query.get("direction", [""]))[0],
                    handoff_from_agent=query.get("handoff_from_agent", query.get("from_agent", [""]))[0],
                    handoff_to_agent=query.get("handoff_to_agent", query.get("to_agent", [""]))[0],
                    handoff_status=query.get("handoff_status", [""])[0],
                    command_history_command=query.get("command_history_command", query.get("command_name", [""]))[0],
                    command_history_status=query.get("command_history_status", [""])[0],
                    command_history_ok=query.get("command_history_ok", [""])[0],
                    command_history_offset=_optional_int(query.get("command_history_offset", [0])[0], default=0) or 0,
                    command_history_limit=bounded_limit(query.get("command_history_limit", ["10"])[0]),
                    role=query.get("role", [""])[0],
                    block_type=query.get("block_type", [""])[0],
                    offset=_optional_int(query.get("offset", [0])[0], default=0) or 0,
                    limit=bounded_limit(query.get("limit", ["20"])[0]),
                    lineage_terminal_only=truthy_query(
                        query.get("lineage_terminal_only", query.get("terminal_only", ["false"]))[0]
                    ),
                ),
            )
            return
        if parsed.path == "/session/artifact-lineage":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_artifact_lineage(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    terminal_only=truthy_query(query.get("terminal_only", query.get("terminal", ["false"]))[0]),
                ),
            )
            return
        if parsed.path == "/session/runtime-state":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_runtime_state(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/agents":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_agents(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/agent-prompts":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_agent_prompts(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/model-client":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(200, session_model_client(query.get("session_id", [""])[0]))
            return
        if parsed.path == "/session/live-replay":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(200, session_live_replay(query.get("session_id", [""])[0]))
            return
        if parsed.path == "/session/provider-diagnostics":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            provider_options = model_provider_options_from_query(query)
            self._send_json(
                200,
                session_provider_diagnostics(
                    query.get("session_id", [""])[0],
                    provider_options=provider_options if provider_options else None,
                ),
            )
            return
        if parsed.path == "/session/skills":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_skills(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    skill=query.get("skill", [""])[0],
                    loaded_from=query.get("loaded_from", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/settings":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_settings(
                    query.get("session_id", [""])[0],
                    source=query.get("source", query.get("settings_source", [""]))[0],
                    key=query.get("key", query.get("settings_key", [""]))[0],
                ),
            )
            return
        if parsed.path == "/session/handoffs":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_handoffs(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    from_agent=query.get("from_agent", query.get("handoff_from_agent", [""]))[0],
                    to_agent=query.get("to_agent", query.get("handoff_to_agent", [""]))[0],
                    direction=query.get("direction", query.get("handoff_direction", [""]))[0],
                    status=query.get("status", query.get("handoff_status", [""]))[0],
                ),
            )
            return
        if parsed.path == "/session/claude/action/snapshot":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_claude_action_snapshot(
                    query.get("session_id", [""])[0],
                    action_id=query.get("action_id", [""])[0],
                    snapshot_path=query.get("snapshot_path", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/commands":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, session_commands(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/session/command-history":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_command_history(
                    query.get("session_id", [""])[0],
                    command=query.get("command", query.get("command_name", [""]))[0],
                    status=query.get("status", [""])[0],
                    ok=query.get("ok", [""])[0],
                    offset=_optional_int(query.get("offset", [0])[0], default=0) or 0,
                    limit=bounded_limit(query.get("limit", ["20"])[0]),
                ),
            )
            return
        if parsed.path == "/session/hooks":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_hooks(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    hook_event=query.get("hook_event", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/tasks":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_tasks(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    status=query.get("status", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/tools":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_tools(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    permission=query.get("permission", [""])[0],
                    tool=query.get("tool", [""])[0],
                ),
            )
            return
        if parsed.path == "/session/transcript":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_transcript(
                    query.get("session_id", [""])[0],
                    agent=query.get("agent", [""])[0],
                    role=query.get("role", [""])[0],
                    block_type=query.get("block_type", [""])[0],
                    offset=_optional_int(query.get("offset", [0])[0], default=0) or 0,
                    limit=bounded_limit(query.get("limit", ["50"])[0]),
                ),
            )
            return
        if parsed.path == "/session/permissions":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, session_permissions(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/status":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, session_status(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/artifacts":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, session_artifacts(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/artifact":
            if not self._require_permission("runtime_read"):
                return
            query = parse_qs(parsed.query)
            self._send_json(
                200,
                session_artifact_content(
                    query.get("session_id", [""])[0],
                    event_id=query.get("event_id", [""])[0],
                    artifact_path=query.get("path", [""])[0],
                ),
            )
            return
        if parsed.path == "/review/dossier":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, dossier_review_summary(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/review/workbench":
            if not self._require_permission("runtime_read"):
                return
            limit = bounded_limit(parse_qs(parsed.query).get("limit", ["50"])[0])
            self._send_json(200, review_workbench_summary(limit=limit))
            return
        if parsed.path == "/review/campaign":
            if not self._require_permission("runtime_read"):
                return
            limit = bounded_limit(parse_qs(parsed.query).get("limit", ["100"])[0], default=100, maximum=250)
            self._send_json(200, review_campaign_summary(limit=limit))
            return
        if parsed.path == "/review/package":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, session_package_summary(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/knowledge/immobilier":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, knowledge_immobilier_summary(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/assistant/workbench":
            if not self._require_permission("runtime_read"):
                return
            self._send_json(200, assistant_workbench(parse_qs(parsed.query).get("session_id", [""])[0]))
            return
        if parsed.path == "/ops":
            if not self._require_permission("ops_read"):
                return
            self._send_json(200, ops_summary())
            return
        if parsed.path == "/ops/snapshot":
            if not self._require_permission("ops_read"):
                return
            self._send_json(200, ops_observability_snapshot())
            return
        if parsed.path.startswith("/ops/"):
            if not self._require_permission("ops_read"):
                return
            self._send_ops_report(parsed.path.removeprefix("/ops/"))
            return
        if parsed.path == "/stream":
            if not self._require_permission("runtime_read"):
                return
            self._stream_events(parse_qs(parsed.query).get("session_id", [None])[0])
            return
        self._send_json(404, {"error": "route introuvable"})

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key, X-Runtime-Role")
        self.end_headers()
        self._write_access_audit(204)

    def do_POST(self) -> None:
        try:
            body = self._read_json_body()
            if self.path == "/session":
                if not self._require_permission("runtime_write"):
                    return
                session = create_session(strict_mode=bool(body.get("strict_mode", True)))
                self._send_json(201, session)
                return
            if self.path == "/start":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, start_runtime(body))
                return
            if self.path == "/product/demo":
                if not self._require_permission("runtime_write"):
                    return
                fixture = str(body.get("fixture") or "case_nominal.json")
                self._send_json(200, start_runtime({"fixture": fixture, "strict_mode": True}))
                return
            if self.path == "/app/demo":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, app_start_demo(body))
                return
            if self.path == "/beta/intake":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, beta_start_dossier(body))
                return
            if self.path == "/resume":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, resume_session(str(body.get("session_id", ""))))
                return
            if self.path == "/session/command":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, execute_session_slash_command(body))
                return
            if self.path == "/session/claude/action":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, session_claude_action(body))
                return
            if self.path == "/session/permissions":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, update_session_permissions(body))
                return
            if self.path == "/review":
                if not self._require_permission("review_write"):
                    return
                self._send_json(200, save_review(body))
                return
            if self.path == "/review/package":
                if not self._require_permission("review_write"):
                    return
                self._send_json(200, generate_v1_package_for_session(str(body.get("session_id", ""))))
                return
            if self.path == "/app/review/validate":
                if not self._require_permission("review_write"):
                    return
                self._send_json(200, app_validate_review(body))
                return
            if self.path == "/app/package":
                if not self._require_permission("review_write"):
                    return
                self._send_json(200, app_generate_package(body))
                return
            if self.path == "/assistant/message":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, assistant_message(body))
                return
            if self.path == "/app/message":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, app_send_message(body))
                return
            if self.path == "/ops/pre-response-run":
                if not self._require_permission("ops_write"):
                    return
                self._send_json(200, run_pre_response_ops(dry_run=bool(body.get("dry_run", False))))
                return
            self._send_json(404, {"error": "route introuvable"})
        except FileNotFoundError as exc:
            self._send_json(404, {"error": str(exc)})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except RuntimeError as exc:
            if exc.__class__.__name__ == "PreResponseLockError":
                self._send_json(409, {"error": str(exc), "code": "PRE_RESPONSE_RUN_LOCKED"})
                return
            self._send_json(500, {"error": f"{type(exc).__name__}: {exc}"})
        except Exception as exc:  # pragma: no cover - defensive API boundary
            self._send_json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _send_json(self, status: int, payload: dict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self._send_cors_headers()
        self.end_headers()
        self._write_access_audit(status)
        self.wfile.write(encoded)

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self._send_json(404, {"error": f"fichier introuvable: {path.name}"})
            return
        encoded = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self._send_cors_headers()
        self.end_headers()
        self._write_access_audit(200)
        self.wfile.write(encoded)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")

    def _auth_context(self) -> dict[str, object]:
        expected = os.environ.get("EVAL_RUNTIME_API_TOKEN", "")
        role = self.headers.get("X-Runtime-Role", "local_dev").strip() or "local_dev"
        if not expected:
            return {"enabled": False, "authorized": True, "role": "local_dev", "reason": "auth_disabled"}

        auth_header = self.headers.get("Authorization", "")
        token = self.headers.get("X-API-Key", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()

        if not token:
            return {"enabled": True, "authorized": False, "role": role, "reason": "token_missing"}
        if token != expected:
            return {"enabled": True, "authorized": False, "role": role, "reason": "token_invalid"}
        if role not in ROLE_PERMISSIONS:
            return {"enabled": True, "authorized": False, "role": role, "reason": "role_invalid"}
        return {"enabled": True, "authorized": True, "role": role, "reason": "ok"}

    def _require_permission(self, permission: str) -> bool:
        context = self._auth_context()
        if not context["authorized"]:
            self._send_json(401, {"error": "authentification requise", "code": context["reason"]})
            return False
        if not context["enabled"]:
            return True

        role = str(context["role"])
        if permission not in ROLE_PERMISSIONS.get(role, set()):
            self._send_json(403, {"error": "permission refusee", "code": "RBAC_FORBIDDEN", "role": role, "permission": permission})
            return False
        return True

    def _write_access_audit(self, status: int) -> None:
        context = self._auth_context()
        append_access_audit(
            {
                "method": self.command,
                "path": self.path.split("?", 1)[0],
                "status": status,
                "auth_enabled": bool(context["enabled"]),
                "role": context["role"],
                "reason": context["reason"],
                "client": self.client_address[0] if self.client_address else "",
            }
        )

    def _send_ops_report(self, name: str) -> None:
        try:
            if name in OPS_JSON_REPORTS:
                self._send_json(200, load_ops_json(name))
                return
            if name in OPS_CSV_REPORTS:
                self._send_json(200, load_ops_csv(name))
                return
        except KeyError:
            pass
        self._send_json(404, {"error": f"rapport ops inconnu: {name}"})

    def _stream_events(self, session_id: str | None) -> None:
        if not session_id:
            self._send_json(400, {"error": "session_id requis"})
            return
        session = load_session(session_id)
        if session is None or "events_path" not in session:
            self._send_json(404, {"error": "session introuvable ou non demarree"})
            return

        events_path = Path(session["events_path"])
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self._send_cors_headers()
        self.end_headers()

        for line in events_path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            event_name = event.get("event", "message")
            self.wfile.write(f"event: {event_name}\n".encode("utf-8"))
            self.wfile.write(f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8"))


def run_server(host: str = "127.0.0.1", port: int = 8787) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), RuntimeApiHandler)
    print(f"Runtime API v0: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
