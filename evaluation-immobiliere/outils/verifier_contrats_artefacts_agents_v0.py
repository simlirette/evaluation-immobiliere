from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeStep, load_steps_from_pipeline_yaml


CONTRACT_PATH_DEFAULT = PROJECT_ROOT / "integration" / "AGENT-ARTIFACT-CONTRACTS-V0.json"
PIPELINE_PATH_DEFAULT = PROJECT_ROOT / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
RUNTIME_DIR_DEFAULT = PROJECT_ROOT / "tests" / "runtime"
REPORT_JSON_NAME = "agent_artifact_contracts_evidence.json"
REPORT_MD_NAME = "AGENT-ARTIFACT-CONTRACTS-EVIDENCE-V0.md"
STATUS_A_REVOIR = "A_REVOIR"
STATUS_ALLOWED = {"BROUILLON", "A_REVOIR", "PRET_REVISION_FINALE"}
COMMON_JSON_FIELDS = ["dossier_id", "step", "artifact", "source_fixture", "agent_skills_allowed", "agent_config"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def normalize_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def contract_agents_by_type(contract: dict) -> dict[str, dict]:
    agents = contract.get("agents", [])
    if not isinstance(agents, list):
        return {}
    return {str(agent.get("agent_type")): agent for agent in agents if isinstance(agent, dict)}


def artifact_contracts_by_name(agent_contract: dict) -> dict[str, dict]:
    artifacts = agent_contract.get("artifacts", [])
    if not isinstance(artifacts, list):
        return {}
    return {str(artifact.get("name")): artifact for artifact in artifacts if isinstance(artifact, dict)}


def resolve_case_dir(case: dict, runtime_dir: Path) -> Path:
    raw = str(case.get("artifact_dir") or "").strip()
    if raw:
        path = Path(raw)
        if path.name:
            candidate = runtime_dir / path.name
            if candidate.exists() or runtime_dir.exists():
                return candidate
        if path.is_absolute() or path.exists():
            return path
    return runtime_dir / str(case.get("dossier_id") or "unknown")


def resolve_artifact_path(raw_path: str, case_dir: Path, agent_type: str, artifact_name: str) -> Path:
    fallback = case_dir / f"{agent_type}.{artifact_name}"
    if not raw_path:
        return fallback

    path = Path(raw_path)
    if path.name:
        candidate = case_dir / path.name
        if candidate.exists() or case_dir.exists():
            return candidate
    if path.is_absolute() or path.exists():
        return path
    return fallback


def executed_steps(case: dict) -> list[str]:
    steps: list[str] = []
    for event in as_list(case.get("events")):
        if isinstance(event, dict) and event.get("event") == "step_start":
            step = str(event.get("step") or "")
            if step and step not in steps:
                steps.append(step)
    return steps


def artifact_events(case: dict) -> dict[tuple[str, str], dict]:
    events: dict[tuple[str, str], dict] = {}
    for event in as_list(case.get("events")):
        if not isinstance(event, dict) or event.get("event") != "artifact_written":
            continue
        step = str(event.get("step") or "")
        artifact = str(event.get("artifact") or "")
        if step and artifact:
            events[(step, artifact)] = event
    return events


def step_start_events(case: dict) -> dict[str, dict]:
    starts: dict[str, dict] = {}
    for event in as_list(case.get("events")):
        if isinstance(event, dict) and event.get("event") == "step_start":
            step = str(event.get("step") or "")
            if step:
                starts[step] = event
    return starts


def validate_contract_shape(contract: dict, steps: list[RuntimeStep], errors: list[str]) -> None:
    if contract.get("schema_version") != "agent_artifact_contracts_v0":
        errors.append("contrat: schema_version inattendu")

    agents = contract_agents_by_type(contract)
    for step in steps:
        agent_contract = agents.get(step.name)
        if not agent_contract:
            errors.append(f"pipeline: agent {step.name} absent du contrat")
            continue
        if agent_contract.get("agent_config") != step.agent_config:
            errors.append(
                f"pipeline: agent_config divergent pour {step.name}: "
                f"{agent_contract.get('agent_config')} != {step.agent_config}"
            )
        contracted = set(artifact_contracts_by_name(agent_contract))
        expected = set(step.writes)
        missing = sorted(expected - contracted)
        extra = sorted(contracted - expected)
        if missing:
            errors.append(f"pipeline: artefacts manquants au contrat pour {step.name}: {missing}")
        if extra:
            errors.append(f"pipeline: artefacts extra hors pipeline pour {step.name}: {extra}")


def validate_agent_artifact_contracts(
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    *,
    contract_path: Path = CONTRACT_PATH_DEFAULT,
    pipeline_path: Path = PIPELINE_PATH_DEFAULT,
) -> dict:
    contract = load_json(contract_path)
    steps = load_steps_from_pipeline_yaml(pipeline_path)
    summary = load_json(runtime_dir / "runtime_summary.json")
    if not isinstance(summary, list):
        summary = []

    errors: list[str] = []
    warnings: list[str] = []
    validate_contract_shape(contract, steps, errors)

    agents = contract_agents_by_type(contract)
    cases_report: list[dict] = []
    artifacts_checked = 0
    artifacts_expected = 0
    artifacts_skipped = 0

    for case in summary:
        if not isinstance(case, dict):
            continue
        case_errors: list[str] = []
        case_warnings: list[str] = []
        case_dir = resolve_case_dir(case, runtime_dir)
        starts = step_start_events(case)
        written = artifact_events(case)
        case_steps = executed_steps(case)
        case_artifacts_checked = 0
        case_artifacts_expected = 0
        case_artifacts_skipped = 0

        for step in steps:
            agent_contract = agents.get(step.name)
            if not agent_contract:
                continue
            if step.name not in case_steps:
                artifacts_skipped += len(step.writes)
                case_artifacts_skipped += len(step.writes)
                continue

            start_event = starts.get(step.name, {})
            if start_event.get("agent_config") != step.agent_config:
                case_errors.append(f"{step.name}: agent_config audit divergent")

            artifact_contracts = artifact_contracts_by_name(agent_contract)
            for artifact_name in step.writes:
                case_artifacts_expected += 1
                artifacts_expected += 1
                artifact_contract = artifact_contracts.get(artifact_name, {})
                event = written.get((step.name, artifact_name), {})
                artifact_path = resolve_artifact_path(str(event.get("path") or ""), case_dir, step.name, artifact_name)

                if not artifact_path.exists():
                    case_errors.append(
                        f"{step.name}.{artifact_name}: artefact attendu introuvable ({normalize_path(artifact_path)})"
                    )
                    continue

                artifact_errors = validate_artifact(
                    path=artifact_path,
                    artifact_contract=artifact_contract,
                    agent_type=step.name,
                    agent_config=step.agent_config,
                    case=case,
                    case_dir=case_dir,
                )
                case_artifacts_checked += 1
                artifacts_checked += 1
                case_errors.extend(f"{step.name}.{artifact_name}: {error}" for error in artifact_errors)

        cases_report.append(
            {
                "dossier_id": case.get("dossier_id", ""),
                "status": case.get("status", "UNKNOWN"),
                "artifact_dir": normalize_path(case_dir),
                "executed_steps": case_steps,
                "artifacts_expected": case_artifacts_expected,
                "artifacts_checked": case_artifacts_checked,
                "artifacts_skipped": case_artifacts_skipped,
                "ok": not case_errors,
                "errors": case_errors,
                "warnings": case_warnings,
            }
        )
        errors.extend(f"{case.get('dossier_id', '-')}: {error}" for error in case_errors)
        warnings.extend(f"{case.get('dossier_id', '-')}: {warning}" for warning in case_warnings)

    return {
        "schema_version": "agent_artifact_contracts_report_v0",
        "ok": not errors,
        "contract_path": normalize_path(contract_path),
        "runtime_dir": normalize_path(runtime_dir),
        "pipeline_path": normalize_path(pipeline_path),
        "cases_count": len(summary),
        "agents_checked": len(agents),
        "artifacts_expected": artifacts_expected,
        "artifacts_checked": artifacts_checked,
        "artifacts_skipped": artifacts_skipped,
        "errors": errors,
        "warnings": warnings,
        "cases": cases_report,
    }


def validate_artifact(
    *,
    path: Path,
    artifact_contract: dict,
    agent_type: str,
    agent_config: str,
    case: dict,
    case_dir: Path,
) -> list[str]:
    fmt = str(artifact_contract.get("format") or "").strip()
    if fmt == "json":
        payload = load_json(path)
        if not isinstance(payload, dict):
            return ["JSON invalide: objet attendu"]
        return validate_json_artifact(
            payload=payload,
            artifact_contract=artifact_contract,
            agent_type=agent_type,
            agent_config=agent_config,
            case=case,
            case_dir=case_dir,
        )
    if fmt == "markdown":
        return validate_markdown_artifact(
            text=path.read_text(encoding="utf-8"),
            artifact_contract=artifact_contract,
            agent_type=agent_type,
            agent_config=agent_config,
            case=case,
        )
    return [f"format inconnu: {fmt}"]


def validate_json_artifact(
    *,
    payload: dict,
    artifact_contract: dict,
    agent_type: str,
    agent_config: str,
    case: dict,
    case_dir: Path,
) -> list[str]:
    errors: list[str] = []
    artifact_name = str(artifact_contract.get("name") or "")
    required = [*COMMON_JSON_FIELDS, *as_list(artifact_contract.get("required_fields"))]

    for field in required:
        if field not in payload:
            errors.append(f"champ requis absent: {field}")

    for field in as_list(artifact_contract.get("required_list_fields")):
        if field in payload and not isinstance(payload.get(field), list):
            errors.append(f"champ {field} doit etre une liste")

    for field in as_list(artifact_contract.get("required_dict_fields")):
        if field in payload and not isinstance(payload.get(field), dict):
            errors.append(f"champ {field} doit etre un objet")

    if payload.get("dossier_id") != case.get("dossier_id"):
        errors.append(f"dossier_id divergent: {payload.get('dossier_id')} != {case.get('dossier_id')}")
    if payload.get("step") != agent_type:
        errors.append(f"step divergent: {payload.get('step')} != {agent_type}")
    if payload.get("artifact") != artifact_name:
        errors.append(f"artifact divergent: {payload.get('artifact')} != {artifact_name}")
    if payload.get("agent_config") != agent_config:
        errors.append(f"agent_config divergent: {payload.get('agent_config')} != {agent_config}")
    if not as_list(payload.get("agent_skills_allowed")):
        errors.append("agent_skills_allowed vide ou absent")

    for rule in as_list(artifact_contract.get("rules")):
        errors.extend(validate_json_rule(str(rule), payload, case, case_dir))

    return errors


def validate_markdown_artifact(
    *,
    text: str,
    artifact_contract: dict,
    agent_type: str,
    agent_config: str,
    case: dict,
) -> list[str]:
    errors: list[str] = []
    dossier_id = str(case.get("dossier_id") or "")
    required_terms = [
        f"- Dossier: {dossier_id}",
        f"- Step: {agent_type}",
        "## agent_skills_allowed",
        "## agent_config",
        agent_config,
        *as_list(artifact_contract.get("required_markdown_terms")),
    ]
    for term in required_terms:
        if term not in text:
            errors.append(f"terme Markdown absent: {term}")

    for rule in as_list(artifact_contract.get("rules")):
        if rule == "markdown_contains_case_status":
            status = str(case.get("status") or "")
            if status and status not in text:
                errors.append(f"statut runtime absent du Markdown: {status}")
        else:
            errors.append(f"regle Markdown inconnue: {rule}")
    return errors


def validate_json_rule(rule: str, payload: dict, case: dict, case_dir: Path) -> list[str]:
    errors: list[str] = []
    status = str(case.get("status") or "UNKNOWN")

    if rule == "confidence_range":
        confidence = payload.get("confidence")
        if not is_number(confidence) or not 0 <= float(confidence) <= 1:
            errors.append("confidence hors bornes [0,1]")
    elif rule == "nonempty_source_ids_when_not_a_revoir":
        if status != STATUS_A_REVOIR and not as_list(payload.get("source_ids")):
            errors.append("source_ids vide hors A_REVOIR")
    elif rule == "timeline_has_date_reference":
        if not any(
            isinstance(event, dict) and event.get("type") == "date_reference" and event.get("date")
            for event in as_list(payload.get("events"))
        ):
            errors.append("timeline sans evenement date_reference")
    elif rule == "sources_have_source_id":
        for idx, source in enumerate(as_list(payload.get("sources"))):
            if not isinstance(source, dict) or not source.get("source_id"):
                errors.append(f"sources[{idx}] sans source_id")
    elif rule == "nonempty_sources_when_not_a_revoir":
        if status != STATUS_A_REVOIR and not as_list(payload.get("sources")):
            errors.append("sources vide hors A_REVOIR")
    elif rule == "nonempty_comparables_when_not_a_revoir":
        if status != STATUS_A_REVOIR and not as_list(payload.get("comparables")):
            errors.append("comparables vide hors A_REVOIR")
    elif rule == "comparables_have_required_fields":
        for idx, comparable in enumerate(as_list(payload.get("comparables"))):
            if not isinstance(comparable, dict):
                errors.append(f"comparables[{idx}] invalide")
                continue
            for field in ["comparable_id", "prix_vente", "source_id", "score", "score_details"]:
                if field not in comparable:
                    errors.append(f"comparables[{idx}] champ absent: {field}")
    elif rule == "comparable_scores_range":
        for idx, comparable in enumerate(as_list(payload.get("comparables"))):
            score = comparable.get("score") if isinstance(comparable, dict) else None
            if not is_number(score) or not 0 <= float(score) <= 1:
                errors.append(f"comparables[{idx}] score hors bornes [0,1]")
    elif rule == "justifications_have_required_fields":
        for idx, justification in enumerate(as_list(payload.get("justifications"))):
            if not isinstance(justification, dict):
                errors.append(f"justifications[{idx}] invalide")
                continue
            for field in ["comparable_id", "source_id", "decision", "raison"]:
                if field not in justification:
                    errors.append(f"justifications[{idx}] champ absent: {field}")
    elif rule == "value_number":
        if not is_number(payload.get("value")):
            errors.append("value doit etre numerique")
    elif rule == "input_count_integer":
        input_count = payload.get("input_count")
        if not isinstance(input_count, int) or isinstance(input_count, bool) or input_count < 0:
            errors.append("input_count doit etre un entier positif ou nul")
    elif rule == "positive_value_when_not_a_revoir":
        if status != STATUS_A_REVOIR and (not is_number(payload.get("value")) or float(payload.get("value")) <= 0):
            errors.append("value doit etre positive hors A_REVOIR")
    elif rule == "positive_input_count_when_not_a_revoir":
        input_count = payload.get("input_count")
        if status != STATUS_A_REVOIR and (not isinstance(input_count, int) or input_count <= 0):
            errors.append("input_count doit etre positif hors A_REVOIR")
    elif rule == "trace_has_selected_comparables":
        trace = as_dict(payload.get("trace"))
        if not isinstance(trace.get("selected_comparables"), list):
            errors.append("trace.selected_comparables doit etre une liste")
    elif rule == "trace_has_weights_used":
        trace = as_dict(payload.get("trace"))
        if not isinstance(trace.get("weights_used"), list):
            errors.append("trace.weights_used doit etre une liste")
    elif rule == "trace_has_calculation_policy":
        trace = as_dict(payload.get("trace"))
        if not as_list(trace.get("calculation_policy")):
            errors.append("trace.calculation_policy vide ou absente")
    elif rule == "status_allowed":
        if payload.get("status") not in STATUS_ALLOWED:
            errors.append(f"status invalide: {payload.get('status')}")
    elif rule == "status_matches_summary":
        if payload.get("status") != case.get("status"):
            errors.append(f"status divergent du resume: {payload.get('status')} != {case.get('status')}")
    elif rule == "status_consistent_with_findings":
        errors.extend(validate_status_consistency(payload))
    elif rule == "valuation_values_match_calculs":
        errors.extend(validate_valuation_values_match_calculs(payload, case_dir))
    else:
        errors.append(f"regle JSON inconnue: {rule}")

    return errors


def validate_status_consistency(payload: dict) -> list[str]:
    status = payload.get("status")
    blocking = as_list(payload.get("blocking_failures"))
    warnings = as_list(payload.get("warnings"))
    if status == "PRET_REVISION_FINALE" and (blocking or warnings):
        return ["PRET_REVISION_FINALE avec blocages ou warnings"]
    if status == "BROUILLON" and blocking:
        return ["BROUILLON avec blocages"]
    if status == "BROUILLON" and not warnings:
        return ["BROUILLON sans warning explicite"]
    if status == STATUS_A_REVOIR and not blocking:
        return ["A_REVOIR sans blocage explicite"]
    return []


def validate_valuation_values_match_calculs(payload: dict, case_dir: Path) -> list[str]:
    errors: list[str] = []
    values = as_dict(payload.get("valuation_values"))
    artifact_by_approach = {
        "approche_comparative": "valuation-draft.calculs_approche_comparative.json",
        "approche_cout": "valuation-draft.calculs_approche_cout.json",
        "approche_revenu": "valuation-draft.calculs_approche_revenu.json",
    }
    for approach, artifact_name in artifact_by_approach.items():
        if approach not in values:
            errors.append(f"valuation_values sans {approach}")
            continue
        artifact_path = case_dir / artifact_name
        if not artifact_path.exists():
            continue
        artifact = load_json(artifact_path)
        expected = artifact.get("value") if isinstance(artifact, dict) else None
        actual = values.get(approach)
        if not is_number(actual) or not is_number(expected):
            errors.append(f"valuation_values.{approach} non numerique")
            continue
        if abs(float(actual) - float(expected)) > 0.001:
            errors.append(f"valuation_values.{approach} divergent du calcul: {actual} != {expected}")
    return errors


def build_markdown(report: dict) -> str:
    lines = [
        "# Agent Artifact Contracts Evidence v0",
        "",
        "## Synthese",
        "",
        f"- OK: **{str(report.get('ok')).lower()}**",
        f"- Agents couverts: **{report.get('agents_checked', 0)}**",
        f"- Dossiers analyses: **{report.get('cases_count', 0)}**",
        f"- Artefacts attendus executes: **{report.get('artifacts_expected', 0)}**",
        f"- Artefacts verifies: **{report.get('artifacts_checked', 0)}**",
        f"- Artefacts ignores car etape non executee: **{report.get('artifacts_skipped', 0)}**",
        f"- Erreurs: **{len(report.get('errors', []))}**",
        "",
        "## Dossiers",
        "",
        "| Dossier | Statut | Etapes executees | Artefacts | Erreurs |",
        "|---|---|---:|---:|---:|",
    ]
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(
            "| {dossier} | {status} | {steps} | {checked}/{expected} | {errors} |".format(
                dossier=case.get("dossier_id", ""),
                status=case.get("status", "UNKNOWN"),
                steps=len(case.get("executed_steps", [])),
                checked=case.get("artifacts_checked", 0),
                expected=case.get("artifacts_expected", 0),
                errors=len(case.get("errors", [])),
            )
        )

    if report.get("errors"):
        lines.extend(["", "## Erreurs", ""])
        for error in report.get("errors", []):
            lines.append(f"- {error}")

    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for warning in report.get("warnings", []):
            lines.append(f"- {warning}")

    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict, json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifier les contrats metier des artefacts produits par agent.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH_DEFAULT)
    parser.add_argument("--pipeline", type=Path, default=PIPELINE_PATH_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    args = parser.parse_args()

    report = validate_agent_artifact_contracts(
        runtime_dir=args.runtime_dir,
        contract_path=args.contract,
        pipeline_path=args.pipeline,
    )
    report_out = args.report_out or args.runtime_dir / REPORT_JSON_NAME
    markdown_out = args.markdown_out or args.runtime_dir / REPORT_MD_NAME
    write_report(report, report_out, markdown_out)

    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, ensure_ascii=False, indent=2))
    print(f"Preuve contrats artefacts JSON: {report_out}")
    print(f"Preuve contrats artefacts Markdown: {markdown_out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
