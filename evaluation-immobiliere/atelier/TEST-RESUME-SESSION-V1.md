# TEST RESUME SESSION V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Documenter la preuve Phase D/P0-03 de reprise session avec intégrité event→artefact.

## Scénario testé
Given une session runtime créée depuis `case_nominal.json`, When le run termine et que la reprise est demandée, Then:
- la session peut être rechargée depuis `session.json`;
- `events.jsonl` est replayable;
- chaque événement est corrélé à `session_id` et `run_id`;
- chaque artefact écrit est indexé avec SHA-256;
- la validation d'intégrité retourne `ok=true`;
- `/resume` retourne `RESUME_READY`.

## Tests automatisés ajoutés
| Test | Preuve |
|---|---|
| `test_start_runtime_persists_resumeable_session_state` | Vérifie `artifact_index.json`, `knowledge_snapshot.json`, event IDs, intégrité et `RESUME_READY` |
| `test_session_http_status_artifacts_review_and_resume_endpoints` | Vérifie `/status`, `/artifacts`, `/review`, `/resume` via HTTP local |

## Commande exécutée
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' -m unittest evaluation-immobiliere/tests/test_api_v0.py evaluation-immobiliere/tests/test_runtime_v0.py
```

Résultat: **18 tests OK**.

## Suite complète
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' -m unittest discover -s evaluation-immobiliere/tests -p 'test_*.py'
```

Résultat: **107 tests OK**.

## Commande registry Phase D
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' evaluation-immobiliere/outils/generer_registry_runtime_v0.py
```

Résultat:
- `runtime_registry.json` généré;
- `RUNTIME-REGISTRY-V0.md` généré;
- `Runs: 5`.

## Résultat Go/No-Go Phase D
Décision: **GO CONDITIONNEL**.

Critères satisfaits:
- sessions persistées;
- événements enrichis et streamables;
- artefacts indexés avec checksum;
- review et reprise persistées;
- validation event→artefact testée.

Conditions avant Go final:
- remplacer le stockage local par une persistance centrale Aston;
- ajouter replay/reprise d'étape interrompue, pas seulement validation de reprise;
- normaliser erreurs HTTP et contrats de réponse;
- définir rétention et sécurité d'accès aux artefacts.
