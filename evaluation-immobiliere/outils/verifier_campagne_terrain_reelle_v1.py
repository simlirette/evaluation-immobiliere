#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTILS_DIR = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from auditer_anonymisation_v0 import build_anonymization_audit  # noqa: E402
from executer_dossiers_pilotes_reels_v0 import CASE_PATTERN, discover_real_pilot_cases  # noqa: E402
from preparer_paquet_evaluateurs_v0 import package_status as computed_package_status  # noqa: E402
from preparer_revue_interne_pilotes_v0 import review_decision  # noqa: E402
from valider_fixtures_v0 import FixtureValidation, validate_fixture  # noqa: E402
from valider_reponses_evaluateurs import validate_file  # noqa: E402
from verifier_point_arret_reponses_v0 import package_status as package_index_status  # noqa: E402
from verifier_point_arret_reponses_v0 import stop_status  # noqa: E402

FIXTURES_DIR_DEFAULT = Path("evaluation-immobiliere/tests/fixtures_external")
RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
PACKAGE_INDEX_DEFAULT = Path("evaluation-immobiliere/paquets_evaluateurs/v0/PAQUET-EVALUATEURS-V0.md")
RESPONSES_INPUT_DEFAULT = Path("evaluation-immobiliere/atelier/REPONSES-EVALUATEURS.csv")
REPORT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "phase_h_campagne_terrain_gate.json"
REPORT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "PHASE-H-CAMPAGNE-TERRAIN-GATE-V1.md"

WAITING_STATUS = "EN_ATTENTE_ENTREES_TERRAIN_REELLES"
READY_STATUS = "PRET_A_RECEVOIR_REPONSES_TERRAIN"
NO_GO_STATUS = "NO_GO_CAMPAGNE_TERRAIN_REELLE"

INGESTION_MANIFEST_NAME = "MANIFESTE-INGESTION-PDF-V0.json"
SUMMARY_NAME = "runtime_summary.json"
REVIEW_REPORT_NAME = "REVUE-INTERNE-PILOTES-REELS-V0.md"
FORBIDDEN_ACTIVE_CASE_DIRS = [PROJECT_ROOT / "tests" / "fixtures"]


def normalize_path(path: Path) -> str:
    return path.as_posix()


def resolved(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def check(name: str, ok: bool, status: str, evidence: str, *, blocking: bool = True) -> dict[str, object]:
    return {
        "name": name,
        "ok": ok,
        "status": status,
        "evidence": evidence,
        "blocking": blocking,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def discover_forbidden_repo_cases() -> list[Path]:
    cases: list[Path] = []
    for directory in FORBIDDEN_ACTIVE_CASE_DIRS:
        cases.extend(sorted(directory.glob(CASE_PATTERN)))
    return sorted(cases, key=lambda item: item.as_posix())


def input_location_check(fixtures_dir: Path, active_cases_count: int) -> dict[str, object]:
    if active_cases_count == 0:
        return check(
            "localisation_entrees_terrain",
            True,
            "NON_APPLICABLE_SANS_ENTREES",
            "Aucun dossier reel actif a localiser.",
            blocking=False,
        )

    fixtures_resolved = resolved(fixtures_dir)
    repo_resolved = resolved(REPO_ROOT)
    project_resolved = resolved(PROJECT_ROOT)
    if not is_relative_to(fixtures_resolved, repo_resolved):
        return check(
            "localisation_entrees_terrain",
            True,
            "HORS_REPO_ACTIF",
            normalize_path(fixtures_dir),
        )
    if is_relative_to(fixtures_resolved, repo_resolved / ".test-tmp"):
        return check(
            "localisation_entrees_terrain",
            True,
            "REPERTOIRE_TEST_IGNORE",
            ".test-tmp est ignore par Git et reserve aux preuves locales non versionnees.",
        )
    if fixtures_resolved == project_resolved / "tests" / "fixtures_external":
        return check(
            "localisation_entrees_terrain",
            True,
            "REPERTOIRE_IGNORE_CONTROLE",
            "fixtures_external est ignore par git sauf fixtures de gates synthetiques explicitement whitelistees.",
        )
    return check(
        "localisation_entrees_terrain",
        False,
        "DANS_REPO_ACTIF_INTERDIT",
        f"Deplacer les dossiers reels anonymises hors repo actif: {normalize_path(fixtures_dir)}",
    )


def validate_cases(case_paths: list[Path]) -> tuple[list[FixtureValidation], list[str]]:
    validations = [validate_fixture(path, strict=True) for path in case_paths]
    errors: list[str] = []
    for validation in validations:
        for issue in validation.errors:
            errors.append(f"{normalize_path(validation.path)} {issue.location}: {issue.message}")
    return validations, errors


def validation_check(case_paths: list[Path]) -> tuple[dict[str, object], list[FixtureValidation]]:
    validations, errors = validate_cases(case_paths)
    if errors:
        return (
            check(
                "validation_fixtures_strictes",
                False,
                "A_CORRIGER",
                "; ".join(errors[:5]),
            ),
            validations,
        )
    return (
        check(
            "validation_fixtures_strictes",
            True,
            "VALIDE",
            f"{len(case_paths)} dossier(s) reel(s) anonymise(s) valides en strict.",
        ),
        validations,
    )


def anonymization_check(fixtures_dir: Path) -> tuple[dict[str, object], dict[str, object]]:
    report = build_anonymization_audit([fixtures_dir])
    status = str(report.get("status", "UNKNOWN"))
    findings = int(report.get("findings_count", 0) or 0)
    return (
        check(
            "audit_anonymisation",
            status == "OK",
            status,
            f"{findings} motif(s) sensible(s) detecte(s) dans {normalize_path(fixtures_dir)}.",
        ),
        report,
    )


def load_runtime_summary(runtime_dir: Path) -> list[dict[str, object]] | None:
    summary_path = runtime_dir / SUMMARY_NAME
    if not summary_path.exists():
        return None
    payload = read_json(summary_path)
    if not isinstance(payload, list):
        return None
    return [item for item in payload if isinstance(item, dict)]


def runtime_check(runtime_dir: Path, active_cases_count: int) -> tuple[dict[str, object], list[dict[str, object]] | None]:
    summary = load_runtime_summary(runtime_dir)
    if summary is None:
        return (
            check(
                "execution_runtime_pilotes_reels",
                False,
                "SUMMARY_ABSENT",
                normalize_path(runtime_dir / SUMMARY_NAME),
            ),
            None,
        )
    ok = len(summary) >= active_cases_count
    return (
        check(
            "execution_runtime_pilotes_reels",
            ok,
            "EXECUTE" if ok else "DOSSIERS_RUNTIME_INSUFFISANTS",
            f"{len(summary)}/{active_cases_count} dossier(s) present(s) dans runtime_summary.json.",
        ),
        summary,
    )


def ingestion_check(runtime_dir: Path, active_cases_count: int) -> dict[str, object]:
    manifest_path = runtime_dir / "ingestion_v0" / INGESTION_MANIFEST_NAME
    if not manifest_path.exists():
        return check(
            "ingestion_normalisation",
            False,
            "MANIFESTE_ABSENT",
            normalize_path(manifest_path),
        )
    payload = read_json(manifest_path)
    errors = payload.get("errors", [])
    normalized_count = int(payload.get("normalized_count", 0) or 0)
    ok = isinstance(errors, list) and not errors and normalized_count >= active_cases_count
    return check(
        "ingestion_normalisation",
        ok,
        "NORMALISE" if ok else "A_CORRIGER",
        f"{normalized_count}/{active_cases_count} dossier(s) normalise(s); erreurs={len(errors) if isinstance(errors, list) else 'inconnu'}.",
    )


def internal_review_check(runtime_dir: Path, summary: list[dict[str, object]] | None) -> dict[str, object]:
    review_path = runtime_dir / REVIEW_REPORT_NAME
    if not review_path.exists():
        return check(
            "revue_interne",
            False,
            "RAPPORT_ABSENT",
            normalize_path(review_path),
        )
    if summary is None:
        return check("revue_interne", False, "SUMMARY_ABSENT", "Impossible de classer les dossiers sans runtime_summary.json.")
    decisions = [review_decision(item) for item in summary]
    blockers = [decision for decision in decisions if decision == "A_CORRIGER_AVANT_EVALUATEURS"]
    return check(
        "revue_interne",
        not blockers,
        "TERMINEE" if not blockers else "A_CORRIGER_AVANT_EVALUATEURS",
        f"decisions={','.join(decisions) if decisions else '-'}",
    )


def evaluator_package_check(runtime_dir: Path, package_index: Path, summary: list[dict[str, object]] | None) -> dict[str, object]:
    computed = computed_package_status(summary, runtime_dir)
    indexed = package_index_status(package_index)
    ok = computed == "PRET_A_ENVOYER" and indexed == "PRET_A_ENVOYER"
    return check(
        "paquet_evaluateurs",
        ok,
        indexed,
        f"statut_calcule={computed}; index={normalize_path(package_index)}",
    )


def response_stop_check(response_input: Path, package_index: Path) -> dict[str, object]:
    if not response_input.exists():
        return check(
            "point_arret_avant_reponses",
            False,
            "FICHIER_REPONSES_ABSENT",
            normalize_path(response_input),
        )
    result = validate_file(response_input)
    package_state = package_index_status(package_index)
    status = stop_status(result, package_state)
    ok = status == "PRET_A_RECEVOIR_REPONSES"
    return check(
        "point_arret_avant_reponses",
        ok,
        status,
        f"lignes_actives={result.active_rows}; erreurs={len(result.errors)}; paquet={package_state}",
    )


def report_ok(checks: list[dict[str, object]]) -> bool:
    return all(bool(item.get("ok")) for item in checks if item.get("blocking") is not False)


def build_phase_h_gate_report(
    *,
    fixtures_dir: Path = FIXTURES_DIR_DEFAULT,
    runtime_dir: Path = RUNTIME_DIR_DEFAULT,
    package_index: Path = PACKAGE_INDEX_DEFAULT,
    response_input: Path = RESPONSES_INPUT_DEFAULT,
) -> dict[str, object]:
    active_cases = discover_real_pilot_cases(fixtures_dir)
    forbidden_cases = discover_forbidden_repo_cases()
    checks: list[dict[str, object]] = []
    checks.append(
        check(
            "aucun_dossier_reel_dans_fixtures_repo",
            not forbidden_cases,
            "OK" if not forbidden_cases else "DREEL_DANS_REPO_ACTIF",
            ", ".join(normalize_path(path) for path in forbidden_cases) if forbidden_cases else "Aucun case_pilote_reel_*.json dans tests/fixtures.",
        )
    )
    checks.append(input_location_check(fixtures_dir, len(active_cases)))

    if not active_cases:
        ok = report_ok(checks)
        return {
            "schema_version": "phase_h_campagne_terrain_gate_v1",
            "ok": ok,
            "decision": WAITING_STATUS if ok else NO_GO_STATUS,
            "mode": "waiting",
            "fixtures_dir": normalize_path(fixtures_dir),
            "runtime_dir": normalize_path(runtime_dir),
            "active_cases_count": 0,
            "active_cases": [],
            "checks": checks,
            "errors": [str(item.get("evidence", "")) for item in checks if item.get("blocking") is not False and not item.get("ok")],
        }

    validation, validations = validation_check(active_cases)
    checks.append(validation)
    anonymization, audit = anonymization_check(fixtures_dir)
    checks.append(anonymization)
    checks.append(ingestion_check(runtime_dir, len(active_cases)))
    runtime, summary = runtime_check(runtime_dir, len(active_cases))
    checks.append(runtime)
    checks.append(internal_review_check(runtime_dir, summary))
    checks.append(evaluator_package_check(runtime_dir, package_index, summary))
    checks.append(response_stop_check(response_input, package_index))

    ok = report_ok(checks)
    return {
        "schema_version": "phase_h_campagne_terrain_gate_v1",
        "ok": ok,
        "decision": READY_STATUS if ok else NO_GO_STATUS,
        "mode": "active",
        "fixtures_dir": normalize_path(fixtures_dir),
        "runtime_dir": normalize_path(runtime_dir),
        "active_cases_count": len(active_cases),
        "active_cases": [normalize_path(path) for path in active_cases],
        "validated_dossiers": [validation.dossier_id for validation in validations],
        "anonymization_status": audit.get("status", "UNKNOWN"),
        "checks": checks,
        "errors": [str(item.get("evidence", "")) for item in checks if item.get("blocking") is not False and not item.get("ok")],
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Gate campagne terrain reelle Phase H V1",
        "",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- OK: **{str(report.get('ok')).lower()}**",
        f"- Mode: **{report.get('mode', 'UNKNOWN')}**",
        f"- Dossiers terrain actifs: **{report.get('active_cases_count', 0)}**",
        f"- Repertoire entrees: `{report.get('fixtures_dir', '-')}`",
        f"- Repertoire runtime: `{report.get('runtime_dir', '-')}`",
        "",
        "## Checks",
        "",
        "| Check | Statut | OK | Preuve |",
        "|---|---|---|---|",
    ]
    for item in report.get("checks", []):
        if isinstance(item, dict):
            lines.append(
                "| {name} | {status} | {ok} | {evidence} |".format(
                    name=item.get("name", "-"),
                    status=item.get("status", "UNKNOWN"),
                    ok=str(item.get("ok")).lower(),
                    evidence=str(item.get("evidence", "-")).replace("\n", " "),
                )
            )

    lines.extend(["", "## Regles", ""])
    if report.get("mode") == "waiting":
        lines.extend(
            [
                "- La Phase H reelle reste en attente de dossiers terrain anonymises.",
                "- Aucun resultat evaluateur ne doit etre simule pour faire avancer cette gate.",
                "- L'arrivee d'un `case_pilote_reel_*.json` active les controles stricts avant runtime et avant paquet evaluateurs.",
            ]
        )
    else:
        lines.extend(
            [
                "- Tous les dossiers actifs doivent passer validation stricte et audit anonymisation.",
                "- Le runtime ne doit exploiter que des entrees terrain validees.",
                "- Le paquet evaluateurs doit rester au point d'arret tant que les reponses ne sont pas recues.",
            ]
        )
    errors = report.get("errors", [])
    if errors:
        lines.extend(["", "## Erreurs bloquantes", ""])
        for error in errors if isinstance(errors, list) else []:
            lines.append(f"- {error}")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    write_json(json_out, report)
    write_text(markdown_out, build_markdown(report))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie le gate Phase H campagne terrain reelle.")
    parser.add_argument("--fixtures-dir", type=Path, default=FIXTURES_DIR_DEFAULT)
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--package-index", type=Path, default=PACKAGE_INDEX_DEFAULT)
    parser.add_argument("--response-input", type=Path, default=RESPONSES_INPUT_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=REPORT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD_DEFAULT)
    parser.add_argument(
        "--require-active",
        action="store_true",
        help="Retourne exit code 2 si aucun dossier terrain actif n'est disponible.",
    )
    args = parser.parse_args()

    report = build_phase_h_gate_report(
        fixtures_dir=args.fixtures_dir,
        runtime_dir=args.runtime_dir,
        package_index=args.package_index,
        response_input=args.response_input,
    )
    write_outputs(report, args.report_out, args.markdown_out)

    print(f"Gate Phase H JSON: {args.report_out}")
    print(f"Gate Phase H Markdown: {args.markdown_out}")
    print(f"Decision: {report['decision']}")
    if args.require_active and report.get("active_cases_count") == 0:
        return 2
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
