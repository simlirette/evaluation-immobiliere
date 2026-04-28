#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
from collections import Counter

RUNTIME_DIR = Path("evaluation-immobiliere/tests/runtime")
SUMMARY_PATH = RUNTIME_DIR / "runtime_summary.json"
OUT_JSON = RUNTIME_DIR / "integrity_report.json"
OUT_MD = RUNTIME_DIR / "integrity_report.md"


def count_audit_events(audit_path: Path) -> Counter:
    c = Counter()
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        c[obj.get("event", "unknown")] += 1
    return c


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    status_counts = Counter()
    total_blocking = 0
    total_warnings = 0
    total_events = 0
    audit_event_counts = Counter()

    for case in summary:
        status_counts[case.get("status", "UNKNOWN")] += 1
        total_blocking += len(case.get("blocking_failures", []))
        total_warnings += len(case.get("warnings", []))
        total_events += len(case.get("events", []))

        audit_log = Path(case.get("audit_log", ""))
        if audit_log.exists():
            audit_event_counts.update(count_audit_events(audit_log))

    report = {
        "cases": len(summary),
        "status_counts": dict(status_counts),
        "total_blocking_failures": total_blocking,
        "total_warnings": total_warnings,
        "total_runtime_events": total_events,
        "audit_event_counts": dict(audit_event_counts),
    }

    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Integrity Report Runtime v0",
        "",
        f"- Cases: **{report['cases']}**",
        f"- Blocking failures total: **{report['total_blocking_failures']}**",
        f"- Warnings total: **{report['total_warnings']}**",
        f"- Runtime events total: **{report['total_runtime_events']}**",
        "",
        "## Status counts",
    ]
    for k, v in report["status_counts"].items():
        lines.append(f"- {k}: {v}")

    lines.append("")
    lines.append("## Audit event counts")
    for k, v in report["audit_event_counts"].items():
        lines.append(f"- {k}: {v}")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Integrity JSON: {OUT_JSON}")
    print(f"Integrity MD: {OUT_MD}")


if __name__ == "__main__":
    main()
