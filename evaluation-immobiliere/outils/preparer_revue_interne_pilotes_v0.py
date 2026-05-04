#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
SUMMARY_NAME = "runtime_summary.json"
REPORT_NAME = "REVUE-INTERNE-PILOTES-REELS-V0.md"
REQUIRED_ARTIFACTS = [
    "compliance-qa.statut_sortie.json",
    "compliance-qa.rapport_non_conformites.json",
    "compliance-qa.recommandations_corrections.md",
]
REDACTION_ARTIFACT = "redaction.brouillon_rapport.md"


def load_summary(runtime_dir: Path) -> list[dict]:
    summary_path = runtime_dir / SUMMARY_NAME
    return json.loads(summary_path.read_text(encoding="utf-8"))


def build_waiting_report(runtime_dir: Path) -> str:
    return "\n".join(
        [
            "# Revue interne dossiers pilotes reels v0",
            "",
            "- Statut: **EN_ATTENTE_EXECUTION_PHASE_3**",
            f"- Repertoire runtime attendu: `{runtime_dir.as_posix()}`",
            f"- Fichier requis: `{SUMMARY_NAME}`",
            "",
            "## Prochaine action",
            "",
            "Executer d'abord `evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py` apres avoir ajoute des fixtures `case_pilote_reel_*.json` anonymisees dans un repertoire hors repo ignore.",
            "",
        ]
    )


def artifact_path(case: dict, artifact_name: str) -> Path:
    return Path(str(case.get("artifact_dir", ""))) / artifact_name


def missing_artifacts(case: dict) -> list[str]:
    missing = [name for name in REQUIRED_ARTIFACTS if not artifact_path(case, name).exists()]
    if case.get("status") != "A_REVOIR" and not artifact_path(case, REDACTION_ARTIFACT).exists():
        missing.append(REDACTION_ARTIFACT)
    return missing


def review_decision(case: dict) -> str:
    if missing_artifacts(case) or case.get("blocking_failures"):
        return "A_CORRIGER_AVANT_EVALUATEURS"
    if case.get("warnings") or case.get("status") == "BROUILLON":
        return "A_CLARIFIER_INTERNE"
    return "PRET_REVUE_EVALUATEUR"


def build_backlog_items(summary: list[dict]) -> list[dict]:
    items: list[dict] = []
    for case in summary:
        case_name = Path(str(case.get("artifact_dir", ""))).name or str(case.get("dossier_id", "-"))
        for artifact in missing_artifacts(case):
            items.append(
                {
                    "case": case_name,
                    "severity": "blocking",
                    "item": f"Artefact manquant: {artifact}",
                    "owner": "tech",
                }
            )
        for failure in case.get("blocking_failures", []):
            items.append(
                {
                    "case": case_name,
                    "severity": "blocking",
                    "item": str(failure),
                    "owner": "tech/metier",
                }
            )
        for warning in case.get("warnings", []):
            items.append(
                {
                    "case": case_name,
                    "severity": "warning",
                    "item": str(warning),
                    "owner": "interne",
                }
            )
    return items


def build_review_markdown(summary: list[dict]) -> str:
    counts = {
        "A_CORRIGER_AVANT_EVALUATEURS": 0,
        "A_CLARIFIER_INTERNE": 0,
        "PRET_REVUE_EVALUATEUR": 0,
    }
    decisions = []
    for case in summary:
        decision = review_decision(case)
        counts[decision] += 1
        decisions.append((case, decision))

    lines = [
        "# Revue interne dossiers pilotes reels v0",
        "",
        "## Synthese",
        "",
        f"- Dossiers analyses: **{len(summary)}**",
        f"- A corriger avant evaluateurs: **{counts['A_CORRIGER_AVANT_EVALUATEURS']}**",
        f"- A clarifier interne: **{counts['A_CLARIFIER_INTERNE']}**",
        f"- Prets pour revue evaluateur: **{counts['PRET_REVUE_EVALUATEUR']}**",
        "",
        "## Decisions par dossier",
        "",
        "| Cas | Dossier | Statut runtime | Decision interne | Blocages | Warnings | Artefacts manquants |",
        "|---|---|---|---|---:|---:|---|",
    ]

    for case, decision in decisions:
        artifact_dir = str(case.get("artifact_dir", ""))
        case_name = Path(artifact_dir).name if artifact_dir else "-"
        missing = missing_artifacts(case)
        lines.append(
            "| {case_name} | {dossier_id} | {status} | {decision} | {blocking} | {warnings} | {missing} |".format(
                case_name=case_name,
                dossier_id=case.get("dossier_id", "-"),
                status=case.get("status", "UNKNOWN"),
                decision=decision,
                blocking=len(case.get("blocking_failures", [])),
                warnings=len(case.get("warnings", [])),
                missing=", ".join(missing) if missing else "-",
            )
        )

    lines.extend(["", "## Backlog avant revue evaluateur", ""])
    backlog_items = build_backlog_items(summary)
    if not backlog_items:
        lines.append("- Aucun item technique ou interne detecte.")
    else:
        lines.extend(["| Cas | Severite | Item | Responsable |", "|---|---|---|---|"])
        for item in backlog_items:
            lines.append(
                "| {case} | {severity} | {text} | {owner} |".format(
                    case=item["case"],
                    severity=item["severity"],
                    text=item["item"],
                    owner=item["owner"],
                )
            )

    lines.extend(
        [
            "",
            "## Critere de passage",
            "",
            "- Aucun artefact obligatoire manquant.",
            "- Aucun blocage non explique avant de solliciter les evaluateurs.",
            "- Les warnings restants sont formules comme questions metier ou points de validation.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare la revue interne des dossiers pilotes reels.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
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

    summary_path = runtime_dir / SUMMARY_NAME
    if not summary_path.exists():
        report_out.write_text(build_waiting_report(runtime_dir), encoding="utf-8")
        print(f"Aucun resume runtime reel trouve: {summary_path}")
        print(f"Rapport d'attente: {report_out}")
        raise SystemExit(0 if args.allow_empty else 2)

    summary = load_summary(runtime_dir)
    report_out.write_text(build_review_markdown(summary), encoding="utf-8")
    print(f"Rapport revue interne: {report_out}")


if __name__ == "__main__":
    main()
