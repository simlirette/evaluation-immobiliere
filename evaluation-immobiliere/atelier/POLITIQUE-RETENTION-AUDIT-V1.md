# POLITIQUE RETENTION AUDIT V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Définir la politique Phase F de rétention, audit et suppression contrôlée des sessions, artefacts et journaux.

## Classification des données
| Catégorie | Exemples | Sensibilité | Rétention cible |
|---|---|---|---|
| Entrées dossier | `<case>.input.json`, documents sources anonymisés | Élevée | Durée projet pilote + purge contrôlée |
| Artefacts runtime | JSON/Markdown par étape | Élevée | Même durée que dossier |
| Événements | `events.jsonl`, stream SSE | Moyenne à élevée | Durée dossier + audit |
| Reviews humaines | `review.json`, décisions évaluateur | Élevée | Durée dossier + obligations métier |
| Journaux accès | `access_audit.jsonl` | Moyenne | 90 jours minimum en pilote |
| Rapports ops | `runtime_pilotes_reels/*.json`, rapports Markdown | Moyenne | Versionner seulement synthèses dans `atelier/` |

## Règles
1. Aucun secret ne doit être écrit dans le repo, les rapports ou les journaux.
2. Les tokens doivent provenir de variables d'environnement ou d'un gestionnaire de secrets.
3. Les dossiers runtime locaux restent ignorés par git.
4. Toute validation client doit conserver `session_id`, `run_id`, `reviewer`, `decision`, `created_at_utc`.
5. Toute suppression doit conserver un événement d'audit de suppression dans le système cible.

## Audit d'accès
Chemin local actuel: `evaluation-immobiliere/runtime_sessions/access_audit.jsonl`.

Champs permis:
- timestamp;
- méthode;
- route;
- statut HTTP;
- rôle;
- mode auth activé/désactivé;
- raison auth/RBAC;
- client.

Champs interdits:
- token;
- payload dossier;
- contenu artefact;
- note complète d'évaluateur;
- chemin local sensible hors workspace.

## Rétention Phase F
| Donnée | Action Phase F | Action cible production |
|---|---|---|
| `runtime_sessions/` | Ignoré git, purge manuelle contrôlée | TTL automatisé par environnement |
| `runtime_pilotes_reels/` | Ignoré git, régénérable par scripts | Store artefacts avec cycle de vie |
| `access_audit.jsonl` | Append-only local | Journal central immuable |
| Synthèses `atelier/` | Versionnées | Archivage projet/homologation |

## Validation
| Preuve | Résultat |
|---|---|
| Chaîne pré-réponses | 18 étapes OK |
| Contrats infra | 8/8 OK |
| Tests API sécurité | 11 tests OK |
| Anonymisation pré-envoi | Rapport généré par chaîne ops |

## Go/No-Go
Décision: **GO CONDITIONNEL**.

Raisons:
- baseline active et testée;
- aucun écart critique infra après régénération complète;
- rétention et audit définis;
- production nécessite encore IAM, journal central et purge automatisée.
