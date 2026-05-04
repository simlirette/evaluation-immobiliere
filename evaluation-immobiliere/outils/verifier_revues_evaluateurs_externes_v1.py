from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

OUTILS_DIR = Path(__file__).resolve().parent
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from verifier_homologation_metier_v0 import (  # noqa: E402
    EXTERNAL_REVIEWS_DEFAULT,
    GRILLE_PATH_DEFAULT,
    PROJECT_ROOT,
    RUNTIME_DIR_DEFAULT,
    as_dict,
    as_list,
    load_json,
    normalize_path,
)

REPORT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "revues_evaluateurs_externes_report.json"
REPORT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "REVUES-EVALUATEURS-EXTERNES-EVIDENCE-V1.md"
GAP_REPORT_DEFAULT = PROJECT_ROOT / "atelier" / "RAPPORT-ECARTS-EVALUATEURS-EXTERNES-V1.md"
GAP_MATRIX_DEFAULT = PROJECT_ROOT / "atelier" / "MATRICE-ECARTS-EVALUATEURS-EXTERNES-V1.csv"

VALID_SCHEMAS = {"homologation_evaluateurs_v1", "homologation_evaluateur_reviews_v1"}
SIGNED_STATUS = "SIGNE"
GAP_PRIORITIES = {"P0", "P1", "P2", "P3"}
GAP_FIELDS = [
    "gap_id",
    "dossier_id",
    "runtime_status",
    "expected_status",
    "status_disagreement",
    "reviewer_id",
    "decision",
    "priority",
    "category",
    "target",
    "status",
    "recommendation",
    "evidence",
]


def load_runtime_cases(runtime_dir: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(runtime_dir / "runtime_summary.json")
    cases = [case for case in as_list(payload) if isinstance(case, dict)]
    return {str(case.get("dossier_id") or ""): case for case in cases if case.get("dossier_id")}


def build_reviewer_signatures(payload: dict[str, Any]) -> dict[str, str]:
    signatures: dict[str, str] = {}
    for reviewer in as_list(payload.get("reviewers")):
        if not isinstance(reviewer, dict):
            continue
        reviewer_id = str(reviewer.get("reviewer_id") or "").strip()
        if reviewer_id:
            signatures[reviewer_id] = str(reviewer.get("signature_status") or "").strip()
    return signatures


def validate_external_evaluator_reviews(
    reviews_path: Path = EXTERNAL_REVIEWS_DEFAULT,
    *,
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    grille_path: Path = GRILLE_PATH_DEFAULT,
    strict: bool = False,
) -> dict[str, Any]:
    grille = load_json(grille_path)
    policy = as_dict(grille.get("external_review_policy"))
    runtime_cases = load_runtime_cases(runtime_dir)
    allowed_statuses = {str(item) for item in as_list(grille.get("status_allowed"))}
    allowed_decisions = {str(item) for item in as_list(policy.get("allowed_decisions"))}
    blocking_decisions = {str(item) for item in as_list(policy.get("blocking_decisions") or ["REJETE"])}
    blocking_gap_priorities = {str(item).upper() for item in as_list(policy.get("blocking_gap_priorities") or ["P0"])}
    minimum_reviewers = int(policy.get("minimum_reviewers", 2))
    minimum_pilots = int(policy.get("minimum_reviewed_pilot_cases", 3))

    errors: list[str] = []
    warnings: list[str] = []
    if not reviews_path.exists():
        message = f"fixture revues evaluateurs absente: {normalize_path(reviews_path)}"
        if strict:
            errors.append(message)
        else:
            warnings.append(message)
        return empty_report(reviews_path, runtime_dir, grille_path, strict, errors, warnings)

    payload = load_json(reviews_path)
    if not isinstance(payload, dict):
        errors.append("fixture revues evaluateurs invalide: racine JSON objet attendue")
        payload = {}
    schema = str(payload.get("schema_version") or "")
    if schema not in VALID_SCHEMAS:
        errors.append(f"schema_version invalide: {schema or 'absent'}")

    reviews = as_list(payload.get("reviews"))
    reviewer_signatures = build_reviewer_signatures(payload)
    reviewers: set[str] = set()
    reviewed_pilots: set[str] = set()
    cases: dict[str, dict[str, Any]] = {}
    gaps: list[dict[str, Any]] = []
    decisions = Counter()
    gap_counts = Counter()
    status_disagreements = 0

    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            errors.append(f"review[{index}] invalide")
            continue

        reviewer_id = str(review.get("reviewer_id") or "").strip()
        dossier_id = str(review.get("dossier_id") or "").strip()
        decision = str(review.get("decision") or "").strip()
        expected_status = str(review.get("expected_status") or review.get("statut_attendu") or "").strip()
        signature_status = str(review.get("signature_status") or reviewer_signatures.get(reviewer_id) or "").strip()
        runtime_case = runtime_cases.get(dossier_id, {})
        runtime_status = str(runtime_case.get("status") or review.get("runtime_status") or "UNKNOWN")

        if reviewer_id:
            reviewers.add(reviewer_id)
        else:
            errors.append(f"review[{index}] reviewer_id absent")
        if dossier_id:
            cases.setdefault(
                dossier_id,
                {
                    "dossier_id": dossier_id,
                    "runtime_status": runtime_status,
                    "expected_statuses": [],
                    "reviewers": [],
                    "decisions": Counter(),
                    "gaps_count": 0,
                },
            )
            if dossier_id.startswith("D-PILOTE-"):
                reviewed_pilots.add(dossier_id)
        else:
            errors.append(f"review[{index}] dossier_id absent")

        if dossier_id and dossier_id not in runtime_cases:
            errors.append(f"{dossier_id}: dossier absent du runtime_summary")
        if review.get("runtime_status") and str(review.get("runtime_status")) != runtime_status:
            errors.append(f"{dossier_id}: runtime_status divergent fixture={review.get('runtime_status')} runtime={runtime_status}")
        if decision not in allowed_decisions:
            errors.append(f"{dossier_id}: decision invalide: {decision or 'absente'}")
        if decision in blocking_decisions:
            errors.append(f"{dossier_id}: decision bloquante evaluateur: {decision}")
        if expected_status not in allowed_statuses:
            errors.append(f"{dossier_id}: expected_status invalide: {expected_status or 'absent'}")
        elif expected_status != runtime_status:
            status_disagreements += 1
            message = f"{dossier_id}: statut attendu evaluateur {expected_status} != runtime {runtime_status}"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)
        if signature_status != SIGNED_STATUS:
            message = f"{dossier_id}: signature evaluateur manquante pour {reviewer_id or 'reviewer inconnu'}"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)

        decisions.update([decision or "INCONNU"])
        if dossier_id in cases:
            case = cases[dossier_id]
            case["expected_statuses"].append(expected_status)
            case["reviewers"].append(reviewer_id)
            case["decisions"].update([decision or "INCONNU"])

        review_gaps = as_list(review.get("gaps") or review.get("ecarts"))
        if decision == "A_REVOIR" and not review_gaps:
            message = f"{dossier_id}: decision A_REVOIR sans ecart documente"
            if strict:
                errors.append(message)
            else:
                warnings.append(message)

        for gap_index, gap in enumerate(review_gaps):
            if not isinstance(gap, dict):
                errors.append(f"{dossier_id}: gap[{gap_index}] invalide")
                continue
            gap_id = str(gap.get("gap_id") or f"{dossier_id}-GAP-{gap_index + 1}").strip()
            priority = str(gap.get("priority") or "").strip().upper()
            if priority not in GAP_PRIORITIES:
                errors.append(f"{dossier_id}: {gap_id}: priorite invalide: {priority or 'absente'}")
            for field in ("category", "target", "status", "summary", "recommendation"):
                if not str(gap.get(field) or "").strip():
                    errors.append(f"{dossier_id}: {gap_id}: champ {field} absent")
            if priority in blocking_gap_priorities:
                errors.append(f"{dossier_id}: {gap_id}: ecart bloquant {priority}")
            elif priority:
                warnings.append(f"{dossier_id}: {gap_id}: ecart conditionnel {priority}")
            gap_counts.update([priority or "INCONNU"])
            if dossier_id in cases:
                cases[dossier_id]["gaps_count"] += 1
            gaps.append(
                {
                    "gap_id": gap_id,
                    "dossier_id": dossier_id,
                    "runtime_status": runtime_status,
                    "expected_status": expected_status,
                    "status_disagreement": expected_status != runtime_status,
                    "reviewer_id": reviewer_id,
                    "decision": decision,
                    "priority": priority,
                    "category": str(gap.get("category") or "").strip(),
                    "target": str(gap.get("target") or "").strip(),
                    "status": str(gap.get("status") or "").strip(),
                    "summary": str(gap.get("summary") or "").strip(),
                    "recommendation": str(gap.get("recommendation") or "").strip(),
                    "evidence": str(gap.get("evidence") or "").strip(),
                }
            )

    if len(reviewers) < minimum_reviewers:
        errors.append(f"reviewers insuffisants ({len(reviewers)}/{minimum_reviewers})")
    if len(reviewed_pilots) < minimum_pilots:
        errors.append(f"dossiers pilotes revus insuffisants ({len(reviewed_pilots)}/{minimum_pilots})")

    normalized_cases = []
    for case in sorted(cases.values(), key=lambda item: str(item.get("dossier_id"))):
        normalized_cases.append(
            {
                "dossier_id": case["dossier_id"],
                "runtime_status": case["runtime_status"],
                "expected_statuses": sorted({status for status in case["expected_statuses"] if status}),
                "reviewers": sorted({reviewer for reviewer in case["reviewers"] if reviewer}),
                "decisions": dict(case["decisions"]),
                "gaps_count": case["gaps_count"],
            }
        )

    ok = not errors
    decision = "NO_GO_REVUES_EVALUATEURS_EXTERNES"
    if ok and gaps:
        decision = "GO_CONDITIONNEL_ECARTS_EVALUATEURS"
    elif ok:
        decision = "GO_REVUES_EVALUATEURS_EXTERNES"

    return {
        "schema_version": "revues_evaluateurs_externes_gate_v1",
        "ok": ok,
        "strict": strict,
        "decision": decision,
        "source_path": normalize_path(reviews_path),
        "runtime_dir": normalize_path(runtime_dir),
        "grille_path": normalize_path(grille_path),
        "reviews_count": len(reviews),
        "reviewers_count": len(reviewers),
        "reviewed_pilot_cases": len(reviewed_pilots),
        "status_disagreements": status_disagreements,
        "gaps_count": len(gaps),
        "gap_counts_by_priority": dict(gap_counts),
        "decisions_count": dict(decisions),
        "errors": errors,
        "warnings": warnings,
        "cases": normalized_cases,
        "gaps": sorted(gaps, key=lambda item: (priority_rank(str(item.get("priority"))), str(item.get("dossier_id")), str(item.get("gap_id")))),
    }


def empty_report(
    reviews_path: Path,
    runtime_dir: Path,
    grille_path: Path,
    strict: bool,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "revues_evaluateurs_externes_gate_v1",
        "ok": not errors,
        "strict": strict,
        "decision": "NO_GO_REVUES_EVALUATEURS_EXTERNES" if errors else "EN_ATTENTE_REVUES_EVALUATEURS_EXTERNES",
        "source_path": normalize_path(reviews_path),
        "runtime_dir": normalize_path(runtime_dir),
        "grille_path": normalize_path(grille_path),
        "reviews_count": 0,
        "reviewers_count": 0,
        "reviewed_pilot_cases": 0,
        "status_disagreements": 0,
        "gaps_count": 0,
        "gap_counts_by_priority": {},
        "decisions_count": {},
        "errors": errors,
        "warnings": warnings,
        "cases": [],
        "gaps": [],
    }


def priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Revues evaluateurs externes Evidence V1",
        "",
        "## Synthese",
        "",
        f"- OK gate strict: **{str(report.get('ok')).lower()}**",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- Source: `{report.get('source_path', '-')}`",
        f"- Reviews: **{report.get('reviews_count', 0)}**",
        f"- Evaluateurs: **{report.get('reviewers_count', 0)}**",
        f"- Dossiers pilotes revus: **{report.get('reviewed_pilot_cases', 0)}**",
        f"- Ecarts: **{report.get('gaps_count', 0)}**",
        f"- Desaccords statut: **{report.get('status_disagreements', 0)}**",
        f"- Erreurs: **{len(as_list(report.get('errors')))}**",
        f"- Warnings: **{len(as_list(report.get('warnings')))}**",
        "",
        "## Couverture",
        "",
        "| Dossier | Statut runtime | Statuts attendus | Evaluateurs | Decisions | Ecarts |",
        "|---|---|---|---|---|---:|",
    ]
    for case in as_list(report.get("cases")):
        if not isinstance(case, dict):
            continue
        lines.append(
            "| {dossier} | {runtime} | {expected} | {reviewers} | {decisions} | {gaps} |".format(
                dossier=case.get("dossier_id", "-"),
                runtime=case.get("runtime_status", "UNKNOWN"),
                expected=format_items(case.get("expected_statuses")),
                reviewers=format_items(case.get("reviewers")),
                decisions=format_counter(case.get("decisions")),
                gaps=case.get("gaps_count", 0),
            )
        )
    lines.extend(["", "## Ecarts", ""])
    lines.extend(build_gap_table(report))
    lines.extend(["", "## Erreurs", ""])
    lines.extend(render_list(report.get("errors")))
    lines.extend(["", "## Warnings", ""])
    lines.extend(render_list(report.get("warnings")))
    return "\n".join(lines).rstrip() + "\n"


def build_gap_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Rapport ecarts evaluateurs externes V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Decision",
        "",
        f"- Gate: **{report.get('decision', 'UNKNOWN')}**",
        f"- Source: `{report.get('source_path', '-')}`",
        f"- Ecarts P0: **{as_dict(report.get('gap_counts_by_priority')).get('P0', 0)}**",
        f"- Ecarts P1: **{as_dict(report.get('gap_counts_by_priority')).get('P1', 0)}**",
        f"- Ecarts P2: **{as_dict(report.get('gap_counts_by_priority')).get('P2', 0)}**",
        f"- Desaccords statut: **{report.get('status_disagreements', 0)}**",
        "",
        "## Synthese des ecarts",
        "",
    ]
    lines.extend(build_gap_table(report))
    lines.extend(
        [
            "",
            "## Regles de sortie",
            "",
            "- P0, rejet evaluateur ou desaccord statut: NO_GO revues externes.",
            "- P1/P2 documentes sans desaccord statut: GO conditionnel, correction a planifier avant signature metier finale.",
            "- Aucun ecart et couverture minimale atteinte: GO revues externes.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_gap_table(report: dict[str, Any]) -> list[str]:
    gaps = [gap for gap in as_list(report.get("gaps")) if isinstance(gap, dict)]
    if not gaps:
        return ["- Aucun ecart evaluateur documente."]
    lines = [
        "| Priorite | Dossier | Cible | Statut | Recommandation | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for gap in gaps:
        lines.append(
            "| {priority} | {dossier} | {target} | {status} | {recommendation} | {evidence} |".format(
                priority=gap.get("priority", "-"),
                dossier=gap.get("dossier_id", "-"),
                target=gap.get("target", "-"),
                status=gap.get("status", "-"),
                recommendation=gap.get("recommendation", "-"),
                evidence=gap.get("evidence", "-"),
            )
        )
    return lines


def render_list(items: object) -> list[str]:
    values = [str(item) for item in as_list(items) if str(item)]
    if not values:
        return ["- Aucune."]
    return [f"- {item}" for item in values]


def format_items(values: object) -> str:
    items = [str(item) for item in as_list(values) if str(item)]
    return ", ".join(items) if items else "-"


def format_counter(value: object) -> str:
    if not isinstance(value, dict) or not value:
        return "-"
    return ", ".join(f"{key}={count}" for key, count in sorted(value.items()))


def write_gap_matrix(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GAP_FIELDS, lineterminator="\n")
        writer.writeheader()
        for gap in as_list(report.get("gaps")):
            if not isinstance(gap, dict):
                continue
            row = {field: gap.get(field, "") for field in GAP_FIELDS}
            row["status_disagreement"] = "oui" if gap.get("status_disagreement") else "non"
            writer.writerow(row)


def write_outputs(
    report: dict[str, Any],
    json_out: Path,
    markdown_out: Path,
    gap_report_out: Path,
    gap_matrix_out: Path,
) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    gap_report_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")
    gap_report_out.write_text(build_gap_report_markdown(report), encoding="utf-8")
    write_gap_matrix(gap_matrix_out, report)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie les revues evaluateurs externes en mode terminal strict.")
    parser.add_argument("--external-reviews", type=Path, default=EXTERNAL_REVIEWS_DEFAULT)
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--grille", type=Path, default=GRILLE_PATH_DEFAULT)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report-out", type=Path, default=REPORT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD_DEFAULT)
    parser.add_argument("--gap-report-out", type=Path, default=GAP_REPORT_DEFAULT)
    parser.add_argument("--gap-matrix-out", type=Path, default=GAP_MATRIX_DEFAULT)
    args = parser.parse_args()

    report = validate_external_evaluator_reviews(
        args.external_reviews,
        runtime_dir=args.runtime_dir,
        grille_path=args.grille,
        strict=args.strict,
    )
    write_outputs(report, args.report_out, args.markdown_out, args.gap_report_out, args.gap_matrix_out)

    print(json.dumps({key: value for key, value in report.items() if key not in {"cases", "gaps"}}, ensure_ascii=False, indent=2))
    print(f"Rapport revues evaluateurs JSON: {args.report_out}")
    print(f"Preuve revues evaluateurs Markdown: {args.markdown_out}")
    print(f"Rapport ecarts evaluateurs: {args.gap_report_out}")
    print(f"Matrice ecarts evaluateurs: {args.gap_matrix_out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
