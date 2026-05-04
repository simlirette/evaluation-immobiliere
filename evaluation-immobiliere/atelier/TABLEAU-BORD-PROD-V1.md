# TABLEAU BORD PROD V1

_As-of date: 2026-05-01 (UTC)_

## Objectif
Definir les indicateurs a surveiller pendant canary, J+7 et J+30.

Statut courant: **DEPLOIEMENT_PROD_BLOQUE**.

## Indicateurs critiques

| Domaine | Indicateur | Source | Seuil alerte | Statut actuel |
|---|---|---|---|---|
| Ops | Ops doctor | `ops_doctor_report.json` | != OK hors attente terrain | EN_ATTENTE_ENTREES_TERRAIN_REELLES |
| Runtime | Delta runtime | `runtime_delta_report.json` | A_CONTROLER | STABLE |
| Handoff | Handoff ops | `ops_handoff_manifest.json` | != PRET_A_TRANSMETTRE hors attente terrain | EN_ATTENTE_ENTREES_TERRAIN_REELLES |
| Schemas | Validation schemas | `schema_validation_report.json` | != OK hors attente terrain | EN_ATTENTE_ENTREES_TERRAIN_REELLES |
| Paquet | Gate evaluateurs | `paquet_evaluateurs_gate.json` | != PRET_A_ENVOYER hors attente terrain | EN_ATTENTE_ENTREES_TERRAIN_REELLES |
| Revue humaine | Items file | `FILE-REVUE-HUMAINE-V0.csv` | derive non triee | 0 |
| Performance | P95 dossier | `SLO-SLA-V1.md` + runtime metrics | > cible | A_INSTRUMENTER |
| Metier | Acceptation terrain | `CRITERES-ACCEPTATION-METIER-V1.md` | non signee | BLOQUE |

## Cadence de revue

| Moment | Revue | Owner | Decision |
|---|---|---|---|
| J+0 | Verification gates avant trafic | Platform | Continuer / rollback |
| J+1 | Qualite, erreurs, support | Product + Platform | Etendre / maintenir |
| J+7 | Stabilisation canary | Lead Metier + Product + Platform | Etendre / stopper |
| J+30 | Passage run standard | Comite produit | Clore hypercare |
