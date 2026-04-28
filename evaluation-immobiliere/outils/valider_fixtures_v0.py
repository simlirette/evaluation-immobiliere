#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

FIXTURES_DIR = Path("evaluation-immobiliere/tests/fixtures")


def validate_fixture(path: Path) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))

    for c in data.get("comparables", []):
        if "source_id" not in c:
            errors.append("Comparable sans source_id")

    for a in data.get("ajustements", []):
        if "source_id" not in a:
            errors.append("Ajustement sans source_id")
        if a.get("montant", 0) >= 25000 and not a.get("validation_humaine", False):
            errors.append("Ajustement sensible sans validation_humaine")

    subject_unit = data.get("surface", {}).get("unit")
    comp_units = {c.get("surface", {}).get("unit") for c in data.get("comparables", []) if isinstance(c.get("surface"), dict)}
    if subject_unit and comp_units and any(u and u != subject_unit for u in comp_units):
        errors.append("Unité incohérente entre sujet et comparables")

    if data.get("confidence", 1) < 0.60:
        errors.append("WARNING: confiance basse")

    return errors


def main() -> None:
    for fixture in sorted(FIXTURES_DIR.glob("case_*.json")):
        issues = validate_fixture(fixture)
        print(f"\n{fixture.name}")
        if not issues:
            print("  OK")
        else:
            for issue in issues:
                print(f"  - {issue}")


if __name__ == "__main__":
    main()
