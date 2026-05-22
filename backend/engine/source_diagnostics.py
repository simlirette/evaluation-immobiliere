"""Lightweight diagnostics for optional public-source integrations."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable

EXPECTED_PUBLIC_SOURCES = ("geocoding", "infolot", "mamh", "sirf")
MAX_DIAGNOSTICS = 80


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def make_source_diagnostic(
    source: str,
    status: str,
    message: str = "",
    *,
    stage: str = "",
    cached: bool = False,
    severity: str = "info",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source": str(source),
        "status": str(status),
        "severity": str(severity),
        "message": str(message),
        "stage": str(stage),
        "cached": bool(cached),
        "timestamp_utc": utc_now_iso(),
    }
    if details:
        payload["details"] = _json_safe(details)
    return payload


def ensure_source_diagnostics(target: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics = target.get("source_diagnostics")
    if not isinstance(diagnostics, list):
        diagnostics = []
        target["source_diagnostics"] = diagnostics
    return diagnostics


def append_source_diagnostic(
    diagnostics_or_case: list[dict[str, Any]] | dict[str, Any] | None,
    diagnostic: dict[str, Any],
) -> None:
    if diagnostics_or_case is None:
        return
    if isinstance(diagnostics_or_case, dict):
        diagnostics = ensure_source_diagnostics(diagnostics_or_case)
    else:
        diagnostics = diagnostics_or_case
    diagnostics.append(diagnostic)
    if len(diagnostics) > MAX_DIAGNOSTICS:
        del diagnostics[:-MAX_DIAGNOSTICS]


def build_source_coverage(
    diagnostics: Iterable[dict[str, Any]] | None,
    expected_sources: Iterable[str] = EXPECTED_PUBLIC_SOURCES,
) -> dict[str, Any]:
    entries = [d for d in (diagnostics or []) if isinstance(d, dict)]
    expected = list(expected_sources)
    latest_by_source: dict[str, dict[str, Any]] = {}
    for entry in entries:
        source = str(entry.get("source") or "")
        if source:
            latest_by_source[source] = entry

    statuses = {src: str((latest_by_source.get(src) or {}).get("status") or "missing") for src in expected}
    ok_count = sum(1 for status in statuses.values() if status == "ok")
    partial_count = sum(1 for status in statuses.values() if status == "partial")
    empty_count = sum(1 for status in statuses.values() if status == "empty")
    skipped_count = sum(1 for status in statuses.values() if status == "skipped")
    failed_count = sum(1 for status in statuses.values() if status == "failed")
    missing_count = sum(1 for status in statuses.values() if status == "missing")
    available_count = ok_count + partial_count

    if not entries:
        status = "unknown"
    elif failed_count:
        status = "degraded"
    elif available_count == len(expected) and missing_count == 0:
        status = "ok"
    elif available_count:
        status = "partial"
    else:
        status = "unavailable"

    last_updated = ""
    for entry in entries:
        ts = str(entry.get("timestamp_utc") or "")
        if ts > last_updated:
            last_updated = ts

    return {
        "status": status,
        "expected_sources": expected,
        "source_statuses": statuses,
        "available_count": available_count,
        "ok_count": ok_count,
        "partial_count": partial_count,
        "empty_count": empty_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "missing_count": missing_count,
        "last_updated_utc": last_updated or None,
        "diagnostics": entries,
    }


def attach_source_coverage(target: dict[str, Any]) -> dict[str, Any]:
    coverage = build_source_coverage(target.get("source_diagnostics"))
    target["source_coverage"] = coverage
    return coverage


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
