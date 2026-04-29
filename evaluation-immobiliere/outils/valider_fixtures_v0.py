#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

FIXTURES_DIR = Path("evaluation-immobiliere/tests/fixtures")
TEMPLATE_DEFAULT = FIXTURES_DIR / "template_dossier_anonymise.json"
REPORT_DEFAULT = Path("evaluation-immobiliere/atelier/RAPPORT-VALIDATION-DOSSIER-PILOTE.md")

TOP_LEVEL_REQUIRED = ["dossier_id", "date_reference", "surface", "comparables", "ajustements", "confidence"]
SURFACE_REQUIRED = ["value", "unit"]
COMPARABLE_REQUIRED = ["comparable_id", "prix_vente", "source_id"]
AJUSTEMENT_REQUIRED = ["ajustement_id", "montant", "source_id", "validation_humaine"]
ALLOWED_UNITS = {"pi2", "m2"}
ANONYMIZATION_PATTERNS = [
    re.compile(r"\b\d{1,6}\s+(rue|avenue|boulevard|boul\.|chemin|ch\.|route)\b", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
]


@dataclass(frozen=True)
class FixtureIssue:
    severity: str
    location: str
    message: str


@dataclass(frozen=True)
class FixtureValidation:
    path: Path
    dossier_id: str
    issues: list[FixtureIssue]

    @property
    def errors(self) -> list[FixtureIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[FixtureIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture(path: Path, *, strict: bool = False) -> FixtureValidation:
    data = load_json(path)
    issues: list[FixtureIssue] = []
    dossier_id = str(data.get("dossier_id", path.stem))

    if strict:
        for field in TOP_LEVEL_REQUIRED:
            if field not in data:
                issues.append(error(field, "Champ obligatoire absent."))

    validate_date(data.get("date_reference"), "date_reference", issues)
    validate_surface(data.get("surface"), "surface", issues, required=strict)
    validate_confidence(data.get("confidence"), "confidence", issues)
    validate_comparables(data.get("comparables", []), issues, strict=strict, subject_unit=nested(data, "surface", "unit"))
    validate_ajustements(data.get("ajustements", []), issues, strict=strict)
    validate_hypotheses(data.get("hypotheses", []), issues)
    validate_timeline(data.get("timeline", []), issues)
    validate_anonymization(data, issues)

    return FixtureValidation(path=path, dossier_id=dossier_id, issues=issues)


def validate_date(value: object, location: str, issues: list[FixtureIssue]) -> None:
    if value in (None, ""):
        return
    try:
        date.fromisoformat(str(value))
    except ValueError:
        issues.append(error(location, "Date invalide; format attendu YYYY-MM-DD."))


def validate_surface(value: object, location: str, issues: list[FixtureIssue], *, required: bool) -> None:
    if not isinstance(value, dict):
        if required:
            issues.append(error(location, "Surface obligatoire avec value/unit."))
        return
    for field in SURFACE_REQUIRED:
        if field not in value and required:
            issues.append(error(f"{location}.{field}", "Champ surface obligatoire absent."))
    unit = value.get("unit")
    if unit and unit not in ALLOWED_UNITS:
        issues.append(error(f"{location}.unit", f"Unite inconnue: {unit}."))
    if "value" in value and to_float(value.get("value")) <= 0:
        issues.append(error(f"{location}.value", "Surface doit etre positive."))


def validate_confidence(value: object, location: str, issues: list[FixtureIssue]) -> None:
    if value in (None, ""):
        return
    confidence = to_float(value)
    if not 0 <= confidence <= 1:
        issues.append(error(location, "Confidence doit etre entre 0 et 1."))
    elif confidence < 0.60:
        issues.append(warning(location, "Confiance basse; le dossier devrait rester en brouillon."))


def validate_comparables(items: object, issues: list[FixtureIssue], *, strict: bool, subject_unit: object) -> None:
    if not isinstance(items, list):
        issues.append(error("comparables", "Liste de comparables invalide."))
        return
    if strict and not items:
        issues.append(error("comparables", "Au moins un comparable est requis."))
    comp_units: set[str] = set()
    for index, item in enumerate(items, start=1):
        location = f"comparables[{index}]"
        if not isinstance(item, dict):
            issues.append(error(location, "Comparable invalide."))
            continue
        for field in COMPARABLE_REQUIRED:
            if field not in item:
                issues.append(error(f"{location}.{field}", "Champ comparable obligatoire absent."))
        if "prix_vente" in item and to_float(item.get("prix_vente")) <= 0:
            issues.append(error(f"{location}.prix_vente", "Prix de vente doit etre positif."))
        validate_surface(item.get("surface"), f"{location}.surface", issues, required=False)
        unit = nested(item, "surface", "unit")
        if isinstance(unit, str):
            comp_units.add(unit)
    if subject_unit and comp_units and any(unit != subject_unit for unit in comp_units):
        issues.append(error("comparables.surface.unit", "Unite incoherente entre sujet et comparables."))


def validate_ajustements(items: object, issues: list[FixtureIssue], *, strict: bool) -> None:
    if not isinstance(items, list):
        issues.append(error("ajustements", "Liste d'ajustements invalide."))
        return
    if strict and not items:
        issues.append(error("ajustements", "Au moins un ajustement est requis."))
    for index, item in enumerate(items, start=1):
        location = f"ajustements[{index}]"
        if not isinstance(item, dict):
            issues.append(error(location, "Ajustement invalide."))
            continue
        for field in AJUSTEMENT_REQUIRED:
            if field not in item:
                issues.append(error(f"{location}.{field}", "Champ ajustement obligatoire absent."))
        montant = to_float(item.get("montant"))
        if "montant" in item and montant < 0:
            issues.append(error(f"{location}.montant", "Montant doit etre positif ou nul."))
        if montant >= 25_000 and not bool(item.get("validation_humaine", False)):
            issues.append(error(f"{location}.validation_humaine", "Ajustement sensible sans validation humaine."))


def validate_hypotheses(items: object, issues: list[FixtureIssue]) -> None:
    if not isinstance(items, list):
        return
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            issues.append(error(f"hypotheses[{index}]", "Hypothese invalide."))
            continue
        source_ids = item.get("source_ids", [])
        if source_ids and not isinstance(source_ids, list):
            issues.append(error(f"hypotheses[{index}].source_ids", "Liste de sources invalide."))


def validate_timeline(items: object, issues: list[FixtureIssue]) -> None:
    if not isinstance(items, list):
        return
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            issues.append(error(f"timeline[{index}]", "Evenement timeline invalide."))
            continue
        validate_date(item.get("date"), f"timeline[{index}].date", issues)
        if item.get("date") and not item.get("source_id"):
            issues.append(warning(f"timeline[{index}].source_id", "Evenement date sans source_id."))


def validate_anonymization(data: object, issues: list[FixtureIssue], location: str = "$") -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            validate_anonymization(value, issues, f"{location}.{key}")
        return
    if isinstance(data, list):
        for index, value in enumerate(data, start=1):
            validate_anonymization(value, issues, f"{location}[{index}]")
        return
    if isinstance(data, str):
        for pattern in ANONYMIZATION_PATTERNS:
            if pattern.search(data):
                issues.append(error(location, "Possible information nominative ou adresse precise."))
                break


def write_report(path: Path, validations: list[FixtureValidation], *, strict: bool) -> None:
    total_errors = sum(len(item.errors) for item in validations)
    total_warnings = sum(len(item.warnings) for item in validations)
    status = "A_CORRIGER" if total_errors else "VALIDE"
    mode = "strict" if strict else "inventaire"
    lines = [
        "# Rapport validation dossier pilote",
        "",
        f"- Mode: **{mode}**",
        f"- Dossiers: **{len(validations)}**",
        f"- Erreurs: **{total_errors}**",
        f"- Avertissements: **{total_warnings}**",
        f"- Statut: **{status}**",
        "",
    ]
    for item in validations:
        lines.append(f"## {item.path.as_posix()}")
        lines.append(f"- Dossier: `{item.dossier_id}`")
        lines.append(f"- Erreurs: **{len(item.errors)}**")
        lines.append(f"- Avertissements: **{len(item.warnings)}**")
        if not item.issues:
            lines.append("- Aucune anomalie detectee.")
        else:
            for issue in item.issues:
                lines.append(f"- {issue.severity.upper()} `{issue.location}`: {issue.message}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def print_validation(item: FixtureValidation) -> None:
    print(f"\n{item.path.name}")
    if not item.issues:
        print("  OK")
        return
    for issue in item.issues:
        print(f"  - {issue.severity.upper()} {issue.location}: {issue.message}")


def error(location: str, message: str) -> FixtureIssue:
    return FixtureIssue("error", location, message)


def warning(location: str, message: str) -> FixtureIssue:
    return FixtureIssue("warning", location, message)


def nested(data: dict, *keys: str) -> object:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Valide les dossiers pilotes anonymises.")
    parser.add_argument("--input", type=Path, help="Fixture unique a valider.")
    parser.add_argument("--strict", action="store_true", help="Retourne une erreur si le dossier n'est pas pret pilote.")
    parser.add_argument("--report-out", type=Path, help="Ecrit un rapport Markdown de validation.")
    args = parser.parse_args()

    paths = [args.input] if args.input else sorted(FIXTURES_DIR.glob("case_*.json"))
    validations = [validate_fixture(path, strict=args.strict) for path in paths]
    for item in validations:
        print_validation(item)

    if args.report_out:
        write_report(args.report_out, validations, strict=args.strict)
        print(f"\nRapport validation: {args.report_out}")

    has_errors = any(item.errors for item in validations)
    raise SystemExit(1 if args.strict and has_errors else 0)


if __name__ == "__main__":
    main()
