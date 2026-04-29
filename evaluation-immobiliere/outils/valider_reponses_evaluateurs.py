#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parent
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from compiler_reponses_evaluateurs import BASE_TASKS, NUMERIC_FIELDS, default_phase, normalize_task, parse_bool

INPUT_DEFAULT = Path("evaluation-immobiliere/atelier/REPONSES-EVALUATEURS.csv")
REPORT_DEFAULT = Path("evaluation-immobiliere/atelier/RAPPORT-VALIDATION-REPONSES.md")

RESPONSE_FIELDS = [
    "respondant_id",
    "role",
    "segment",
    "phase",
    "tache",
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
    "sortie_minimale",
    "commentaires",
]

RATING_FIELDS = {
    "douleur_1_5",
    "risque_conformite_1_5",
    "automatisation_potentielle_1_5",
    "complexite_technique_1_5",
    "disponibilite_donnees_1_5",
}
NON_NEGATIVE_FIELDS = {"temps_moyen_min", "frequence_par_mois"}
BOOL_FIELDS = {"validation_humaine_obligatoire", "decision_non_delegable"}
TEXT_RESPONSE_FIELDS = {"source_donnees_requise", "irritant_principal", "sortie_minimale", "commentaires"}
ALLOWED_PHASES = {phase for _task, phase in BASE_TASKS}
KNOWN_TASKS = {task for task, _phase in BASE_TASKS}


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    message: str
    row_number: int | None = None
    field: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    path: Path
    total_rows: int
    active_rows: int
    respondent_count: int
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.errors


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def validate_file(path: Path) -> ValidationResult:
    fieldnames, rows = read_csv(path)
    header_errors, header_warnings = validate_headers(fieldnames)
    row_result = validate_rows(path, rows)
    return ValidationResult(
        path=path,
        total_rows=row_result.total_rows,
        active_rows=row_result.active_rows,
        respondent_count=row_result.respondent_count,
        errors=[*header_errors, *row_result.errors],
        warnings=[*header_warnings, *row_result.warnings],
    )


def validate_headers(fieldnames: list[str]) -> tuple[list[ValidationIssue], list[ValidationIssue]]:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    missing = [field for field in RESPONSE_FIELDS if field not in fieldnames]
    extras = [field for field in fieldnames if field not in RESPONSE_FIELDS]
    for field in missing:
        errors.append(ValidationIssue("error", "Colonne requise manquante.", field=field))
    for field in extras:
        warnings.append(ValidationIssue("warning", "Colonne non reconnue ignoree par le compilateur.", field=field))
    return errors, warnings


def validate_rows(path: Path, rows: list[dict[str, str]]) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    seen_respondent_tasks: set[tuple[str, str]] = set()
    respondents: set[str] = set()
    active_rows = 0

    for index, row in enumerate(rows, start=2):
        task = normalize_task(row.get("tache", ""))
        phase = clean(row.get("phase", ""))
        active = is_active_response(row)

        if task and task not in KNOWN_TASKS:
            errors.append(issue(index, "tache", f"Tache inconnue: {task}."))
        if phase and phase not in ALLOWED_PHASES:
            errors.append(issue(index, "phase", f"Phase inconnue: {phase}."))
        if task in KNOWN_TASKS and phase and phase != default_phase(task):
            errors.append(issue(index, "phase", f"Phase incoherente pour {task}; attendu: {default_phase(task)}."))

        if not active:
            continue

        active_rows += 1
        for field in ("respondant_id", "role", "segment", "phase", "tache"):
            if not clean(row.get(field, "")):
                errors.append(issue(index, field, "Champ requis pour une ligne de reponse active."))

        respondent_id = clean(row.get("respondant_id", ""))
        if respondent_id:
            respondents.add(respondent_id)
        if respondent_id and task:
            key = (respondent_id, task)
            if key in seen_respondent_tasks:
                errors.append(issue(index, "tache", f"Doublon pour {respondent_id}/{task}."))
            seen_respondent_tasks.add(key)

        numeric_present = False
        for field in NUMERIC_FIELDS:
            value = clean(row.get(field, ""))
            if not value:
                continue
            numeric_present = True
            try:
                number = float(value)
            except ValueError:
                errors.append(issue(index, field, "Valeur numerique invalide."))
                continue
            if field in NON_NEGATIVE_FIELDS and number < 0:
                errors.append(issue(index, field, "La valeur doit etre positive ou nulle."))
            if field in RATING_FIELDS and not 1 <= number <= 5:
                errors.append(issue(index, field, "La valeur doit etre entre 1 et 5."))

        for field in BOOL_FIELDS:
            value = clean(row.get(field, ""))
            if value and parse_bool(value) is None:
                errors.append(issue(index, field, "Valeur attendue: oui/non."))

        if not numeric_present:
            warnings.append(issue(index, "temps_moyen_min", "Aucune donnee numerique renseignee pour cette ligne.", "warning"))

    if active_rows == 0:
        warnings.append(ValidationIssue("warning", "Aucune reponse evaluateur active encore renseignee."))

    return ValidationResult(
        path=path,
        total_rows=len(rows),
        active_rows=active_rows,
        respondent_count=len(respondents),
        errors=errors,
        warnings=warnings,
    )


def is_active_response(row: dict[str, str]) -> bool:
    if clean(row.get("respondant_id", "")):
        return True
    fields = [*NUMERIC_FIELDS, *BOOL_FIELDS, *TEXT_RESPONSE_FIELDS]
    return any(clean(row.get(field, "")) for field in fields)


def issue(row_number: int, field: str, message: str, severity: str = "error") -> ValidationIssue:
    return ValidationIssue(severity=severity, row_number=row_number, field=field, message=message)


def clean(value: str | None) -> str:
    return (value or "").strip()


def write_report(path: Path, result: ValidationResult) -> None:
    status = "A_CORRIGER" if result.errors else "VALIDE"
    if not result.errors and result.active_rows == 0:
        status = "PRET_A_RECEVOIR"

    lines = [
        "# Rapport validation reponses evaluateurs",
        "",
        f"- Fichier source: `{result.path.as_posix()}`",
        f"- Statut: **{status}**",
        f"- Lignes totales: **{result.total_rows}**",
        f"- Lignes actives: **{result.active_rows}**",
        f"- Repondants uniques: **{result.respondent_count}**",
        f"- Erreurs: **{len(result.errors)}**",
        f"- Avertissements: **{len(result.warnings)}**",
        "",
        "## Erreurs",
        "",
    ]
    lines.extend(render_issues(result.errors))
    lines.extend(["", "## Avertissements", ""])
    lines.extend(render_issues(result.warnings))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_issues(issues: list[ValidationIssue]) -> list[str]:
    if not issues:
        return ["- Aucune."]
    lines: list[str] = []
    for item in issues:
        location = "fichier"
        if item.row_number is not None:
            location = f"ligne {item.row_number}"
        if item.field:
            location = f"{location}, champ `{item.field}`"
        lines.append(f"- {location}: {item.message}")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Valide le fichier de reponses evaluateurs avant compilation.")
    parser.add_argument("--input", type=Path, default=INPUT_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args()

    result = validate_file(args.input)
    write_report(args.report_out, result)
    print(f"Rapport validation: {args.report_out}")
    print(f"Erreurs: {len(result.errors)} | Avertissements: {len(result.warnings)}")
    raise SystemExit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
