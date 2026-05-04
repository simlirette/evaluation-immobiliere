from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
from verifier_revues_evaluateurs_externes_v1 import validate_external_evaluator_reviews  # noqa: E402

REGISTER_DEFAULT = PROJECT_ROOT / "atelier" / "REGISTRE-FERMETURE-ECARTS-EVALUATEURS-V1.json"
REPORT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "fermeture_ecarts_evaluateurs_report.json"
REPORT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "FERMETURE-ECARTS-EVALUATEURS-EVIDENCE-V1.md"
PV_SIGNATURE_DEFAULT = PROJECT_ROOT / "atelier" / "PV-SIGNATURE-METIER-V1.md"

VALID_SCHEMA = "registre_fermeture_ecarts_evaluateurs_v1"
SIGNED_STATUS = "SIGNE"
DEFAULT_ACCEPTABLE_STATUSES = {"FERME", "ACCEPTE_FORMELLEMENT", "NON_APPLICABLE"}
DEFAULT_REQUIRED_SIGNATURE_ROLES = {"Lead Metier", "Product"}


def validate_gap_closure_register(
    register_path: Path = REGISTER_DEFAULT,
    *,
    external_reviews_path: Path = EXTERNAL_REVIEWS_DEFAULT,
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    grille_path: Path = GRILLE_PATH_DEFAULT,
    strict: bool = False,
) -> dict[str, Any]:
    external_report = validate_external_evaluator_reviews(
        external_reviews_path,
        runtime_dir=runtime_dir,
        grille_path=grille_path,
        strict=True,
    )
    errors: list[str] = []
    warnings: list[str] = []
    if not external_report.get("ok"):
        errors.append("revues evaluateurs externes non exploitables")
        errors.extend(str(error) for error in as_list(external_report.get("errors")))

    if not register_path.exists():
        message = f"registre fermeture ecarts absent: {normalize_path(register_path)}"
        if strict:
            errors.append(message)
        else:
            warnings.append(message)
        return build_report(
            register_path,
            external_report,
            {},
            errors,
            warnings,
            strict,
            closures=[],
            signatures=[],
            missing_gap_ids=[gap_id(gap) for gap in external_gaps_to_close(external_report)],
        )

    payload = load_json(register_path)
    if not isinstance(payload, dict):
        errors.append("registre fermeture invalide: racine JSON objet attendue")
        payload = {}
    if payload.get("schema_version") != VALID_SCHEMA:
        errors.append(f"schema_version invalide: {payload.get('schema_version') or 'absent'}")

    source = str(payload.get("source_external_reviews_fixture") or "").strip()
    expected_source = str(external_report.get("source_path") or "").strip()
    if source and source != expected_source:
        message = f"registre lie a une autre fixture: {source} != {expected_source}"
        if strict:
            errors.append(message)
        else:
            warnings.append(message)

    policy = as_dict(payload.get("closure_policy"))
    acceptable_statuses = {
        str(status)
        for status in as_list(policy.get("acceptable_statuses"))
        if str(status).strip()
    } or DEFAULT_ACCEPTABLE_STATUSES
    required_roles = {
        str(role)
        for role in as_list(policy.get("required_signature_roles"))
        if str(role).strip()
    } or DEFAULT_REQUIRED_SIGNATURE_ROLES
    p0_required_status = str(policy.get("p0_requires_status") or "FERME")

    closures = [item for item in as_list(payload.get("closures")) if isinstance(item, dict)]
    signatures = [item for item in as_list(payload.get("signatures")) if isinstance(item, dict)]
    closure_by_gap = {str(closure.get("gap_id") or ""): closure for closure in closures if closure.get("gap_id")}
    missing_gap_ids: list[str] = []

    for gap in external_gaps_to_close(external_report):
        expected_id = gap_id(gap)
        closure = closure_by_gap.get(expected_id)
        if not closure:
            missing_gap_ids.append(expected_id)
            errors.append(f"{expected_id}: fermeture absente")
            continue
        closure_status = str(closure.get("closure_status") or "").strip()
        priority = str(gap.get("priority") or "").strip().upper()
        if closure_status not in acceptable_statuses:
            errors.append(f"{expected_id}: statut fermeture invalide: {closure_status or 'absent'}")
        if priority == "P0" and closure_status != p0_required_status:
            errors.append(f"{expected_id}: P0 doit etre {p0_required_status}")
        for field in ("owner", "closed_at", "evidence", "action"):
            if not str(closure.get(field) or "").strip():
                errors.append(f"{expected_id}: champ {field} absent")

    signed_roles = {
        str(signature.get("role") or "").strip()
        for signature in signatures
        if str(signature.get("signature_status") or "").strip() == SIGNED_STATUS
    }
    missing_roles = sorted(role for role in required_roles if role not in signed_roles)
    for role in missing_roles:
        errors.append(f"signature requise manquante: {role}")

    for signature in signatures:
        role = str(signature.get("role") or "role inconnu").strip()
        if str(signature.get("signature_status") or "").strip() == SIGNED_STATUS and not str(signature.get("signed_at") or "").strip():
            errors.append(f"{role}: signed_at absent")

    return build_report(
        register_path,
        external_report,
        payload,
        errors,
        warnings,
        strict,
        closures=closures,
        signatures=signatures,
        missing_gap_ids=missing_gap_ids,
    )


def external_gaps_to_close(external_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        gap
        for gap in as_list(external_report.get("gaps"))
        if isinstance(gap, dict) and str(gap.get("priority") or "").strip().upper() in {"P0", "P1", "P2"}
    ]


def gap_id(gap: dict[str, Any]) -> str:
    return str(gap.get("gap_id") or "").strip()


def build_report(
    register_path: Path,
    external_report: dict[str, Any],
    payload: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    strict: bool,
    *,
    closures: list[dict[str, Any]],
    signatures: list[dict[str, Any]],
    missing_gap_ids: list[str],
) -> dict[str, Any]:
    closure_counts = Counter(str(closure.get("closure_status") or "INCONNU") for closure in closures)
    closure_priority_counts = Counter(str(closure.get("priority") or "INCONNU").upper() for closure in closures)
    signed_roles = sorted(
        str(signature.get("role") or "")
        for signature in signatures
        if str(signature.get("signature_status") or "") == SIGNED_STATUS and str(signature.get("role") or "")
    )
    ok = not errors
    if not ok:
        decision = "NO_GO_FERMETURE_ECARTS"
    elif missing_gap_ids:
        decision = "NO_GO_FERMETURE_ECARTS"
    else:
        decision = "GO_PROD_PREPARATION"

    return {
        "schema_version": "fermeture_ecarts_evaluateurs_gate_v1",
        "ok": ok,
        "strict": strict,
        "decision": decision,
        "register_path": normalize_path(register_path),
        "external_reviews_decision": external_report.get("decision", "UNKNOWN"),
        "external_reviews_source": external_report.get("source_path", "-"),
        "external_gaps_to_close": len(external_gaps_to_close(external_report)),
        "closures_count": len(closures),
        "closure_counts": dict(closure_counts),
        "closure_priority_counts": dict(closure_priority_counts),
        "signed_roles": signed_roles,
        "missing_gap_ids": missing_gap_ids,
        "errors": errors,
        "warnings": warnings,
        "signatures": signatures,
        "closures": sorted(closures, key=lambda item: str(item.get("gap_id") or "")),
        "source_schema_version": payload.get("schema_version", "UNKNOWN"),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Fermeture ecarts evaluateurs Evidence V1",
        "",
        "## Synthese",
        "",
        f"- OK gate strict: **{str(report.get('ok')).lower()}**",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- Registre: `{report.get('register_path', '-')}`",
        f"- Ecarts externes a fermer: **{report.get('external_gaps_to_close', 0)}**",
        f"- Fermetures: **{report.get('closures_count', 0)}**",
        f"- Roles signes: **{len(as_list(report.get('signed_roles')))}**",
        f"- Erreurs: **{len(as_list(report.get('errors')))}**",
        f"- Warnings: **{len(as_list(report.get('warnings')))}**",
        "",
        "## Fermetures",
        "",
    ]
    lines.extend(build_closure_table(report))
    lines.extend(["", "## Signatures", ""])
    lines.extend(build_signature_table(report))
    lines.extend(["", "## Erreurs", ""])
    lines.extend(render_list(report.get("errors")))
    lines.extend(["", "## Warnings", ""])
    lines.extend(render_list(report.get("warnings")))
    return "\n".join(lines).rstrip() + "\n"


def build_pv_signature_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# PV SIGNATURE METIER V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Decision",
        "",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- Ecarts fermes ou acceptes: **{report.get('closures_count', 0)}/{report.get('external_gaps_to_close', 0)}**",
        f"- Roles signes: **{format_items(report.get('signed_roles'))}**",
        "- Go live: **A_PLANIFIER_APRES_DRESS_REHEARSAL**",
        "",
        "## Fermeture des ecarts",
        "",
    ]
    lines.extend(build_closure_table(report))
    lines.extend(["", "## Signatures", ""])
    lines.extend(build_signature_table(report))
    lines.extend(
        [
            "",
            "## Conditions restantes",
            "",
            "- Dress rehearsal staging rejoue sur le commit a promouvoir.",
            "- CI verte sur le commit exact.",
            "- Runbook rollback relu et lie au tag release-candidate.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_closure_table(report: dict[str, Any]) -> list[str]:
    closures = [item for item in as_list(report.get("closures")) if isinstance(item, dict)]
    if not closures:
        return ["- Aucune fermeture documentee."]
    lines = [
        "| Ecart | Priorite | Dossier | Statut | Owner | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for closure in closures:
        lines.append(
            "| {gap_id} | {priority} | {dossier} | {status} | {owner} | {evidence} |".format(
                gap_id=closure.get("gap_id", "-"),
                priority=closure.get("priority", "-"),
                dossier=closure.get("dossier_id", "-"),
                status=closure.get("closure_status", "-"),
                owner=closure.get("owner", "-"),
                evidence=closure.get("evidence", "-"),
            )
        )
    return lines


def build_signature_table(report: dict[str, Any]) -> list[str]:
    signatures = [item for item in as_list(report.get("signatures")) if isinstance(item, dict)]
    if not signatures:
        return ["- Aucune signature documentee."]
    lines = [
        "| Role | Owner | Statut | Decision | Date |",
        "|---|---|---|---|---|",
    ]
    for signature in signatures:
        lines.append(
            "| {role} | {owner} | {status} | {decision} | {date} |".format(
                role=signature.get("role", "-"),
                owner=signature.get("owner", "-"),
                status=signature.get("signature_status", "-"),
                decision=signature.get("decision", "-"),
                date=signature.get("signed_at", "-"),
            )
        )
    return lines


def render_list(items: object) -> list[str]:
    values = [str(item) for item in as_list(items) if str(item)]
    if not values:
        return ["- Aucune."]
    return [f"- {item}" for item in values]


def format_items(items: object) -> str:
    values = [str(item) for item in as_list(items) if str(item)]
    return ", ".join(values) if values else "-"


def write_outputs(report: dict[str, Any], json_out: Path, markdown_out: Path, pv_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    pv_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")
    pv_out.write_text(build_pv_signature_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie la fermeture des ecarts evaluateurs externes avant preparation prod.")
    parser.add_argument("--register", type=Path, default=REGISTER_DEFAULT)
    parser.add_argument("--external-reviews", type=Path, default=EXTERNAL_REVIEWS_DEFAULT)
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--grille", type=Path, default=GRILLE_PATH_DEFAULT)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report-out", type=Path, default=REPORT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD_DEFAULT)
    parser.add_argument("--pv-out", type=Path, default=PV_SIGNATURE_DEFAULT)
    args = parser.parse_args()

    report = validate_gap_closure_register(
        args.register,
        external_reviews_path=args.external_reviews,
        runtime_dir=args.runtime_dir,
        grille_path=args.grille,
        strict=args.strict,
    )
    write_outputs(report, args.report_out, args.markdown_out, args.pv_out)
    print(json.dumps({key: value for key, value in report.items() if key not in {"closures", "signatures"}}, ensure_ascii=False, indent=2))
    print(f"Rapport fermeture ecarts JSON: {args.report_out}")
    print(f"Preuve fermeture ecarts Markdown: {args.markdown_out}")
    print(f"PV signature metier: {args.pv_out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
