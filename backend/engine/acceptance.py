"""Acceptance helpers for anonymized evaluator dossier trials."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)")
_SIN_RE = re.compile(r"(?<!\d)\d{3}[\s-]?\d{3}[\s-]?\d{3}(?!\d)")
_POSTAL_RE = re.compile(r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d\b", re.IGNORECASE)
_PII_FIELDS = {
    "nom",
    "prenom",
    "telephone",
    "phone",
    "courriel",
    "email",
    "adresse",
    "client",
    "proprietaire",
    "owner",
}
_ANON_OK_MARKERS = ("anon", "anonym", "[", "redacted", "masque", "pilote", "exemple")
_RUNTIME_BLOCKED_STATUSES = {"A_REVOIR", "BLOCKED", "BLOQUE", "CONFLIT_DETECTE", "FAILED", "ERROR"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _string_values(payload: Any, path: str = "") -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child_path = f"{path}.{key}" if path else str(key)
            values.extend(_string_values(value, child_path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            child_path = f"{path}[{index}]"
            values.extend(_string_values(value, child_path))
    elif isinstance(payload, str):
        values.append((path, payload))
    return values


def _looks_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return any(marker in lowered for marker in _ANON_OK_MARKERS)


def _append_missing(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate_anonymized_case(case: dict[str, Any]) -> dict[str, Any]:
    """Validate that an acceptance fixture is usable and anonymized."""
    errors: list[str] = []
    warnings: list[str] = []

    _append_missing(errors, bool(str(case.get("dossier_id") or "").strip()), "dossier_id_missing")
    _append_missing(errors, bool(str(case.get("date_reference") or "").strip()), "date_reference_missing")
    _append_missing(errors, bool(str(case.get("type_bien") or "").strip()), "type_bien_missing")
    _append_missing(errors, bool(str(case.get("adresse_anonymisee") or "").strip()), "adresse_anonymisee_missing")
    if case.get("adresse") and not _looks_placeholder(str(case.get("adresse"))):
        errors.append("raw_address_present")

    commanditaire = case.get("commanditaire") if isinstance(case.get("commanditaire"), dict) else {}
    _append_missing(errors, bool(commanditaire.get("fin_evaluation")), "commanditaire_fin_evaluation_missing")
    for key in ("nom", "organisation"):
        value = str(commanditaire.get(key) or "")
        if value and not _looks_placeholder(value):
            warnings.append(f"commanditaire_{key}_not_obviously_anonymized")

    comparables = case.get("comparables") if isinstance(case.get("comparables"), list) else []
    if len(comparables) < 3:
        errors.append("comparables_minimum_not_met")
    for index, comparable in enumerate(comparables):
        if not isinstance(comparable, dict):
            errors.append(f"comparables[{index}]_invalid")
            continue
        _append_missing(errors, bool(comparable.get("source_id")), f"comparables[{index}]_source_id_missing")
        _append_missing(errors, float(comparable.get("prix_vente") or 0) > 0, f"comparables[{index}]_prix_vente_invalid")
        _append_missing(errors, bool(comparable.get("date_vente")), f"comparables[{index}]_date_vente_missing")
        if comparable.get("adresse") and not _looks_placeholder(str(comparable.get("adresse"))):
            warnings.append(f"comparables[{index}]_address_not_obviously_anonymized")

    adjustments = case.get("ajustements") if isinstance(case.get("ajustements"), list) else []
    if not adjustments:
        warnings.append("adjustments_absent")
    for index, adjustment in enumerate(adjustments):
        if not isinstance(adjustment, dict):
            errors.append(f"ajustements[{index}]_invalid")
            continue
        _append_missing(errors, bool(adjustment.get("source_id")), f"ajustements[{index}]_source_id_missing")
        _append_missing(
            errors,
            adjustment.get("validation_humaine") is True,
            f"ajustements[{index}]_human_validation_missing",
        )

    hypotheses = case.get("hypotheses") if isinstance(case.get("hypotheses"), list) else []
    if not hypotheses:
        warnings.append("hypotheses_absent")
    for index, hypothesis in enumerate(hypotheses):
        if not isinstance(hypothesis, dict):
            errors.append(f"hypotheses[{index}]_invalid")
            continue
        source_ids = hypothesis.get("source_ids") if isinstance(hypothesis.get("source_ids"), list) else []
        _append_missing(errors, bool(source_ids), f"hypotheses[{index}]_source_ids_missing")

    pii_hits: list[dict[str, str]] = []
    for path, value in _string_values(case):
        lowered_path = path.lower()
        if _EMAIL_RE.search(value):
            pii_hits.append({"path": path, "type": "email"})
        if _PHONE_RE.search(value):
            pii_hits.append({"path": path, "type": "phone"})
        if _SIN_RE.search(value):
            pii_hits.append({"path": path, "type": "sin_like_number"})
        if _POSTAL_RE.search(value):
            pii_hits.append({"path": path, "type": "postal_code"})
        if any(field in lowered_path.split(".")[-1] for field in _PII_FIELDS):
            if value and not _looks_placeholder(value):
                pii_hits.append({"path": path, "type": "direct_identifier_field"})

    if pii_hits:
        errors.append("pii_detected")

    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))
    return {
        "schema_version": "ea_acceptance_anonymization_v1",
        "ok": not errors,
        "status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "warnings": warnings,
        "pii_hits": pii_hits,
    }


def build_acceptance_report(
    *,
    case: dict[str, Any],
    anonymization: dict[str, Any],
    session: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    package: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    session = session or {}
    result = result or {}
    review = review or {}
    package = package or {}
    gate = package.get("gate") if isinstance(package.get("gate"), dict) else {}
    manifest = package.get("manifest") if isinstance(package.get("manifest"), dict) else {}

    checks = [
        {
            "id": "anonymization",
            "ok": bool(anonymization.get("ok")),
            "detail": anonymization.get("errors", []),
        },
        {
            "id": "runtime_ready",
            "ok": str(result.get("status") or "").upper() not in _RUNTIME_BLOCKED_STATUSES
            and not result.get("blocking_failures"),
            "detail": result.get("blocking_failures", []),
        },
        {
            "id": "review_valide",
            "ok": review.get("decision") == "VALIDE",
            "detail": review.get("decision", "ABSENT"),
        },
        {
            "id": "certifiability_gate",
            "ok": bool(gate.get("ok")),
            "detail": gate.get("blocking_errors", []),
        },
        {
            "id": "package_ready",
            "ok": package.get("status") == "PRET_REVUE_EVALUATEUR_AGREE",
            "detail": package.get("status", "ABSENT"),
        },
        {
            "id": "no_external_evaluator_answers",
            "ok": package.get("external_evaluator_responses_included") is False
            and manifest.get("external_evaluator_responses_included") is False,
            "detail": manifest.get("external_evaluator_responses_included", "ABSENT"),
        },
    ]
    blocking = [check["id"] for check in checks if not check["ok"]]
    report = {
        "schema_version": "ea_acceptance_report_v1",
        "generated_at_utc": utc_now_iso(),
        "status": "PASS" if not blocking else "BLOCKED",
        "blocking_checks": blocking,
        "dossier_id": case.get("dossier_id", session.get("dossier_id", "")),
        "session_id": session.get("session_id", ""),
        "run_id": session.get("run_id", ""),
        "human_signoff_required": True,
        "certification_automatic": False,
        "checks": checks,
        "anonymization": anonymization,
        "package": {
            "status": package.get("status", "ABSENT"),
            "manifest_path": package.get("manifest_path", ""),
            "files_count": len(package.get("files", [])) if isinstance(package.get("files"), list) else 0,
        },
        "reviewer_evidence": {
            "decision": review.get("decision", ""),
            "reviewer": review.get("reviewer", ""),
            "confirmed_by": review.get("confirmed_by", ""),
            "notes": review.get("notes", ""),
        },
        "output_path": str(output_path or ""),
    }
    return report
