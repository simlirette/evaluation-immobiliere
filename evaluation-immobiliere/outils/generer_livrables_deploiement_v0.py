#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OPS_DOCTOR_DEFAULT = RUNTIME_DIR_DEFAULT / "ops_doctor_report.json"
PV_HOMOLOGATION_DEFAULT = ATELIER_DIR_DEFAULT / "PV-HOMOLOGATION-V1.md"
PREPROD_REGISTER_DEFAULT = ATELIER_DIR_DEFAULT / "REGISTRE-ECARTS-PREPROD-V1.md"
ROLLBACK_DEFAULT = ATELIER_DIR_DEFAULT / "RUNBOOK-ROLLBACK-V1.md"
OPS_RUNBOOK_DEFAULT = ATELIER_DIR_DEFAULT / "RUNBOOK-OPERATIONS-PRE-REPONSES.md"
CANARY_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "PLAN-DEPLOIEMENT-CANARY-V1.md"
DASHBOARD_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "TABLEAU-BORD-PROD-V1.md"
STABILIZATION_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "RAPPORT-STABILISATION-J7.md"


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def count_open_preprod_gaps(register_text: str) -> tuple[int, int, int]:
    p0 = p1 = total = 0
    for line in register_text.splitlines():
        if "| PREPROD-" not in line or "| ouvert |" not in line:
            continue
        total += 1
        if "| P0 |" in line:
            p0 += 1
        if "| P1 |" in line:
            p1 += 1
    return total, p0, p1


def build_deployment_context(
    ops_doctor: dict[str, object],
    pv_text: str,
    register_text: str,
    rollback_text: str,
    ops_runbook_text: str,
) -> dict[str, object]:
    open_gaps, p0_open, p1_open = count_open_preprod_gaps(register_text)
    ops_ok = ops_doctor.get("status") == "OK"
    prod_no_go = "Go production: **NON**" in pv_text or "NO_GO_PROD_PREPARATION" in pv_text
    rollback_ready = "RUNBOOK ROLLBACK V1" in rollback_text
    ops_runbook_ready = "Ops doctor" in ops_runbook_text or "OPS-DOCTOR-V0" in ops_runbook_text

    if prod_no_go or p0_open > 0:
        decision = "DEPLOIEMENT_PROD_BLOQUE"
    elif not ops_ok or not rollback_ready or not ops_runbook_ready:
        decision = "CANARY_A_COMPLETER"
    else:
        decision = "CANARY_PRET_A_PLANIFIER"

    summary = ops_doctor.get("summary", {}) if isinstance(ops_doctor.get("summary"), dict) else {}
    return {
        "decision": decision,
        "ops_ok": ops_ok,
        "ops_status": ops_doctor.get("status", "UNKNOWN"),
        "prod_no_go": prod_no_go,
        "rollback_ready": rollback_ready,
        "ops_runbook_ready": ops_runbook_ready,
        "open_preprod_gaps": open_gaps,
        "p0_open": p0_open,
        "p1_open": p1_open,
        "review_queue_items": summary.get("review_queue_items", 0),
        "delta_status": summary.get("delta_status", "UNKNOWN"),
        "handoff_status": summary.get("handoff_status", "UNKNOWN"),
        "schema_validation_status": summary.get("schema_validation_status", "UNKNOWN"),
        "package_gate_status": summary.get("package_gate_status", "UNKNOWN"),
    }


def build_canary_markdown(context: dict[str, object]) -> str:
    lines = [
        "# PLAN DEPLOIEMENT CANARY V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Preparer un deploiement progressif et reversible sans executer la production tant que les gates metier et preprod restent ouverts.",
        "",
        "## Decision",
        "",
        f"- Statut Phase K: **{context.get('decision', 'UNKNOWN')}**",
        f"- Ops doctor: **{context.get('ops_status', 'UNKNOWN')}**",
        f"- Ecarts preprod ouverts: **{context.get('open_preprod_gaps', 0)}**",
        f"- P0 ouverts: **{context.get('p0_open', 0)}**",
        f"- P1 ouverts: **{context.get('p1_open', 0)}**",
        "",
        "## Gates d'ouverture canary",
        "",
        "| Gate | Cible | Statut courant | Bloque canary prod |",
        "|---|---|---|---|",
        f"| Homologation production | Go production signe | {'NON' if context.get('prod_no_go') else 'OK'} | oui |",
        f"| Ops doctor | OK | {context.get('ops_status', 'UNKNOWN')} | oui |",
        f"| Rollback | Runbook relu/teste | {'PRET' if context.get('rollback_ready') else 'A_COMPLETER'} | oui |",
        f"| Runbook operations | Disponible | {'PRET' if context.get('ops_runbook_ready') else 'A_COMPLETER'} | oui |",
        "| Perimetre canary | Equipe/dossiers limites designes | A_DESIGNER | oui |",
        "",
        "## Perimetre canary propose",
        "",
        "| Vague | Perimetre | Duree observation | Critere extension | Statut |",
        "|---|---|---|---|---|",
        "| K0 | Aucun trafic prod | Jusqu'a fermeture P0 | P0=0 et Go metier signe | Bloque |",
        "| K1 | 1 evaluateur interne, dossiers non clients | 1 jour ouvre | 0 incident P0/P1 | Prepare |",
        "| K2 | 1 bureau pilote, dossiers anonymises controles | 7 jours | SLO tenus + avis metier OK | Prepare |",
        "| K3 | Extension progressive | 30 jours | Stabilite J+7/J+30 | A planifier |",
        "",
        "## Rollback instantane",
        "",
        "- Declencher rollback si incident securite, donnees, contrat, qualite metier ou indisponibilite majeure.",
        "- Revenir au tag sain precedent et reexecuter CI + ops doctor.",
        "- Suspendre toute extension de perimetre tant que le post-mortem n'est pas clos.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_dashboard_markdown(context: dict[str, object]) -> str:
    lines = [
        "# TABLEAU BORD PROD V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Definir les indicateurs a surveiller pendant canary, J+7 et J+30.",
        "",
        f"Statut courant: **{context.get('decision', 'UNKNOWN')}**.",
        "",
        "## Indicateurs critiques",
        "",
        "| Domaine | Indicateur | Source | Seuil alerte | Statut actuel |",
        "|---|---|---|---|---|",
        f"| Ops | Ops doctor | `ops_doctor_report.json` | != OK | {context.get('ops_status', 'UNKNOWN')} |",
        f"| Runtime | Delta runtime | `runtime_delta_report.json` | A_CONTROLER | {context.get('delta_status', 'UNKNOWN')} |",
        f"| Handoff | Handoff ops | `ops_handoff_manifest.json` | != PRET_A_TRANSMETTRE | {context.get('handoff_status', 'UNKNOWN')} |",
        f"| Schemas | Validation schemas | `schema_validation_report.json` | != OK | {context.get('schema_validation_status', 'UNKNOWN')} |",
        f"| Paquet | Gate evaluateurs | `paquet_evaluateurs_gate.json` | != PRET_A_ENVOYER | {context.get('package_gate_status', 'UNKNOWN')} |",
        f"| Revue humaine | Items file | `FILE-REVUE-HUMAINE-V0.csv` | derive non triee | {context.get('review_queue_items', 0)} |",
        "| Performance | P95 dossier | `SLO-SLA-V1.md` + runtime metrics | > cible | A_INSTRUMENTER |",
        "| Metier | Acceptation terrain | `CRITERES-ACCEPTATION-METIER-V1.md` | non signee | BLOQUE |",
        "",
        "## Cadence de revue",
        "",
        "| Moment | Revue | Owner | Decision |",
        "|---|---|---|---|",
        "| J+0 | Verification gates avant trafic | Platform | Continuer / rollback |",
        "| J+1 | Qualite, erreurs, support | Product + Platform | Etendre / maintenir |",
        "| J+7 | Stabilisation canary | Lead Metier + Product + Platform | Etendre / stopper |",
        "| J+30 | Passage run standard | Comite produit | Clore hypercare |",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_stabilization_markdown(context: dict[str, object]) -> str:
    lines = [
        "# RAPPORT STABILISATION J7",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Preparer le rapport J+7 de stabilisation canary. Aucun resultat prod reel n'est declare tant que le canary n'est pas ouvert.",
        "",
        "## Synthese",
        "",
        "| Indicateur | Valeur |",
        "|---|---:|",
        f"| Statut Phase K | {context.get('decision', 'UNKNOWN')} |",
        "| Canary ouvert | non |",
        "| Incidents prod | n/a |",
        "| Rollback execute | non |",
        f"| P0 preprod ouverts | {context.get('p0_open', 0)} |",
        f"| P1 preprod ouverts | {context.get('p1_open', 0)} |",
        "",
        "## Conditions pour produire un vrai J+7",
        "",
        "- Homologation production signee.",
        "- Perimetre canary K1/K2 active.",
        "- Tableau de bord prod alimente avec mesures reelles.",
        "- Support et rollback disponibles pendant toute la fenetre.",
        "",
        "## Decision J+7 actuelle",
        "",
        f"Decision: **{context.get('decision', 'UNKNOWN')}**.",
        "",
        "Aucune stabilisation production ne peut etre constatee avant ouverture controlee du canary.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_phase_k_deliverables(
    *,
    ops_doctor_path: Path = OPS_DOCTOR_DEFAULT,
    pv_path: Path = PV_HOMOLOGATION_DEFAULT,
    register_path: Path = PREPROD_REGISTER_DEFAULT,
    rollback_path: Path = ROLLBACK_DEFAULT,
    ops_runbook_path: Path = OPS_RUNBOOK_DEFAULT,
    canary_out: Path = CANARY_OUT_DEFAULT,
    dashboard_out: Path = DASHBOARD_OUT_DEFAULT,
    stabilization_out: Path = STABILIZATION_OUT_DEFAULT,
) -> dict[str, object]:
    context = build_deployment_context(
        load_json(ops_doctor_path),
        read_text(pv_path),
        read_text(register_path),
        read_text(rollback_path),
        read_text(ops_runbook_path),
    )
    write_text(canary_out, build_canary_markdown(context))
    write_text(dashboard_out, build_dashboard_markdown(context))
    write_text(stabilization_out, build_stabilization_markdown(context))
    return {
        "decision": context["decision"],
        "canary_out": canary_out.as_posix(),
        "dashboard_out": dashboard_out.as_posix(),
        "stabilization_out": stabilization_out.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere les livrables Phase K deploiement canary et stabilisation.")
    parser.add_argument("--ops-doctor", type=Path, default=OPS_DOCTOR_DEFAULT)
    parser.add_argument("--pv", type=Path, default=PV_HOMOLOGATION_DEFAULT)
    parser.add_argument("--register", type=Path, default=PREPROD_REGISTER_DEFAULT)
    parser.add_argument("--rollback", type=Path, default=ROLLBACK_DEFAULT)
    parser.add_argument("--ops-runbook", type=Path, default=OPS_RUNBOOK_DEFAULT)
    parser.add_argument("--canary-out", type=Path, default=CANARY_OUT_DEFAULT)
    parser.add_argument("--dashboard-out", type=Path, default=DASHBOARD_OUT_DEFAULT)
    parser.add_argument("--stabilization-out", type=Path, default=STABILIZATION_OUT_DEFAULT)
    args = parser.parse_args()

    outputs = generate_phase_k_deliverables(
        ops_doctor_path=args.ops_doctor,
        pv_path=args.pv,
        register_path=args.register,
        rollback_path=args.rollback,
        ops_runbook_path=args.ops_runbook,
        canary_out=args.canary_out,
        dashboard_out=args.dashboard_out,
        stabilization_out=args.stabilization_out,
    )
    print(f"Plan canary: {outputs['canary_out']}")
    print(f"Tableau bord prod: {outputs['dashboard_out']}")
    print(f"Rapport stabilisation J7: {outputs['stabilization_out']}")
    print(f"Decision: {outputs['decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
