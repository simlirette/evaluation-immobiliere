#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

QUALITY_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/quality_report.json")
OUT_CSV_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/FILE-REVUE-HUMAINE-V0.csv")
OUT_MD_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/FILE-REVUE-HUMAINE-V0.md")
QUEUE_FIELDS = ["id", "priority", "dossier_id", "item_type", "target", "artifact", "question", "source"]


def load_quality_report(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def build_review_queue(quality_report: dict) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for case in quality_report.get("cases", []):
        if not isinstance(case, dict):
            continue
        dossier_id = str(case.get("dossier_id", "-"))
        add_item(items, "P3", dossier_id, "statut", str(case.get("status", "UNKNOWN")), "compliance-qa.statut_sortie.json", "Confirmer que le statut runtime correspond au jugement evaluateur.", "runtime_status")
        for failure in case.get("blocking_failures", []):
            add_item(items, "P1", dossier_id, "blocage", str(failure), "compliance-qa.rapport_non_conformites.json", "Confirmer si ce blocage doit rester bloquant ou etre assoupli.", "runtime_blocking")
        for warning in case.get("warnings", []):
            add_item(items, "P2", dossier_id, "warning", str(warning), "compliance-qa.rapport_non_conformites.json", "Decider si ce warning reste informatif ou devient bloquant.", "runtime_warning")
        for error in case.get("contract_errors", []):
            if isinstance(error, dict):
                add_item(items, "P1", dossier_id, "contrat", format_failures(error.get("failures", [])), str(error.get("artifact", "")), "Verifier l'echec contrat et sa severite metier.", "contract_report")
        artifacts = case.get("artifacts", {}) if isinstance(case.get("artifacts"), dict) else {}
        for artifact in artifacts.get("missing", []):
            add_item(items, "P2", dossier_id, "artefact", str(artifact), str(artifact), "Valider si l'artefact manquant bloque la revue.", "artifact_inventory")
        ingestion = case.get("ingestion_pdf", {}) if isinstance(case.get("ingestion_pdf"), dict) else {}
        for flag in ingestion.get("review_flags", []):
            priority = "P2" if str(flag) == "LOW_CONFIDENCE" else "P3"
            add_item(items, priority, dossier_id, "ingestion_pdf", str(flag), str(ingestion.get("trace_path", "")), "Verifier si le flag PDF demande une validation humaine.", "ingestion_pdf")
    return sorted(items, key=lambda item: (priority_rank(item["priority"]), item["dossier_id"], item["id"]))


def add_item(
    items: list[dict[str, str]],
    priority: str,
    dossier_id: str,
    item_type: str,
    target: str,
    artifact: str,
    question: str,
    source: str,
) -> None:
    items.append(
        {
            "id": f"REV-{len(items) + 1:03d}",
            "priority": priority,
            "dossier_id": dossier_id,
            "item_type": item_type,
            "target": target,
            "artifact": artifact,
            "question": question,
            "source": source,
        }
    )


def format_failures(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value or "")


def priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(priority, 9)


def write_queue_csv(path: Path, items: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(items)


def build_markdown(items: list[dict[str, str]]) -> str:
    lines = [
        "# File de revue humaine v0",
        "",
        f"- Items: **{len(items)}**",
        "",
        "| ID | Priorite | Dossier | Type | Cible | Question |",
        "|---|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| - | - | - | - | - | Aucun item ouvert. |")
    for item in items:
        lines.append(
            "| {id} | {priority} | {dossier} | {item_type} | {target} | {question} |".format(
                id=item["id"],
                priority=item["priority"],
                dossier=item["dossier_id"],
                item_type=item["item_type"],
                target=item["target"],
                question=item["question"],
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def write_markdown(path: Path, items: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown(items), encoding="utf-8")


def generate_review_queue(quality_path: Path, csv_out: Path, markdown_out: Path) -> list[dict[str, str]]:
    items = build_review_queue(load_quality_report(quality_path))
    write_queue_csv(csv_out, items)
    write_markdown(markdown_out, items)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere une file de revue humaine depuis le rapport qualite runtime.")
    parser.add_argument("--quality-report", type=Path, default=QUALITY_DEFAULT)
    parser.add_argument("--csv-out", type=Path, default=OUT_CSV_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    items = generate_review_queue(args.quality_report, args.csv_out, args.markdown_out)
    print(f"File CSV: {args.csv_out}")
    print(f"File Markdown: {args.markdown_out}")
    print(f"Items: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
