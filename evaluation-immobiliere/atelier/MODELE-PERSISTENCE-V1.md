# MODELE PERSISTENCE V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Définir et commencer à implémenter le modèle de persistance Phase D pour sessions, événements, artefacts, snapshots de connaissance, revue humaine et reprise runtime.

## Statut Phase D
Décision actuelle: **GO CONDITIONNEL**.

La persistance produit est maintenant structurée dans `api.py` pour les sessions locales:
- session persistée en `runtime_sessions/<session_id>/session.json`;
- `run_id` stable par session;
- événements enrichis avec `event_id`, `sequence`, `session_id`, `run_id`;
- index d'artefacts avec taille et SHA-256;
- snapshot de connaissance par session;
- fichier de review humaine;
- fichier de reprise avec validation d'intégrité.

## Modèle de fichiers session
| Fichier | Producteur | Rôle | Criticité |
|---|---|---|---|
| `session.json` | `create_session()` / `save_session()` | État canonique session, URLs, statut runtime, chemins persistés | P0 |
| `<case>.input.json` | `start_runtime()` | Copie immuable de l'entrée dossier utilisée pour le run | P0 |
| `result.json` | `start_runtime()` | Résultat runtime complet avec événements enrichis | P0 |
| `events.jsonl` | `start_runtime()` | Event stream replayable côté API | P0 |
| `artifact_index.json` | `build_artifact_index()` | Liste artefacts écrits, bytes, checksum SHA-256, event source | P0 |
| `knowledge_snapshot.json` | `build_knowledge_snapshot()` | Résumé session pour reprise/ops/UI | P1 |
| `review.json` | `save_review()` | Décision humaine et notes de revue | P0 pour validation finale |
| `resume.json` | `resume_session()` | Preuve de reprise et intégrité event→artefact | P0 |

## Champs minimaux session
| Champ | Description |
|---|---|
| `schema_version` | `runtime_session_v1` |
| `session_id` | Identifiant court de session |
| `run_id` | Identifiant de run sous forme `run_<timestamp>_<session_id>` |
| `strict_mode` | Active les garde-fous runtime stricts |
| `status` | `CREATED`, `PRET_REVISION_FINALE`, `BROUILLON`, `A_REVOIR`, etc. |
| `created_at_utc` / `updated_at_utc` | Horodatage session |
| `events_path` | Source du stream SSE |
| `artifact_index_path` | Source de vérité artefacts persistés |
| `knowledge_snapshot_path` | Résumé pour reprise et UI |
| `resume_status` | `RESUME_READY` ou `RESUME_BLOCKED` après reprise |

## Contrat d'intégrité
La reprise est considérée valide si:
- `events.jsonl` existe et contient des événements;
- chaque événement contient `event_id`, `session_id`, `run_id`, `sequence`, `event`;
- chaque événement référence le bon `session_id` et le bon `run_id`;
- aucun `event_id` n'est dupliqué;
- chaque événement `artifact_written` pointe vers un fichier existant;
- chaque artefact indexé référence un événement existant;
- aucun artefact indexé n'est marqué absent.

## Preuve Phase D exécutée
| Vérification | Résultat |
|---|---|
| Tests API/runtime ciblés | 18 tests OK |
| Suite unittest complète | 107 tests OK |
| Commande registry Phase D | `generer_registry_runtime_v0.py` OK |
| Runs registry après génération | 5 |
| Reprise session testée | `RESUME_READY` |

## Limites restantes
- La persistance reste locale fichier, pas encore stockage central Aston.
- Les ACL, migrations, rétention et chiffrement au repos ne sont pas encore implémentés.
- La reprise valide l'intégrité et recharge l'état, mais ne rejoue pas encore automatiquement une étape interrompue.
- Le stream SSE est replayable depuis `events.jsonl`; il n'est pas encore live pendant l'exécution d'un long run.

## Décisions prises
- Garder `runtime_sessions/` ignoré par git et versionner seulement les contrats/preuves dans `atelier/`.
- Utiliser SHA-256 dans l'index artefacts pour préparer checksum obligatoire du contrat Aston V1.
- Séparer `review.json` et `resume.json` pour rendre les décisions humaines et techniques auditables indépendamment.

## Questions ouvertes
- Quelle base ou stockage objet deviendra la source de vérité des sessions Aston ?
- Quel niveau de replay automatique est requis pour une reprise après crash en production ?
- Qui possède la politique de rétention des sessions et artefacts client ?
