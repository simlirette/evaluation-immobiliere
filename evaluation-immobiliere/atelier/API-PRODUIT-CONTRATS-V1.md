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

## Contrat `/session/summary`
Sortie: `session_summary_v1`.

Le resume consolide la session, le resultat runtime, l'integrite,
la review persistante, le snapshot knowledge et l'index d'artefacts.
Il alimente l'UI produit/revue sans recalcul cote navigateur.

## Contrat `/artifact`
Sortie: `session_artifact_content_v1`.

Contraintes:
- l'artefact doit etre present dans `artifact_index_v1`;
- la lecture est resolue sous le repertoire de session uniquement;
- le contenu est renvoye en texte avec detection JSON/Markdown;
- l'apercu est plafonne a 64 KiB et signale par `truncated`.

## Contrat `/review/dossier`
Sortie: `dossier_review_summary_v1`.

La synthese dossier agrege les artefacts indexes de session:
- `data-facts.fiche_bien.json` pour les faits de base;
- `comps-market.comparables_proposes.json` pour les comparables;
- `valuation-draft.calculs_approche_*.json` pour les valeurs;
- `compliance-qa.statut_sortie.json` pour les warnings/blocages;
- `redaction.brouillon_rapport.md` pour l'apercu rapport.

Elle signale les artefacts requis manquants dans `coverage.missing`.

## Contrat `/review`
La review produit `review.json`.

Champs:
- `session_id`;
- `run_id`;
- `decision`;
- `reviewer`;
- `notes`;
- `created_at_utc`.

Validation minimale:
- `decision` doit etre dans `PRET_REVUE`, `A_CORRIGER`, `VALIDE`, `REJETE`;
- `reviewer` est obligatoire;
- `notes` est obligatoire pour `A_CORRIGER`, `VALIDE` et `REJETE`;
- `VALIDE` est refuse si l'integrite session est invalide ou si le runtime
  contient des blocages.

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
- L'index d'artefacts expose les checksums; le contenu est accessible via
  `/artifact` seulement pour les fichiers indexes dans la session.

## Questions ouvertes
- Faut-il normaliser les erreurs HTTP avant Phase E UI évaluateur ?
- Le stream doit-il devenir live pendant exécution ou rester replayable tant que les runs sont courts ?
