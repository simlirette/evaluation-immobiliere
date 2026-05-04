# SECURITY BASELINE V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Activer une baseline sécurité minimale pour l'API/runtime avant homologation client: RBAC, secrets hors repo, journal d'accès, audit infra et rétention.

## Statut Phase F
Décision actuelle: **GO CONDITIONNEL**.

La baseline est active en mode local avec sécurité opt-in:
- authentification activée si `EVAL_RUNTIME_API_TOKEN` est défini;
- RBAC par rôle via `X-Runtime-Role`;
- support `Authorization: Bearer <token>` ou `X-API-Key`;
- journal d'accès JSONL dans `runtime_sessions/access_audit.jsonl`;
- routes publiques limitées aux pages UI et `/health`;
- routes données/actions protégées quand le token est actif;
- pages UI capables de fournir localement le token et le rôle via `/auth/client.js`;
- statut d'authentification consultable via `/auth/status`.

## Contrôles actifs
| Contrôle | Implémentation | Statut |
|---|---|---|
| Secrets hors repo | Token lu depuis variable d'environnement `EVAL_RUNTIME_API_TOKEN` | Actif |
| RBAC minimal | Rôles `evaluator`, `ops`, `supervisor` dans `api.py` | Actif |
| Journal d'accès | `access_audit.jsonl` écrit pour réponses JSON/fichiers/options | Actif |
| CORS explicite | Headers `Authorization`, `X-API-Key`, `X-Runtime-Role` autorisés | Actif |
| Auth UI locale | Panneau role/token sur cockpits produit, runtime, ops et revue | Actif |
| Audit infra | `valider_rapports_infra_v0.py` | OK |
| Chaîne ops complète | `executer_pre_reponses_v0.py --force-lock` | OK |
| Anonymisation | `anonymisation_audit.json` via chaîne pré-réponses | OK |

## Commandes de preuve
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' evaluation-immobiliere/outils/executer_pre_reponses_v0.py --force-lock
```

Résultat: `OK: True`, 20 étapes OK; statut ops final `EN_ATTENTE_ENTREES_TERRAIN_REELLES` tant qu'aucun dossier reel anonymise actif n'est fourni.

```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' evaluation-immobiliere/outils/valider_rapports_infra_v0.py
```

Résultat: `OK: True`, 8 fichiers vérifiés, 0 invalide.

## Tests de sécurité
| Test | Résultat |
|---|---|
| Auth désactivée en local | Flux existant conserve compatibilité |
| Token requis si `EVAL_RUNTIME_API_TOKEN` actif | Requête `/fixtures` sans token retourne 401 |
| RBAC par rôle | `evaluator` refusé sur `/ops/pre-response-run` avec 403 |
| Journal d'accès | Entrées 401/403 écrites dans `access_audit.jsonl` |
| Statut auth | `/auth/status` retourne role, permissions et autorisation |
| Suite API | 17 tests OK |

## Limites restantes
- Le token statique est une baseline locale; un fournisseur IAM externe reste requis avant production.
- Le chiffrement au repos dépend encore du poste/volume, pas d'un store applicatif.
- Le journal d'accès est fichier local, pas encore centralisé ni immuable.
- Le token UI est stocke dans `localStorage`; acceptable pour usage local/dev,
  mais a remplacer par IAM/proxy en staging/prod.

## Go/No-Go
Décision: **GO CONDITIONNEL** vers suite Phase G.

Conditions avant Go final sécurité:
- intégrer IAM/proxy réel;
- centraliser l'audit d'accès;
- définir rotation token/secrets;
- valider la rétention et suppression contrôlée des dossiers client.
