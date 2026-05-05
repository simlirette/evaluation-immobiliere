# MATRICE TRACABILITE UI V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Relier les éléments affichés dans l'interface évaluateur aux sources runtime, contrats API et preuves persistées.

## Matrice
| Élément UI | Source API/fichier | Champ clé | Preuve d'audit |
|---|---|---|---|
| File de revue | `/ops/review_queue` | `id`, `priority`, `dossier_id`, `target` | `FILE-REVUE-HUMAINE-V0.csv` |
| Sélection dossier | `/fixtures` | `dossier_id`, `name` | fixture `case_pilote_reel_*.json` |
| Ouverture dossier | `/start` | `session_id`, `run_id`, `status` | `session.json`, `result.json` |
| Statut session | `/status` | `integrity.ok`, `events_count` | validation event→artefact |
| Artefacts | `/artifacts` | `event_id`, `step`, `artifact`, `sha256` | `artifact_index.json` |
| Événements | `/stream` | `event_id`, `sequence`, `session_id`, `run_id` | `events.jsonl` |
| Décision humaine | `/review` | `decision`, `reviewer`, `notes` | `review.json` |
| Campagne revue | `/review/campaign` | `reviews_count`, `decision_counts`, `ready_for_package_count` | `runtime_sessions/*/review.json` |
| Paquet V1 session | `/review/package` | `session_package_v1`, `package_origin`, `external_evaluator_responses_included` | `runtime_sessions/*/package_v1/DEMO-MANIFEST-V1.json` |
| Reprise | `/resume` | `RESUME_READY` / `RESUME_BLOCKED` | `resume.json` |

## Couverture des items Phase E
| Besoin Phase E | Couverture actuelle | Écart |
|---|---|---|
| File dossiers | Couvert par `/ops/review_queue` et table UI | Filtrage avancé à ajouter |
| Vue comparables | Partiel via artefacts indexés | Vue métier dédiée à créer |
| Vue approches de valeur | Partiel via artefacts indexés | Comparaison méthodes et écarts à créer |
| Conformité | Partiel via statut et items P1/P2 | Vue anomalies/recommandations à créer |
| Validation finale | Couvert par `/review` | Justification obligatoire à durcir |
| Historique auditable | Couvert par `review.json`, `events.jsonl`, `resume.json`, `/review/campaign` | Registre central long terme a brancher si necessaire |

## Invariants
- Aucune décision UI ne doit être enregistrée sans `session_id`.
- Aucun artefact affiché ne doit être considéré valide sans `event_id` source.
- Une session avec `integrity.ok=false` ne doit pas être validée.
- Les P1 non résolus bloquent la validation finale.

## Tests et preuves
| Preuve | Résultat |
|---|---|
| Route `/review/ui` | Testée via `test_ops_http_endpoints_read_runtime_reports` |
| Fichier UI | Testé via `test_evaluator_ui_file_exists` |
| File revue | 16 items générés |
| Suite complète | 186 tests OK après ajout du registre de campagne |

## Prochain durcissement
- Registre `review_campaign_v1` disponible via `/review/campaign`; un stockage central long terme reste optionnel.
- Ajouter validation API: notes obligatoires pour `A_CORRIGER`, `REJETE`, et overrides P1.
- Ajouter liens directs vers contenu artefact filtré par type.
