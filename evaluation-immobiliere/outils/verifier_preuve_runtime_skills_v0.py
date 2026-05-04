from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeStep, load_steps_from_pipeline_yaml
from engine.skills import load_agent_config_skills

RUNTIME_DIR_DEFAULT = PROJECT_ROOT / "tests" / "runtime"
SUMMARY_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_summary.json"
PIPELINE_DEFAULT = PROJECT_ROOT / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
INTEGRATION_DIR_DEFAULT = PROJECT_ROOT / "integration"
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "skills_runtime_evidence.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "SKILLS-RUNTIME-EVIDENCE-V0.md"
REVIEW_STOP_STATUS = "A_REVOIR"
REVIEW_STOP_STEP = "compliance-qa"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    events: list[dict] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            events.append({"event": "json_error", "line": line_number, "error": str(exc)})
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def validate_runtime_skill_evidence(
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    *,
    summary_path: Path | None = None,
    pipeline_path: Path = PIPELINE_DEFAULT,
    integration_dir: Path = INTEGRATION_DIR_DEFAULT,
) -> dict[str, object]:
    summary_path = summary_path or runtime_dir / "runtime_summary.json"
    errors: list[str] = []
    warnings: list[str] = []
    cases_report: list[dict[str, object]] = []
    artifacts_checked = 0
    step_events_checked = 0

    if not summary_path.exists():
        errors.append(f"{display_path(summary_path)}: runtime_summary introuvable")
        return build_report(runtime_dir, summary_path, 0, 0, 0, 0, [], errors, warnings)

    summary = load_json(summary_path)
    if not isinstance(summary, list):
        errors.append(f"{display_path(summary_path)}: runtime_summary doit etre une liste")
        return build_report(runtime_dir, summary_path, 0, 0, 0, 0, [], errors, warnings)

    steps = load_steps_from_pipeline_yaml(pipeline_path)
    expected_by_step = expected_skill_context_by_step(steps, integration_dir)
    expected_order = [step.name for step in steps]
    summary_audit_paths: set[Path] = set()

    for case in summary:
        if not isinstance(case, dict):
            errors.append(f"{display_path(summary_path)}: entree runtime non objet")
            continue
        case_errors: list[str] = []
        case_name = case_name_from_summary(case)
        status = str(case.get("status") or "UNKNOWN")

        validate_summary_skills(case, expected_by_step, case_errors)

        audit_path = resolve_runtime_path(case.get("audit_log"))
        if audit_path is None:
            case_errors.append("audit_log manquant dans le resume")
            events: list[dict] = []
        elif not audit_path.exists():
            case_errors.append(f"audit_log introuvable: {display_path(audit_path)}")
            events = []
        else:
            summary_audit_paths.add(audit_path.resolve())
            events = load_jsonl(audit_path)

        step_start_events = [event for event in events if event.get("event") == "step_start"]
        executed_steps = [str(event.get("step") or "") for event in step_start_events]
        step_events_checked += len(step_start_events)
        validate_executed_step_order(executed_steps, expected_order, status, case_errors)

        for event in step_start_events:
            step_name = str(event.get("step") or "")
            expected = expected_by_step.get(step_name)
            if expected is None:
                case_errors.append(f"{step_name}: step_start inconnu")
                continue
            if event.get("agent_config") != expected["agent_config"]:
                case_errors.append(f"{step_name}: agent_config audit divergent")
            if event.get("skills_allowed") != expected["skills_allowed"]:
                case_errors.append(f"{step_name}: skills_allowed audit divergents")

        event_artifacts_checked = validate_artifact_skill_context(events, expected_by_step, case_errors)
        artifacts_checked += event_artifacts_checked

        cases_report.append(
            {
                "case": case_name,
                "dossier_id": case.get("dossier_id", ""),
                "status": status,
                "audit_log": display_path(audit_path) if audit_path else "",
                "executed_steps": executed_steps,
                "artifacts_checked": event_artifacts_checked,
                "ok": not case_errors,
                "errors": case_errors,
            }
        )
        errors.extend(f"{case_name}: {error}" for error in case_errors)

    audit_paths = {path.resolve() for path in runtime_dir.glob("*/*.audit.jsonl")}
    extra_audits = sorted(audit_paths - summary_audit_paths)
    missing_audits = sorted(summary_audit_paths - audit_paths)
    for path in extra_audits:
        errors.append(f"{display_path(path)}: audit_log non reference dans runtime_summary")
    for path in missing_audits:
        errors.append(f"{display_path(path)}: audit_log reference hors repertoire runtime")

    return build_report(
        runtime_dir,
        summary_path,
        len(summary),
        len(summary_audit_paths),
        step_events_checked,
        artifacts_checked,
        cases_report,
        errors,
        warnings,
    )


def expected_skill_context_by_step(steps: list[RuntimeStep], integration_dir: Path) -> dict[str, dict[str, object]]:
    expected: dict[str, dict[str, object]] = {}
    for step in steps:
        config_path = integration_dir / str(step.agent_config or "")
        config_skills = load_agent_config_skills(config_path)
        expected[step.name] = {
            "agent_config": step.agent_config,
            "skills_allowed": config_skills,
        }
    return expected


def validate_summary_skills(case: dict, expected_by_step: dict[str, dict[str, object]], errors: list[str]) -> None:
    skills_by_agent = case.get("skills_by_agent")
    if not isinstance(skills_by_agent, dict):
        errors.append("skills_by_agent manquant dans runtime_summary")
        return
    for step_name, expected in sorted(expected_by_step.items()):
        if skills_by_agent.get(step_name) != expected["skills_allowed"]:
            errors.append(f"{step_name}: skills_by_agent divergent du AgentConfig")


def validate_executed_step_order(executed_steps: list[str], expected_order: list[str], status: str, errors: list[str]) -> None:
    if not executed_steps:
        errors.append("aucun step_start dans audit_log")
        return
    expected_prefix = expected_order[: len(executed_steps)]
    if executed_steps != expected_prefix:
        errors.append(f"ordre steps execute divergent (audit={executed_steps}, attendu_prefix={expected_prefix})")
    if status == REVIEW_STOP_STATUS:
        if not executed_steps or executed_steps[-1] != REVIEW_STOP_STEP:
            errors.append(f"statut {REVIEW_STOP_STATUS}: dernier step attendu {REVIEW_STOP_STEP}")
        if len(executed_steps) >= len(expected_order):
            errors.append(f"statut {REVIEW_STOP_STATUS}: redaction ne devrait pas s'executer")
    elif executed_steps != expected_order:
        errors.append(f"statut {status}: tous les steps doivent s'executer")


def validate_artifact_skill_context(
    events: list[dict],
    expected_by_step: dict[str, dict[str, object]],
    errors: list[str],
) -> int:
    checked = 0
    for event in events:
        if event.get("event") != "artifact_written":
            continue
        step_name = str(event.get("step") or "")
        expected = expected_by_step.get(step_name)
        artifact_path = resolve_runtime_path(event.get("path"))
        if expected is None or artifact_path is None:
            continue
        if not artifact_path.exists():
            errors.append(f"{step_name}: artefact introuvable {event.get('path')}")
            continue
        if artifact_path.suffix == ".json":
            payload = load_json(artifact_path)
            checked += 1
            if not isinstance(payload, dict):
                errors.append(f"{step_name}: artefact JSON non objet {display_path(artifact_path)}")
                continue
            if payload.get("agent_config") != expected["agent_config"]:
                errors.append(f"{step_name}: agent_config artefact divergent {artifact_path.name}")
            if payload.get("agent_skills_allowed") != expected["skills_allowed"]:
                errors.append(f"{step_name}: agent_skills_allowed artefact divergent {artifact_path.name}")
        elif artifact_path.suffix == ".md":
            text = artifact_path.read_text(encoding="utf-8")
            checked += 1
            if "## agent_config" not in text or "## agent_skills_allowed" not in text:
                errors.append(f"{step_name}: contexte skills absent de l'artefact Markdown {artifact_path.name}")
    return checked


def resolve_runtime_path(value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = [REPO_ROOT / path, PROJECT_ROOT / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def case_name_from_summary(case: dict) -> str:
    artifact_dir = str(case.get("artifact_dir") or "")
    if artifact_dir:
        return Path(artifact_dir).name
    return str(case.get("dossier_id") or "unknown")


def build_report(
    runtime_dir: Path,
    summary_path: Path,
    cases_count: int,
    audit_logs_checked: int,
    step_events_checked: int,
    artifacts_checked: int,
    cases: list[dict[str, object]],
    errors: list[str],
    warnings: list[str],
) -> dict[str, object]:
    return {
        "schema_version": "runtime_skills_evidence_v0",
        "ok": not errors,
        "runtime_dir": display_path(runtime_dir),
        "summary_path": display_path(summary_path),
        "cases_count": cases_count,
        "audit_logs_checked": audit_logs_checked,
        "step_events_checked": step_events_checked,
        "artifacts_checked": artifacts_checked,
        "cases": cases,
        "errors": errors,
        "warnings": warnings,
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Skills runtime evidence v0",
        "",
        f"- Statut: **{'OK' if report.get('ok') else 'A_CORRIGER'}**",
        f"- Cas verifies: **{report.get('cases_count', 0)}**",
        f"- Audit logs verifies: **{report.get('audit_logs_checked', 0)}**",
        f"- Step events verifies: **{report.get('step_events_checked', 0)}**",
        f"- Artefacts verifies: **{report.get('artifacts_checked', 0)}**",
        "",
        "## Cas",
        "",
        "| Cas | Dossier | Statut | Steps executes | Artefacts verifies | Statut preuve |",
        "|---|---|---|---|---:|---|",
    ]
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(
            "| {case} | {dossier} | {status} | {steps} | {artifacts} | {proof} |".format(
                case=case.get("case", "-"),
                dossier=case.get("dossier_id", "-"),
                status=case.get("status", "-"),
                steps=", ".join(case.get("executed_steps", [])) if isinstance(case.get("executed_steps"), list) else "-",
                artifacts=case.get("artifacts_checked", 0),
                proof="OK" if case.get("ok") else "A_CORRIGER",
            )
        )

    lines.extend(["", "## Erreurs", ""])
    errors = report.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- Aucune erreur.")
    return "\n".join(lines).rstrip() + "\n"


def write_reports(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie la preuve runtime des skills par audit log et artefacts.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--pipeline", type=Path, default=PIPELINE_DEFAULT)
    parser.add_argument("--integration-dir", type=Path, default=INTEGRATION_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = validate_runtime_skill_evidence(
        args.runtime_dir,
        summary_path=args.summary,
        pipeline_path=args.pipeline,
        integration_dir=args.integration_dir,
    )
    write_reports(report, args.json_out, args.markdown_out)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Preuve runtime skills JSON: {args.json_out}")
    print(f"Preuve runtime skills Markdown: {args.markdown_out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
