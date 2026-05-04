from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
ATELIER_DIR = PROJECT_ROOT / "atelier"
RUNTIME_DIR = PROJECT_ROOT / "tests" / "runtime"

MANIFEST_DEFAULT = ATELIER_DIR / "RELEASE-CANDIDATE-MANIFEST-V1.json"
HOMOLOGATION_REPORT_DEFAULT = RUNTIME_DIR / "homologation_metier_report.json"
EXTERNAL_REVIEWS_REPORT_DEFAULT = RUNTIME_DIR / "revues_evaluateurs_externes_report.json"
CLOSURE_REPORT_DEFAULT = RUNTIME_DIR / "fermeture_ecarts_evaluateurs_report.json"
WORKFLOW_DEFAULT = REPO_ROOT / ".github" / "workflows" / "validation.yml"
ROLLBACK_RUNBOOK_DEFAULT = ATELIER_DIR / "RUNBOOK-ROLLBACK-V1.md"
REPORT_JSON_DEFAULT = RUNTIME_DIR / "release_candidate_report.json"
REPORT_MD_DEFAULT = RUNTIME_DIR / "RELEASE-CANDIDATE-EVIDENCE-V1.md"
STAGING_REPORT_DEFAULT = ATELIER_DIR / "RAPPORT-DRESS-REHEARSAL-STAGING-V1.md"
ROLLBACK_REPORT_DEFAULT = ATELIER_DIR / "RAPPORT-ROLLBACK-REHEARSAL-V1.md"

VALID_SCHEMA = "release_candidate_manifest_v1"
REQUIRED_ROLLBACK_SIGNALS = [
    "RUNBOOK ROLLBACK V1",
    "Procedure applicative",
    "Reexecuter CI complet",
    "tag sain precedent",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def normalize_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_repo_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def resolve_git_commit(ref: str = "HEAD") -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"
    return result.stdout.strip()


def scenario_statuses(payload: dict[str, Any], section: str) -> list[str]:
    scenarios = as_list(as_dict(payload.get(section)).get("scenarios"))
    return [str(item.get("status") or "UNKNOWN") for item in scenarios if isinstance(item, dict)]


def validate_release_candidate(
    manifest_path: Path = MANIFEST_DEFAULT,
    *,
    homologation_report_path: Path = HOMOLOGATION_REPORT_DEFAULT,
    external_reviews_report_path: Path = EXTERNAL_REVIEWS_REPORT_DEFAULT,
    closure_report_path: Path = CLOSURE_REPORT_DEFAULT,
    workflow_path: Path = WORKFLOW_DEFAULT,
    rollback_runbook_path: Path = ROLLBACK_RUNBOOK_DEFAULT,
    strict: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not manifest_path.exists():
        errors.append(f"manifest release candidate absent: {normalize_path(manifest_path)}")
        manifest: dict[str, Any] = {}
    else:
        manifest = read_json_dict(manifest_path)

    if manifest.get("schema_version") != VALID_SCHEMA:
        errors.append(f"schema_version invalide: {manifest.get('schema_version') or 'absent'}")
    if not str(manifest.get("release_candidate_id") or "").strip():
        errors.append("release_candidate_id absent")

    commit_ref = str(manifest.get("commit_ref") or "HEAD").strip()
    resolved_commit = resolve_git_commit(commit_ref or "HEAD")
    commit_resolved = resolved_commit != "UNKNOWN"
    if not commit_resolved:
        errors.append(f"commit_ref non resolu: {commit_ref or 'HEAD'}")
    reported_commit = commit_ref if commit_ref == "HEAD" else resolved_commit

    missing_reports = []
    for raw in as_list(manifest.get("required_reports")):
        if not isinstance(raw, str):
            continue
        if not resolve_repo_path(raw).exists():
            missing_reports.append(raw)
    for item in missing_reports:
        errors.append(f"rapport requis absent: {item}")

    missing_artifacts = []
    for raw in as_list(manifest.get("required_artifacts")):
        if not isinstance(raw, str):
            continue
        if not resolve_repo_path(raw).exists():
            missing_artifacts.append(raw)
    for item in missing_artifacts:
        errors.append(f"artefact requis absent: {item}")

    homologation = read_json_dict(homologation_report_path)
    external = read_json_dict(external_reviews_report_path)
    closure = read_json_dict(closure_report_path)

    if homologation.get("ok") is not True:
        errors.append("homologation metier non OK")
    if homologation.get("production_decision") != "GO_PROD_PREPARATION":
        errors.append(f"production_decision invalide: {homologation.get('production_decision') or 'UNKNOWN'}")
    if external.get("ok") is not True:
        errors.append("revues evaluateurs externes non OK")
    if external.get("decision") not in {"GO_CONDITIONNEL_ECARTS_EVALUATEURS", "GO_REVUES_EVALUATEURS_EXTERNES"}:
        errors.append(f"decision revues externes invalide: {external.get('decision') or 'UNKNOWN'}")
    if closure.get("ok") is not True or closure.get("decision") != "GO_PROD_PREPARATION":
        errors.append(f"fermeture ecarts invalide: {closure.get('decision') or 'UNKNOWN'}")
    if as_list(closure.get("missing_gap_ids")):
        errors.append("fermeture ecarts incomplete")
    if int(closure.get("external_gaps_to_close", 0) or 0) != int(closure.get("closures_count", 0) or 0):
        errors.append("nombre fermetures divergent du nombre ecarts externes")

    workflow_text = read_text(workflow_path)
    for gate in as_list(manifest.get("required_ci_gates")):
        if not isinstance(gate, str):
            continue
        signal = gate.split()[0]
        if signal not in workflow_text:
            errors.append(f"gate CI absent: {gate}")

    rollback_text = read_text(rollback_runbook_path)
    for signal in REQUIRED_ROLLBACK_SIGNALS:
        if signal not in rollback_text:
            errors.append(f"rollback runbook incomplet: signal absent `{signal}`")

    staging_statuses = scenario_statuses(manifest, "staging_rehearsal")
    rollback_statuses = scenario_statuses(manifest, "rollback_rehearsal")
    if not staging_statuses or any(status != "SIMULE_OK" for status in staging_statuses):
        errors.append("dress rehearsal staging incomplet")
    if not rollback_statuses or any(status != "SIMULE_OK" for status in rollback_statuses):
        errors.append("rollback rehearsal incomplet")

    if strict and str(manifest.get("target_environment") or "") != "staging":
        errors.append("target_environment doit etre staging en mode strict")

    decision = "PRET_GO_LIVE_CONTROLE" if not errors else "NO_GO_RELEASE_CANDIDATE"
    return {
        "schema_version": "release_candidate_report_v1",
        "ok": not errors,
        "strict": strict,
        "decision": decision,
        "release_candidate_id": manifest.get("release_candidate_id", "UNKNOWN"),
        "commit_ref": commit_ref or "HEAD",
        "resolved_commit": reported_commit,
        "commit_resolved": commit_resolved,
        "target_environment": manifest.get("target_environment", "UNKNOWN"),
        "go_live_status": manifest.get("go_live_status", "UNKNOWN"),
        "manifest_path": normalize_path(manifest_path),
        "homologation_decision": homologation.get("production_decision", "UNKNOWN"),
        "external_reviews_decision": external.get("decision", "UNKNOWN"),
        "closure_decision": closure.get("decision", "UNKNOWN"),
        "required_reports_count": len(as_list(manifest.get("required_reports"))),
        "required_artifacts_count": len(as_list(manifest.get("required_artifacts"))),
        "missing_reports": missing_reports,
        "missing_artifacts": missing_artifacts,
        "staging_scenarios_count": len(staging_statuses),
        "rollback_scenarios_count": len(rollback_statuses),
        "errors": errors,
        "warnings": warnings,
        "manifest": manifest,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Release Candidate Evidence V1",
        "",
        "## Synthese",
        "",
        f"- OK gate strict: **{str(report.get('ok')).lower()}**",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- Release candidate: **{report.get('release_candidate_id', 'UNKNOWN')}**",
        f"- Commit: `{report.get('resolved_commit', 'UNKNOWN')}`",
        f"- Environnement cible: **{report.get('target_environment', 'UNKNOWN')}**",
        f"- Go live: **{report.get('go_live_status', 'UNKNOWN')}**",
        f"- Homologation: **{report.get('homologation_decision', 'UNKNOWN')}**",
        f"- Fermeture ecarts: **{report.get('closure_decision', 'UNKNOWN')}**",
        f"- Scenarios staging: **{report.get('staging_scenarios_count', 0)}**",
        f"- Scenarios rollback: **{report.get('rollback_scenarios_count', 0)}**",
        f"- Erreurs: **{len(as_list(report.get('errors')))}**",
        "",
        "## Gates",
        "",
        "| Gate | Statut |",
        "|---|---|",
        f"| Homologation metier | {report.get('homologation_decision', 'UNKNOWN')} |",
        f"| Revues externes | {report.get('external_reviews_decision', 'UNKNOWN')} |",
        f"| Fermeture ecarts | {report.get('closure_decision', 'UNKNOWN')} |",
        f"| Rollback rehearsal | {'OK' if report.get('rollback_scenarios_count', 0) else 'A_COMPLETER'} |",
        "",
        "## Erreurs",
        "",
    ]
    lines.extend(render_list(report.get("errors")))
    return "\n".join(lines).rstrip() + "\n"


def build_staging_markdown(report: dict[str, Any]) -> str:
    manifest = as_dict(report.get("manifest"))
    scenarios = as_list(as_dict(manifest.get("staging_rehearsal")).get("scenarios"))
    lines = [
        "# Rapport dress rehearsal staging V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Decision",
        "",
        f"- Release candidate: **{report.get('release_candidate_id', 'UNKNOWN')}**",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- Commit: `{report.get('resolved_commit', 'UNKNOWN')}`",
        "- Go live: **A_CONTROLER_APRES_STAGING**",
        "",
        "## Scenarios staging",
        "",
        "| Scenario | Statut | Evidence |",
        "|---|---|---|",
    ]
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        lines.append(
            "| {name} | {status} | {evidence} |".format(
                name=scenario.get("name", "-"),
                status=scenario.get("status", "-"),
                evidence=scenario.get("evidence", "-"),
            )
        )
    lines.extend(
        [
            "",
            "## Conditions avant go live",
            "",
            "- Rejouer cette repetition sur le commit exact tague release-candidate.",
            "- Confirmer CI verte et artefacts generes propres.",
            "- Confirmer support et rollback disponibles pendant la fenetre controlee.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_rollback_markdown(report: dict[str, Any]) -> str:
    manifest = as_dict(report.get("manifest"))
    scenarios = as_list(as_dict(manifest.get("rollback_rehearsal")).get("scenarios"))
    lines = [
        "# Rapport rollback rehearsal V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Decision",
        "",
        f"- Release candidate: **{report.get('release_candidate_id', 'UNKNOWN')}**",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        "- Rollback: **SIMULE_OK**",
        "",
        "## Scenarios rollback",
        "",
        "| Scenario | Statut | Evidence |",
        "|---|---|---|",
    ]
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        lines.append(
            "| {name} | {status} | {evidence} |".format(
                name=scenario.get("name", "-"),
                status=scenario.get("status", "-"),
                evidence=scenario.get("evidence", "-"),
            )
        )
    lines.extend(
        [
            "",
            "## Conditions de sortie rollback",
            "",
            "- CI complet relance sur le tag restaure.",
            "- Gates metier et ops relances avant reprise promotion.",
            "- Incident documente avant nouvelle tentative de go live.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_list(items: object) -> list[str]:
    values = [str(item) for item in as_list(items) if str(item)]
    if not values:
        return ["- Aucune."]
    return [f"- {item}" for item in values]


def write_outputs(
    report: dict[str, Any],
    json_out: Path,
    markdown_out: Path,
    staging_out: Path,
    rollback_out: Path,
) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    staging_out.parent.mkdir(parents=True, exist_ok=True)
    rollback_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")
    staging_out.write_text(build_staging_markdown(report), encoding="utf-8")
    rollback_out.write_text(build_rollback_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie le release-candidate et la repetition staging.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--homologation-report", type=Path, default=HOMOLOGATION_REPORT_DEFAULT)
    parser.add_argument("--external-reviews-report", type=Path, default=EXTERNAL_REVIEWS_REPORT_DEFAULT)
    parser.add_argument("--closure-report", type=Path, default=CLOSURE_REPORT_DEFAULT)
    parser.add_argument("--workflow", type=Path, default=WORKFLOW_DEFAULT)
    parser.add_argument("--rollback-runbook", type=Path, default=ROLLBACK_RUNBOOK_DEFAULT)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report-out", type=Path, default=REPORT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD_DEFAULT)
    parser.add_argument("--staging-out", type=Path, default=STAGING_REPORT_DEFAULT)
    parser.add_argument("--rollback-out", type=Path, default=ROLLBACK_REPORT_DEFAULT)
    args = parser.parse_args()

    report = validate_release_candidate(
        args.manifest,
        homologation_report_path=args.homologation_report,
        external_reviews_report_path=args.external_reviews_report,
        closure_report_path=args.closure_report,
        workflow_path=args.workflow,
        rollback_runbook_path=args.rollback_runbook,
        strict=args.strict,
    )
    write_outputs(report, args.report_out, args.markdown_out, args.staging_out, args.rollback_out)
    print(json.dumps({key: value for key, value in report.items() if key != "manifest"}, ensure_ascii=False, indent=2))
    print(f"Rapport release candidate JSON: {args.report_out}")
    print(f"Preuve release candidate Markdown: {args.markdown_out}")
    print(f"Rapport dress rehearsal staging: {args.staging_out}")
    print(f"Rapport rollback rehearsal: {args.rollback_out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
