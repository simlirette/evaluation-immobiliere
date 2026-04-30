#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
QUALITY_DEFAULT = RUNTIME_DIR_DEFAULT / "quality_report.json"
REGISTRY_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_registry.json"
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_delta_report.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "RAPPORT-DELTA-RUNTIME-V0.md"
TOTAL_KEYS = ["blocking_failures", "warnings", "contract_errors", "missing_artifacts"]
REGRESSION_KEYS = {"blocking_failures", "contract_errors", "missing_artifacts"}


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def int_value(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def latest_registry_entry(registry: object) -> dict[str, object] | None:
    if not isinstance(registry, dict) or not isinstance(registry.get("runs"), list):
        return None
    runs = [item for item in registry["runs"] if isinstance(item, dict)]
    return runs[-1] if runs else None


def summarize_quality(quality: object) -> dict[str, object]:
    if not isinstance(quality, dict):
        quality = {}
    totals = quality.get("totals", {}) if isinstance(quality.get("totals"), dict) else {}
    return {
        "cases_count": int_value(quality.get("cases_count")),
        "status_counts": quality.get("status_counts", {}) if isinstance(quality.get("status_counts"), dict) else {},
        "totals": {key: int_value(totals.get(key)) for key in TOTAL_KEYS},
        "averages": quality.get("averages", {}) if isinstance(quality.get("averages"), dict) else {},
    }


def summarize_registry_entry(entry: dict[str, object] | None) -> dict[str, object] | None:
    if entry is None:
        return None
    totals = entry.get("totals", {}) if isinstance(entry.get("totals"), dict) else {}
    return {
        "run_id": entry.get("run_id", ""),
        "timestamp_utc": entry.get("timestamp_utc", ""),
        "commit_sha": entry.get("commit_sha", ""),
        "runtime_fingerprint_sha256": entry.get("runtime_fingerprint_sha256", ""),
        "cases_count": int_value(entry.get("cases_count")),
        "status_counts": entry.get("status_counts", {}) if isinstance(entry.get("status_counts"), dict) else {},
        "totals": {key: int_value(totals.get(key)) for key in TOTAL_KEYS},
    }


def diff_counts(current: dict[str, int], previous: dict[str, int] | None) -> dict[str, int]:
    previous = previous or {}
    keys = sorted(set(current) | set(previous))
    return {key: int_value(current.get(key)) - int_value(previous.get(key)) for key in keys}


def build_regressions(metric_deltas: dict[str, int], status_deltas: dict[str, int]) -> list[dict[str, object]]:
    regressions: list[dict[str, object]] = []
    for key in sorted(REGRESSION_KEYS):
        delta = metric_deltas.get(key, 0)
        if delta > 0:
            regressions.append({"metric": key, "delta": delta, "severity": "warning"})
    if status_deltas.get("A_REVOIR", 0) > 0:
        regressions.append({"metric": "status_counts.A_REVOIR", "delta": status_deltas["A_REVOIR"], "severity": "warning"})
    return regressions


def build_delta_report(quality_report: object, registry: object) -> dict[str, object]:
    current = summarize_quality(quality_report)
    previous = summarize_registry_entry(latest_registry_entry(registry))
    previous_totals = previous.get("totals", {}) if previous else {}
    previous_status_counts = previous.get("status_counts", {}) if previous else {}
    metric_deltas = diff_counts(current["totals"], previous_totals)
    status_deltas = diff_counts(current["status_counts"], previous_status_counts)
    regressions = build_regressions(metric_deltas, status_deltas) if previous else []
    status = "OBSERVATION_INITIALE" if previous is None else "A_CONTROLER" if regressions else "STABLE"

    return {
        "schema_version": "runtime_delta_report_v0",
        "status": status,
        "current": current,
        "previous": previous,
        "deltas": {
            "cases_count": current["cases_count"] - int_value(previous.get("cases_count") if previous else 0),
            "status_counts": status_deltas,
            "totals": metric_deltas,
        },
        "regressions": regressions,
    }


def format_delta(value: object) -> str:
    number = int_value(value)
    if number > 0:
        return f"+{number}"
    return str(number)


def build_markdown(report: dict[str, object]) -> str:
    current = report.get("current", {}) if isinstance(report.get("current"), dict) else {}
    previous = report.get("previous", {}) if isinstance(report.get("previous"), dict) else None
    deltas = report.get("deltas", {}) if isinstance(report.get("deltas"), dict) else {}
    total_deltas = deltas.get("totals", {}) if isinstance(deltas.get("totals"), dict) else {}
    status_deltas = deltas.get("status_counts", {}) if isinstance(deltas.get("status_counts"), dict) else {}
    regressions = report.get("regressions", []) if isinstance(report.get("regressions"), list) else []

    lines = [
        "# Rapport delta runtime v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Run precedent: `{previous.get('run_id', '-') if isinstance(previous, dict) else '-'}`",
        f"- Dossiers courants: **{current.get('cases_count', 0)}**",
        f"- Regressions detectees: **{len(regressions)}**",
        "",
        "## Deltas metriques",
        "",
        "| Metrique | Delta |",
        "|---|---:|",
    ]
    for key in TOTAL_KEYS:
        lines.append(f"| {key} | {format_delta(total_deltas.get(key, 0))} |")

    lines.extend(["", "## Deltas statuts", "", "| Statut | Delta |", "|---|---:|"])
    for key in sorted(status_deltas):
        lines.append(f"| {key} | {format_delta(status_deltas.get(key, 0))} |")

    lines.extend(["", "## Regressions", ""])
    if regressions:
        for item in regressions:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('metric', '-')}`: {format_delta(item.get('delta', 0))}")
    else:
        lines.append("- Aucune regression operationnelle detectee.")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def generate_delta_report(quality_path: Path, registry_path: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    report = build_delta_report(load_json(quality_path, {}), load_json(registry_path, {}))
    write_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare la qualite runtime courante au dernier run registre.")
    parser.add_argument("--quality-report", type=Path, default=QUALITY_DEFAULT)
    parser.add_argument("--registry", type=Path, default=REGISTRY_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = generate_delta_report(args.quality_report, args.registry, args.json_out, args.markdown_out)
    print(f"Delta runtime JSON: {args.json_out}")
    print(f"Delta runtime Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return 0 if report["status"] != "A_CONTROLER" else 1


if __name__ == "__main__":
    raise SystemExit(main())
