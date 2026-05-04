# PLAN HYPERCARE V1

_As-of date: 2026-05-01 (UTC)_

## Objectif
Preparer la cellule hypercare, le support incident et le passage en run standard sans declarer une production active.

## Statut

- Decision Phase L: **HYPERCARE_PREPARE_PROD_BLOQUEE**
- Production active: **non**
- Ecarts preprod ouverts: **2**
- P0 ouverts: **1**
- Retours evaluateurs actifs manquants: **oui**

## Cellule hypercare

| Role | Responsabilite | Owner | Statut |
|---|---|---|---|
| Incident commander | Triage P0/P1 et decision rollback | A nommer | A_NOMMER |
| Support metier | Qualification retours evaluateurs | A nommer | A_NOMMER |
| Runtime/Platform | Correctifs techniques et observabilite | A nommer | A_NOMMER |
| Product | Arbitrage backlog court terme vs v2 | A nommer | A_NOMMER |

## Playbook incidents

| Severite | Exemple | SLA initial | Action |
|---|---|---|---|
| P0 | Donnee client exposee, resultat critique faux en prod | immediat | Stop canary + rollback |
| P1 | Regression runtime, SLO depasse, blocage revue | 1 jour ouvre | Hotfix ou maintien perimetre |
| P2 | Irritant UX, demande amelioration | 7 jours | Backlog v2 |

## Conditions d'activation

- Canary K1/K2 ouvert avec perimetre nomme.
- Tableau de bord prod alimente avec donnees reelles.
- Owners hypercare nommes.
- Rollback teste avant tout trafic client.
