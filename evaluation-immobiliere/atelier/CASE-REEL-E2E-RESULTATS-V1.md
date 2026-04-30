# CASE REEL E2E RESULTATS V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Synthétiser les résultats Phase C/P0-02 du run E2E sur dossiers pilotes anonymisés, avec lecture métier, technique et décision de suite.

## Résumé exécutif
| Indicateur | Valeur |
|---|---:|
| Dossiers exécutés | 3 |
| Prêts révision finale | 1 |
| Brouillons | 1 |
| À revoir | 1 |
| Blocages détectés | 2 |
| Warnings détectés | 2 |
| Événements runtime | 78 |
| Artefacts produits | 46/48 |
| Erreurs contrat | 1 |

## Détail par dossier
| Dossier | Cas | Statut | Preuve principale | Décision |
|---|---|---|---|---|
| `D-REEL-001` | `case_pilote_reel_001` | `PRET_REVISION_FINALE` | 16/16 artefacts, aucun blocage | Candidat revue évaluateur |
| `D-REEL-002` | `case_pilote_reel_002` | `BROUILLON` | 16/16 artefacts, warning confiance faible | Revue humaine avant conclusion |
| `D-REEL-003` | `case_pilote_reel_003` | `A_REVOIR` | Stop après compliance, 14/16 artefacts | Correction obligatoire avant rédaction |

## Blocages et warnings
| Dossier | Type | Signal | Action attendue |
|---|---|---|---|
| `D-REEL-002` | Warning | `W001: confiance faible` | Maintenir en brouillon et demander validation humaine |
| `D-REEL-003` | Blocage | `B003: vente comparable future vs date_reference` | Corriger la vente ou la date de référence |
| `D-REEL-003` | Contrat | `CONF005: comparable[2] hors fenetre temporelle` | Retirer/remplacer le comparable hors fenêtre |
| `D-REEL-003` | Warning | `W002: comparable eloigne` | Justifier l'usage ou remplacer par comparable plus proche |

## Preuve de complétude
| Cas | Artefacts attendus | Artefacts produits | Artefacts manquants |
|---|---:|---:|---|
| `case_pilote_reel_001` | 16 | 16 | Aucun |
| `case_pilote_reel_002` | 16 | 16 | Aucun |
| `case_pilote_reel_003` | 16 | 14 | `redaction.brouillon_rapport.md`, `redaction.annexe_sources.md` |

L'absence des artefacts de rédaction pour `case_pilote_reel_003` est cohérente avec le stop compliance sur statut `A_REVOIR`.

## Comparaison IA vs évaluateur
Statut actuel: **à produire**.

Le run fournit les artefacts et les décisions runtime, mais la comparaison signée avec un évaluateur humain n'est pas encore versionnée. Elle reste requise pour clore P0-02.

## Décision Phase C
Décision: **GO CONDITIONNEL**.

Raisons:
- le run E2E local démontre les trois chemins attendus: clean, brouillon, stop bloquant;
- les audits JSONL et artefacts par étape sont générés;
- la commande stricte échoue sur une erreur contrat d'un cas négatif, ce qui doit être clarifié avant automatisation P0-02;
- le branchement reste local déterministe, pas encore Aston natif.

## Actions suivantes
1. Clarifier le contrat de succès de P0-02: un cas négatif `A_REVOIR` doit-il compter comme succès de garde-fou ou échec global ?
2. Ajouter un rapport comparatif IA vs évaluateur pour `D-REEL-001`.
3. Brancher un wrapper documentaire réel pour remplacer au moins une entrée fixture.
4. Préparer le passage Phase D seulement après preuve session/artifact/event persistée hors dossier local.
