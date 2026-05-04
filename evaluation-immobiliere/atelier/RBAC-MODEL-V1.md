# RBAC MODEL V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Définir le modèle RBAC minimal Phase F pour séparer les responsabilités évaluateur, ops et superviseur.

## Activation
Le RBAC est activé uniquement si `EVAL_RUNTIME_API_TOKEN` est présent dans l'environnement.

Headers acceptés:
- `Authorization: Bearer <token>`;
- `X-API-Key: <token>`;
- `X-Runtime-Role: evaluator|ops|supervisor`.

Sans `EVAL_RUNTIME_API_TOKEN`, l'API reste en mode `local_dev` pour conserver l'usage local et les tests existants.

## Rôles
| Rôle | Permissions | Usage |
|---|---|---|
| `evaluator` | `runtime_read`, `runtime_write`, `review_write` | Ouvrir un dossier, lire artefacts/stream, enregistrer une décision |
| `ops` | `runtime_read`, `ops_read`, `ops_write` | Lire cockpit ops, lancer chaîne pré-réponses, vérifier rapports |
| `supervisor` | Toutes permissions | Supervision, arbitrage et opérations sensibles |
| `local_dev` | Toutes permissions si auth désactivée | Développement local uniquement |

## Matrice routes
| Route | Permission | Public si auth active |
|---|---|---|
| `GET /health` | Aucune | Oui |
| `GET /`, `/product`, `/ui`, `/ops/ui`, `/review/ui`, `/auth/client.js` | Aucune | Oui |
| `GET /auth/status` | Aucune | Oui |
| `GET /product/summary` | `runtime_read` | Non |
| `POST /product/demo` | `runtime_write` | Non |
| `GET /fixtures` | `runtime_read` | Non |
| `POST /session` | `runtime_write` | Non |
| `POST /start` | `runtime_write` | Non |
| `GET /session` | `runtime_read` | Non |
| `GET /status` | `runtime_read` | Non |
| `GET /artifacts` | `runtime_read` | Non |
| `GET /artifact` | `runtime_read` | Non |
| `GET /review/dossier` | `runtime_read` | Non |
| `GET /stream` | `runtime_read` | Non |
| `POST /review` | `review_write` | Non |
| `POST /resume` | `runtime_write` | Non |
| `GET /ops`, `/ops/snapshot`, `/ops/*` | `ops_read` | Non |
| `POST /ops/pre-response-run` | `ops_write` | Non |

## Comportements d'erreur
| Cas | HTTP | Code |
|---|---:|---|
| Token absent | 401 | `token_missing` |
| Token invalide | 401 | `token_invalid` |
| Rôle invalide | 401 | `role_invalid` |
| Permission refusée | 403 | `RBAC_FORBIDDEN` |

## Journalisation
Chaque réponse écrit une ligne JSONL avec:
- `timestamp_utc`;
- `method`;
- `path`;
- `status`;
- `auth_enabled`;
- `role`;
- `reason`;
- `client`.

Le journal ne contient pas de payload métier ni de token.

## Décisions prises
- Garder l'auth opt-in tant qu'il n'y a pas d'IAM/proxy réel.
- Séparer `ops_write` de `review_write` afin qu'un évaluateur ne puisse pas relancer la chaîne ops.
- Ne jamais versionner `runtime_sessions/access_audit.jsonl`.

## Questions ouvertes
- Quel IdP/IAM portera les rôles en staging/prod ?
- Faut-il distinguer `evaluator` et `lead_evaluator` pour les overrides P1 ?
- Quel format de signature électronique est attendu pour `VALIDE` ?
