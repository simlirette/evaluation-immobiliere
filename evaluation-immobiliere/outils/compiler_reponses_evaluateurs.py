#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parent
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from prioriser_mvp import compute_score

INPUT_DEFAULT = Path("evaluation-immobiliere/atelier/REPONSES-EVALUATEURS.csv")
MATRIX_DEFAULT = Path("evaluation-immobiliere/atelier/MATRICE-PRIORISATION-MVP.csv")
REPORT_DEFAULT = Path("evaluation-immobiliere/atelier/MATRICE-PRIORISATION-MVP.md")

MATRIX_FIELDS = [
    "tache",
    "phase",
    "temps_moyen_min",
    "frequence_par_mois",
    "douleur_1_5",
    "risque_conformite_1_5",
    "automatisation_potentielle_1_5",
    "complexite_technique_1_5",
    "disponibilite_donnees_1_5",
    "validation_humaine_obligatoire",
    "decision_non_delegable",
    "source_donnees_requise",
    "irritant_principal",
    "valeur_score",
    "readiness_score",
    "score_mvp",
    "repondants",
    "commentaires",
]

NUMERIC_FIELDS = [
    "temps_moyen_min",
    "frequence_par_mois",
    "douleur_1_5",
    "risque_conformite_1_5",
    "automatisation_potentielle_1_5",
    "complexite_technique_1_5",
    "disponibilite_donnees_1_5",
]

TEXT_FIELDS = [
    "source_donnees_requise",
    "irritant_principal",
    "sortie_minimale",
    "commentaires",
]

BASE_TASKS = [
    ("reception_mandat", "intake"),
    ("collecte_documents", "intake"),
    ("extraction_caracteristiques_bien", "data_facts"),
    ("selection_comparables", "comps_market"),
    ("proposition_ajustements", "valuation_draft"),
    ("redaction_brouillon_rapport", "redaction"),
    ("controle_qualite_npp", "compliance_qa"),
]


@dataclass
class AggregatedTask:
    task: str
    row: dict[str, str]
    numeric_counts: dict[str, int]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MATRIX_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def compile_matrix(response_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in response_rows:
        task = normalize_task(row.get("tache", ""))
        if task:
            grouped[task].append(row)

    compiled: list[dict[str, str]] = []
    base_order = [task for task, _phase in BASE_TASKS]
    all_tasks = [*base_order, *sorted(task for task in grouped if task not in base_order)]

    for task in all_tasks:
        rows = grouped.get(task, [])
        phase = default_phase(task)
        if rows:
            phase = most_common_text(row.get("phase", "") for row in rows) or phase
        aggregated = aggregate_task(task, phase, rows)
        compiled.append(aggregated.row)

    return compiled


def aggregate_task(task: str, phase: str, rows: list[dict[str, str]]) -> AggregatedTask:
    out: dict[str, str] = {field: "" for field in MATRIX_FIELDS}
    out["tache"] = task
    out["phase"] = phase
    out["repondants"] = str(len(unique_nonempty(row.get("respondant_id", "") for row in rows)))

    numeric_counts: dict[str, int] = {}
    for field in NUMERIC_FIELDS:
        values = [to_float(row.get(field, "")) for row in rows if has_value(row.get(field, ""))]
        numeric_counts[field] = len(values)
        if values:
            out[field] = format_number(statistics.mean(values))

    out["validation_humaine_obligatoire"] = majority_bool(row.get("validation_humaine_obligatoire", "") for row in rows)
    out["decision_non_delegable"] = majority_bool(row.get("decision_non_delegable", "") for row in rows)

    out["source_donnees_requise"] = join_unique(row.get("source_donnees_requise", "") for row in rows)
    out["irritant_principal"] = join_unique(row.get("irritant_principal", "") for row in rows)
    comments = []
    for field in ("sortie_minimale", "commentaires"):
        comments.extend(nonempty(row.get(field, "") for row in rows))
    out["commentaires"] = join_unique(comments)

    score = compute_score(out)
    out["valeur_score"] = format_number(float(score.details["valeur_score"]))
    out["readiness_score"] = format_number(float(score.details["readiness_score"]))
    out["score_mvp"] = format_number(score.score)
    return AggregatedTask(task=task, row=out, numeric_counts=numeric_counts)


def write_report(path: Path, matrix_rows: list[dict[str, str]], response_rows: list[dict[str, str]]) -> None:
    ranked = sorted(matrix_rows, key=lambda row: to_float(row.get("score_mvp", "")), reverse=True)
    respondent_count = len(unique_nonempty(row.get("respondant_id", "") for row in response_rows))
    completed_rows = [row for row in response_rows if any(has_value(row.get(field, "")) for field in NUMERIC_FIELDS)]

    lines = [
        "# Matrice de priorisation MVP",
        "",
        f"- Repondants uniques: **{respondent_count}**",
        f"- Lignes reponses avec donnees numeriques: **{len(completed_rows)}**",
        f"- Taches compilees: **{len(matrix_rows)}**",
        "",
        "## Classement",
        "",
        "| Rang | Tache | Phase | Score MVP | Validation humaine | Decision non delegable |",
        "|---:|---|---|---:|---|---|",
    ]

    for idx, row in enumerate(ranked, start=1):
        lines.append(
            "| {idx} | {task} | {phase} | {score} | {validation} | {non_delegable} |".format(
                idx=idx,
                task=row.get("tache", ""),
                phase=row.get("phase", ""),
                score=row.get("score_mvp", ""),
                validation=row.get("validation_humaine_obligatoire", ""),
                non_delegable=row.get("decision_non_delegable", ""),
            )
        )

    lines.extend(["", "## Notes par tache", ""])
    for row in ranked:
        lines.append(f"### {row.get('tache', '')}")
        lines.append(f"- Irritant: {row.get('irritant_principal') or '-'}")
        lines.append(f"- Sources requises: {row.get('source_donnees_requise') or '-'}")
        lines.append(f"- Commentaires: {row.get('commentaires') or '-'}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def normalize_task(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def default_phase(task: str) -> str:
    return dict(BASE_TASKS).get(task, "")


def has_value(value: str | None) -> bool:
    return bool((value or "").strip())


def to_float(value: str | None) -> float:
    return float((value or "0").strip() or 0)


def format_number(value: float) -> str:
    rounded = round(value, 3)
    if rounded == int(rounded):
        return str(int(rounded))
    return str(rounded)


def majority_bool(values: object) -> str:
    votes = [parse_bool(v) for v in values if parse_bool(v) is not None]
    if not votes:
        return ""
    return "oui" if votes.count(True) >= votes.count(False) else "non"


def parse_bool(value: str | None) -> bool | None:
    normalized = (value or "").strip().lower()
    if normalized in {"1", "true", "oui", "yes", "y"}:
        return True
    if normalized in {"0", "false", "non", "no", "n"}:
        return False
    return None


def most_common_text(values: object) -> str:
    items = list(nonempty(values))
    if not items:
        return ""
    return Counter(items).most_common(1)[0][0]


def join_unique(values: object) -> str:
    return " | ".join(unique_nonempty(values))


def unique_nonempty(values: object) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in nonempty(values):
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def nonempty(values: object) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            out.append(text)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile les reponses evaluateurs vers la matrice MVP.")
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--matrix-out", type=Path, default=MATRIX_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args()

    rows = read_rows(args.input)
    matrix = compile_matrix(rows)
    write_rows(args.matrix_out, matrix)
    write_report(args.report_out, matrix, rows)
    print(f"Matrice ecrite: {args.matrix_out}")
    print(f"Rapport ecrit: {args.report_out}")


if __name__ == "__main__":
    main()
