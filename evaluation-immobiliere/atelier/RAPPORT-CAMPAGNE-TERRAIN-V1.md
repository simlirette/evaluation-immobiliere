# RAPPORT CAMPAGNE TERRAIN V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Documenter la validation metier terrain des sorties IA et transformer les ecarts evaluateurs en decisions de calibration.

## Synthese

| Indicateur | Valeur |
|---|---:|
| Source calibration | `evaluation-immobiliere/atelier/CALIBRATION-EVALUATEURS.csv` |
| Statut Phase H | EN_ATTENTE_REPONSES_TERRAIN |
| Reponses actives | 0 |
| Repondants uniques | 0 |
| Desaccords statut | 0 |
| Items backlog | 0 |

## Point d'arret

- Aucune ligne active n'est presente dans le fichier de calibration evaluateur.
- La campagne terrain n'est pas closee et aucune conclusion metier ne doit etre inventee.
- Utiliser les questions runtime ci-dessous pour guider la collecte des reponses.

## Couverture dossiers

| Dossier | Statut runtime | Reponses | Statuts attendus | Desaccord |
|---|---|---:|---|---|
| D-REEL-001 | PRET_REVISION_FINALE | 0 | - | non |
| D-REEL-002 | BROUILLON | 0 | - | non |
| D-REEL-003 | A_REVOIR | 0 | - | non |

## Ecarts et backlog

- Aucun ecart evaluateur confirme pour l'instant.

## Questions terrain ouvertes

| Dossier | Type | Cible | Question |
|---|---|---|---|
| D-REEL-002 | warning | W001: confiance faible | Decider si ce warning reste informatif ou devient bloquant. |
| D-REEL-003 | blocage | B003: vente comparable future vs date_reference | Confirmer si ce blocage doit rester bloquant ou etre assoupli. |
| D-REEL-003 | blocage | CONF005: comparable[2] hors fenetre temporelle | Confirmer si ce blocage doit rester bloquant ou etre assoupli. |
| D-REEL-003 | warning | W002: comparable eloigne | Decider si ce warning reste informatif ou devient bloquant. |
| D-REEL-003 | artefact | redaction.brouillon_rapport.md | Valider si l'artefact manquant bloque la revue evaluateur. |
| D-REEL-003 | artefact | redaction.annexe_sources.md | Valider si l'artefact manquant bloque la revue evaluateur. |

## Decision Phase H

Decision: **EN_ATTENTE_REPONSES_TERRAIN**.

Dependances Phase I:
- campagne terrain signee ou point d'arret explicite;
- matrice d'ecarts exploitable;
- criteres d'acceptation metier revus par Lead Metier + Product.
