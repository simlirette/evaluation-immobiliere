#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

INPUT_DEFAULT = Path("evaluation-immobiliere/atelier/CALIBRATION-EVALUATEURS.csv")
QUALITY_REPORT_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/quality_report.json")
OUT_JSON_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/calibration_evaluateurs.json")
OUT_REPORT_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/RAPPORT-CALIBRATION-EVALUATEURS-V0.md")
OUT_BACKLOG_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/BACKLOG-V1.md")
ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
OUT_CAMPAIGN_REPORT_DEFAULT = ATELIER_DIR_DEFAULT / "RAPPORT-CAMPAGNE-TERRAIN-V1.md"
OUT_GAP_MATRIX_DEFAULT = ATELIER_DIR_DEFAULT / "MATRICE-ECARTS-EVALUATEURS-V1.csv"
OUT_ACCEPTANCE_DEFAULT = ATELIER_DIR_DEFAULT / "CRITERES-ACCEPTATION-METIER-V1.md"

CALIBRATION_FIELDS = [
    "respondant_id",
    "role",
    "dossier_id",
    "cible_type",
    "cible_id",
    "artefact",
    "statut_attendu",
    "decision",
    "impact_1_5",
    "effort_1_5",
    "priorite",
    "commentaire",
]
ALLOWED_TARGET_TYPES = {
    "statut",
    "blocage",
    "warning",
    "comparable",
    "score_comparable",
    "trace",
    "artefact",
    "contrat",
    "general",
}
ALLOWED_DECISIONS = {
    "confirmer",
    "assouplir",
    "durcir",
    "retirer",
    "accepter",
    "refuser",
    "ajuster",
    "ajouter_source",
    "corriger_artefact",
    "a_discuter",
}
ALLOWED_STATUSES = {"PRET_REVISION_FINALE", "BROUILLON", "A_REVOIR", ""}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3", ""}
ACTIONABLE_DECISIONS = {
    "assouplir",
    "durcir",
    "retirer",
    "refuser",
    "ajuster",
    "ajouter_source",
    "corriger_artefact",
    "a_discuter",
}
GAP_MATRIX_FIELDS = [
    "dossier_id",
    "runtime_status",
    "statut_attendu",
    "status_disagreement",
    "cible_type",
    "cible_id",
    "artefact",
    "decision",
    "priorite",
    "impact_1_5",
    "effort_1_5",
    "respondant_id",
    "ecart_type",
    "action_recommandee",
    "evidence",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALIBRATION_FIELDS, lineterminator="\n")
        writer.writeheader()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def normalize(value: object) -> str:
    return str(value or "").strip()


def normalize_lower(value: object) -> str:
    return normalize(value).lower().replace(" ", "_").replace("-", "_")


def active_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if is_active_response(row)]


def is_active_response(row: dict[str, str]) -> bool:
    return any(normalize(row.get(field)) for field in CALIBRATION_FIELDS)


def validate_rows(rows: list[dict[str, str]], quality_report: dict) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    case_ids = {str(case.get("dossier_id")) for case in quality_report.get("cases", []) if isinstance(case, dict)}
    for index, row in enumerate(rows, start=2):
        if not is_active_response(row):
            continue
        target_type = normalize_lower(row.get("cible_type"))
        decision = normalize_lower(row.get("decision"))
        status = normalize(row.get("statut_attendu"))
        priority = normalize(row.get("priorite")).upper()
        dossier_id = normalize(row.get("dossier_id"))

        for field in ("respondant_id", "dossier_id", "cible_type", "decision"):
            if not normalize(row.get(field)):
                issues.append(issue(index, field, "Champ requis pour une ligne de calibration active."))
        if dossier_id and case_ids and dossier_id not in case_ids:
            issues.append(issue(index, "dossier_id", f"Dossier inconnu dans le rapport qualite: {dossier_id}.", "warning"))
        if target_type and target_type not in ALLOWED_TARGET_TYPES:
            issues.append(issue(index, "cible_type", f"Type de cible inconnu: {target_type}."))
        if decision and decision not in ALLOWED_DECISIONS:
            issues.append(issue(index, "decision", f"Decision inconnue: {decision}."))
        if status not in ALLOWED_STATUSES:
            issues.append(issue(index, "statut_attendu", f"Statut attendu invalide: {status}."))
        if priority not in ALLOWED_PRIORITIES:
            issues.append(issue(index, "priorite", f"Priorite invalide: {priority}."))
        for field in ("impact_1_5", "effort_1_5"):
            value = normalize(row.get(field))
            if not value:
                continue
            try:
                number = float(value)
            except ValueError:
                issues.append(issue(index, field, "Valeur numerique invalide."))
                continue
            if not 1 <= number <= 5:
                issues.append(issue(index, field, "La valeur doit etre entre 1 et 5."))
    return issues


def issue(row_number: int, field: str, message: str, severity: str = "error") -> dict[str, object]:
    return {"severity": severity, "row_number": row_number, "field": field, "message": message}


def build_calibration_report(response_rows: list[dict[str, str]], quality_report: dict, input_path: Path) -> dict[str, object]:
    rows = active_rows(response_rows)
    issues = validate_rows(response_rows, quality_report)
    errors = [item for item in issues if item["severity"] == "error"]
    cases = build_case_calibrations(rows, quality_report)
    backlog = build_backlog(rows, quality_report)
    status = calibration_status(rows, errors)

    return {
        "schema_version": "calibration_evaluateurs_v0",
        "status": status,
        "input_path": input_path.as_posix(),
        "runtime_quality_status_counts": quality_report.get("status_counts", {}),
        "responses_count": len(rows),
        "respondent_count": len({normalize(row.get("respondant_id")) for row in rows if normalize(row.get("respondant_id"))}),
        "issues": issues,
        "summary": {
            "responses_by_target_type": dict(Counter(normalize_lower(row.get("cible_type")) or "inconnu" for row in rows)),
            "responses_by_decision": dict(Counter(normalize_lower(row.get("decision")) or "inconnu" for row in rows)),
            "status_disagreements": sum(1 for case in cases if case.get("status_disagreement")),
            "backlog_items": len(backlog),
        },
        "cases": cases,
        "responses": [normalize_response(row) for row in rows],
        "backlog": backlog,
        "runtime_questions": build_runtime_questions(quality_report),
    }


def calibration_status(rows: list[dict[str, str]], errors: list[dict[str, object]]) -> str:
    if errors:
        return "A_CORRIGER"
    if not rows:
        return "PRET_A_RECEVOIR_REPONSES"
    return "CALIBRATION_COMPILEE"


def normalize_response(row: dict[str, str]) -> dict[str, object]:
    return {
        "respondant_id": normalize(row.get("respondant_id")),
        "role": normalize(row.get("role")),
        "dossier_id": normalize(row.get("dossier_id")),
        "target_type": normalize_lower(row.get("cible_type")),
        "target_id": normalize(row.get("cible_id")),
        "artifact": normalize(row.get("artefact")),
        "expected_status": normalize(row.get("statut_attendu")),
        "decision": normalize_lower(row.get("decision")),
        "impact": parse_optional_float(row.get("impact_1_5")),
        "effort": parse_optional_float(row.get("effort_1_5")),
        "priority": normalize(row.get("priorite")).upper(),
        "comment": normalize(row.get("commentaire")),
    }


def parse_optional_float(value: object) -> float | None:
    text = normalize(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def build_case_calibrations(rows: list[dict[str, str]], quality_report: dict) -> list[dict[str, object]]:
    responses_by_case: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        response = normalize_response(row)
        responses_by_case[str(response["dossier_id"])].append(response)

    cases: list[dict[str, object]] = []
    for case in quality_report.get("cases", []):
        if not isinstance(case, dict):
            continue
        dossier_id = str(case.get("dossier_id", ""))
        responses = responses_by_case.get(dossier_id, [])
        expected_statuses = sorted(
            {
                str(response.get("expected_status"))
                for response in responses
                if response.get("target_type") == "statut" and response.get("expected_status")
            }
        )
        runtime_status = str(case.get("status", "UNKNOWN"))
        cases.append(
            {
                "dossier_id": dossier_id,
                "runtime_status": runtime_status,
                "expected_statuses": expected_statuses,
                "status_disagreement": bool(expected_statuses and runtime_status not in expected_statuses),
                "responses_count": len(responses),
                "decisions": dict(Counter(str(response.get("decision") or "inconnu") for response in responses)),
            }
        )
    return cases


def build_backlog(rows: list[dict[str, str]], quality_report: dict) -> list[dict[str, object]]:
    case_index = {
        str(case.get("dossier_id")): case
        for case in quality_report.get("cases", [])
        if isinstance(case, dict) and case.get("dossier_id")
    }
    backlog: list[dict[str, object]] = []
    for row in rows:
        response = normalize_response(row)
        case = case_index.get(str(response["dossier_id"]), {})
        if not is_actionable(response, case):
            continue
        backlog.append(
            {
                "id": f"BKV1-{len(backlog) + 1:03d}",
                "priority": infer_priority(response, case),
                "area": infer_area(response),
                "dossier_id": response["dossier_id"],
                "target_type": response["target_type"],
                "target_id": response["target_id"],
                "artifact": response["artifact"],
                "action": infer_action(response, case),
                "evidence": evidence_text(response, case),
                "respondant_id": response["respondant_id"],
                "impact": response["impact"],
                "effort": response["effort"],
            }
        )
    return sorted(backlog, key=lambda item: (priority_rank(str(item["priority"])), str(item["id"])))


def is_actionable(response: dict[str, object], case: dict) -> bool:
    decision = str(response.get("decision") or "")
    target_type = str(response.get("target_type") or "")
    expected_status = str(response.get("expected_status") or "")
    runtime_status = str(case.get("status") or "")
    if target_type == "statut" and expected_status and runtime_status and expected_status != runtime_status:
        return True
    return decision in ACTIONABLE_DECISIONS


def infer_priority(response: dict[str, object], case: dict) -> str:
    explicit = str(response.get("priority") or "").upper()
    if explicit in {"P0", "P1", "P2", "P3"}:
        return explicit
    impact = response.get("impact")
    target_type = str(response.get("target_type") or "")
    decision = str(response.get("decision") or "")
    expected_status = str(response.get("expected_status") or "")
    runtime_status = str(case.get("status") or "")
    if target_type == "statut" and expected_status and runtime_status and expected_status != runtime_status:
        return "P0"
    if target_type in {"blocage", "contrat"} and decision in {"assouplir", "retirer", "durcir"}:
        return "P1"
    if isinstance(impact, float) and impact >= 5:
        return "P1"
    if target_type in {"warning", "comparable", "score_comparable", "trace", "artefact"}:
        return "P2"
    return "P3"


def priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9)


def infer_area(response: dict[str, object]) -> str:
    target_type = str(response.get("target_type") or "")
    if target_type == "statut":
        return "statut_runtime"
    if target_type in {"blocage", "warning", "contrat"}:
        return "contrats_qa"
    if target_type in {"comparable", "score_comparable"}:
        return "scoring_comparables"
    if target_type == "trace":
        return "tracabilite"
    if target_type == "artefact":
        return "artefacts_runtime"
    return "produit"


def infer_action(response: dict[str, object], case: dict) -> str:
    target_type = str(response.get("target_type") or "")
    decision = str(response.get("decision") or "")
    expected_status = str(response.get("expected_status") or "")
    runtime_status = str(case.get("status") or "")
    if target_type == "statut" and expected_status and runtime_status and expected_status != runtime_status:
        return f"Reviser la regle de statut: runtime={runtime_status}, attendu={expected_status}."
    if target_type in {"blocage", "warning", "contrat"}:
        return f"Reviser le contrat QA pour decision evaluateur `{decision}`."
    if target_type in {"comparable", "score_comparable"}:
        return f"Recalibrer la selection ou le scoring comparable pour decision `{decision}`."
    if target_type == "trace":
        return "Renforcer les sources ou la trace champ par champ."
    if target_type == "artefact":
        return "Corriger ou completer l'artefact runtime indique."
    return f"Traiter la decision evaluateur `{decision}`."


def evidence_text(response: dict[str, object], case: dict) -> str:
    comment = str(response.get("comment") or "")
    parts = []
    if response.get("target_id"):
        parts.append(f"cible={response['target_id']}")
    if response.get("artifact"):
        parts.append(f"artefact={response['artifact']}")
    if comment:
        parts.append(comment)
    if not parts and case:
        parts.append(f"statut_runtime={case.get('status', 'UNKNOWN')}")
    return " | ".join(parts) if parts else "-"


def build_runtime_questions(quality_report: dict) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    for case in quality_report.get("cases", []):
        if not isinstance(case, dict):
            continue
        dossier_id = str(case.get("dossier_id", "-"))
        for failure in case.get("blocking_failures", []):
            questions.append(
                {
                    "dossier_id": dossier_id,
                    "target_type": "blocage",
                    "target_id": str(failure),
                    "question": "Confirmer si ce blocage doit rester bloquant ou etre assoupli.",
                }
            )
        for warning in case.get("warnings", []):
            questions.append(
                {
                    "dossier_id": dossier_id,
                    "target_type": "warning",
                    "target_id": str(warning),
                    "question": "Decider si ce warning reste informatif ou devient bloquant.",
                }
            )
        artifacts = case.get("artifacts", {}) if isinstance(case.get("artifacts"), dict) else {}
        for artifact in artifacts.get("missing", []):
            questions.append(
                {
                    "dossier_id": dossier_id,
                    "target_type": "artefact",
                    "target_id": str(artifact),
                    "question": "Valider si l'artefact manquant bloque la revue evaluateur.",
                }
            )
    return questions


def build_markdown_report(report: dict[str, object]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Rapport calibration evaluateurs v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Reponses actives: **{report.get('responses_count', 0)}**",
        f"- Repondants uniques: **{report.get('respondent_count', 0)}**",
        f"- Desaccords statut: **{summary.get('status_disagreements', 0)}**",
        f"- Items backlog v1: **{summary.get('backlog_items', 0)}**",
        "",
    ]
    if report.get("status") == "PRET_A_RECEVOIR_REPONSES":
        lines.extend(
            [
                "## Point d'arret",
                "",
                "- Aucune reponse evaluateur active n'est presente.",
                "- Ne pas inventer de calibration; utiliser les questions ci-dessous pour guider la collecte.",
                "",
            ]
        )
    lines.extend(["## Dossiers", "", "| Dossier | Statut runtime | Statuts attendus | Desaccord | Reponses |", "|---|---|---|---|---:|"])
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(
            "| {dossier} | {runtime} | {expected} | {disagreement} | {count} |".format(
                dossier=case.get("dossier_id", "-"),
                runtime=case.get("runtime_status", "UNKNOWN"),
                expected=format_items(case.get("expected_statuses", [])),
                disagreement="oui" if case.get("status_disagreement") else "non",
                count=case.get("responses_count", 0),
            )
        )
    lines.extend(["", "## Decisions", ""])
    lines.append(f"- Par type cible: {format_counter(summary.get('responses_by_target_type', {}))}")
    lines.append(f"- Par decision: {format_counter(summary.get('responses_by_decision', {}))}")

    lines.extend(["", "## Questions runtime a faire trancher", ""])
    questions = report.get("runtime_questions", [])
    if questions:
        lines.extend(["| Dossier | Type | Cible | Question |", "|---|---|---|---|"])
        for item in questions:
            if isinstance(item, dict):
                lines.append(
                    "| {dossier} | {target_type} | {target_id} | {question} |".format(
                        dossier=item.get("dossier_id", "-"),
                        target_type=item.get("target_type", "-"),
                        target_id=item.get("target_id", "-"),
                        question=item.get("question", "-"),
                    )
                )
    else:
        lines.append("- Aucune question runtime ouverte.")

    lines.extend(["", "## Erreurs de saisie", ""])
    errors = [issue for issue in report.get("issues", []) if isinstance(issue, dict) and issue.get("severity") == "error"]
    if errors:
        for item in errors:
            lines.append(f"- ligne {item.get('row_number')}, `{item.get('field')}`: {item.get('message')}")
    else:
        lines.append("- Aucune.")
    return "\n".join(lines).rstrip() + "\n"


def build_backlog_markdown(report: dict[str, object]) -> str:
    backlog = report.get("backlog", []) if isinstance(report.get("backlog"), list) else []
    lines = [
        "# Backlog v1 issu calibration evaluateurs",
        "",
        f"- Statut calibration: **{report.get('status', 'UNKNOWN')}**",
        f"- Items retenus: **{len(backlog)}**",
        "",
        "| ID | Priorite | Zone | Dossier | Cible | Action | Evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    if not backlog:
        lines.append("| - | - | - | - | - | Aucun item confirme avant reponses evaluateurs. | - |")
    for item in backlog:
        if not isinstance(item, dict):
            continue
        target = str(item.get("target_id") or item.get("target_type") or "-")
        lines.append(
            "| {id} | {priority} | {area} | {dossier} | {target} | {action} | {evidence} |".format(
                id=item.get("id", "-"),
                priority=item.get("priority", "-"),
                area=item.get("area", "-"),
                dossier=item.get("dossier_id", "-"),
                target=target,
                action=item.get("action", "-"),
                evidence=item.get("evidence", "-"),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def format_items(values: object) -> str:
    if not isinstance(values, list) or not values:
        return "-"
    return ", ".join(str(value) for value in values)


def format_counter(value: object) -> str:
    if not isinstance(value, dict) or not value:
        return "-"
    return ", ".join(f"{key}={count}" for key, count in sorted(value.items()))


def write_outputs(report: dict[str, object], json_out: Path, report_out: Path, backlog_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    backlog_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_out.write_text(build_markdown_report(report), encoding="utf-8")
    backlog_out.write_text(build_backlog_markdown(report), encoding="utf-8")


def phase_h_status(report: dict[str, object]) -> str:
    if report.get("status") == "A_CORRIGER":
        return "A_CORRIGER"
    if int(report.get("responses_count", 0)) == 0:
        return "EN_ATTENTE_REPONSES_TERRAIN"
    backlog = report.get("backlog", []) if isinstance(report.get("backlog"), list) else []
    if any(isinstance(item, dict) and item.get("priority") == "P0" for item in backlog):
        return "NO_GO_METIER"
    if backlog:
        return "GO_CONDITIONNEL"
    return "GO_METIER_CONDITIONNEL_SIGNATURE"


def build_gap_matrix_rows(report: dict[str, object]) -> list[dict[str, object]]:
    cases = {
        str(case.get("dossier_id")): case
        for case in report.get("cases", [])
        if isinstance(case, dict) and case.get("dossier_id")
    }
    backlog_by_key = {
        (
            str(item.get("dossier_id") or ""),
            str(item.get("target_type") or ""),
            str(item.get("target_id") or ""),
            str(item.get("artifact") or ""),
            str(item.get("respondant_id") or ""),
        ): item
        for item in report.get("backlog", [])
        if isinstance(item, dict)
    }
    rows: list[dict[str, object]] = []
    for response in report.get("responses", []):
        if not isinstance(response, dict):
            continue
        dossier_id = str(response.get("dossier_id") or "")
        case = cases.get(dossier_id, {})
        runtime_status = str(case.get("runtime_status") or "UNKNOWN")
        expected_status = str(response.get("expected_status") or "")
        disagreement = bool(response.get("target_type") == "statut" and expected_status and runtime_status != expected_status)
        key = (
            dossier_id,
            str(response.get("target_type") or ""),
            str(response.get("target_id") or ""),
            str(response.get("artifact") or ""),
            str(response.get("respondant_id") or ""),
        )
        backlog_item = backlog_by_key.get(key, {})
        rows.append(
            {
                "dossier_id": dossier_id,
                "runtime_status": runtime_status,
                "statut_attendu": expected_status,
                "status_disagreement": "oui" if disagreement else "non",
                "cible_type": response.get("target_type", ""),
                "cible_id": response.get("target_id", ""),
                "artefact": response.get("artifact", ""),
                "decision": response.get("decision", ""),
                "priorite": backlog_item.get("priority") or response.get("priority") or "",
                "impact_1_5": response.get("impact") if response.get("impact") is not None else "",
                "effort_1_5": response.get("effort") if response.get("effort") is not None else "",
                "respondant_id": response.get("respondant_id", ""),
                "ecart_type": gap_type(response, disagreement, bool(backlog_item)),
                "action_recommandee": backlog_item.get("action", ""),
                "evidence": backlog_item.get("evidence") or response.get("comment") or "",
            }
        )
    return rows


def gap_type(response: dict[str, object], disagreement: bool, actionable: bool) -> str:
    if disagreement:
        return "desaccord_statut"
    if actionable:
        return "action_calibration"
    if response.get("decision") == "confirmer":
        return "accord"
    return "observation"


def build_campaign_markdown(report: dict[str, object]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    backlog = report.get("backlog", []) if isinstance(report.get("backlog"), list) else []
    status = phase_h_status(report)
    lines = [
        "# RAPPORT CAMPAGNE TERRAIN V1",
        "",
        "_As-of date: 2026-04-30 (UTC)_",
        "",
        "## Objectif",
        "Documenter la validation metier terrain des sorties IA et transformer les ecarts evaluateurs en decisions de calibration.",
        "",
        "## Synthese",
        "",
        "| Indicateur | Valeur |",
        "|---|---:|",
        f"| Source calibration | `{report.get('input_path', '-')}` |",
        f"| Statut Phase H | {status} |",
        f"| Reponses actives | {report.get('responses_count', 0)} |",
        f"| Repondants uniques | {report.get('respondent_count', 0)} |",
        f"| Desaccords statut | {summary.get('status_disagreements', 0)} |",
        f"| Items backlog | {summary.get('backlog_items', 0)} |",
        "",
    ]
    if status == "EN_ATTENTE_REPONSES_TERRAIN":
        lines.extend(
            [
                "## Point d'arret",
                "",
                "- Aucune ligne active n'est presente dans le fichier de calibration evaluateur.",
                "- La campagne terrain n'est pas closee et aucune conclusion metier ne doit etre inventee.",
                "- Utiliser les questions runtime ci-dessous pour guider la collecte des reponses.",
                "",
            ]
        )
    lines.extend(
        [
            "## Couverture dossiers",
            "",
            "| Dossier | Statut runtime | Reponses | Statuts attendus | Desaccord |",
            "|---|---|---:|---|---|",
        ]
    )
    for case in report.get("cases", []):
        if not isinstance(case, dict):
            continue
        lines.append(
            "| {dossier} | {runtime} | {count} | {expected} | {disagreement} |".format(
                dossier=case.get("dossier_id", "-"),
                runtime=case.get("runtime_status", "UNKNOWN"),
                count=case.get("responses_count", 0),
                expected=format_items(case.get("expected_statuses", [])),
                disagreement="oui" if case.get("status_disagreement") else "non",
            )
        )
    lines.extend(["", "## Ecarts et backlog", ""])
    if backlog:
        lines.extend(["| ID | Priorite | Zone | Dossier | Action |", "|---|---|---|---|---|"])
        for item in backlog:
            if isinstance(item, dict):
                lines.append(
                    "| {id} | {priority} | {area} | {dossier} | {action} |".format(
                        id=item.get("id", "-"),
                        priority=item.get("priority", "-"),
                        area=item.get("area", "-"),
                        dossier=item.get("dossier_id", "-"),
                        action=item.get("action", "-"),
                    )
                )
    else:
        lines.append("- Aucun ecart evaluateur confirme pour l'instant.")
    lines.extend(["", "## Questions terrain ouvertes", ""])
    questions = report.get("runtime_questions", []) if isinstance(report.get("runtime_questions"), list) else []
    if questions:
        lines.extend(["| Dossier | Type | Cible | Question |", "|---|---|---|---|"])
        for item in questions:
            if isinstance(item, dict):
                lines.append(
                    "| {dossier} | {target_type} | {target_id} | {question} |".format(
                        dossier=item.get("dossier_id", "-"),
                        target_type=item.get("target_type", "-"),
                        target_id=item.get("target_id", "-"),
                        question=item.get("question", "-"),
                    )
                )
    else:
        lines.append("- Aucune question terrain ouverte.")
    lines.extend(
        [
            "",
            "## Decision Phase H",
            "",
            f"Decision: **{status}**.",
            "",
            "Dependances Phase I:",
            "- campagne terrain signee ou point d'arret explicite;",
            "- matrice d'ecarts exploitable;",
            "- criteres d'acceptation metier revus par Lead Metier + Product.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_acceptance_markdown(report: dict[str, object]) -> str:
    status = phase_h_status(report)
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    backlog = report.get("backlog", []) if isinstance(report.get("backlog"), list) else []
    cases = report.get("cases", []) if isinstance(report.get("cases"), list) else []
    cases_count = len([case for case in cases if isinstance(case, dict)])
    covered_cases = sum(1 for case in cases if isinstance(case, dict) and int(case.get("responses_count", 0)) > 0)
    p0_count = sum(1 for item in backlog if isinstance(item, dict) and item.get("priority") == "P0")
    criteria = [
        ("Panel evaluateurs", int(report.get("respondent_count", 0)), ">= 2", int(report.get("respondent_count", 0)) >= 2),
        ("Couverture dossiers", covered_cases, f">= {cases_count}", cases_count > 0 and covered_cases >= cases_count),
        ("Desaccords statut", int(summary.get("status_disagreements", 0)), "0", int(summary.get("status_disagreements", 0)) == 0),
        ("Backlog P0 metier", p0_count, "0", p0_count == 0),
        ("Saisie valide", report.get("status", "UNKNOWN"), "!= A_CORRIGER", report.get("status") != "A_CORRIGER"),
        ("Signature metier", "A_SIGNER", "SIGNE", False),
    ]
    lines = [
        "# CRITERES ACCEPTATION METIER V1",
        "",
        "_As-of date: 2026-04-30 (UTC)_",
        "",
        "## Objectif",
        "Fixer les seuils de passage Phase H vers industrialisation CI/CD sans confondre preparation et validation terrain signee.",
        "",
        f"Statut courant: **{status}**.",
        "",
        "## Criteres",
        "",
        "| Critere | Courant | Cible | Statut |",
        "|---|---:|---:|---|",
    ]
    for name, current, target, ok in criteria:
        lines.append(f"| {name} | {current} | {target} | {'OK' if ok else 'A_TRAITER'} |")
    lines.extend(
        [
            "",
            "## Regles Go/No-Go",
            "",
            "- **GO**: tous les criteres sont OK et la signature metier est obtenue.",
            "- **GO_CONDITIONNEL**: aucun P0 metier ouvert, mais des P1/P2 restent planifies.",
            "- **NO_GO_METIER**: desaccord statut non resolu, P0 metier ouvert ou rejet evaluateur majeur.",
            "- **EN_ATTENTE_REPONSES_TERRAIN**: aucune reponse evaluateur exploitable; ne pas conclure.",
            "",
            "## Owners de signature",
            "",
            "| Role | Owner | Statut |",
            "|---|---|---|",
            "| Lead Metier | A nommer | A_SIGNER |",
            "| Product | A nommer | A_SIGNER |",
            "| QA/Platform | A nommer | A_SIGNER |",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_gap_matrix(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GAP_MATRIX_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_phase_h_outputs(report: dict[str, object], campaign_out: Path, matrix_out: Path, acceptance_out: Path) -> None:
    campaign_out.parent.mkdir(parents=True, exist_ok=True)
    matrix_out.parent.mkdir(parents=True, exist_ok=True)
    acceptance_out.parent.mkdir(parents=True, exist_ok=True)
    campaign_out.write_text(build_campaign_markdown(report), encoding="utf-8")
    write_gap_matrix(matrix_out, build_gap_matrix_rows(report))
    acceptance_out.write_text(build_acceptance_markdown(report), encoding="utf-8")


def run_calibration(
    input_path: Path,
    quality_report_path: Path,
    json_out: Path,
    report_out: Path,
    backlog_out: Path,
    campaign_out: Path | None = None,
    matrix_out: Path | None = None,
    acceptance_out: Path | None = None,
) -> dict[str, object]:
    rows = read_csv_rows(input_path)
    quality_report = load_json(quality_report_path)
    report = build_calibration_report(rows, quality_report, input_path)
    write_outputs(report, json_out, report_out, backlog_out)
    if campaign_out and matrix_out and acceptance_out:
        write_phase_h_outputs(report, campaign_out, matrix_out, acceptance_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile les retours evaluateurs en rapport de calibration et backlog v1.")
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--quality-report", type=Path, default=QUALITY_REPORT_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=OUT_REPORT_DEFAULT)
    parser.add_argument("--backlog-out", type=Path, default=OUT_BACKLOG_DEFAULT)
    parser.add_argument("--campaign-out", type=Path, default=OUT_CAMPAIGN_REPORT_DEFAULT)
    parser.add_argument("--matrix-out", type=Path, default=OUT_GAP_MATRIX_DEFAULT)
    parser.add_argument("--acceptance-out", type=Path, default=OUT_ACCEPTANCE_DEFAULT)
    parser.add_argument("--write-template", type=Path, help="Ecrit seulement un gabarit CSV de calibration a ce chemin.")
    args = parser.parse_args()

    if args.write_template:
        write_csv_template(args.write_template)
        print(f"Gabarit calibration: {args.write_template}")
        return 0

    report = run_calibration(
        args.input,
        args.quality_report,
        args.json_out,
        args.report_out,
        args.backlog_out,
        args.campaign_out,
        args.matrix_out,
        args.acceptance_out,
    )
    print(f"Calibration JSON: {args.json_out}")
    print(f"Rapport calibration: {args.report_out}")
    print(f"Backlog v1: {args.backlog_out}")
    print(f"Rapport campagne terrain: {args.campaign_out}")
    print(f"Matrice ecarts evaluateurs: {args.matrix_out}")
    print(f"Criteres acceptation metier: {args.acceptance_out}")
    print(f"Statut Phase H: {phase_h_status(report)}")
    print(f"Statut: {report['status']}")
    return 0 if report["status"] != "A_CORRIGER" else 1


if __name__ == "__main__":
    raise SystemExit(main())
