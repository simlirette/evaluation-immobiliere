#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


SCHEMA_VERSION = "closed_beta_launch_evidence_v1"


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _truthy(value: object) -> bool:
    return value is True


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _https_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip().startswith("https://"):
        return False
    if "<" in value or ">" in value:
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc) and parsed.path in {"", "/"}


def _check(
    check_id: str,
    ok: bool,
    detail: str,
    action: str,
    *,
    severity: str = "blocking",
) -> dict[str, object]:
    return {
        "id": check_id,
        "status": "ok" if ok else severity,
        "ok": ok,
        "detail": detail,
        "action": "" if ok else action,
    }


def _required_bool(section: dict[str, object], key: str, action: str, *, prefix: str) -> dict[str, object]:
    value = section.get(key)
    return _check(f"{prefix}.{key}", _truthy(value), f"{key}={value!r}", action)


def _validate_production(evidence: dict[str, object]) -> list[dict[str, object]]:
    production = _as_dict(evidence.get("production"))
    return [
        _check(
            "production.frontend_url",
            _https_url(production.get("frontend_url")),
            str(production.get("frontend_url") or ""),
            "Set the Vercel production HTTPS URL.",
        ),
        _check(
            "production.backend_url",
            _https_url(production.get("backend_url")),
            str(production.get("backend_url") or ""),
            "Set the Railway backend HTTPS URL.",
        ),
        _required_bool(production, "railway_readiness_ok", "Run /readiness or check_deploy_readiness.py in production.", prefix="production"),
        _required_bool(production, "vercel_bff_smoke_ok", "Run smoke_beta_ea_link_v1.py through the Vercel URL.", prefix="production"),
        _required_bool(production, "runtime_token_set", "Set matching RUNTIME_API_TOKEN and EVAL_RUNTIME_API_TOKEN.", prefix="production"),
        _required_bool(production, "cors_strict", "Set EVAL_RUNTIME_ALLOWED_ORIGIN to the exact Vercel origin.", prefix="production"),
        _required_bool(production, "persistent_sessions", "Mount and verify a persistent SESSIONS_DIR volume.", prefix="production"),
        _required_bool(production, "persistent_data_cache", "Mount and verify a persistent DATA_CACHE_DIR volume.", prefix="production"),
        _required_bool(production, "mamh_cache_provisioned", "Provision the MAMH cache on the production volume.", prefix="production"),
        _required_bool(production, "openai_configured", "Set OPENAI_API_KEY and the intended model.", prefix="production"),
    ]


def _validate_privacy(evidence: dict[str, object]) -> list[dict[str, object]]:
    privacy = _as_dict(evidence.get("privacy"))
    retention_days = privacy.get("retention_days")
    retention_ok = isinstance(retention_days, int) and 1 <= retention_days <= 90
    raw_client_files_allowed = privacy.get("raw_client_files_allowed")
    contract_signed = privacy.get("raw_client_file_contract_signed")
    return [
        _required_bool(privacy, "data_inventory_approved", "Approve the Loi 25 data inventory for beta.", prefix="privacy"),
        _check(
            "privacy.retention_days",
            retention_ok,
            f"retention_days={retention_days!r}",
            "Set an integer retention period between 1 and 90 days.",
        ),
        _required_bool(privacy, "deletion_workflow_approved", "Approve who can request deletion and how it is executed.", prefix="privacy"),
        _required_bool(privacy, "access_logging_reviewable", "Confirm access logs can be reviewed during beta.", prefix="privacy"),
        _required_bool(privacy, "backup_restore_defined", "Define backup and restore expectations for sessions.", prefix="privacy"),
        _required_bool(privacy, "incident_response_defined", "Define incident response for leaked dossier or wrong access.", prefix="privacy"),
        _required_bool(privacy, "professional_disclaimer_approved", "Approve wording that the tool assists but does not certify value.", prefix="privacy"),
        _check(
            "privacy.raw_client_files_policy",
            raw_client_files_allowed is False or contract_signed is True,
            f"raw_client_files_allowed={raw_client_files_allowed!r}, raw_client_file_contract_signed={contract_signed!r}",
            "Keep raw client files disabled or attach an approved contract before beta.",
        ),
    ]


def _validate_pilot(evidence: dict[str, object]) -> list[dict[str, object]]:
    pilot = _as_dict(evidence.get("pilot_ea"))
    return [
        _check(
            "pilot_ea.pilot_ea_id",
            _non_empty(pilot.get("pilot_ea_id")),
            str(pilot.get("pilot_ea_id") or ""),
            "Record a non-identifying pilot E.A. id or internal user id.",
        ),
        _required_bool(pilot, "terms_accepted", "Record beta terms acceptance from the pilot E.A.", prefix="pilot_ea"),
        _required_bool(pilot, "workflow_signoff", "Record pilot E.A. signoff after the guided workflow.", prefix="pilot_ea"),
    ]


def _validate_real_dossiers(evidence: dict[str, object]) -> list[dict[str, object]]:
    dossiers = _as_list(evidence.get("real_dossiers"))
    checks = [
        _check(
            "real_dossiers.count",
            len(dossiers) >= 3,
            f"count={len(dossiers)}",
            "Run at least three anonymized real dossiers before launch.",
        )
    ]
    required_types = {"standard_residential", "edge_or_low_confidence", "correction_or_blocked"}
    seen_types: set[str] = set()
    for index, raw in enumerate(dossiers):
        dossier = _as_dict(raw)
        prefix = f"real_dossiers[{index}]"
        dossier_type = str(dossier.get("type") or "")
        if dossier_type:
            seen_types.add(dossier_type)
        acceptance_status = str(dossier.get("acceptance_status") or "")
        p0_open_count = dossier.get("p0_open_count")
        checks.extend(
            [
                _check(f"{prefix}.id", _non_empty(dossier.get("id")), str(dossier.get("id") or ""), "Set a non-identifying dossier id."),
                _check(f"{prefix}.type", dossier_type in required_types, dossier_type, "Use one of the required beta dossier types."),
                _check(f"{prefix}.anonymized", _truthy(dossier.get("anonymized")), f"anonymized={dossier.get('anonymized')!r}", "Confirm anonymization before beta."),
                _check(
                    f"{prefix}.acceptance_status",
                    acceptance_status in {"PASS", "JUSTIFIED_BLOCKED"},
                    acceptance_status,
                    "Run E.A. acceptance and record PASS or JUSTIFIED_BLOCKED.",
                ),
                _check(
                    f"{prefix}.package_or_block_evidence",
                    _non_empty(dossier.get("package_or_block_evidence")),
                    str(dossier.get("package_or_block_evidence") or ""),
                    "Link the package manifest or blocked-state evidence.",
                ),
                _check(
                    f"{prefix}.p0_open_count",
                    p0_open_count == 0,
                    f"p0_open_count={p0_open_count!r}",
                    "Close all P0 feedback before beta launch.",
                ),
            ]
        )
    checks.append(
        _check(
            "real_dossiers.required_types",
            required_types.issubset(seen_types),
            "seen=" + ",".join(sorted(seen_types)),
            "Include standard, edge/low-confidence, and correction/blocked dossiers.",
        )
    )
    return checks


def _validate_data_sources(evidence: dict[str, object]) -> list[dict[str, object]]:
    sources = _as_dict(evidence.get("data_sources"))
    sirf_status = sources.get("sirf_status")
    jlr_policy = sources.get("jlr_policy")
    cost_status = sources.get("cost_approach_status")
    return [
        _required_bool(sources, "mamh_validated", "Validate MAMH cache behavior in production.", prefix="data_sources"),
        _required_bool(sources, "infolot_validated", "Run the Infolot live smoke when network access is approved.", prefix="data_sources"),
        _check(
            "data_sources.sirf_status",
            sirf_status in {"configured", "explicitly_disabled_for_beta"},
            str(sirf_status or ""),
            "Configure SIRF or explicitly disable it for the beta scope.",
        ),
        _check(
            "data_sources.jlr_policy",
            jlr_policy in {"required", "manual_export", "not_required_for_beta"},
            str(jlr_policy or ""),
            "Define whether JLR is required, manual-export only, or out of beta scope.",
        ),
        _check(
            "data_sources.cost_approach_status",
            cost_status in {"accepted_source_available", "explicitly_marked_incomplete"},
            str(cost_status or ""),
            "Provide an accepted cost source or keep cost approach visibly incomplete.",
        ),
        _required_bool(
            sources,
            "insufficient_data_blocking_policy",
            "Define when weak source data blocks a report instead of producing one.",
            prefix="data_sources",
        ),
    ]


def _validate_launch(evidence: dict[str, object]) -> list[dict[str, object]]:
    launch = _as_dict(evidence.get("launch"))
    max_users = launch.get("max_named_users")
    p0_open_count = launch.get("p0_open_count")
    return [
        _required_bool(launch, "named_users_only", "Restrict the beta to named users.", prefix="launch"),
        _check(
            "launch.max_named_users",
            isinstance(max_users, int) and 1 <= max_users <= 5,
            f"max_named_users={max_users!r}",
            "Start with 1 to 5 named users maximum.",
        ),
        _check(
            "launch.support_owner",
            _non_empty(launch.get("support_owner")),
            str(launch.get("support_owner") or ""),
            "Record the support owner for beta week 1.",
        ),
        _check(
            "launch.daily_review_owner",
            _non_empty(launch.get("daily_review_owner")),
            str(launch.get("daily_review_owner") or ""),
            "Record who reviews logs and errors daily.",
        ),
        _required_bool(launch, "week1_review_schedule", "Schedule daily beta week 1 review.", prefix="launch"),
        _required_bool(launch, "rollback_plan", "Document how to pause beta and revoke access.", prefix="launch"),
        _check(
            "launch.p0_open_count",
            p0_open_count == 0,
            f"p0_open_count={p0_open_count!r}",
            "Close all P0 items before sharing the link.",
        ),
    ]


def validate_evidence(evidence: dict[str, object]) -> dict[str, object]:
    checks: list[dict[str, object]] = [
        _check(
            "schema_version",
            evidence.get("schema_version") == SCHEMA_VERSION,
            str(evidence.get("schema_version") or ""),
            f"Set schema_version to {SCHEMA_VERSION}.",
        )
    ]
    checks.extend(_validate_production(evidence))
    checks.extend(_validate_privacy(evidence))
    checks.extend(_validate_pilot(evidence))
    checks.extend(_validate_real_dossiers(evidence))
    checks.extend(_validate_data_sources(evidence))
    checks.extend(_validate_launch(evidence))
    blocking = [check for check in checks if check["status"] == "blocking"]
    warnings = [check for check in checks if check["status"] == "warning"]
    return {
        "schema_version": "closed_beta_launch_report_v1",
        "status": "READY_FOR_CLOSED_BETA" if not blocking else "BLOCKED",
        "ok": not blocking,
        "summary": {
            "checks": len(checks),
            "blocking": len(blocking),
            "warnings": len(warnings),
        },
        "blocking_checks": [check["id"] for check in blocking],
        "checks": checks,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate closed beta launch evidence.")
    parser.add_argument("evidence", type=Path, help="Path to closed beta launch evidence JSON.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise SystemExit("Evidence JSON must be an object.")
    report = validate_evidence(evidence)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status: {report['status']}")
        print(f"blocking: {report['summary']['blocking']}")
        for check_id in report["blocking_checks"]:
            print(f"- {check_id}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
