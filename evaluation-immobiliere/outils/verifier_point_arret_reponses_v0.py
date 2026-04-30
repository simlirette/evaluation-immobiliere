#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parent
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from valider_reponses_evaluateurs import INPUT_DEFAULT, REPORT_DEFAULT, ValidationResult, validate_file, write_report

PACKAGE_INDEX_DEFAULT = Path("evaluation-immobiliere/paquets_evaluateurs/v0/PAQUET-EVALUATEURS-V0.md")
OUT_REPORT_DEFAULT = Path("evaluation-immobiliere/paquets_evaluateurs/v0/POINT-ARRET-REPONSES-EVALUATEURS-V0.md")


def validation_status(result: ValidationResult) -> str:
    if result.errors:
        return "A_CORRIGER"
    if result.active_rows == 0:
        return "PRET_A_RECEVOIR"
    return "REPONSES_PRESENTES"


def package_status(package_index: Path) -> str:
    if not package_index.exists():
        return "PAQUET_ABSENT"
    text = package_index.read_text(encoding="utf-8")
    match = re.search(r"- Statut: \*\*(.+?)\*\*", text)
    return match.group(1).strip() if match else "STATUT_PAQUET_INCONNU"


def stop_status(result: ValidationResult, package_state: str) -> str:
    if result.errors:
        return "A_CORRIGER_AVANT_ATTENTE"
    if result.active_rows > 0:
        return "REPONSES_DEJA_PRESENTES"
    if package_state == "PRET_A_ENVOYER":
        return "PRET_A_RECEVOIR_REPONSES"
    return "EN_ATTENTE_AVANT_REPONSES"


def build_stop_report(result: ValidationResult, package_state: str, response_report: Path, package_index: Path) -> str:
    status = stop_status(result, package_state)
    lines = [
        "# Point d'arret reponses evaluateurs v0",
        "",
        f"- Statut: **{status}**",
        f"- Fichier reponses: `{result.path.as_posix()}`",
        f"- Rapport validation reponses: `{response_report.as_posix()}`",
        f"- Statut validation reponses: **{validation_status(result)}**",
        f"- Lignes actives: **{result.active_rows}**",
        f"- Repondants uniques: **{result.respondent_count}**",
        f"- Statut paquet evaluateurs: **{package_state}**",
        f"- Index paquet: `{package_index.as_posix()}`",
        "",
        "## Decision",
        "",
    ]
    if status == "PRET_A_RECEVOIR_REPONSES":
        lines.append("- Le paquet est pret et le CSV consolide est vide: attendre les reponses evaluateurs.")
    elif status == "EN_ATTENTE_AVANT_REPONSES":
        lines.append("- Ne pas saisir de reponses maintenant; completer d'abord les phases qui precedent l'envoi aux evaluateurs.")
    elif status == "REPONSES_DEJA_PRESENTES":
        lines.append("- Des reponses sont deja presentes; passer au flux de validation/compilation au lieu du point d'arret.")
    else:
        lines.append("- Corriger les erreurs de structure avant de poursuivre.")

    lines.extend(
        [
            "",
            "## Regles",
            "",
            "- Ne pas inventer de `respondant_id`.",
            "- Ne pas pre-remplir les scores, booleens ou commentaires.",
            "- Garder `REPONSES-EVALUATEURS.csv` vide ou avec des lignes gabarit inactives tant que les reponses ne sont pas recues.",
            "- Quand les reponses arrivent, lancer `valider_reponses_evaluateurs.py` avant toute compilation.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_stop_report(path: Path, result: ValidationResult, package_state: str, response_report: Path, package_index: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_stop_report(result, package_state, response_report, package_index), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifie le point d'arret avant saisie des reponses evaluateurs.")
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--response-report", type=Path, default=REPORT_DEFAULT)
    parser.add_argument("--package-index", type=Path, default=PACKAGE_INDEX_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=OUT_REPORT_DEFAULT)
    parser.add_argument(
        "--allow-waiting",
        action="store_true",
        help="Retourne exit code 0 si les reponses sont vides mais que le paquet n'est pas encore PRET_A_ENVOYER.",
    )
    args = parser.parse_args()

    result = validate_file(args.input)
    write_report(args.response_report, result)
    state = package_status(args.package_index)
    write_stop_report(args.report_out, result, state, args.response_report, args.package_index)

    status = stop_status(result, state)
    print(f"Point d'arret: {args.report_out}")
    print(f"Statut: {status}")
    if status == "PRET_A_RECEVOIR_REPONSES":
        raise SystemExit(0)
    if status == "EN_ATTENTE_AVANT_REPONSES" and args.allow_waiting:
        raise SystemExit(0)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
