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
    "doctor": "ops_doctor_report.json",
}
OPS_CSV_REPORTS = {
    "review_queue": "FILE-REVUE-HUMAINE-V0.csv",
}
ACCESS_AUDIT_FILENAME = "access_audit.jsonl"
ARTIFACT_PREVIEW_MAX_BYTES = 64 * 1024
REVIEW_DECISIONS = {"PRET_REVUE", "A_CORRIGER", "VALIDE", "REJETE"}
REVIEW_NOTES_REQUIRED = {"A_CORRIGER", "VALIDE", "REJETE"}
ROLE_PERMISSIONS = {
    "evaluator": {"runtime_read", "runtime_write", "review_write"},
    "ops": {"runtime_read", "ops_read", "ops_write"},
    "supervisor": {"runtime_read", "runtime_write", "review_write", "ops_read", "ops_write"},
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


def recent_sessions(limit: int = 8) -> list[dict]:
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
        sessions.append(
            {
                "session_id": session.get("session_id", ""),
                "run_id": session.get("run_id", ""),
                "dossier_id": session.get("dossier_id", ""),
                "status": session.get("status", "CREATED"),
                "updated_at_utc": session.get("updated_at_utc", ""),
                "review_decision": session.get("review_decision", ""),
                "artifact_index_path": session.get("artifact_index_path", ""),
            }
        )
    sessions.sort(key=lambda item: str(item.get("updated_at_utc") or ""), reverse=True)
    return sessions[:limit]


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
        "ops": ops,
        "package": {
            "status": package_manifest.get("status", "UNKNOWN"),
            "dossier_id": package_manifest.get("dossier_id", ""),
            "runtime_status": package_manifest.get("runtime_status", "UNKNOWN"),
            "artifacts_count": package_manifest.get("artifacts_count", 0),
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
            "session_summary": "/session/summary",
            "artifact_content": "/artifact",
            "dossier_review": "/review/dossier",
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
    schemas = load_ops_json("schema_validation", runtime_dir)
    package_gate = load_ops_json("package_gate", runtime_dir)
    doctor = load_ops_json("doctor", runtime_dir)
    review_queue = load_ops_csv("review_queue", runtime_dir)
    return {
        "readiness_status": readiness.get("status", "ABSENT"),
        "delta_status": delta.get("status", "ABSENT"),
        "handoff_status": handoff.get("status", "ABSENT"),
        "schema_validation_status": schemas.get("status", "ABSENT"),
        "package_gate_status": package_gate.get("status", "ABSENT"),
        "doctor_status": doctor.get("status", "ABSENT"),
        "quality_cases_count": quality.get("cases_count", 0),
        "runtime_fingerprint_sha256": readiness.get("runtime_fingerprint_sha256", ""),
        "registry_runs_count": registry.get("runs_count", 0),
        "review_queue_items": review_queue.get("rows_count", 0),
        "reports": {
            key: str(runtime_dir / filename)
            for key, filename in {**OPS_JSON_REPORTS, **OPS_CSV_REPORTS}.items()
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
    return {
        "schema_version": "session_knowledge_snapshot_v1",
        "session_id": session["session_id"],
        "run_id": session["run_id"],
        "dossier_id": result.get("dossier_id", ""),
        "status": result.get("status", "UNKNOWN"),
        "blocking_failures": result.get("blocking_failures", []),
        "warnings": result.get("warnings", []),
        "events_count": len(result.get("events", [])),
        "artifacts_count": artifact_index.get("artifacts_count", 0),
        "latest_event_id": result.get("events", [{}])[-1].get("event_id", "") if result.get("events") else "",
    }


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
    if not path.exists():
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
        if parsed.path == "/ops":
            if not self._require_permission("ops_read"):
                return
            self._send_json(200, ops_summary())
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
