#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml
from outils.generer_rapport_pilote_runtime_v0 import build_markdown
from outils.analyser_qualite_runtime_v0 import generate_quality_report
from outils.valider_contrats_runtime_v0 import validate_runtime_contracts
from outils.valider_fixtures_v0 import FixtureValidation, validate_fixture, write_report

FIXTURES_DIR = Path("evaluation-immobiliere/tests/fixtures")
CASE_PATTERN = "case_pilote_reel_*.json"
PIPELINE_PATH = Path("evaluation-immobiliere/integration/PIPELINE-RUNTIME-ASTON-V0.yaml")
OUT_DIR = Path("evaluation-immobiliere/runtime_pilotes_reels")
SUMMARY_PATH = OUT_DIR / "runtime_summary.json"
VALIDATION_REPORT_PATH = OUT_DIR / "validation_dossiers_reels.md"
CONTRACTS_REPORT_PATH = OUT_DIR / "contracts_report.json"
RUNTIME_REPORT_PATH = OUT_DIR / "RAPPORT-PILOTE-REEL-RUNTIME-V0.md"
QUALITY_REPORT_JSON_PATH = OUT_DIR / "quality_report.json"
QUALITY_REPORT_MD_PATH = OUT_DIR / "RAPPORT-QUALITE-RUNTIME-V0.md"
PRESERVED_OUTPUT_NAMES = {
    "ingestion_v0",
    "source_text",
    "DURCISSEMENT-CONTRATS-PILOTES-REELS-V0.md",
    "REVUE-INTERNE-PILOTES-REELS-V0.md",
    "runtime_registry.json",
    "RUNTIME-REGISTRY-V0.md",
}


def discover_real_pilot_cases(fixtures_dir: Path = FIXTURES_DIR) -> list[Path]:
    return sorted(fixtures_dir.glob(CASE_PATTERN))


def build_waiting_report(fixtures_dir: Path = FIXTURES_DIR) -> str:
    return "\n".join(
        [
            "# Execution dossiers pilotes reels v0",
            "",
            "- Statut: **EN_ATTENTE_DOSSIERS**",
            f"- Repertoire fixtures: `{fixtures_dir.as_posix()}`",
            f"- Pattern attendu: `{CASE_PATTERN}`",
            "",
            "## Prochaine action",
            "",
            "Remplir et valider les brouillons `draft_dossier_reel_*.json`, puis renommer chaque dossier pret en `case_pilote_reel_*.json`.",
            "",
        ]
    )


def reset_output_dir(out_dir: Path) -> None:
    if out_dir.exists():
        for path in out_dir.iterdir():
            if path.name in PRESERVED_OUTPUT_NAMES:
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)


def validate_cases(case_paths: list[Path]) -> list[FixtureValidation]:
    return [validate_fixture(path, strict=True) for path in case_paths]


def has_errors(validations: list[FixtureValidation]) -> bool:
    return any(item.errors for item in validations)


def write_contract_report(runtime_dir: Path, report_path: Path) -> bool:
    report = validate_runtime_contracts(runtime_dir)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Rapport contrats reels: {report_path} | ok={report.get('ok')}")
    return bool(report.get("ok"))


def write_quality_reports(runtime_dir: Path) -> dict:
    report = generate_quality_report(
        runtime_dir=runtime_dir,
        summary_path=runtime_dir / SUMMARY_PATH.name,
        pipeline_path=PIPELINE_PATH,
        ingestion_dir=runtime_dir / "ingestion_v0",
        json_out=runtime_dir / QUALITY_REPORT_JSON_PATH.name,
        markdown_out=runtime_dir / QUALITY_REPORT_MD_PATH.name,
    )
    print(f"Rapport qualite reel JSON: {runtime_dir / QUALITY_REPORT_JSON_PATH.name}")
    print(f"Rapport qualite reel Markdown: {runtime_dir / QUALITY_REPORT_MD_PATH.name}")
    return report


def run_real_pilot_cases(case_paths: list[Path], out_dir: Path) -> list[dict]:
    os.environ.setdefault("RUNTIME_DETERMINISTIC", "1")
    os.environ.setdefault("RUNTIME_FIXED_TIMESTAMP_UTC", "2026-04-28T00:00:00+00:00")

    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
    engine = RuntimeEngine(steps=steps, strict_mode=True)
    results: list[dict] = []

    print(f"Pipeline charge: {len(steps)} steps depuis {PIPELINE_PATH}")
    for case_path in case_paths:
        result = engine.run_case(case_path, out_dir, case_subdir=True)
        results.append(result)
        print(f"Simule reel: {case_path.name} -> {len(result['events'])} events | status={result['status']}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Valide et execute les dossiers pilotes reels anonymises.")
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURES_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Retourne exit code 0 et ecrit un rapport d'attente si aucun dossier reel actif n'existe.",
    )
    parser.add_argument(
        "--fail-on-contract-errors",
        action="store_true",
        help="Retourne exit code 1 si le rapport de contrats contient des erreurs.",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    reset_output_dir(out_dir)

    case_paths = discover_real_pilot_cases(args.fixtures_dir)
    if not case_paths:
        waiting_report = build_waiting_report(args.fixtures_dir)
        (out_dir / RUNTIME_REPORT_PATH.name).write_text(waiting_report, encoding="utf-8")
        print(f"Aucun dossier reel actif trouve avec le pattern {CASE_PATTERN}.")
        print(f"Rapport d'attente: {out_dir / RUNTIME_REPORT_PATH.name}")
        raise SystemExit(0 if args.allow_empty else 2)

    validations = validate_cases(case_paths)
    write_report(out_dir / VALIDATION_REPORT_PATH.name, validations, strict=True)
    print(f"Rapport validation reels: {out_dir / VALIDATION_REPORT_PATH.name}")
    if has_errors(validations):
        print("Validation stricte echouee: corriger les dossiers reels avant execution runtime.")
        raise SystemExit(1)

    results = run_real_pilot_cases(case_paths, out_dir)
    (out_dir / SUMMARY_PATH.name).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / RUNTIME_REPORT_PATH.name).write_text(build_markdown(results), encoding="utf-8")
    print(f"Resume runtime reel: {out_dir / SUMMARY_PATH.name}")
    print(f"Rapport runtime reel: {out_dir / RUNTIME_REPORT_PATH.name}")

    contracts_ok = write_contract_report(out_dir, out_dir / CONTRACTS_REPORT_PATH.name)
    write_quality_reports(out_dir)
    if args.fail_on_contract_errors and not contracts_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
