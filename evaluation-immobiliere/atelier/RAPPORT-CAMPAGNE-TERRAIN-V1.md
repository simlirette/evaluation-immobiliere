# RAPPORT CAMPAGNE TERRAIN V1

_As-of date: 2026-05-04 (UTC)_

## Objectif

Documenter la campagne terrain reelle Phase H a partir de dossiers reels anonymises et de reponses evaluateurs recues, sans utiliser de reponses synthetiques.

## Synthese

| Indicateur | Valeur |
|---|---:|
| Statut Phase H reelle | EN_ATTENTE_ENTREES_TERRAIN_REELLES |
| Dossiers terrain actifs | 0 |
| Reponses evaluateurs actives | 0 |
| Gate de preuve | `verifier_campagne_terrain_reelle_v1.py` |

## Point d'arret

- Aucun dossier `case_pilote_reel_*.json` actif n'est versionne dans le repo.
- Les revues synthetiques et fixtures externes existantes restent des preuves de preparation, pas des reponses terrain.
- Aucune conclusion metier Phase H ne doit etre inventee avant reception de dossiers anonymises et de reponses evaluateurs.

## Flux requis

1. Valider anonymisation et structure des dossiers hors repo actif.
2. Normaliser les sources anonymisees dans `runtime_pilotes_reels/ingestion_v0/`.
3. Executer le runtime pilotes reels.
4. Produire la revue interne.
5. Generer le paquet evaluateurs.
6. Verifier le point d'arret avant reponses.

## Decision Phase H

Decision: **EN_ATTENTE_ENTREES_TERRAIN_REELLES**.

La production reste bloquee pour validation terrain tant que le gate Phase H ne retourne pas `PRET_A_RECEVOIR_REPONSES_TERRAIN` puis que les vraies reponses evaluateurs ne sont pas validees.
