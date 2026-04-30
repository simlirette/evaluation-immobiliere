# PLAN EXECUTION TERMINAL P0

_As-of date: 2026-04-30 (UTC)_

## Objectif
Plan prêt à lancer pour exécuter les commandes lourdes P0 avec ordre, prérequis, owner, sortie attendue, signal d’échec et fallback.

## Prérequis globaux
- Python 3.11+ et dépendances projet installées.
- Variables runtime/secrets Aston injectées hors repo.
- Accès aux sources externes pour P0-02.
- Espace disque suffisant pour `tests/runtime/` et `tests/reports/`.

## Ordonnancement des commandes (issu du handoff)
| Ordre | Ticket P0 lié | Commande | Owner | Sortie attendue | Signal d’échec | Fallback |
|---|---|---|---|---|---|---|
| 1 | P0-01 | `python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py` | Lead Runtime | Cohérence runtime validée | Incohérence structurelle runtime | Corriger fixtures/contrats puis rerun |
| 2 | P0-01 | `python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py` | Lead Runtime | Simulation E2E sans blocage | Exception pipeline | Isoler étape fautive via logs |
| 3 | P0-03 | `python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py` | Lead Plateforme | Rapport intégrité généré | Trou event→artefact | Rejouer run avec audit renforcé |
| 4 | P0-01 | `python evaluation-immobiliere/outils/analyser_qualite_runtime_v0.py` | QA Runtime | Rapport qualité/scoring généré | Score sous seuil Go | Revue humaine + recalibration |
| 5 | P0-01/P0-04 | `python -m unittest evaluation-immobiliere/tests/test_runtime_v0.py evaluation-immobiliere/tests/test_api_v0.py evaluation-immobiliere/tests/test_ops_professional_gates_v0.py` | QA Runtime | Baseline tests pass | Régression API/runtime/ops | Bloquer homologation |
| 6 | P0-02 | `python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py` | Lead Intégration | Run E2E réel + audit JSONL | Données indisponibles | Replanifier fenêtre + run anonymisé |
| 7 | P0-02 | `python evaluation-immobiliere/outils/generer_rapport_pilote_runtime_v0.py` | Lead Intégration | Rapport pilote runtime | Rapport incomplet | Vérifier artefacts run 6 |
| 8 | P0-03/P0-04 | `python evaluation-immobiliere/outils/preparer_handoff_ops_v0.py` | Lead Plateforme | Manifest handoff ops final | Manifest invalide | Revalider schémas ops |

## Template Go/No-Go post-run
- Run ID:
- Date/heure UTC:
- Owner run:
- Résultat commandes 1→8: PASS/FAIL
- Scoring global et statut homologation:
- Décision finale: GO / GO CONDITIONNEL / NO-GO
- Actions hypercare J+7:

## Décisions prises
- Mode d’exécution initial: manuel étape par étape pour la première homologation.
- SLA hypercare critique: 4h accusé / 24h plan / 72h résolution ou rollback.

## Questions ouvertes
- Aucune question bloquante web; lancement terminal requis pour clôture P0.
