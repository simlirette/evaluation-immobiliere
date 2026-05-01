#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
REPORTS_DIR_DEFAULT = Path("evaluation-immobiliere/tests/reports")
VALIDATION_RESPONSES_DEFAULT = ATELIER_DIR_DEFAULT / "RAPPORT-VALIDATION-REPONSES.md"
SUMMARY_JSON_DEFAULT = REPORTS_DIR_DEFAULT / "summary.json"
CANARY_PLAN_DEFAULT = ATELIER_DIR_DEFAULT / "PLAN-DEPLOIEMENT-CANARY-V1.md"
STABILIZATION_DEFAULT = ATELIER_DIR_DEFAULT / "RAPPORT-STABILISATION-J7.md"
PREPROD_REGISTER_DEFAULT = ATELIER_DIR_DEFAULT / "REGISTRE-ECARTS-PREPROD-V1.md"
HYPERCARE_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "PLAN-HYPERCARE-V1.md"
BACKLOG_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "BACKLOG-AMELIORATION-V2.md"
ADOPTION_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "RAPPORT-ADOPTION-V1.md"


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_preprod_open_counts(register_text: str) -> tuple[int, int, int]:
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


def build_hypercare_context(
    validation_responses_text: str,
    summary: dict[str, object],
    canary_text: str,
    stabilization_text: str,
    preprod_register_text: str,
) -> dict[str, object]:
    open_gaps, p0_open, p1_open = parse_preprod_open_counts(preprod_register_text)
    prod_blocked = "DEPLOIEMENT_PROD_BLOQUE" in canary_text or "Canary ouvert | non" in stabilization_text
    active_responses_missing = "Lignes actives: **0**" in validation_responses_text
    total_cases = int(summary.get("total_cases", 0) or 0)
    ready_cases = 0
    status_counts = summary.get("status_counts", {}) if isinstance(summary.get("status_counts"), dict) else {}
    ready_cases = int(status_counts.get("PRET_REVISION_FINALE", 0) or 0)

    if prod_blocked:
        decision = "HYPERCARE_PREPARE_PROD_BLOQUEE"
    elif active_responses_missing:
        decision = "HYPERCARE_A_COMPLETER_RETOURS"
    else:
        decision = "HYPERCARE_PRET_A_ACTIVER"

    return {
        "decision": decision,
        "prod_blocked": prod_blocked,
        "active_responses_missing": active_responses_missing,
        "open_preprod_gaps": open_gaps,
        "p0_open": p0_open,
        "p1_open": p1_open,
        "dry_run_cases": total_cases,
        "dry_run_ready_cases": ready_cases,
        "dry_run_ready_rate": round(ready_cases / total_cases, 4) if total_cases else None,
        "conformite_globale_pct": summary.get("conformite_globale_pct"),
        "top_blocking_failures": summary.get("top_blocking_failures", []),
        "top_warnings": summary.get("top_warnings", []),
    }


def build_improvement_items(context: dict[str, object]) -> list[dict[str, str]]:
    items = [
        {
            "id": "V2-001",
            "priority": "P0",
            "domain": "metier",
            "status": "bloque",
            "owner": "Lead Metier + Product",
            "item": "Completer la campagne Phase H et signer les criteres d'acceptation metier.",
            "evidence": "CRITERES-ACCEPTATION-METIER-V1.md",
        },
        {
            "id": "V2-002",
            "priority": "P0",
            "domain": "release",
            "status": "bloque",
            "owner": "Platform",
            "item": "Fermer les ecarts preprod P0 avant ouverture canary.",
            "evidence": "REGISTRE-ECARTS-PREPROD-V1.md",
        },
        {
            "id": "V2-003",
            "priority": "P1",
            "domain": "performance",
            "status": "a_planifier",
            "owner": "Platform",
            "item": "Instrumenter p95 wall-clock par dossier et par etape.",
            "evidence": "SLO-SLA-V1.md",
        },
        {
            "id": "V2-004",
            "priority": "P1",
            "domain": "support",
            "status": "prepare",
            "owner": "Product + Support",
            "item": "Nommer la cellule hypercare et definir rotation support J+0/J+7.",
            "evidence": "PLAN-HYPERCARE-V1.md",
        },
        {
            "id": "V2-005",
            "priority": "P2",
            "domain": "adoption",
            "status": "a_mesurer",
            "owner": "Product",
            "item": "Mesurer adoption, satisfaction et temps gagne apres canary reel.",
            "evidence": "RAPPORT-ADOPTION-V1.md",
        },
    ]
    if int(context.get("p1_open", 0) or 0) > 0:
        items.append(
            {
                "id": "V2-006",
                "priority": "P1",
                "domain": "preprod",
                "status": "a_traiter",
                "owner": "Platform",
                "item": "Fermer ou accepter formellement les ecarts preprod P1.",
                "evidence": "REGISTRE-ECARTS-PREPROD-V1.md",
            }
        )
    return items


def build_hypercare_markdown(context: dict[str, object]) -> str:
    lines = [
        "# PLAN HYPERCARE V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Preparer la cellule hypercare, le support incident et le passage en run standard sans declarer une production active.",
        "",
        "## Statut",
        "",
        f"- Decision Phase L: **{context.get('decision', 'UNKNOWN')}**",
        f"- Production active: **{'non' if context.get('prod_blocked') else 'oui'}**",
        f"- Ecarts preprod ouverts: **{context.get('open_preprod_gaps', 0)}**",
        f"- P0 ouverts: **{context.get('p0_open', 0)}**",
        f"- Retours evaluateurs actifs manquants: **{'oui' if context.get('active_responses_missing') else 'non'}**",
        "",
        "## Cellule hypercare",
        "",
        "| Role | Responsabilite | Owner | Statut |",
        "|---|---|---|---|",
        "| Incident commander | Triage P0/P1 et decision rollback | A nommer | A_NOMMER |",
        "| Support metier | Qualification retours evaluateurs | A nommer | A_NOMMER |",
        "| Runtime/Platform | Correctifs techniques et observabilite | A nommer | A_NOMMER |",
        "| Product | Arbitrage backlog court terme vs v2 | A nommer | A_NOMMER |",
        "",
        "## Playbook incidents",
        "",
        "| Severite | Exemple | SLA initial | Action |",
        "|---|---|---|---|",
        "| P0 | Donnee client exposee, resultat critique faux en prod | immediat | Stop canary + rollback |",
        "| P1 | Regression runtime, SLO depasse, blocage revue | 1 jour ouvre | Hotfix ou maintien perimetre |",
        "| P2 | Irritant UX, demande amelioration | 7 jours | Backlog v2 |",
        "",
        "## Conditions d'activation",
        "",
        "- Canary K1/K2 ouvert avec perimetre nomme.",
        "- Tableau de bord prod alimente avec donnees reelles.",
        "- Owners hypercare nommes.",
        "- Rollback teste avant tout trafic client.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_backlog_markdown(items: list[dict[str, str]]) -> str:
    lines = [
        "# BACKLOG AMELIORATION V2",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "| ID | Priorite | Domaine | Statut | Owner | Item | Evidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in items:
        lines.append(
            "| {id} | {priority} | {domain} | {status} | {owner} | {item} | `{evidence}` |".format(
                id=item["id"],
                priority=item["priority"],
                domain=item["domain"],
                status=item["status"],
                owner=item["owner"],
                item=item["item"],
                evidence=item["evidence"],
            )
        )
    return "\n".join(lines).rstrip() + "\n"


def build_adoption_markdown(context: dict[str, object]) -> str:
    ready_rate = context.get("dry_run_ready_rate")
    ready_rate_text = "n/d" if ready_rate is None else f"{float(ready_rate) * 100:.1f}%"
    lines = [
        "# RAPPORT ADOPTION V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Preparer le suivi adoption et satisfaction. Aucun usage production reel n'est encore mesure.",
        "",
        "## Synthese",
        "",
        "| Indicateur | Valeur |",
        "|---|---:|",
        f"| Statut Phase L | {context.get('decision', 'UNKNOWN')} |",
        "| Utilisateurs prod actifs | 0 |",
        "| Bureaux actifs | 0 |",
        "| Dossiers prod traites | 0 |",
        "| Satisfaction mesuree | n/a |",
        f"| Dry-run cas | {context.get('dry_run_cases', 0)} |",
        f"| Dry-run PRET_REVISION_FINALE | {context.get('dry_run_ready_cases', 0)} |",
        f"| Dry-run taux pret | {ready_rate_text} |",
        f"| Conformite globale dry-run | {context.get('conformite_globale_pct', 'n/d')}% |",
        "",
        "## Mesures a activer apres canary",
        "",
        "- Taux dossiers termines sans intervention technique.",
        "- Temps moyen de revue evaluateur.",
        "- Taux de correction humaine par artefact.",
        "- Satisfaction evaluateur apres dossier.",
        "- Incidents par severite et temps de resolution.",
        "",
        "## Decision adoption",
        "",
        f"Decision: **{context.get('decision', 'UNKNOWN')}**.",
        "",
        "L'adoption reste non mesurable tant que le canary production n'est pas ouvert.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_phase_l_deliverables(
    *,
    validation_responses_path: Path = VALIDATION_RESPONSES_DEFAULT,
    summary_json_path: Path = SUMMARY_JSON_DEFAULT,
    canary_plan_path: Path = CANARY_PLAN_DEFAULT,
    stabilization_path: Path = STABILIZATION_DEFAULT,
    preprod_register_path: Path = PREPROD_REGISTER_DEFAULT,
    hypercare_out: Path = HYPERCARE_OUT_DEFAULT,
    backlog_out: Path = BACKLOG_OUT_DEFAULT,
    adoption_out: Path = ADOPTION_OUT_DEFAULT,
) -> dict[str, object]:
    context = build_hypercare_context(
        read_text(validation_responses_path),
        load_json(summary_json_path),
        read_text(canary_plan_path),
        read_text(stabilization_path),
        read_text(preprod_register_path),
    )
    items = build_improvement_items(context)
    write_text(hypercare_out, build_hypercare_markdown(context))
    write_text(backlog_out, build_backlog_markdown(items))
    write_text(adoption_out, build_adoption_markdown(context))
    return {
        "decision": context["decision"],
        "items_count": len(items),
        "hypercare_out": hypercare_out.as_posix(),
        "backlog_out": backlog_out.as_posix(),
        "adoption_out": adoption_out.as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere les livrables Phase L hypercare et amelioration continue.")
    parser.add_argument("--validation-responses", type=Path, default=VALIDATION_RESPONSES_DEFAULT)
    parser.add_argument("--summary-json", type=Path, default=SUMMARY_JSON_DEFAULT)
    parser.add_argument("--canary-plan", type=Path, default=CANARY_PLAN_DEFAULT)
    parser.add_argument("--stabilization", type=Path, default=STABILIZATION_DEFAULT)
    parser.add_argument("--preprod-register", type=Path, default=PREPROD_REGISTER_DEFAULT)
    parser.add_argument("--hypercare-out", type=Path, default=HYPERCARE_OUT_DEFAULT)
    parser.add_argument("--backlog-out", type=Path, default=BACKLOG_OUT_DEFAULT)
    parser.add_argument("--adoption-out", type=Path, default=ADOPTION_OUT_DEFAULT)
    args = parser.parse_args()

    outputs = generate_phase_l_deliverables(
        validation_responses_path=args.validation_responses,
        summary_json_path=args.summary_json,
        canary_plan_path=args.canary_plan,
        stabilization_path=args.stabilization,
        preprod_register_path=args.preprod_register,
        hypercare_out=args.hypercare_out,
        backlog_out=args.backlog_out,
        adoption_out=args.adoption_out,
    )
    print(f"Plan hypercare: {outputs['hypercare_out']}")
    print(f"Backlog amelioration v2: {outputs['backlog_out']}")
    print(f"Rapport adoption: {outputs['adoption_out']}")
    print(f"Decision: {outputs['decision']}")
    print(f"Items backlog: {outputs['items_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
