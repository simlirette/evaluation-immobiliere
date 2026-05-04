#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

SUMMARY_DEFAULT = Path("evaluation-immobiliere/tests/runtime/runtime_summary.json")
REPORT_DEFAULT = Path("evaluation-immobiliere/atelier/RAPPORT-PILOTE-RUNTIME-V0.md")
STATUS_ORDER = ["PRET_REVISION_FINALE", "BROUILLON", "A_REVOIR", "UNKNOWN"]


def load_summary(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(summary: list[dict]) -> dict:
    status_counts = Counter(case.get("status") or "UNKNOWN" for case in summary)
    total_blocking = sum(len(case.get("blocking_failures", [])) for case in summary)
    total_warnings = sum(len(case.get("warnings", [])) for case in summary)
    total_events = sum(len(case.get("events", [])) for case in summary)
    ready = status_counts.get("PRET_REVISION_FINALE", 0)
    draft = status_counts.get("BROUILLON", 0)
    review = status_counts.get("A_REVOIR", 0)

    return {
        "cases": len(summary),
        "status_counts": dict(status_counts),
        "total_blocking_failures": total_blocking,
        "total_warnings": total_warnings,
        "total_runtime_events": total_events,
        "ready_for_review": ready,
        "draft": draft,
        "needs_review": review,
    }


def build_markdown(summary: list[dict]) -> str:
    metrics = summarize(summary)
    lines = [
        "# Rapport pilote runtime v0",
        "",
        "## Baseline",
        "",
        f"- Cas executes: **{metrics['cases']}**",
        f"- Prets revision finale: **{metrics['ready_for_review']}**",
        f"- Brouillons: **{metrics['draft']}**",
        f"- A revoir: **{metrics['needs_review']}**",
        f"- Blocages detectes: **{metrics['total_blocking_failures']}**",
        f"- Warnings detectes: **{metrics['total_warnings']}**",
        f"- Evenements runtime: **{metrics['total_runtime_events']}**",
        "",
        "## Distribution des statuts",
        "",
    ]

    status_counts = metrics["status_counts"]
    for status in ordered_statuses(status_counts):
        lines.append(f"- {status}: {status_counts.get(status, 0)}")

    lines.extend(
        [
            "",
            "## Cas pilotes",
            "",
            "| Cas | Dossier | Statut | Blocages | Warnings | Artefacts |",
            "|---|---|---|---:|---:|---|",
        ]
    )
    for case in summary:
        artifact_dir = str(case.get("artifact_dir", ""))
        case_name = Path(artifact_dir).name if artifact_dir else "-"
        lines.append(
            "| {case_name} | {dossier_id} | {status} | {blocking} | {warnings} | `{artifact_dir}` |".format(
                case_name=case_name,
                dossier_id=case.get("dossier_id", "-"),
                status=case.get("status", "UNKNOWN"),
                blocking=len(case.get("blocking_failures", [])),
                warnings=len(case.get("warnings", [])),
                artifact_dir=artifact_dir or "-",
            )
        )

    lines.extend(["", "## Blocages et warnings", ""])
    for case in summary:
        blocking = case.get("blocking_failures", [])
        warnings = case.get("warnings", [])
        if not blocking and not warnings:
            continue
        artifact_dir = str(case.get("artifact_dir", ""))
        case_name = Path(artifact_dir).name if artifact_dir else str(case.get("dossier_id", "-"))
        lines.append(f"### {case_name}")
        if blocking:
            lines.append(f"- Blocages: {format_items(blocking)}")
        if warnings:
            lines.append(f"- Warnings: {format_items(warnings)}")
        lines.append("")

    lines.extend(
        [
            "## Lecture produit",
            "",
            "- Les cas `PRET_REVISION_FINALE` servent de reference positive pour les fixtures de validation.",
            "- Les cas `BROUILLON` indiquent que les donnees sont exploitables mais demandent encore jugement humain ou confiance accrue.",
            "- Les cas `A_REVOIR` valident que les garde-fous bloquants stoppent les dossiers incomplets ou incoherents.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def ordered_statuses(status_counts: dict[str, int]) -> list[str]:
    ordered = [status for status in STATUS_ORDER if status in status_counts]
    ordered.extend(sorted(status for status in status_counts if status not in STATUS_ORDER))
    return ordered


def format_items(items: list[str]) -> str:
    return "; ".join(str(item) for item in items) if items else "-"


def write_report(path: Path, summary: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown(summary), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genere un rapport baseline pour les executions runtime pilotes.")
    parser.add_argument("--summary", type=Path, default=SUMMARY_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args()

    summary = load_summary(args.summary)
    write_report(args.report_out, summary)
    print(f"Rapport pilote runtime: {args.report_out}")


if __name__ == "__main__":
    main()
