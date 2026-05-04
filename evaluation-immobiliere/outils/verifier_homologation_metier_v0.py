from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
RUNTIME_DIR_DEFAULT = PROJECT_ROOT / "tests" / "runtime"
GRILLE_PATH_DEFAULT = PROJECT_ROOT / "atelier" / "HOMOLOGATION-METIER-GRILLE-V1.json"
EXTERNAL_REVIEWS_DEFAULT = PROJECT_ROOT / "tests" / "fixtures_external" / "homologation_evaluateurs_v1.json"
CLOSURE_REGISTER_DEFAULT = PROJECT_ROOT / "atelier" / "REGISTRE-FERMETURE-ECARTS-EVALUATEURS-V1.json"
REPORT_JSON_NAME = "homologation_metier_report.json"
REPORT_MD_NAME = "HOMOLOGATION-METIER-EVIDENCE-V1.md"
RELEASE_CANDIDATE_REPORT_NAME = "release_candidate_report.json"
PV_DEFAULT = PROJECT_ROOT / "atelier" / "PV-HOMOLOGATION-V1.md"

READY_STATUS = "PRET_REVISION_FINALE"
DRAFT_STATUS = "BROUILLON"
REVIEW_STATUS = "A_REVOIR"
WAITING_FIELD_STATUS = "EN_ATTENTE_REPONSES_TERRAIN"
RUNTIME_OK_STATUS = "PRET_HOMOLOGATION_SYNTHETIQUE_EN_ATTENTE_TERRAIN"
RUNTIME_FAIL_STATUS = "NO_GO_HOMOLOGATION_METIER"
SIGNED_STATUS = "SIGNE"
REQUIRED_SIGNATURE_ROLES = {"Lead Metier", "Product"}
ACCEPTABLE_CLOSURE_STATUSES = {"FERME", "ACCEPTE_FORMELLEMENT", "NON_APPLICABLE"}


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


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def normalize_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_case_dir(case: dict[str, Any], runtime_dir: Path) -> Path:
    raw = str(case.get("artifact_dir") or "").strip()
    if raw:
        path = Path(raw)
        if path.name:
            return runtime_dir / path.name
    return runtime_dir / str(case.get("dossier_id") or "unknown")


def load_summary(runtime_dir: Path) -> list[dict[str, Any]]:
    payload = load_json(runtime_dir / "runtime_summary.json")
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def count_sources(case_dir: Path) -> int:
    source_index = read_json_dict(case_dir / "data-facts.source_index.json")
    return len([source for source in as_list(source_index.get("sources")) if isinstance(source, dict) and source.get("source_id")])


def count_fiche_source_ids(case_dir: Path) -> int:
    fiche = read_json_dict(case_dir / "data-facts.fiche_bien.json")
    return len([source_id for source_id in as_list(fiche.get("source_ids")) if str(source_id).strip()])


def count_comparables(case_dir: Path) -> int:
    comps = read_json_dict(case_dir / "comps-market.comparables_proposes.json")
    return len([comp for comp in as_list(comps.get("comparables")) if isinstance(comp, dict)])


def count_justifications(case_dir: Path) -> int:
    justifications = read_json_dict(case_dir / "comps-market.justifications_comparables.json")
    return len([item for item in as_list(justifications.get("justifications")) if isinstance(item, dict)])


def valuation_values(case_dir: Path) -> dict[str, Any]:
    status = read_json_dict(case_dir / "compliance-qa.statut_sortie.json")
    return as_dict(status.get("valuation_values"))


def status_artifact(case_dir: Path) -> dict[str, Any]:
    return read_json_dict(case_dir / "compliance-qa.statut_sortie.json")


def recommendations_present(case_dir: Path) -> bool:
    text = read_text(case_dir / "compliance-qa.recommandations_corrections.md")
    return "# recommandations_corrections.md" in text and "## recommendations" in text and len(text.strip()) > 80


def redaction_artifacts_present(case_dir: Path) -> bool:
    report = read_text(case_dir / "redaction.brouillon_rapport.md")
    annex = read_text(case_dir / "redaction.annexe_sources.md")
    return "# brouillon_rapport.md" in report and "# annexe_sources.md" in annex


def calculation_trace_complete(case_dir: Path, required_approaches: list[str]) -> bool:
    artifact_by_approach = {
        "approche_comparative": "valuation-draft.calculs_approche_comparative.json",
        "approche_cout": "valuation-draft.calculs_approche_cout.json",
        "approche_revenu": "valuation-draft.calculs_approche_revenu.json",
    }
    for approach in required_approaches:
        artifact_name = artifact_by_approach.get(approach)
        if not artifact_name:
            return False
        payload = read_json_dict(case_dir / artifact_name)
        trace = as_dict(payload.get("trace"))
        if not is_number(payload.get("value")):
            return False
        if "selected_comparables" not in trace or not isinstance(trace.get("selected_comparables"), list):
            return False
        if "weights_used" not in trace or not isinstance(trace.get("weights_used"), list):
            return False
        if not as_list(trace.get("calculation_policy")):
            return False
    return True


def valuation_values_positive(values: dict[str, Any], required_approaches: list[str]) -> bool:
    for approach in required_approaches:
        value = values.get(approach)
        if not is_number(value) or float(value) <= 0:
            return False
    return True


def documented_blocking(case: dict[str, Any], status_payload: dict[str, Any]) -> bool:
    case_blocking = {str(item) for item in as_list(case.get("blocking_failures")) if str(item).strip()}
    payload_blocking = {str(item) for item in as_list(status_payload.get("blocking_failures")) if str(item).strip()}
    return bool(case_blocking) and case_blocking.issubset(payload_blocking)


def documented_warnings(case: dict[str, Any], status_payload: dict[str, Any]) -> bool:
    case_warnings = {str(item) for item in as_list(case.get("warnings")) if str(item).strip()}
    payload_warnings = {str(item) for item in as_list(status_payload.get("warnings")) if str(item).strip()}
    return bool(case_warnings) and case_warnings.issubset(payload_warnings)


def evaluate_case(case: dict[str, Any], runtime_dir: Path, grille: dict[str, Any]) -> dict[str, Any]:
    status = str(case.get("status") or "UNKNOWN")
    case_dir = resolve_case_dir(case, runtime_dir)
    status_payload = status_artifact(case_dir)
    required_approaches = [str(item) for item in as_list(grille.get("required_valuation_approaches"))]
    minimums = as_dict(grille.get("minimums"))
    source_min = int(minimums.get("source_count_for_ready_or_draft", 1))
    comp_min = int(minimums.get("comparables_for_ready_or_draft", 1))

    metrics = {
        "sources_count": count_sources(case_dir),
        "fiche_source_ids_count": count_fiche_source_ids(case_dir),
        "comparables_count": count_comparables(case_dir),
        "justifications_count": count_justifications(case_dir),
        "valuation_values": valuation_values(case_dir),
        "calculation_traces_complete": calculation_trace_complete(case_dir, required_approaches),
        "recommendations_present": recommendations_present(case_dir),
        "redaction_artifacts_present": redaction_artifacts_present(case_dir),
    }

    errors: list[str] = []
    warnings: list[str] = []

    allowed_statuses = set(str(item) for item in as_list(grille.get("status_allowed")))
    if status not in allowed_statuses:
        errors.append(f"statut runtime non autorise: {status}")
    if status_payload.get("status") != status:
        errors.append(f"statut compliance divergent: {status_payload.get('status')} != {status}")

    if status in {READY_STATUS, DRAFT_STATUS}:
        if as_list(case.get("blocking_failures")):
            errors.append(f"{status}: blocages presents")
        if metrics["sources_count"] < source_min or metrics["fiche_source_ids_count"] < source_min:
            errors.append(f"{status}: sources insuffisantes")
        if metrics["comparables_count"] < comp_min:
            errors.append(f"{status}: comparables insuffisants")
        if not valuation_values_positive(metrics["valuation_values"], required_approaches):
            errors.append(f"{status}: valeurs de valuation non positives ou incompletes")
        if not metrics["calculation_traces_complete"]:
            errors.append(f"{status}: traces de calcul incompletes")
        if not metrics["redaction_artifacts_present"]:
            errors.append(f"{status}: artefacts de redaction absents")

    if status == READY_STATUS:
        if as_list(case.get("warnings")):
            errors.append(f"{READY_STATUS}: warnings presents")

    if status == DRAFT_STATUS:
        if not as_list(case.get("warnings")):
            errors.append(f"{DRAFT_STATUS}: aucun warning documente")
        if not documented_warnings(case, status_payload):
            errors.append(f"{DRAFT_STATUS}: warnings non reportes dans statut_sortie")
        if not metrics["recommendations_present"]:
            errors.append(f"{DRAFT_STATUS}: recommandations absentes")

    if status == REVIEW_STATUS:
        if not as_list(case.get("blocking_failures")):
            errors.append(f"{REVIEW_STATUS}: aucun blocage documente")
        if not documented_blocking(case, status_payload):
            errors.append(f"{REVIEW_STATUS}: blocages non reportes dans statut_sortie")
        if not metrics["recommendations_present"]:
            errors.append(f"{REVIEW_STATUS}: recommandations absentes")
        if metrics["redaction_artifacts_present"]:
            warnings.append(f"{REVIEW_STATUS}: redaction presente malgre arret attendu")

    decision = case_decision(status, errors)
    return {
        "dossier_id": case.get("dossier_id", ""),
        "status": status,
        "decision": decision,
        "artifact_dir": normalize_path(case_dir),
        "metrics": metrics,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def case_decision(status: str, errors: list[str]) -> str:
    if errors:
        return "NON_HOMOLOGABLE"
    if status == READY_STATUS:
        return "PRET_REVISION_EVALUATEUR"
    if status == DRAFT_STATUS:
        return "BROUILLON_CORRECTIONS_MINEURES"
    if status == REVIEW_STATUS:
        return "RETOUR_CORRECTION_OBLIGATOIRE"
    return "STATUT_INCONNU"


def evaluate_external_reviews(path: Path, grille: dict[str, Any], *, require_external_reviews: bool) -> tuple[dict[str, Any], list[str], list[str]]:
    policy = as_dict(grille.get("external_review_policy"))
    errors: list[str] = []
    warnings: list[str] = []
    if not path.exists():
        status = str(policy.get("default_status_when_absent") or WAITING_FIELD_STATUS)
        payload = {
            "status": status,
            "path": normalize_path(path),
            "reviews_count": 0,
            "reviewers_count": 0,
            "reviewed_pilot_cases": 0,
            "gap_counts_by_priority": {},
            "decisions_count": {},
        }
        message = f"revues evaluateurs absentes: {normalize_path(path)}"
        if require_external_reviews:
            errors.append(message)
        else:
            warnings.append(message)
        return payload, errors, warnings

    raw = load_json(path)
    reviews = as_list(raw.get("reviews")) if isinstance(raw, dict) else []
    allowed = set(str(item) for item in as_list(policy.get("allowed_decisions")))
    blocking_decisions = set(str(item) for item in as_list(policy.get("blocking_decisions") or ["REJETE"]))
    blocking_gap_priorities = set(str(item).upper() for item in as_list(policy.get("blocking_gap_priorities") or ["P0"]))
    reviewers = {str(review.get("reviewer_id") or review.get("reviewer_role") or "") for review in reviews if isinstance(review, dict)}
    reviewed_pilots = {
        str(review.get("dossier_id") or "")
        for review in reviews
        if isinstance(review, dict) and str(review.get("dossier_id") or "").startswith("D-PILOTE-")
    }
    decisions = Counter(str(review.get("decision") or "INCONNU") for review in reviews if isinstance(review, dict))
    gap_counts: Counter[str] = Counter()

    for idx, review in enumerate(reviews):
        if not isinstance(review, dict):
            errors.append(f"review[{idx}] invalide")
            continue
        if review.get("decision") not in allowed:
            errors.append(f"review[{idx}] decision invalide: {review.get('decision')}")
        if review.get("decision") in blocking_decisions:
            errors.append(f"review[{idx}] decision bloquante evaluateur: {review.get('decision')}")
        if not review.get("dossier_id"):
            errors.append(f"review[{idx}] dossier_id absent")
        for gap_idx, gap in enumerate(as_list(review.get("gaps") or review.get("ecarts"))):
            if not isinstance(gap, dict):
                errors.append(f"review[{idx}].gap[{gap_idx}] invalide")
                continue
            priority = str(gap.get("priority") or "").upper()
            gap_id = str(gap.get("gap_id") or f"gap[{gap_idx}]")
            gap_counts.update([priority or "INCONNU"])
            if priority in blocking_gap_priorities:
                errors.append(f"review[{idx}] {gap_id}: ecart bloquant {priority}")
            elif priority:
                warnings.append(f"review[{idx}] {gap_id}: ecart conditionnel {priority}")

    min_reviewers = int(policy.get("minimum_reviewers", 2))
    min_pilots = int(policy.get("minimum_reviewed_pilot_cases", 3))
    if len([item for item in reviewers if item]) < min_reviewers:
        errors.append(f"revues evaluateurs: reviewers insuffisants ({len(reviewers)}/{min_reviewers})")
    if len([item for item in reviewed_pilots if item]) < min_pilots:
        errors.append(f"revues evaluateurs: dossiers pilotes insuffisants ({len(reviewed_pilots)}/{min_pilots})")

    status = "REVUES_TERRAIN_EXPLOITABLES" if not errors else "REVUES_TERRAIN_A_CORRIGER"
    return (
        {
            "status": status,
            "path": normalize_path(path),
            "reviews_count": len(reviews),
            "reviewers_count": len([item for item in reviewers if item]),
            "reviewed_pilot_cases": len([item for item in reviewed_pilots if item]),
            "gap_counts_by_priority": dict(gap_counts),
            "decisions_count": dict(decisions),
        },
        errors,
        warnings,
    )


def evaluate_gap_closure(
    path: Path,
    external: dict[str, Any],
    *,
    require_gap_closure: bool,
) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    external_status = str(external.get("status") or "")
    if external_status != "REVUES_TERRAIN_EXPLOITABLES":
        return (
            {
                "status": "NON_APPLICABLE_AVANT_REVUES_TERRAIN",
                "path": normalize_path(path),
                "closures_count": 0,
                "signed_roles": [],
            },
            errors,
            warnings,
        )

    if not path.exists():
        message = f"registre fermeture ecarts absent: {normalize_path(path)}"
        if require_gap_closure:
            errors.append(message)
        else:
            warnings.append(message)
        return (
            {
                "status": "EN_ATTENTE_FERMETURE_ECARTS",
                "path": normalize_path(path),
                "closures_count": 0,
                "signed_roles": [],
            },
            errors,
            warnings,
        )

    payload = load_json(path)
    if not isinstance(payload, dict) or payload.get("schema_version") != "registre_fermeture_ecarts_evaluateurs_v1":
        errors.append("registre fermeture ecarts invalide")
        payload = {}

    source = str(payload.get("source_external_reviews_fixture") or "").strip()
    expected_source = str(external.get("path") or "").strip()
    if source and source != expected_source:
        message = f"registre fermeture ecarts lie a une autre fixture: {source} != {expected_source}"
        if require_gap_closure:
            errors.append(message)
        else:
            warnings.append(message)

    closures = [item for item in as_list(payload.get("closures")) if isinstance(item, dict)]
    signatures = [item for item in as_list(payload.get("signatures")) if isinstance(item, dict)]
    closure_counts = Counter(str(item.get("closure_status") or "INCONNU") for item in closures)
    priority_closed_counts = Counter(
        str(item.get("priority") or "INCONNU").upper()
        for item in closures
        if str(item.get("closure_status") or "") in ACCEPTABLE_CLOSURE_STATUSES
    )
    external_gap_counts = as_dict(external.get("gap_counts_by_priority"))

    for priority in ("P0", "P1", "P2"):
        required = int(external_gap_counts.get(priority, 0) or 0)
        closed = int(priority_closed_counts.get(priority, 0) or 0)
        if closed < required:
            errors.append(f"fermetures {priority} insuffisantes ({closed}/{required})")

    signed_roles = sorted(
        str(signature.get("role") or "")
        for signature in signatures
        if str(signature.get("signature_status") or "") == SIGNED_STATUS and str(signature.get("role") or "")
    )
    missing_roles = sorted(role for role in REQUIRED_SIGNATURE_ROLES if role not in set(signed_roles))
    if missing_roles:
        message = "signatures metier manquantes: " + ", ".join(missing_roles)
        if require_gap_closure:
            errors.append(message)
        else:
            warnings.append(message)

    status = "FERMETURE_ECARTS_A_CORRIGER"
    if not errors and not missing_roles:
        status = "ECARTS_FERMES_SIGNATURES_SIGNEES"
    elif not errors:
        status = "ECARTS_FERMES_SIGNATURES_A_SIGNER"

    return (
        {
            "status": status,
            "path": normalize_path(path),
            "closures_count": len(closures),
            "closure_counts": dict(closure_counts),
            "priority_closed_counts": dict(priority_closed_counts),
            "signed_roles": signed_roles,
            "missing_signature_roles": missing_roles,
        },
        errors,
        warnings,
    )


def evaluate_release_candidate_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "A_PREPARER",
            "path": normalize_path(path),
            "decision": "A_PREPARER",
        }
    payload = read_json_dict(path)
    decision = str(payload.get("decision") or "UNKNOWN")
    status = "PRET_GO_LIVE_CONTROLE" if payload.get("ok") is True and decision == "PRET_GO_LIVE_CONTROLE" else "A_CORRIGER"
    return {
        "status": status,
        "path": normalize_path(path),
        "decision": decision,
        "release_candidate_id": payload.get("release_candidate_id", "UNKNOWN"),
        "go_live_status": payload.get("go_live_status", "UNKNOWN"),
        "commit_ref": payload.get("commit_ref", "UNKNOWN"),
    }


def validate_homologation_metier(
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    *,
    grille_path: Path = GRILLE_PATH_DEFAULT,
    external_reviews_path: Path = EXTERNAL_REVIEWS_DEFAULT,
    require_external_reviews: bool = False,
    closure_register_path: Path = CLOSURE_REGISTER_DEFAULT,
    require_gap_closure: bool = False,
    release_candidate_report_path: Path | None = None,
) -> dict[str, Any]:
    grille = load_json(grille_path)
    summary = load_summary(runtime_dir)
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(grille, dict) or grille.get("schema_version") != "homologation_metier_grille_v1":
        errors.append("grille homologation invalide")
        grille = {}

    cases = [evaluate_case(case, runtime_dir, grille) for case in summary]
    for case_report in cases:
        errors.extend(f"{case_report['dossier_id']}: {error}" for error in as_list(case_report.get("errors")))
        warnings.extend(f"{case_report['dossier_id']}: {warning}" for warning in as_list(case_report.get("warnings")))

    status_counts = Counter(str(case.get("status") or "UNKNOWN") for case in cases)
    pilot_cases_count = sum(1 for case in cases if str(case.get("dossier_id") or "").startswith("D-PILOTE-"))
    ready_cases_count = status_counts.get(READY_STATUS, 0)
    minimums = as_dict(grille.get("minimums"))
    min_cases = int(minimums.get("cases", 3))
    min_pilots = int(minimums.get("pilot_cases", 3))
    min_ready = int(minimums.get("ready_cases", 1))

    if len(cases) < min_cases:
        errors.append(f"dossiers insuffisants pour homologation synthetique ({len(cases)}/{min_cases})")
    if pilot_cases_count < min_pilots:
        errors.append(f"dossiers pilotes insuffisants ({pilot_cases_count}/{min_pilots})")
    if ready_cases_count < min_ready:
        errors.append(f"dossiers prets revision insuffisants ({ready_cases_count}/{min_ready})")

    external, external_errors, external_warnings = evaluate_external_reviews(
        external_reviews_path,
        grille,
        require_external_reviews=require_external_reviews,
    )
    errors.extend(external_errors)
    warnings.extend(external_warnings)

    gap_closure, closure_errors, closure_warnings = evaluate_gap_closure(
        closure_register_path,
        external,
        require_gap_closure=require_gap_closure,
    )
    errors.extend(closure_errors)
    warnings.extend(closure_warnings)
    release_candidate = evaluate_release_candidate_snapshot(release_candidate_report_path or runtime_dir / RELEASE_CANDIDATE_REPORT_NAME)

    ok = not errors
    runtime_decision = RUNTIME_OK_STATUS if ok else RUNTIME_FAIL_STATUS
    production_decision = "NO_GO_PROD_PREPARATION"
    if ok and external.get("status") == "REVUES_TERRAIN_EXPLOITABLES":
        production_decision = "GO_CONDITIONNEL_SIGNATURE_METIER"
        if gap_closure.get("status") == "ECARTS_FERMES_SIGNATURES_A_SIGNER":
            production_decision = "PRET_SIGNATURE_PROD"
        if gap_closure.get("status") == "ECARTS_FERMES_SIGNATURES_SIGNEES":
            production_decision = "GO_PROD_PREPARATION"

    return {
        "schema_version": "homologation_metier_report_v1",
        "ok": ok,
        "runtime_decision": runtime_decision,
        "production_decision": production_decision,
        "runtime_dir": normalize_path(runtime_dir),
        "grille_path": normalize_path(grille_path),
        "cases_count": len(cases),
        "pilot_cases_count": pilot_cases_count,
        "status_counts": dict(status_counts),
        "external_reviews": external,
        "gap_closure": gap_closure,
        "release_candidate": release_candidate,
        "errors": errors,
        "warnings": warnings,
        "cases": cases,
    }


def build_markdown(report: dict[str, Any]) -> str:
    external = as_dict(report.get("external_reviews"))
    gap_counts = as_dict(external.get("gap_counts_by_priority"))
    gap_closure = as_dict(report.get("gap_closure"))
    release_candidate = as_dict(report.get("release_candidate"))
    lines = [
        "# Homologation Metier Evidence V1",
        "",
        "## Synthese",
        "",
        f"- OK runtime synthetique: **{str(report.get('ok')).lower()}**",
        f"- Decision runtime: **{report.get('runtime_decision', 'UNKNOWN')}**",
        f"- Decision production: **{report.get('production_decision', 'UNKNOWN')}**",
        f"- Dossiers analyses: **{report.get('cases_count', 0)}**",
        f"- Dossiers pilotes: **{report.get('pilot_cases_count', 0)}**",
        f"- Revues terrain: **{external.get('status', 'UNKNOWN')}**",
        f"- Fermeture ecarts: **{gap_closure.get('status', 'UNKNOWN')}**",
        f"- Release candidate: **{release_candidate.get('status', 'UNKNOWN')}**",
        f"- Ecarts evaluateurs P1/P2: **{int(gap_counts.get('P1', 0) or 0) + int(gap_counts.get('P2', 0) or 0)}**",
        f"- Erreurs: **{len(as_list(report.get('errors')))}**",
        f"- Warnings: **{len(as_list(report.get('warnings')))}**",
        "",
        "## Distribution Statuts",
        "",
    ]
    for status, count in as_dict(report.get("status_counts")).items():
        lines.append(f"- {status}: {count}")

    lines.extend(
        [
            "",
            "## Dossiers",
            "",
            "| Dossier | Statut | Decision | Sources | Comparables | Traces calcul | Redaction | Erreurs |",
            "|---|---|---|---:|---:|---|---|---:|",
        ]
    )
    for case in as_list(report.get("cases")):
        if not isinstance(case, dict):
            continue
        metrics = as_dict(case.get("metrics"))
        lines.append(
            "| {dossier} | {status} | {decision} | {sources} | {comparables} | {traces} | {redaction} | {errors} |".format(
                dossier=case.get("dossier_id", ""),
                status=case.get("status", "UNKNOWN"),
                decision=case.get("decision", "UNKNOWN"),
                sources=metrics.get("sources_count", 0),
                comparables=metrics.get("comparables_count", 0),
                traces="oui" if metrics.get("calculation_traces_complete") else "non",
                redaction="oui" if metrics.get("redaction_artifacts_present") else "non",
                errors=len(as_list(case.get("errors"))),
            )
        )

    if report.get("errors"):
        lines.extend(["", "## Erreurs", ""])
        for error in as_list(report.get("errors")):
            lines.append(f"- {error}")

    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for warning in as_list(report.get("warnings")):
            lines.append(f"- {warning}")

    return "\n".join(lines).rstrip() + "\n"


def build_pv_markdown(report: dict[str, Any]) -> str:
    external = as_dict(report.get("external_reviews"))
    external_status = external.get("status", "UNKNOWN")
    gap_counts = as_dict(external.get("gap_counts_by_priority"))
    gap_closure = as_dict(report.get("gap_closure"))
    release_candidate = as_dict(report.get("release_candidate"))
    status_counts = as_dict(report.get("status_counts"))
    p0_open = int(gap_counts.get("P0", 0) or 0)
    if not report.get("ok"):
        p0_open = max(p0_open, len(as_list(report.get("errors"))))
    external_p1_p2 = int(gap_counts.get("P1", 0) or 0) + int(gap_counts.get("P2", 0) or 0)
    if gap_closure.get("status") == "ECARTS_FERMES_SIGNATURES_SIGNEES":
        p1_open = 0
    else:
        p1_open = external_p1_p2
    if p1_open == 0 and external_p1_p2 == 0:
        p1_open = len(as_list(report.get("warnings")))
    go_production = "PREPARATION_AUTORISEE" if report.get("production_decision") == "GO_PROD_PREPARATION" else "NON"
    go_live = release_candidate.get("go_live_status", "A_PREPARER")
    signed_roles = set(str(role) for role in as_list(gap_closure.get("signed_roles")))
    lines = [
        "# PV HOMOLOGATION V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Objet",
        "Proces-verbal preparatoire d'homologation metier et pre-production multi-parties.",
        "",
        "## Decision",
        "",
        f"- Decision runtime metier: **{report.get('runtime_decision', 'UNKNOWN')}**",
        f"- Decision Phase J: **{report.get('production_decision', 'UNKNOWN')}**",
        f"- Revues terrain: **{external_status}**",
        f"- Fermeture ecarts: **{gap_closure.get('status', 'UNKNOWN')}**",
        f"- Release candidate: **{release_candidate.get('status', 'UNKNOWN')}**",
        f"- P0 ouverts: **{p0_open}**",
        f"- P1/P2 ouverts: **{p1_open}**",
        f"- Go production: **{go_production}**",
        f"- Go live: **{go_live}**",
        "",
        "## Synthese Runtime",
        "",
        f"- Dossiers analyses: **{report.get('cases_count', 0)}**",
        f"- Dossiers pilotes: **{report.get('pilot_cases_count', 0)}**",
        f"- PRET_REVISION_FINALE: **{status_counts.get(READY_STATUS, 0)}**",
        f"- BROUILLON: **{status_counts.get(DRAFT_STATUS, 0)}**",
        f"- A_REVOIR: **{status_counts.get(REVIEW_STATUS, 0)}**",
        "",
        "## Conditions avant Go production",
        "",
        "- Revues terrain signees par au moins deux evaluateurs agrees.",
        "- Couverture de trois dossiers pilotes revue et acceptee.",
        "- Tous les ecarts P0 fermes, P1/P2 acceptes formellement ou fermes.",
        "- Dress rehearsal staging rejoue avec CI/CD et rollback.",
        "- Signature metier et Product obtenue.",
        "",
        "## Signatures",
        "",
        "| Role | Owner | Statut | Commentaire |",
        "|---|---|---|---|",
        f"| Lead Metier | A nommer | {'SIGNE' if 'Lead Metier' in signed_roles else 'A_SIGNER'} | {'Preparation prod approuvee' if 'Lead Metier' in signed_roles else 'Bloque par signature finale'} |",
        f"| Product | A nommer | {'SIGNE' if 'Product' in signed_roles else 'A_SIGNER'} | {'Preparation prod approuvee' if 'Product' in signed_roles else 'Bloque par signature finale'} |",
        "| Platform | A nommer | A_SIGNER | Preprod preparable |",
        f"| QA/Securite | A nommer | {'SIGNE' if 'QA/Securite' in signed_roles else 'A_SIGNER'} | {'Controles finaux approuves' if 'QA/Securite' in signed_roles else 'Revue finale requise'} |",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, Any], json_out: Path, markdown_out: Path, pv_out: Path | None) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")
    if pv_out is not None:
        pv_out.parent.mkdir(parents=True, exist_ok=True)
        pv_out.write_text(build_pv_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifier l'homologation metier synthetique des sorties runtime.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--grille", type=Path, default=GRILLE_PATH_DEFAULT)
    parser.add_argument("--external-reviews", type=Path, default=EXTERNAL_REVIEWS_DEFAULT)
    parser.add_argument("--require-external-reviews", action="store_true")
    parser.add_argument("--closure-register", type=Path, default=CLOSURE_REGISTER_DEFAULT)
    parser.add_argument("--require-gap-closure", action="store_true")
    parser.add_argument("--release-candidate-report", type=Path, default=None)
    parser.add_argument("--report-out", type=Path, default=None)
    parser.add_argument("--markdown-out", type=Path, default=None)
    parser.add_argument("--pv-out", type=Path, default=PV_DEFAULT)
    parser.add_argument("--no-pv", action="store_true")
    args = parser.parse_args()

    report = validate_homologation_metier(
        runtime_dir=args.runtime_dir,
        grille_path=args.grille,
        external_reviews_path=args.external_reviews,
        require_external_reviews=args.require_external_reviews,
        closure_register_path=args.closure_register,
        require_gap_closure=args.require_gap_closure,
        release_candidate_report_path=args.release_candidate_report,
    )
    report_out = args.report_out or args.runtime_dir / REPORT_JSON_NAME
    markdown_out = args.markdown_out or args.runtime_dir / REPORT_MD_NAME
    pv_out = None if args.no_pv else args.pv_out
    write_outputs(report, report_out, markdown_out, pv_out)

    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, ensure_ascii=False, indent=2))
    print(f"Rapport homologation metier JSON: {report_out}")
    print(f"Preuve homologation metier Markdown: {markdown_out}")
    if pv_out is not None:
        print(f"PV homologation: {pv_out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
