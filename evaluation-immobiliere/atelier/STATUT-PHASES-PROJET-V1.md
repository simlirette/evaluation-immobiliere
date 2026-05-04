# Statut phases projet V1

_As-of date: 2026-05-04 (UTC)_

## Synthese

- Decision: **PROJET_PRET_REVUE_EVALUATEUR_AGREE_PROD_BLOQUEE**
- Cible produit: **V1_PRE_EVALUATEUR**
- Decision pre-evaluateur: **PRET_REVUE_EVALUATEUR_AGREE**
- Paquet V1 pre-evaluateur: **PRET_REVUE_EVALUATEUR_AGREE**
- OK coherence: **true**
- Phase H reelle: **EN_ATTENTE_ENTREES_TERRAIN_REELLES**
- Dossiers terrain actifs: **0**
- Reponses evaluateurs actives: **0**
- Calibration evaluateurs active: **0**
- Release candidate: **PRET_GO_LIVE_CONTROLE**
- Ecarts preprod ouverts: **2**

## Phases

| Phase | Nom | Statut | Decision | Bloquant prod | Evidence |
|---|---|---|---|---|---|
| A | Cadrage | TERMINE | BASELINE_DOCUMENTEE | non | `PLAN-DIRECTEUR-COMPLET-V1.md` |
| B | Contrats Aston | TERMINE | CONTRATS_DOCUMENTES | non | `CONTRATS-INTEGRATION-ASTON-V1.yaml` |
| C | Runtime v0 | TERMINE | RUNTIME_EN_CI | non | `tests/runtime/runtime_summary.json` |
| D | API persistence | PREPARE | CONTRATS_API_DOCUMENTES | non | `API-RUNTIME-V0.md` |
| E | UI evaluateur | PREPARE | SPEC_UI_DOCUMENTEE | non | `SPEC-UI-EVALUATEUR-V1.md` |
| F | Securite gouvernance | PREPARE | BASELINE_DOCUMENTEE | non | `SECURITY-BASELINE-V1.md` |
| G | Perf fiabilite cout | GO_CONDITIONNEL | SLO_A_FERMER | oui | `SLO-SLA-V1.md` |
| H | Campagne terrain reelle | EN_ATTENTE_ENTREES_TERRAIN_REELLES | EN_ATTENTE_ENTREES_TERRAIN_REELLES | oui | `verifier_campagne_terrain_reelle_v1.py` |
| I | CI/CD | PRET_STAGING | GO_PREPARATION_STAGING | non | `.github/workflows/validation.yml` |
| J | Preproduction | PROD_BLOQUEE | NO_GO_PROD_PREPARATION | oui | `RAPPORT-DRESS-REHEARSAL-V1.md` |
| K | Canary | PROD_BLOQUEE | DEPLOIEMENT_PROD_BLOQUE | oui | `PLAN-DEPLOIEMENT-CANARY-V1.md` |
| L | Hypercare | PREPARE_PROD_BLOQUEE | HYPERCARE_PREPARE_PROD_BLOQUEE | oui | `PLAN-HYPERCARE-V1.md` |

## Gates coherence

| Gate | Statut | OK | Evidence |
|---|---|---|---|
| phase_h_gate | EN_ATTENTE_ENTREES_TERRAIN_REELLES | true | 0 dossier(s) terrain actif(s) |
| aucune_reponse_inventee | AUCUNE_REPONSE_ACTIVE | true | reponses=0; calibration=0; erreurs_reponses=0 |
| ci_couvre_phase_h_et_statut_projet | COUVERT | true | .github/workflows/validation.yml |
| production_bloquee_avant_phase_h_reelle | BLOQUEE | true | Phase J/K/L et CD declarent le blocage production. |
| pv_homologation_scope_reel | PORTEE_REELLE_EXPLICITE | true | evaluation-immobiliere/atelier/PV-HOMOLOGATION-V1.md |
| phase_h_non_bloquante_pour_v1_pre_evaluateur | PHASE_H_POST_V1 | true | La Phase H bloque seulement la validation terrain/prod reelle, pas la finalisation produit pre-evaluateur. |
| plan_v1_pre_evaluateur | PRESENT | true | evaluation-immobiliere/atelier/PLAN-V1-PRE-EVALUATEUR-AGREE.md |
| paquet_v1_pre_evaluateur | PRET_REVUE_EVALUATEUR_AGREE | true | evaluation-immobiliere/atelier/PAQUET-V1-PRE-EVALUATEUR |

## Situation dossiers/reponses

- Aucun dossier reel anonymise actif n'est versionne dans le repo.
- Aucune reponse evaluateur active n'est presente dans les CSV de collecte.
- Les revues evaluateurs externes versionnees restent des fixtures d'homologation/preparation, pas des retours de campagne terrain reelle.
- La prochaine action produit est la revue de la V1 avec l'evaluateur a partir du paquet versionne.
- La prochaine action non simulable, apres V1, est la reception de dossiers anonymises valides hors repo actif, puis l'envoi du paquet evaluateurs.
