from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
import uuid

from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml, safe_path_id


ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT / "tests" / "fixtures"
PIPELINE_PATH = ROOT / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
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
ASSISTANT_MAX_MESSAGE_CHARS = 4000
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
        "next_action": next_action,
        "session_summary_url": f"/session/summary?session_id={session_id}",
        "dossier_review_url": f"/review/dossier?session_id={session_id}",
        "package_status": package.get("status", "ABSENT"),
        "package_origin": package.get("package_origin", ""),
        "package_generated": bool(package),
        "package_url": f"/review/package?session_id={session_id}",
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
            "session_summary": "/session/summary",
            "artifact_content": "/artifact",
            "dossier_review": "/review/dossier",
            "ops_snapshot": "/ops/snapshot",
        },
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

    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
    engine = RuntimeEngine(steps=steps, strict_mode=bool(session.get("strict_mode", True)))
    result = engine.run_case_data(
        case,
        session_dir / "artifacts",
        source_fixture=source_fixture,
        case_stem=case_key,
        case_subdir=True,
    )

    result_path = session_dir / "result.json"
    events_path = session_dir / "events.jsonl"
    artifact_index_path = session_dir / "artifact_index.json"
    knowledge_snapshot_path = session_dir / "knowledge_snapshot.json"

    enriched_events = enrich_events(result["events"], session)
    result["events"] = enriched_events
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
            "result_path": str(result_path),
            "events_path": str(events_path),
            "artifact_dir": result["artifact_dir"],
            "artifact_index_path": str(artifact_index_path),
            "knowledge_snapshot_path": str(knowledge_snapshot_path),
        }
    )
    save_session(session)
    return {"session": session, "result": result}


def enrich_events(events: list[dict], session: dict) -> list[dict]:
    enriched: list[dict] = []
    session_id = str(session["session_id"])
    run_id = str(session["run_id"])
    for sequence, event in enumerate(events, start=1):
        item = dict(event)
        item["event_id"] = item.get("event_id") or f"{run_id}_{sequence:04d}"
        item["sequence"] = sequence
        item["session_id"] = session_id
        item["run_id"] = run_id
        item.setdefault("step", "session")
        item.setdefault("artifact", "")
        if item.get("path"):
            item.setdefault("artifact_path", item["path"])
        enriched.append(item)
    return enriched


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
    resume = {
        "schema_version": "session_resume_v1",
        "session_id": session["session_id"],
        "run_id": session["run_id"],
        "status": "RESUME_READY" if validation["ok"] else "RESUME_BLOCKED",
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
    events = load_jsonl(Path(session.get("events_path", "")))
    event_ids: set[str] = set()
    artifact_events = 0

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

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "events_count": len(events),
        "artifact_events_count": artifact_events,
        "indexed_artifacts_count": len(indexed_artifacts),
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
            if self.path == "/resume":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, resume_session(str(body.get("session_id", ""))))
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
            if self.path == "/assistant/message":
                if not self._require_permission("runtime_write"):
                    return
                self._send_json(200, assistant_message(body))
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
