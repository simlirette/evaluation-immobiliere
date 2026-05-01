# PLAN DEPLOIEMENT CANARY V1

_As-of date: 2026-05-01 (UTC)_

## Objectif
Preparer un deploiement progressif et reversible sans executer la production tant que les gates metier et preprod restent ouverts.

## Decision

- Statut Phase K: **DEPLOIEMENT_PROD_BLOQUE**
- Ops doctor: **OK**
- Ecarts preprod ouverts: **2**
- P0 ouverts: **1**
- P1 ouverts: **1**

## Gates d'ouverture canary

| Gate | Cible | Statut courant | Bloque canary prod |
|---|---|---|---|
| Homologation production | Go production signe | NON | oui |
| Ops doctor | OK | OK | oui |
| Rollback | Runbook relu/teste | PRET | oui |
| Runbook operations | Disponible | PRET | oui |
| Perimetre canary | Equipe/dossiers limites designes | A_DESIGNER | oui |

## Perimetre canary propose

| Vague | Perimetre | Duree observation | Critere extension | Statut |
|---|---|---|---|---|
| K0 | Aucun trafic prod | Jusqu'a fermeture P0 | P0=0 et Go metier signe | Bloque |
| K1 | 1 evaluateur interne, dossiers non clients | 1 jour ouvre | 0 incident P0/P1 | Prepare |
| K2 | 1 bureau pilote, dossiers anonymises controles | 7 jours | SLO tenus + avis metier OK | Prepare |
| K3 | Extension progressive | 30 jours | Stabilite J+7/J+30 | A planifier |

## Rollback instantane

- Declencher rollback si incident securite, donnees, contrat, qualite metier ou indisponibilite majeure.
- Revenir au tag sain precedent et reexecuter CI + ops doctor.
- Suspendre toute extension de perimetre tant que le post-mortem n'est pas clos.
