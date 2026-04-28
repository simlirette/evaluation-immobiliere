#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPORTS_DIR = Path("evaluation-immobiliere/tests/reports")
SUMMARY_JSON = REPORTS_DIR / "summary.json"
SUMMARY_MD = REPORTS_DIR / "summary.md"


def load_reports() -> list[dict]:
    reports: list[dict] = []
    for path in sorted(REPORTS_DIR.glob("case_*.report.json")):
        reports.append(json.loads(path.read_text(encoding="utf-8")))
    return reports


def build_summary(reports: list[dict]) -> dict:
    status_counts = Counter(r.get("status", "UNKNOWN") for r in reports)
    blocking_counts = Counter()
    warning_counts = Counter()

    for r in reports:
        for b in r.get("blocking_failures", []):
            blocking_counts[b] += 1
        for w in r.get("warnings", []):
            warning_counts[w] += 1

    total = len(reports)
    conformes = status_counts.get("PRET_REVISION_FINALE", 0)

    return {
        "total_cases": total,
        "status_counts": dict(status_counts),
        "top_blocking_failures": blocking_counts.most_common(5),
        "top_warnings": warning_counts.most_common(5),
        "conformite_globale_pct": round((conformes / total) * 100, 1) if total else 0.0,
    }


def write_markdown(summary: dict) -> None:
    lines = [
        "# Résumé dry-run v0",
        "",
        f"- Total de cas: **{summary['total_cases']}**",
        f"- Conformité globale (`PRET_REVISION_FINALE`): **{summary['conformite_globale_pct']}%**",
        "",
        "## Répartition des statuts",
    ]

    for k, v in summary["status_counts"].items():
        lines.append(f"- {k}: {v}")

    lines.append("")
    lines.append("## Top causes bloquantes")
    if summary["top_blocking_failures"]:
        for name, count in summary["top_blocking_failures"]:
            lines.append(f"- {name}: {count}")
    else:
        lines.append("- Aucune")

    lines.append("")
    lines.append("## Top warnings")
    if summary["top_warnings"]:
        for name, count in summary["top_warnings"]:
            lines.append(f"- {name}: {count}")
    else:
        lines.append("- Aucun")

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    reports = load_reports()
    summary = build_summary(reports)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(summary)
    print(f"Résumé généré: {SUMMARY_JSON}")
    print(f"Résumé généré: {SUMMARY_MD}")


if __name__ == "__main__":
    main()
