# PIPELINE CI V1

_As-of date: 2026-05-01 (UTC)_

## Objectif
Formaliser le pipeline CI bloquant pour chaque pull request et chaque push vers `main`.

## Statut

- Workflow source: `.github/workflows/validation.yml`
- Statut Phase H: **EN_ATTENTE_REPONSES_TERRAIN**
- Decision Phase I: **GO_CONDITIONNEL_PREPARATION** tant que les retours terrain ne sont pas signes.

## Gates CI

| Gate | Commande / signal | Statut | Bloquant |
|---|---|---|---|
| Compilation Python | `python -m py_compile` | present | oui |
| Validation reponses evaluateurs | `valider_reponses_evaluateurs.py` | present | oui |
| Validation fixtures | `valider_fixtures_v0.py --strict` | present | oui |
| Simulation runtime | `simuler_runtime_engine_v0.py` | present | oui |
| Integrite runtime | `analyser_integrite_runtime_v0.py` | present | oui |
| Chaine pre-reponses | `executer_pre_reponses_v0.py` | present | oui |
| Contrats infra | `valider_rapports_infra_v0.py` | present | oui |
| Tests unitaires | `python -m unittest discover` | present | oui |

## Commande de preuve locale Phase I

```powershell
python -m unittest evaluation-immobiliere/tests/test_runtime_v0.py evaluation-immobiliere/tests/test_ops_professional_gates_v0.py
```

## Politique de merge

- Aucun merge vers `main` si un gate CI bloquant echoue.
- Les artefacts generes versionnes doivent etre propres: `git diff --exit-code` sur les sorties attendues.
- Les rapports runtime locaux ignores par git restent des preuves d'execution, pas des artefacts de release.
- Les changements de contrat doivent inclure tests, matrice d'impact et plan de rollback.

## Risques et mitigations

| Risque | Mitigation | Owner |
|---|---|---|
| Derive des artefacts generes | Gate `git diff --exit-code` | Platform |
| Tests locaux dependants du dossier temporaire Windows | `.test-tmp/` controle et ignore par git | QA/Platform |
| Phase H non signee | CI autorisee, promotion prod bloquee | Product + Lead Metier |
