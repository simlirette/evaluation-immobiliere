#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path("evaluation-immobiliere/tests/fixtures")
REPORTS_DIR = Path("evaluation-immobiliere/tests/reports")


@dataclass
class DryRunResult:
    fixture: str
    status: str
    blocking_failures: list[str]
    warnings: list[str]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(data: dict[str, Any]) -> DryRunResult:
    blocking: list[str] = []
    warnings: list[str] = []

    for c in data.get("comparables", []):
        if "source_id" not in c:
            blocking.append("B002: comparable sans source_id")

    for a in data.get("ajustements", []):
        if "source_id" not in a:
            blocking.append("B002: ajustement sans source_id")
        if a.get("montant", 0) >= 25000 and not a.get("validation_humaine", False):
            blocking.append("B005: ajustement sensible sans validation_humaine")

    subject_unit = data.get("surface", {}).get("unit")
    comp_units = {c.get("surface", {}).get("unit") for c in data.get("comparables", []) if isinstance(c.get("surface"), dict)}
    if subject_unit and comp_units and any(u and u != subject_unit for u in comp_units):
        blocking.append("B004: unité incohérente sujet/comparables")

    if data.get("confidence", 1) < 0.60:
        warnings.append("W001: confiance faible")

    status = "A_REVOIR" if blocking else ("BROUILLON" if warnings else "PRET_REVISION_FINALE")

    return DryRunResult(
        fixture=data.get("dossier_id", "unknown"),
        status=status,
        blocking_failures=blocking,
        warnings=warnings,
    )


def write_report(src_path: Path, result: DryRunResult) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{src_path.stem}.report.json"
    out.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    all_results: list[DryRunResult] = []

    for fixture_path in sorted(FIXTURES_DIR.glob("case_*.json")):
        data = load_json(fixture_path)
        result = evaluate(data)
        write_report(fixture_path, result)
        all_results.append(result)

    print("Dry-run terminé. Résumé:")
    for r in all_results:
        print(f"- {r.fixture}: {r.status} | blocking={len(r.blocking_failures)} warnings={len(r.warnings)}")


if __name__ == "__main__":
    main()
