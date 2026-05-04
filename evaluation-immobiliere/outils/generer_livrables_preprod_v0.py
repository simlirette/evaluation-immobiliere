#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OPS_DOCTOR_DEFAULT = RUNTIME_DIR_DEFAULT / "ops_doctor_report.json"
HANDOFF_DEFAULT = RUNTIME_DIR_DEFAULT / "ops_handoff_manifest.json"
READINESS_DEFAULT = RUNTIME_DIR_DEFAULT / "readiness_pre_reponses.json"
SLO_DEFAULT = ATELIER_DIR_DEFAULT / "SLO-SLA-V1.md"
ACCEPTANCE_DEFAULT = ATELIER_DIR_DEFAULT / "CRITERES-ACCEPTATION-METIER-V1.md"
CD_DEFAULT = ATELIER_DIR_DEFAULT / "PIPELINE-CD-V1.md"
ROLLBACK_DEFAULT = ATELIER_DIR_DEFAULT / "RUNBOOK-ROLLBACK-V1.md"
DRESS_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "RAPPORT-DRESS-REHEARSAL-V1.md"
PV_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "PV-HOMOLOGATION-V1.md"
REGISTER_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "REGISTRE-ECARTS-PREPROD-V1.md"


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def contains_blocking_phase_h(acceptance_text: str) -> bool:
    return "EN_ATTENTE_REPONSES_TERRAIN" in acceptance_text or "Signature metier | A_SIGNER" in acceptance_text


def contains_open_slo(slo_text: str) -> bool:
    return "INSTRUMENTATION_REQUISE" in slo_text or "A_TRAITER" in slo_text


def build_preprod_context(
    ops_doctor: dict[str, object],
    handoff: dict[str, object],
    readiness: dict[str, object],
    acceptance_text: str,
    slo_text: str,
    cd_text: str,
    rollback_text: str,
) -> dict[str, object]:
    phase_h_blocking = contains_blocking_phase_h(acceptance_text)
    open_slo = contains_open_slo(slo_text)
    ops_ok = ops_doctor.get("status") == "OK"
    handoff_ok = handoff.get("status") == "PRET_A_TRANSMETTRE"
    prod_blocked_by_cd = "production reste bloquee" in cd_text
    rollback_ready = "RUNBOOK ROLLBACK V1" in rollback_text
    readiness_status = str(readiness.get("status") or "UNKNOWN")

    if phase_h_blocking:
        decision = "NO_GO_PROD_PREPARATION"
    elif ops_ok and handoff_ok and rollback_ready and not open_slo:
        decision = "GO_PREPROD"
    else:
        decision = "GO_CONDITIONNEL_PREPROD"

    return {
        "decision": decision,
        "ops_ok": ops_ok,
        "handoff_ok": handoff_ok,
        "readiness_status": readiness_status,
        "phase_h_blocking": phase_h_blocking,
        "open_slo": open_slo,
        "prod_blocked_by_cd": prod_blocked_by_cd,
        "rollback_ready": rollback_ready,
        "ops_status": ops_doctor.get("status", "UNKNOWN"),
        "handoff_status": handoff.get("status", "UNKNOWN"),
        "required_handoff_present": handoff.get("required_present", 0),
        "required_handoff_count": handoff.get("required_count", 0),
        "review_queue_items": (ops_doctor.get("summary", {}) if isinstance(ops_doctor.get("summary"), dict) else {}).get("review_queue_items", 0),
        "risks_to_calibrate": readiness.get("risks_to_calibrate", {}) if isinstance(readiness.get("risks_to_calibrate"), dict) else {},
    }


def build_preprod_gaps(context: dict[str, object]) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    if context.get("phase_h_blocking"):
        gaps.append(
            {
                "id": "PREPROD-J-001",
                "severity": "P0",
                "domain": "metier",
                "status": "ouvert",
                "owner": "Lead Metier + Product",
                "gap": "Phase H sans retours terrain signes.",
                "mitigation": "Collecter calibration evaluateurs et signer criteres acceptation metier.",
                "blocks_prod": "oui",
            }
        )
    if context.get("open_slo"):
        gaps.append(
            {
                "id": "PREPROD-J-002",
                "severity": "P1",
                "domain": "performance",
                "status": "ouvert",
                "owner": "Platform",
                "gap": "SLO Phase G encore ouverts: wall-clock non instrumente et seuils a traiter.",
                "mitigation": "Executer run non deterministe avec p95 par dossier/etape et rebaseliner SLO.",
                "blocks_prod": "oui",
            }
        )
    if not context.get("ops_ok"):
        gaps.append(
            {
                "id": "PREPROD-J-003",
                "severity": "P0",
                "domain": "ops",
                "status": "ouvert",
                "owner": "QA/Platform",
                "gap": f"Ops doctor non OK: {context.get('ops_status', 'UNKNOWN')}.",
                "mitigation": "Corriger gates ops et relancer ops doctor avant homologation.",
                "blocks_prod": "oui",
            }
        )
    if not context.get("handoff_ok"):
        gaps.append(
            {
                "id": "PREPROD-J-004",
                "severity": "P0",
                "domain": "handoff",
                "status": "ouvert",
                "owner": "Platform",
                "gap": f"Handoff ops non pret: {context.get('handoff_status', 'UNKNOWN')}.",
                "mitigation": "Regenerer le manifeste handoff et fournir tous les fichiers requis.",
                "blocks_prod": "oui",
            }
        )
    if not context.get("rollback_ready"):
        gaps.append(
            {
                "id": "PREPROD-J-005",
                "severity": "P1",
                "domain": "release",
                "status": "ouvert",
                "owner": "Platform",
                "gap": "Runbook rollback absent ou incomplet.",
                "mitigation": "Versionner runbook rollback et lier a la promotion staging.",
                "blocks_prod": "oui",
            }
        )
    if not gaps:
        gaps.append(
            {
                "id": "PREPROD-J-000",
                "severity": "INFO",
                "domain": "preprod",
                "status": "ferme",
                "owner": "Platform",
                "gap": "Aucun ecart preprod bloquant detecte par la consolidation automatique.",
                "mitigation": "Conserver preuves et proceder a homologation manuelle.",
                "blocks_prod": "non",
            }
        )
    return gaps


def build_dress_rehearsal_markdown(context: dict[str, object], gaps: list[dict[str, str]]) -> str:
    risks = context.get("risks_to_calibrate", {}) if isinstance(context.get("risks_to_calibrate"), dict) else {}
    lines = [
        "# RAPPORT DRESS REHEARSAL V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Simuler le passage pre-production avec les preuves disponibles, les incidents attendus et les gates bloquants.",
        "",
        "## Synthese",
        "",
        "| Indicateur | Valeur |",
        "|---|---:|",
        f"| Decision Phase J | {context.get('decision', 'UNKNOWN')} |",
        f"| Ops doctor | {context.get('ops_status', 'UNKNOWN')} |",
        f"| Handoff ops | {context.get('handoff_status', 'UNKNOWN')} |",
        f"| Fichiers handoff requis | {context.get('required_handoff_present', 0)}/{context.get('required_handoff_count', 0)} |",
        f"| Readiness | {context.get('readiness_status', 'UNKNOWN')} |",
        f"| Items revue humaine | {context.get('review_queue_items', 0)} |",
        f"| Ecarts preprod ouverts | {sum(1 for gap in gaps if gap.get('status') == 'ouvert')} |",
        "",
        "## Scenarios executes / simules",
        "",
        "| Scenario | Statut | Preuve |",
        "|---|---|---|",
        f"| Handoff operationnel | {'OK' if context.get('handoff_ok') else 'A_TRAITER'} | `ops_handoff_manifest.json` |",
        f"| Gates ops professionnels | {'OK' if context.get('ops_ok') else 'A_TRAITER'} | `ops_doctor_report.json` |",
        "| Promotion staging | PREPAREE | `PIPELINE-CD-V1.md` |",
        "| Rollback release | PREPARE | `RUNBOOK-ROLLBACK-V1.md` |",
        "| Gate metier terrain | BLOQUE | `CRITERES-ACCEPTATION-METIER-V1.md` |",
        "",
        "## Risques runtime a calibrer",
        "",
        f"- Blocages runtime: {risks.get('runtime_blocking_failures', 0)}",
        f"- Warnings runtime: {risks.get('runtime_warnings', 0)}",
        f"- Erreurs contrat: {risks.get('contract_errors', 0)}",
        f"- Artefacts manquants: {risks.get('missing_artifacts', 0)}",
        f"- Questions runtime ouvertes: {risks.get('open_runtime_questions', 0)}",
        "",
        "## Decision",
        "",
        f"Decision: **{context.get('decision', 'UNKNOWN')}**.",
        "",
        "La pre-production peut etre preparee et repetee, mais la production demeure bloquee tant que les ecarts P0/P1 ci-dessous ne sont pas fermes.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_pv_markdown(context: dict[str, object], gaps: list[dict[str, str]]) -> str:
    p0_open = sum(1 for gap in gaps if gap.get("severity") == "P0" and gap.get("status") == "ouvert")
    p1_open = sum(1 for gap in gaps if gap.get("severity") == "P1" and gap.get("status") == "ouvert")
    lines = [
        "# PV HOMOLOGATION V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objet",
        "Proces-verbal preparatoire d'homologation pre-production multi-parties.",
        "",
        "## Decision",
        "",
        f"- Decision Phase J: **{context.get('decision', 'UNKNOWN')}**",
        f"- P0 ouverts: **{p0_open}**",
        f"- P1 ouverts: **{p1_open}**",
        "- Go production: **NON**",
        "",
        "## Conditions avant Go production",
        "",
        "- Phase H signee par Lead Metier + Product.",
        "- SLO Phase G sans instrumentation manquante.",
        "- Dress rehearsal staging rejoue avec CI/CD et rollback.",
        "- Tous les ecarts P0 fermes, P1 acceptes formellement ou fermes.",
        "",
        "## Signatures",
        "",
        "| Role | Owner | Statut | Commentaire |",
        "|---|---|---|---|",
        "| Lead Metier | A nommer | A_SIGNER | Bloque par retours terrain |",
        "| Product | A nommer | A_SIGNER | Bloque par retours terrain |",
        "| Platform | A nommer | A_SIGNER | Preprod preparable |",
        "| QA/Securite | A nommer | A_SIGNER | Revue finale requise |",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_register_markdown(gaps: list[dict[str, str]]) -> str:
    lines = [
        "# REGISTRE ECARTS PREPROD V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "| ID | Severite | Domaine | Statut | Bloque prod | Owner | Ecart | Mitigation |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for gap in gaps:
        lines.append(
            "| {id} | {severity} | {domain} | {status} | {blocks_prod} | {owner} | {gap} | {mitigation} |".format(
                id=gap.get("id", "-"),
                severity=gap.get("severity", "-"),
                domain=gap.get("domain", "-"),
                status=gap.get("status", "-"),
                blocks_prod=gap.get("blocks_prod", "-"),
                owner=gap.get("owner", "-"),
                gap=gap.get("gap", "-"),
                mitigation=gap.get("mitigation", "-"),
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_phase_j_deliverables(
    *,
    ops_doctor_path: Path = OPS_DOCTOR_DEFAULT,
    handoff_path: Path = HANDOFF_DEFAULT,
    readiness_path: Path = READINESS_DEFAULT,
    slo_path: Path = SLO_DEFAULT,
    acceptance_path: Path = ACCEPTANCE_DEFAULT,
    cd_path: Path = CD_DEFAULT,
    rollback_path: Path = ROLLBACK_DEFAULT,
    dress_out: Path = DRESS_OUT_DEFAULT,
    pv_out: Path = PV_OUT_DEFAULT,
    register_out: Path = REGISTER_OUT_DEFAULT,
) -> dict[str, object]:
    context = build_preprod_context(
        load_json(ops_doctor_path),
        load_json(handoff_path),
        load_json(readiness_path),
        read_text(acceptance_path),
        read_text(slo_path),
        read_text(cd_path),
        read_text(rollback_path),
    )
    gaps = build_preprod_gaps(context)
    write_text(dress_out, build_dress_rehearsal_markdown(context, gaps))
    write_text(pv_out, build_pv_markdown(context, gaps))
    write_text(register_out, build_register_markdown(gaps))
    return {
        "decision": context["decision"],
        "gaps_count": len([gap for gap in gaps if gap.get("status") == "ouvert"]),
        "dress_out": dress_out.as_posix(),
        "pv_out": pv_out.as_posix(),
        "register_out": register_out.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere les livrables Phase J pre-production et homologation.")
    parser.add_argument("--ops-doctor", type=Path, default=OPS_DOCTOR_DEFAULT)
    parser.add_argument("--handoff", type=Path, default=HANDOFF_DEFAULT)
    parser.add_argument("--readiness", type=Path, default=READINESS_DEFAULT)
    parser.add_argument("--slo", type=Path, default=SLO_DEFAULT)
    parser.add_argument("--acceptance", type=Path, default=ACCEPTANCE_DEFAULT)
    parser.add_argument("--cd", type=Path, default=CD_DEFAULT)
    parser.add_argument("--rollback", type=Path, default=ROLLBACK_DEFAULT)
    parser.add_argument("--dress-out", type=Path, default=DRESS_OUT_DEFAULT)
    parser.add_argument("--pv-out", type=Path, default=PV_OUT_DEFAULT)
    parser.add_argument("--register-out", type=Path, default=REGISTER_OUT_DEFAULT)
    args = parser.parse_args()

    outputs = generate_phase_j_deliverables(
        ops_doctor_path=args.ops_doctor,
        handoff_path=args.handoff,
        readiness_path=args.readiness,
        slo_path=args.slo,
        acceptance_path=args.acceptance,
        cd_path=args.cd,
        rollback_path=args.rollback,
        dress_out=args.dress_out,
        pv_out=args.pv_out,
        register_out=args.register_out,
    )
    print(f"Rapport dress rehearsal: {outputs['dress_out']}")
    print(f"PV homologation: {outputs['pv_out']}")
    print(f"Registre ecarts preprod: {outputs['register_out']}")
    print(f"Decision: {outputs['decision']}")
    print(f"Ecarts ouverts: {outputs['gaps_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
