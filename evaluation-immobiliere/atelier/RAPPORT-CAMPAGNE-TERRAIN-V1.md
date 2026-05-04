# RAPPORT CAMPAGNE TERRAIN V1

_As-of date: 2026-05-04 (UTC)_

## Objectif
Documenter la campagne terrain reelle Phase H a partir de dossiers reels anonymises et de reponses evaluateurs recues, sans utiliser de reponses synthetiques.

## Synthese

| Indicateur | Valeur |
|---|---:|
| Source calibration | `evaluation-immobiliere/atelier/CALIBRATION-EVALUATEURS.csv` |
| Statut Phase H reelle | EN_ATTENTE_ENTREES_TERRAIN_REELLES |
| Dossiers terrain actifs | 0 |
| Reponses actives | 0 |
| Repondants uniques | 0 |
| Desaccords statut | 0 |
| Items backlog | 0 |
| Gate de preuve | `verifier_campagne_terrain_reelle_v1.py` |

## Point d'arret

- Aucun dossier `case_pilote_reel_*.json` actif n'est versionne dans le repo.
- Aucun resultat evaluateur reel exploitable n'est present.
- La campagne terrain n'est pas closee et aucune conclusion metier ne doit etre inventee.
- Les revues synthetiques et fixtures externes existantes restent des preuves de preparation, pas des reponses terrain.
- Utiliser les questions runtime ci-dessous pour guider la collecte des reponses.

## Couverture dossiers

| Dossier | Statut runtime | Reponses | Statuts attendus | Desaccord |
|---|---|---:|---|---|

## Ecarts et backlog

- Aucun ecart evaluateur confirme pour l'instant.

## Questions terrain ouvertes

- Aucune question terrain ouverte.

## Decision Phase H

Decision: **EN_ATTENTE_ENTREES_TERRAIN_REELLES**.

Dependances Phase I:
- campagne terrain reelle signee ou point d'arret explicite;
- matrice d'ecarts exploitable;
- criteres d'acceptation metier revus par Lead Metier + Product.
