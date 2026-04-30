# API PRODUIT CONTRATS V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Versionner le contrat API produit Phase D pour démarrer, suivre, streamer, relire, revoir et reprendre une session runtime.

## Endpoints disponibles
| Méthode | Route | Entrée | Sortie | Statut Phase D |
|---|---|---|---|---|
| `GET` | `/health` | Aucun | `{ "status": "ok" }` | Existant |
| `GET` | `/fixtures` | Aucun | Liste fixtures disponibles | Existant |
| `POST` | `/session` | `{ "strict_mode": true }` | Session créée | Existant enrichi |
| `POST` | `/start` | `{ "fixture": "case_nominal.json" }` ou `{ "case": {...} }` | Session + résultat runtime | Existant enrichi |
| `GET` | `/session?session_id=...` | `session_id` | État session persisté | Nouveau Phase D |
| `GET` | `/status?session_id=...` | `session_id` | Session + intégrité | Nouveau Phase D |
| `GET` | `/stream?session_id=...` | `session_id` | SSE depuis `events.jsonl` | Existant enrichi |
| `GET` | `/artifacts?session_id=...` | `session_id` | `artifact_index_v1` | Nouveau Phase D |
| `POST` | `/review` | `session_id`, `decision`, `reviewer`, `notes` | Review persistée | Nouveau Phase D |
| `POST` | `/resume` | `session_id` | Résultat reprise + intégrité | Nouveau Phase D |

## Contrat `/start`
### Requête fixture
```json
{
  "fixture": "case_nominal.json",
  "strict_mode": true
}
```

### Requête case inline
```json
{
  "case": {
    "dossier_id": "D-001",
    "date_reference": "2026-04-28",
    "comparables": [],
    "ajustements": [],
    "confidence": 0.85
  },
  "source_fixture": "inline"
}
```

### Sortie minimale
```json
{
  "session": {
    "schema_version": "runtime_session_v1",
    "session_id": "...",
    "run_id": "run_...",
    "status": "PRET_REVISION_FINALE",
    "events_path": ".../events.jsonl",
    "artifact_index_path": ".../artifact_index.json",
    "knowledge_snapshot_path": ".../knowledge_snapshot.json"
  },
  "result": {
    "dossier_id": "D-001",
    "status": "PRET_REVISION_FINALE",
    "events": []
  }
}
```

## Contrat événement streamable
Chaque événement persisté doit contenir:
| Champ | Rôle |
|---|---|
| `event_id` | Identifiant unique et stable dans le run |
| `sequence` | Ordre strict de replay |
| `session_id` | Corrélation session |
| `run_id` | Corrélation run |
| `event` | Type (`step_start`, `artifact_written`, `step_done`, etc.) |
| `step` | Étape runtime ou `session` |
| `artifact` | Nom artefact si applicable |
| `artifact_path` | Chemin artefact pour `artifact_written` |

## Contrat `/artifacts`
Sortie: `artifact_index_v1`.

Chaque artefact contient:
- `event_id`;
- `step`;
- `artifact`;
- `path`;
- `exists`;
- `bytes`;
- `sha256`.

## Contrat `/review`
La review produit `review.json`.

Champs:
- `session_id`;
- `run_id`;
- `decision`;
- `reviewer`;
- `notes`;
- `created_at_utc`.

## Contrat `/resume`
La reprise produit `resume.json` et ne modifie pas le statut métier du runtime. Elle ajoute seulement un état technique:
- `RESUME_READY` si l'intégrité persistance/event/artifact est valide;
- `RESUME_BLOCKED` si un fichier, event ou lien artefact est incohérent.

## Codes d'erreur
| Cas | HTTP | Code logique |
|---|---:|---|
| Session absente | 400 actuellement | `SESSION_NOT_FOUND` à formaliser |
| Fixture absente | 404 | `FIXTURE_NOT_FOUND` |
| JSON invalide | 500 actuellement | `INVALID_JSON` à formaliser |
| Pré-réponse verrouillée | 409 | `PRE_RESPONSE_RUN_LOCKED` |

## Décisions prises
- Les endpoints Phase D restent compatibles avec les routes existantes `/session`, `/start`, `/stream`.
- Les nouveaux endpoints utilisent `session_id` comme clé unique côté produit.
- L'index d'artefacts expose les checksums, mais pas le contenu brut des fichiers pour l'instant.

## Questions ouvertes
- Faut-il exposer un endpoint de téléchargement d'artefact par identifiant plutôt que par chemin ?
- Faut-il normaliser les erreurs HTTP avant Phase E UI évaluateur ?
- Le stream doit-il devenir live pendant exécution ou rester replayable tant que les runs sont courts ?
