#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
CONTRACTS_PATH_DEFAULT = Path("evaluation-immobiliere/mvp/CONTRATS-DONNEES-V0.yaml")
SUMMARY_NAME = "runtime_summary.json"
CONTRACTS_REPORT_NAME = "contracts_report.json"
REPORT_NAME = "DURCISSEMENT-CONTRATS-PILOTES-REELS-V0.md"
CONSTRAINT_KEYS = [
    "date_vente_max_delta_days",
    "similarite_score_range",
    "status",
    "max_comparable_distance_km_warning",
    "ajustement_sensible_montant_min",
    "confidence_min_warning",
    "valuation_inter_approach_max_delta_ratio",
]


def parse_contract_constraints(path: Path) -> dict[str, str]:
    constraints: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        for key in CONSTRAINT_KEYS:
            if stripped.startswith(f"{key}:"):
                constraints[key] = stripped.split(":", 1)[1].strip()
    return constraints


def load_json_if_exists(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def build_waiting_report(runtime_dir: Path, contracts_path: Path, constraints: dict[str, str]) -> str:
    lines = [
        "# Durcissement contrats pilotes reels v0",
        "",
        "- Statut: **EN_ATTENTE_SORTIES_PHASE_3**",
        f"- Repertoire runtime attendu: `{runtime_dir.as_posix()}`",
        f"- Fichier requis: `{SUMMARY_NAME}`",
        f"- Contrats lus: `{contracts_path.as_posix()}`",
        "",
        "## Seuils actuels a ne pas modifier sans donnees reelles",
        "",
    ]
    lines.extend(format_constraints(constraints))
    lines.extend(
        [
            "",
            "## Prochaine action",
            "",
            "Executer les dossiers reels, produire la revue interne phase 4, puis utiliser ce rapport pour decider quels seuils ou statuts doivent etre ajustes.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def status_counts(summary: list[dict]) -> Counter:
    return Counter(str(case.get("status", "UNKNOWN")) for case in summary)


def collect_issue_counts(summary: list[dict]) -> tuple[Counter, Counter]:
    blocking = Counter()
    warnings = Counter()
    for case in summary:
        blocking.update(str(item) for item in case.get("blocking_failures", []))
        warnings.update(str(item) for item in case.get("warnings", []))
    return blocking, warnings


def build_contract_decisions(summary: list[dict], contracts_report: dict) -> list[dict[str, str]]:
    decisions: list[dict[str, str]] = []
    blocking, warnings = collect_issue_counts(summary)

    if contracts_report.get("files_invalid", 0):
        decisions.append(
            {
                "priority": "P0",
                "area": "contrats_runtime",
                "decision": "Corriger les artefacts ou clarifier le contrat avant revue evaluateur.",
                "evidence": f"{contracts_report.get('files_invalid')} fichier(s) invalides sur {contracts_report.get('files_checked', 0)}.",
            }
        )

    for issue, count in blocking.most_common():
        decisions.append(
            {
                "priority": "P1",
                "area": infer_contract_area(issue),
                "decision": "Confirmer que ce blocage doit rester bloquant pour les dossiers reels.",
                "evidence": f"{count} occurrence(s): {issue}",
            }
        )

    for issue, count in warnings.most_common():
        decisions.append(
            {
                "priority": "P2",
                "area": infer_contract_area(issue),
                "decision": "Decider si ce warning doit rester un warning, devenir bloquant, ou etre assoupli.",
                "evidence": f"{count} occurrence(s): {issue}",
            }
        )

    if not decisions:
        decisions.append(
            {
                "priority": "P3",
                "area": "baseline",
                "decision": "Conserver les seuils actuels jusqu'a apparition d'un ecart metier.",
                "evidence": "Aucun blocage, warning ou echec contrat detecte dans les dossiers reels.",
            }
        )

    return decisions


def infer_contract_area(issue: str) -> str:
    lowered = issue.lower()
    if "confiance" in lowered or "confidence" in lowered:
        return "confidence_min_warning"
    if "distance" in lowered or "eloigne" in lowered:
        return "max_comparable_distance_km_warning"
    if "ajustement" in lowered:
        return "ajustement_sensible_montant_min"
    if "future" in lowered or "date" in lowered:
        return "date_vente_max_delta_days"
    if "coherence" in lowered or "approche" in lowered or "valuation" in lowered:
        return "valuation_inter_approach_max_delta_ratio"
    if "source" in lowered:
        return "source_traceability"
    return "rapport_conformite"


def build_hardening_markdown(summary: list[dict], contracts_report: dict, constraints: dict[str, str]) -> str:
    counts = status_counts(summary)
    blocking, warnings = collect_issue_counts(summary)
    decisions = build_contract_decisions(summary, contracts_report)

    lines = [
        "# Durcissement contrats pilotes reels v0",
        "",
        "## Synthese",
        "",
        f"- Dossiers analyses: **{len(summary)}**",
        f"- Statuts runtime: **{format_counter(counts)}**",
        f"- Blocages distincts: **{len(blocking)}**",
        f"- Warnings distincts: **{len(warnings)}**",
        f"- Fichiers contrat invalides: **{contracts_report.get('files_invalid', 0)}**",
        "",
        "## Seuils actuels",
        "",
    ]
    lines.extend(format_constraints(constraints))

    lines.extend(
        [
            "",
            "## Decisions a prendre",
            "",
            "| Priorite | Zone contrat | Decision | Evidence |",
            "|---|---|---|---|",
        ]
    )
    for item in decisions:
        lines.append(
            "| {priority} | {area} | {decision} | {evidence} |".format(
                priority=item["priority"],
                area=item["area"],
                decision=item["decision"],
                evidence=item["evidence"],
            )
        )

    lines.extend(["", "## Echecs contrats detailles", ""])
    failures = contracts_report.get("failures", [])
    if not failures:
        lines.append("- Aucun echec contrat runtime detecte.")
    else:
        for failure in failures:
            lines.append(f"- `{failure.get('path', '-')}`: {', '.join(failure.get('failures', []))}")

    lines.extend(
        [
            "",
            "## Regle de modification",
            "",
            "- Modifier `CONTRATS-DONNEES-V0.yaml` seulement si un ecart se repete ou bloque un dossier reel valide.",
            "- Ajouter ou ajuster un test runtime pour chaque changement de seuil.",
            "- Regenerer les artefacts runtime apres toute modification de contrat.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def format_constraints(constraints: dict[str, str]) -> list[str]:
    if not constraints:
        return ["- Aucun seuil extrait."]
    return [f"- `{key}`: `{value}`" for key, value in sorted(constraints.items())]


def format_counter(counter: Counter) -> str:
    if not counter:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in sorted(counter.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare le durcissement des contrats a partir des pilotes reels.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--contracts", type=Path, default=CONTRACTS_PATH_DEFAULT)
    parser.add_argument("--report-out", type=Path)
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Retourne exit code 0 et ecrit un rapport d'attente si la phase 3 n'a pas encore produit de resume.",
    )
    args = parser.parse_args()

    runtime_dir = args.runtime_dir
    report_out = args.report_out or runtime_dir / REPORT_NAME
    report_out.parent.mkdir(parents=True, exist_ok=True)
    constraints = parse_contract_constraints(args.contracts)

    summary_path = runtime_dir / SUMMARY_NAME
    if not summary_path.exists():
        report_out.write_text(build_waiting_report(runtime_dir, args.contracts, constraints), encoding="utf-8")
        print(f"Aucun resume runtime reel trouve: {summary_path}")
        print(f"Rapport d'attente: {report_out}")
        raise SystemExit(0 if args.allow_empty else 2)

    summary = load_json_if_exists(summary_path, [])
    contracts_report = load_json_if_exists(runtime_dir / CONTRACTS_REPORT_NAME, {"files_checked": 0, "files_invalid": 0, "failures": []})
    report_out.write_text(build_hardening_markdown(summary, contracts_report, constraints), encoding="utf-8")
    print(f"Rapport durcissement contrats: {report_out}")


if __name__ == "__main__":
    main()
