# Persistence et streaming cible type Aston

## Objectif

Decrire le pont entre le runtime actuel et une future execution dans un engine
type Aston avec sessions, persistence et streaming.

## Session

Champs minimum:

- `session_id`
- `dossier_id`
- `runtime_version`
- `pipeline_version`
- `status`
- `created_at_utc`
- `updated_at_utc`
- `artifact_dir`
- `manifest_fingerprint`

## Evenements stream

Types minimum:

- `session_started`
- `step_start`
- `artifact_written`
- `contract_invalid`
- `warning_detected`
- `blocking_detected`
- `human_review_required`
- `session_done`

## Persistence

Tables ou collections cible:

- `sessions`
- `artifacts`
- `audit_events`
- `knowledge_snapshots`
- `human_review_items`
- `calibration_responses`

## Regles

- Le stream expose des evenements, pas les fichiers complets.
- Les artefacts restent source de verite.
- `knowledge_snapshots` est reconstructible depuis artefacts + manifest.
- Les decisions humaines sont append-only.
- Les corrections automatiques ne modifient pas une decision evaluateur.

## Done

- Un dossier peut etre execute avec progression visible.
- Chaque artefact a un hash et un chemin.
- La file humaine est consultable depuis la session.
- Le manifest final scelle la session.

