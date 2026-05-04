# Rapport dress rehearsal staging V1

_As-of date: 2026-05-04 (UTC)_

## Decision

- Release candidate: **rc-2026-05-04-001**
- Decision: **PRET_GO_LIVE_CONTROLE**
- Commit: `HEAD`
- Go live: **A_CONTROLER_APRES_STAGING**

## Scenarios staging

| Scenario | Statut | Evidence |
|---|---|---|
| ci_exact_commit | SIMULE_OK | Workflow Validation inclut les gates metier, revues externes, fermeture ecarts et tests unitaires. |
| generated_artifacts_clean | SIMULE_OK | La CI verifie git diff --exit-code sur les artefacts generes versionnes. |
| no_open_evaluator_gaps | SIMULE_OK | Le registre de fermeture couvre les 3 ecarts externes P1/P2. |

## Conditions avant go live

- Rejouer cette repetition sur le commit exact tague release-candidate.
- Confirmer CI verte et artefacts generes propres.
- Confirmer support et rollback disponibles pendant la fenetre controlee.
