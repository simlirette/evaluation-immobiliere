#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

WORKFLOW_DEFAULT = Path(".github/workflows/validation.yml")
ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
CI_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "PIPELINE-CI-V1.md"
CD_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "PIPELINE-CD-V1.md"
ROLLBACK_OUT_DEFAULT = ATELIER_DIR_DEFAULT / "RUNBOOK-ROLLBACK-V1.md"
PHASE_H_STATUS_DEFAULT = "GO_PROD_PREPARATION"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def workflow_signal(workflow_text: str, needle: str) -> str:
    return "present" if needle in workflow_text else "a_ajouter"


def build_ci_markdown(workflow_path: Path, workflow_text: str, phase_h_status: str = PHASE_H_STATUS_DEFAULT) -> str:
    checks = [
        ("Compilation Python", "python -m py_compile", workflow_signal(workflow_text, "python -m py_compile")),
        ("Validation reponses evaluateurs", "valider_reponses_evaluateurs.py", workflow_signal(workflow_text, "valider_reponses_evaluateurs.py")),
        ("Validation fixtures", "valider_fixtures_v0.py --strict", workflow_signal(workflow_text, "valider_fixtures_v0.py")),
        ("Simulation runtime", "simuler_runtime_engine_v0.py", workflow_signal(workflow_text, "simuler_runtime_engine_v0.py")),
        ("Integrite runtime", "analyser_integrite_runtime_v0.py", workflow_signal(workflow_text, "analyser_integrite_runtime_v0.py")),
        ("Chaine pre-reponses", "executer_pre_reponses_v0.py", workflow_signal(workflow_text, "executer_pre_reponses_v0.py")),
        ("Contrats infra", "valider_rapports_infra_v0.py", workflow_signal(workflow_text, "valider_rapports_infra_v0.py")),
        ("Revues evaluateurs externes strictes", "verifier_revues_evaluateurs_externes_v1.py --strict", workflow_signal(workflow_text, "verifier_revues_evaluateurs_externes_v1.py")),
        ("Fermeture ecarts evaluateurs stricte", "verifier_fermeture_ecarts_evaluateurs_v1.py --strict", workflow_signal(workflow_text, "verifier_fermeture_ecarts_evaluateurs_v1.py")),
        ("Release candidate strict", "verifier_release_candidate_v1.py --strict", workflow_signal(workflow_text, "verifier_release_candidate_v1.py")),
        ("Tests unitaires", "python -m unittest discover", workflow_signal(workflow_text, "python -m unittest discover")),
    ]

    lines = [
        "# PIPELINE CI V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Formaliser le pipeline CI bloquant pour chaque pull request et chaque push vers `main`.",
        "",
        "## Statut",
        "",
        f"- Workflow source: `{workflow_path.as_posix()}`",
        f"- Statut Phase H: **{phase_h_status}**",
        "- Decision Phase I: **GO_PREPARATION_PROD**; le go live reste soumis au dress rehearsal et au tag release-candidate.",
        "",
        "## Gates CI",
        "",
        "| Gate | Commande / signal | Statut | Bloquant |",
        "|---|---|---|---|",
    ]
    for name, command, status in checks:
        lines.append(f"| {name} | `{command}` | {status} | oui |")

    lines.extend(
        [
            "",
            "## Commande de preuve locale Phase I",
            "",
            "```powershell",
            "python -m unittest evaluation-immobiliere/tests/test_runtime_v0.py evaluation-immobiliere/tests/test_ops_professional_gates_v0.py",
            "```",
            "",
            "## Politique de merge",
            "",
            "- Aucun merge vers `main` si un gate CI bloquant echoue.",
            "- Les artefacts generes versionnes doivent etre propres: `git diff --exit-code` sur les sorties attendues.",
            "- Les rapports runtime locaux ignores par git restent des preuves d'execution, pas des artefacts de release.",
            "- Les changements de contrat doivent inclure tests, matrice d'impact et plan de rollback.",
            "",
            "## Risques et mitigations",
            "",
            "| Risque | Mitigation | Owner |",
            "|---|---|---|",
            "| Derive des artefacts generes | Gate `git diff --exit-code` | Platform |",
            "| Tests locaux dependants du dossier temporaire Windows | `.test-tmp/` controle et ignore par git | QA/Platform |",
            "| Go live avant dress rehearsal | CI autorisee, promotion prod bloquee jusqu'au tag release-candidate | Product + Platform |",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_cd_markdown(phase_h_status: str = PHASE_H_STATUS_DEFAULT) -> str:
    status_line = (
        f"Statut Phase H: **{phase_h_status}**. La preparation prod est autorisee; le go live reste bloque jusqu'au dress rehearsal staging."
        if phase_h_status == "GO_PROD_PREPARATION"
        else f"Statut Phase H: **{phase_h_status}**. La production reste bloquee tant que la campagne terrain n'est pas signee."
    )
    lines = [
        "# PIPELINE CD V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Definir les promotions dev -> staging -> prod avec approbations et preuves minimales.",
        "",
        status_line,
        "",
        "## Environnements",
        "",
        "| Environnement | Declencheur | Gates requis | Approbation | Statut actuel |",
        "|---|---|---|---|---|",
        "| dev | Pull request ou branche de travail | CI complet | Maintainer technique | Actif |",
        "| staging | Merge `main` ou tag release-candidate | CI complet + docs Phase I | Product + Platform | A preparer |",
        "| prod | Release approuvee | Phase H signee + Phase J homologuee | Lead Metier + Product + Platform | Bloque |",
        "",
        "## Promotion",
        "",
        "1. Dev: executer CI, tests unitaires, contrats, runtime smoke et gates ops.",
        "2. Staging: figer un tag release-candidate, regenerer preuves, verifier compatibilite session/artefacts.",
        "3. Prod: autoriser seulement apres validation metier terrain, homologation pre-prod et runbook rollback relu.",
        "",
        "## Artefacts de release",
        "",
        "| Artefact | Source | Role |",
        "|---|---|---|",
        "| Commit SHA | GitHub | Version applicative |",
        "| Tag release | GitHub | Point de rollback |",
        "| Contrats YAML/JSON | `mvp/`, `schemas/`, `atelier/` | Compatibilite donnees |",
        "| Rapports Phase G/H/I | `atelier/` | Preuves go/no-go |",
        "| Workflow CI | `.github/workflows/validation.yml` | Gate automatisable |",
        "",
        "## Gates de promotion",
        "",
        "- CI vert sur le commit exact a promouvoir.",
        "- Aucun P0 metier ouvert dans la matrice d'ecarts evaluateurs.",
        "- Aucun `A_CORRIGER` dans les gates ops professionnels.",
        "- Rollback teste ou simule avant staging, obligatoire avant prod.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_rollback_markdown(phase_h_status: str = PHASE_H_STATUS_DEFAULT) -> str:
    context_line = (
        f"Contexte Phase H: **{phase_h_status}**. Le rollback staging doit etre repete avant tout go live controle."
        if phase_h_status == "GO_PROD_PREPARATION"
        else f"Contexte Phase H: **{phase_h_status}**. Aucun rollback prod reel n'est execute tant que la prod n'est pas ouverte."
    )
    lines = [
        "# RUNBOOK ROLLBACK V1",
        "",
        "_As-of date: 2026-05-01 (UTC)_",
        "",
        "## Objectif",
        "Fournir une procedure de retour arriere applicative, contrats et donnees sessionnelles.",
        "",
        context_line,
        "",
        "## Declencheurs",
        "",
        "| Declencheur | Niveau | Action | Owner |",
        "|---|---|---|---|",
        "| Regression CI apres merge | dev/main | Revert PR ou hotfix | Platform |",
        "| Contrat de donnees incompatible | staging/prod | Restaurer version contrat + bloquer promotion | QA/Platform |",
        "| Erreur runtime critique | staging/prod | Revenir au tag precedent | Runtime |",
        "| Rejet metier terrain | staging/prod | Suspendre release + ouvrir backlog P0 | Product + Lead Metier |",
        "",
        "## Procedure applicative",
        "",
        "1. Identifier le commit ou tag sain precedent.",
        "2. Geler toute promotion en cours.",
        "3. Creer un revert non destructif ou rediriger le deploiement vers le tag sain.",
        "4. Reexecuter CI complet et gates ops.",
        "5. Documenter incident, impact, decision et owner.",
        "",
        "## Procedure contrats et donnees",
        "",
        "- Ne jamais modifier retroactivement un artefact de session deja produit.",
        "- Versionner tout changement de schema/contrat avec compatibilite explicite.",
        "- Si migration incomplete: bloquer reprise session, conserver lecture seule, ouvrir correction P0.",
        "- Les snapshots de connaissance et index d'artefacts doivent rester correlables au `run_id` initial.",
        "",
        "## Checklist de sortie rollback",
        "",
        "- [ ] CI vert sur version restauree.",
        "- [ ] Aucun gate ops en `A_CORRIGER`.",
        "- [ ] Sessions/artefacts existants lisibles ou explicitement bloques avec message utilisateur.",
        "- [ ] Product + Platform informes.",
        "- [ ] Post-mortem cree avant nouvelle promotion.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_phase_i_deliverables(
    *,
    workflow_path: Path = WORKFLOW_DEFAULT,
    ci_out: Path = CI_OUT_DEFAULT,
    cd_out: Path = CD_OUT_DEFAULT,
    rollback_out: Path = ROLLBACK_OUT_DEFAULT,
    phase_h_status: str = PHASE_H_STATUS_DEFAULT,
) -> dict[str, object]:
    workflow_text = read_text(workflow_path)
    write_text(ci_out, build_ci_markdown(workflow_path, workflow_text, phase_h_status))
    write_text(cd_out, build_cd_markdown(phase_h_status))
    write_text(rollback_out, build_rollback_markdown(phase_h_status))
    return {
        "workflow_path": workflow_path.as_posix(),
        "ci_out": ci_out.as_posix(),
        "cd_out": cd_out.as_posix(),
        "rollback_out": rollback_out.as_posix(),
        "phase_h_status": phase_h_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere les livrables Phase I CI/CD et rollback.")
    parser.add_argument("--workflow", type=Path, default=WORKFLOW_DEFAULT)
    parser.add_argument("--ci-out", type=Path, default=CI_OUT_DEFAULT)
    parser.add_argument("--cd-out", type=Path, default=CD_OUT_DEFAULT)
    parser.add_argument("--rollback-out", type=Path, default=ROLLBACK_OUT_DEFAULT)
    parser.add_argument("--phase-h-status", default=PHASE_H_STATUS_DEFAULT)
    args = parser.parse_args()

    outputs = generate_phase_i_deliverables(
        workflow_path=args.workflow,
        ci_out=args.ci_out,
        cd_out=args.cd_out,
        rollback_out=args.rollback_out,
        phase_h_status=args.phase_h_status,
    )
    print(f"Pipeline CI: {outputs['ci_out']}")
    print(f"Pipeline CD: {outputs['cd_out']}")
    print(f"Runbook rollback: {outputs['rollback_out']}")
    print(f"Statut Phase H: {outputs['phase_h_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
