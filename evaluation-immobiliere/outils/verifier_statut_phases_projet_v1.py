#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
OUTILS_DIR = Path(__file__).resolve().parent
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from valider_reponses_evaluateurs import validate_file  # noqa: E402
from verifier_campagne_terrain_reelle_v1 import (  # noqa: E402
    NO_GO_STATUS as PHASE_H_NO_GO,
)
from verifier_campagne_terrain_reelle_v1 import (
    READY_STATUS as PHASE_H_READY_FOR_RESPONSES,
)
from verifier_campagne_terrain_reelle_v1 import (
    WAITING_STATUS as PHASE_H_WAITING_INPUTS,
)
from verifier_campagne_terrain_reelle_v1 import build_phase_h_gate_report

ATELIER_DIR = PROJECT_ROOT / "atelier"
RUNTIME_DIR = PROJECT_ROOT / "tests" / "runtime"
FIXTURES_EXTERNAL_DIR = PROJECT_ROOT / "tests" / "fixtures_external"
RUNTIME_REELS_DIR = PROJECT_ROOT / "runtime_pilotes_reels"

WORKFLOW_DEFAULT = REPO_ROOT / ".github" / "workflows" / "validation.yml"
RESPONSE_INPUT_DEFAULT = ATELIER_DIR / "REPONSES-EVALUATEURS.csv"
CALIBRATION_INPUT_DEFAULT = ATELIER_DIR / "CALIBRATION-EVALUATEURS.csv"
REPORT_JSON_DEFAULT = ATELIER_DIR / "STATUT-PHASES-PROJET-V1.json"
REPORT_MD_DEFAULT = ATELIER_DIR / "STATUT-PHASES-PROJET-V1.md"
PRE_EVALUATOR_TARGET = "V1_PRE_EVALUATEUR"
PRE_EVALUATOR_DECISION = "PRET_FINALISATION_V1_PRE_EVALUATEUR"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def normalize_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def bool_status(value: bool, ok: str = "OK", ko: str = "A_TRAITER") -> str:
    return ok if value else ko


def csv_active_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return sum(1 for row in csv.DictReader(handle) if any(str(value or "").strip() for value in row.values()))


def count_open_preprod_gaps(register_text: str) -> tuple[int, int, int]:
    total = p0 = p1 = 0
    for line in register_text.splitlines():
        if "| PREPROD-" not in line or "| ouvert |" not in line:
            continue
        total += 1
        if "| P0 |" in line:
            p0 += 1
        if "| P1 |" in line:
            p1 += 1
    return total, p0, p1


def check(name: str, ok: bool, status: str, evidence: str) -> dict[str, Any]:
    return {
        "name": name,
        "ok": ok,
        "status": status,
        "evidence": evidence,
    }


def phase(code: str, name: str, status: str, decision: str, evidence: str, *, blocking: bool) -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "status": status,
        "decision": decision,
        "blocking": blocking,
        "evidence": evidence,
    }


def workflow_has_required_phase_gates(workflow_text: str) -> bool:
    required = [
        "verifier_campagne_terrain_reelle_v1.py",
        "verifier_statut_phases_projet_v1.py",
        "verifier_release_candidate_v1.py",
        "python -m unittest discover",
    ]
    return all(item in workflow_text for item in required)


def build_project_status_report(
    *,
    workflow_path: Path = WORKFLOW_DEFAULT,
    response_input: Path = RESPONSE_INPUT_DEFAULT,
    calibration_input: Path = CALIBRATION_INPUT_DEFAULT,
    report_phase_h: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow_text = read_text(workflow_path)
    cd_text = read_text(ATELIER_DIR / "PIPELINE-CD-V1.md")
    pv_text = read_text(ATELIER_DIR / "PV-HOMOLOGATION-V1.md")
    slo_text = read_text(ATELIER_DIR / "SLO-SLA-V1.md")
    dress_text = read_text(ATELIER_DIR / "RAPPORT-DRESS-REHEARSAL-V1.md")
    register_text = read_text(ATELIER_DIR / "REGISTRE-ECARTS-PREPROD-V1.md")
    canary_text = read_text(ATELIER_DIR / "PLAN-DEPLOIEMENT-CANARY-V1.md")
    hypercare_text = read_text(ATELIER_DIR / "PLAN-HYPERCARE-V1.md")

    phase_h_report = report_phase_h or build_phase_h_gate_report(
        fixtures_dir=FIXTURES_EXTERNAL_DIR,
        runtime_dir=RUNTIME_REELS_DIR,
        response_input=response_input,
    )
    phase_h_decision = str(phase_h_report.get("decision") or "UNKNOWN")
    active_real_cases = int(phase_h_report.get("active_cases_count", 0) or 0)

    response_result = validate_file(response_input) if response_input.exists() else None
    response_active_rows = response_result.active_rows if response_result else 0
    response_errors = len(response_result.errors) if response_result else 0
    calibration_active_rows = csv_active_rows(calibration_input)

    rc_report = read_json_dict(RUNTIME_DIR / "release_candidate_report.json")
    homologation_report = read_json_dict(RUNTIME_DIR / "homologation_metier_report.json")
    external_report = read_json_dict(RUNTIME_DIR / "revues_evaluateurs_externes_report.json")
    closure_report = read_json_dict(RUNTIME_DIR / "fermeture_ecarts_evaluateurs_report.json")
    open_preprod_gaps, open_p0, open_p1 = count_open_preprod_gaps(register_text)
    open_slo = "INSTRUMENTATION_REQUISE" in slo_text or "A_TRAITER" in slo_text
    prod_blocked = (
        "production reste bloquee" in cd_text
        and "NO_GO_PROD_PREPARATION" in dress_text
        and "DEPLOIEMENT_PROD_BLOQUE" in canary_text
        and "Production active: **non**" in hypercare_text
    )
    pv_real_scope_ok = "Go production reelle: **NON**" in pv_text or "Go production: **NON**" in pv_text
    no_active_responses_before_stop = response_active_rows == 0 and calibration_active_rows == 0 and response_errors == 0
    pre_evaluator_plan_exists = (ATELIER_DIR / "PLAN-V1-PRE-EVALUATEUR-AGREE.md").exists()

    checks = [
        check(
            "phase_h_gate",
            phase_h_decision != PHASE_H_NO_GO,
            phase_h_decision,
            f"{active_real_cases} dossier(s) terrain actif(s)",
        ),
        check(
            "aucune_reponse_inventee",
            no_active_responses_before_stop,
            bool_status(no_active_responses_before_stop, "AUCUNE_REPONSE_ACTIVE", "REPONSES_PRESENTES_OU_INVALIDES"),
            f"reponses={response_active_rows}; calibration={calibration_active_rows}; erreurs_reponses={response_errors}",
        ),
        check(
            "ci_couvre_phase_h_et_statut_projet",
            workflow_has_required_phase_gates(workflow_text),
            bool_status(workflow_has_required_phase_gates(workflow_text), "COUVERT", "INCOMPLET"),
            normalize_path(workflow_path),
        ),
        check(
            "production_bloquee_avant_phase_h_reelle",
            prod_blocked,
            bool_status(prod_blocked, "BLOQUEE", "A_DURCIR"),
            "Phase J/K/L et CD declarent le blocage production.",
        ),
        check(
            "pv_homologation_scope_reel",
            pv_real_scope_ok,
            bool_status(pv_real_scope_ok, "PORTEE_REELLE_EXPLICITE", "AMBIGU"),
            normalize_path(ATELIER_DIR / "PV-HOMOLOGATION-V1.md"),
        ),
        check(
            "phase_h_non_bloquante_pour_v1_pre_evaluateur",
            phase_h_decision in {PHASE_H_WAITING_INPUTS, PHASE_H_READY_FOR_RESPONSES},
            "PHASE_H_POST_V1" if phase_h_decision in {PHASE_H_WAITING_INPUTS, PHASE_H_READY_FOR_RESPONSES} else "A_CONTROLER",
            "La Phase H bloque seulement la validation terrain/prod reelle, pas la finalisation produit pre-evaluateur.",
        ),
        check(
            "plan_v1_pre_evaluateur",
            pre_evaluator_plan_exists,
            "PRESENT" if pre_evaluator_plan_exists else "ABSENT",
            normalize_path(ATELIER_DIR / "PLAN-V1-PRE-EVALUATEUR-AGREE.md"),
        ),
    ]

    phases = [
        phase("A", "Cadrage", "TERMINE", "BASELINE_DOCUMENTEE", "PLAN-DIRECTEUR-COMPLET-V1.md", blocking=False),
        phase("B", "Contrats Aston", "TERMINE", "CONTRATS_DOCUMENTES", "CONTRATS-INTEGRATION-ASTON-V1.yaml", blocking=False),
        phase("C", "Runtime v0", "TERMINE", "RUNTIME_EN_CI", "tests/runtime/runtime_summary.json", blocking=False),
        phase("D", "API persistence", "PREPARE", "CONTRATS_API_DOCUMENTES", "API-RUNTIME-V0.md", blocking=False),
        phase("E", "UI evaluateur", "PREPARE", "SPEC_UI_DOCUMENTEE", "SPEC-UI-EVALUATEUR-V1.md", blocking=False),
        phase("F", "Securite gouvernance", "PREPARE", "BASELINE_DOCUMENTEE", "SECURITY-BASELINE-V1.md", blocking=False),
        phase("G", "Perf fiabilite cout", "GO_CONDITIONNEL", "SLO_A_FERMER" if open_slo else "SLO_PRETS", "SLO-SLA-V1.md", blocking=open_slo),
        phase("H", "Campagne terrain reelle", phase_h_decision, phase_h_decision, "verifier_campagne_terrain_reelle_v1.py", blocking=phase_h_decision != PHASE_H_READY_FOR_RESPONSES),
        phase("I", "CI/CD", "PRET_STAGING", "GO_PREPARATION_STAGING", normalize_path(workflow_path), blocking=False),
        phase("J", "Preproduction", "PROD_BLOQUEE", "NO_GO_PROD_PREPARATION" if open_preprod_gaps else "GO_PREPROD", "RAPPORT-DRESS-REHEARSAL-V1.md", blocking=open_preprod_gaps > 0),
        phase("K", "Canary", "PROD_BLOQUEE", "DEPLOIEMENT_PROD_BLOQUE" if "DEPLOIEMENT_PROD_BLOQUE" in canary_text else "A_CONTROLER", "PLAN-DEPLOIEMENT-CANARY-V1.md", blocking=True),
        phase("L", "Hypercare", "PREPARE_PROD_BLOQUEE", "HYPERCARE_PREPARE_PROD_BLOQUEE" if "HYPERCARE_PREPARE_PROD_BLOQUEE" in hypercare_text else "A_CONTROLER", "PLAN-HYPERCARE-V1.md", blocking=True),
    ]

    ok = all(item["ok"] for item in checks)
    return {
        "schema_version": "statut_phases_projet_v1",
        "ok": ok,
        "decision": "PROJET_PRET_FINALISATION_V1_PRE_EVALUATEUR_PROD_BLOQUEE" if ok else "STATUT_PHASES_A_CORRIGER",
        "target": PRE_EVALUATOR_TARGET,
        "pre_evaluator_decision": PRE_EVALUATOR_DECISION if ok else "A_CORRIGER",
        "phase_h_decision": phase_h_decision,
        "active_real_cases": active_real_cases,
        "response_active_rows": response_active_rows,
        "calibration_active_rows": calibration_active_rows,
        "release_candidate_decision": rc_report.get("decision", "UNKNOWN"),
        "homologation_synthetic_decision": homologation_report.get("production_decision", "UNKNOWN"),
        "external_reviews_decision": external_report.get("decision", "UNKNOWN"),
        "closure_decision": closure_report.get("decision", "UNKNOWN"),
        "open_preprod_gaps": open_preprod_gaps,
        "open_preprod_p0": open_p0,
        "open_preprod_p1": open_p1,
        "open_slo": open_slo,
        "checks": checks,
        "phases": phases,
        "errors": [item["name"] for item in checks if not item["ok"]],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Statut phases projet V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Synthese",
        "",
        f"- Decision: **{report.get('decision', 'UNKNOWN')}**",
        f"- Cible produit: **{report.get('target', 'UNKNOWN')}**",
        f"- Decision pre-evaluateur: **{report.get('pre_evaluator_decision', 'UNKNOWN')}**",
        f"- OK coherence: **{str(report.get('ok')).lower()}**",
        f"- Phase H reelle: **{report.get('phase_h_decision', 'UNKNOWN')}**",
        f"- Dossiers terrain actifs: **{report.get('active_real_cases', 0)}**",
        f"- Reponses evaluateurs actives: **{report.get('response_active_rows', 0)}**",
        f"- Calibration evaluateurs active: **{report.get('calibration_active_rows', 0)}**",
        f"- Release candidate: **{report.get('release_candidate_decision', 'UNKNOWN')}**",
        f"- Ecarts preprod ouverts: **{report.get('open_preprod_gaps', 0)}**",
        "",
        "## Phases",
        "",
        "| Phase | Nom | Statut | Decision | Bloquant prod | Evidence |",
        "|---|---|---|---|---|---|",
    ]
    for item in report.get("phases", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            "| {code} | {name} | {status} | {decision} | {blocking} | `{evidence}` |".format(
                code=item.get("code", "-"),
                name=item.get("name", "-"),
                status=item.get("status", "UNKNOWN"),
                decision=item.get("decision", "UNKNOWN"),
                blocking="oui" if item.get("blocking") else "non",
                evidence=item.get("evidence", "-"),
            )
        )

    lines.extend(["", "## Gates coherence", "", "| Gate | Statut | OK | Evidence |", "|---|---|---|---|"])
    for item in report.get("checks", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            "| {name} | {status} | {ok} | {evidence} |".format(
                name=item.get("name", "-"),
                status=item.get("status", "UNKNOWN"),
                ok=str(item.get("ok")).lower(),
                evidence=str(item.get("evidence", "-")).replace("\n", " "),
            )
        )

    lines.extend(
        [
            "",
            "## Situation dossiers/reponses",
            "",
            "- Aucun dossier reel anonymise actif n'est versionne dans le repo.",
            "- Aucune reponse evaluateur active n'est presente dans les CSV de collecte.",
            "- Les revues evaluateurs externes versionnees restent des fixtures d'homologation/preparation, pas des retours de campagne terrain reelle.",
            "- La prochaine action produit est la finalisation V1 pre-evaluateur: demo, UI/API, rapport exemple et paquet de revue.",
            "- La prochaine action non simulable, apres V1, est la reception de dossiers anonymises valides hors repo actif, puis l'envoi du paquet evaluateurs.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, Any], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie le statut global des phases A-L sans simuler la Phase H reelle.")
    parser.add_argument("--workflow", type=Path, default=WORKFLOW_DEFAULT)
    parser.add_argument("--response-input", type=Path, default=RESPONSE_INPUT_DEFAULT)
    parser.add_argument("--calibration-input", type=Path, default=CALIBRATION_INPUT_DEFAULT)
    parser.add_argument("--report-out", type=Path, default=REPORT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=REPORT_MD_DEFAULT)
    args = parser.parse_args()

    report = build_project_status_report(
        workflow_path=args.workflow,
        response_input=args.response_input,
        calibration_input=args.calibration_input,
    )
    write_outputs(report, args.report_out, args.markdown_out)
    print(f"Statut phases JSON: {args.report_out}")
    print(f"Statut phases Markdown: {args.markdown_out}")
    print(f"Decision: {report['decision']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
