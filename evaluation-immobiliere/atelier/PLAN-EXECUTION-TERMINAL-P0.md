# PLAN EXECUTION TERMINAL P0

## Objectif
Plan prêt à lancer pour exécuter les commandes lourdes P0 avec ordre, prérequis, signaux d'échec et fallback.

## Prérequis globaux
- Python 3.11+ et dépendances projet installées.
- Variables runtime/secrets Aston injectées hors repo.
- Accès aux sources de données externes si run réel P0-02.
- Espace disque suffisant pour `tests/runtime/` et `tests/reports/`.

## Ordonnancement des commandes (issu du handoff)
| Ordre | Ticket P0 lié | Commande | Owner | Sortie attendue | Signal d’échec | Fallback |
|---|---|---|---|---|---|---|
| 1 | P0-01 | `python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py` | Lead Runtime | Cohérence runtime validée | Incohérence structurelle runtime | Corriger fixtures/contrats puis rerun |
| 2 | P0-01 | `python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py` | Lead Runtime | Simulation bout-en-bout sans blocage | Exception pipeline/artefact manquant | Isoler étape fautive via logs |
| 3 | P0-03 | `python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py` | Lead Plateforme | Rapport intégrité généré | Trou event→artefact | Rejouer run avec audit renforcé |
| 4 | P0-01 | `python evaluation-immobiliere/outils/analyser_qualite_runtime_v0.py` | QA Runtime | Rapport qualité/scoring généré | Score sous seuil Go | Basculer revue humaine et recalibrer |
| 5 | P0-01/P0-04 | `python -m unittest evaluation-immobiliere/tests/test_runtime_v0.py evaluation-immobiliere/tests/test_api_v0.py evaluation-immobiliere/tests/test_ops_professional_gates_v0.py` | QA Runtime | Baseline tests pass | Régression API/runtime/ops | Bloquer homologation, rollback code |
| 6 | P0-02 | `python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py` | Lead Intégration | Run E2E réel et audit JSONL | Données réelles indisponibles | Replanifier fenêtre + run anonymisé |
| 7 | P0-02 | `python evaluation-immobiliere/outils/generer_rapport_pilote_runtime_v0.py` | Lead Intégration | Rapport pilote runtime | Rapport incomplet | Vérifier artefacts du run 6 |
| 8 | P0-03/P0-04 | `python evaluation-immobiliere/outils/preparer_handoff_ops_v0.py` | Lead Plateforme | Manifest handoff ops final | Manifest invalide | Revalider schémas ops + régénérer |

## Notes d’exécution
- Stop immédiat si signal d’échec critique rencontré avant l’étape 6.
- Ne pas poursuivre homologation si étape 5 échoue.
- Hypercare (P0-05 post-homologation) démarre seulement après handoff ops valide.

## Décisions prises
- L’ordre suit `HANDOFF-TERMINAL-CHECKLIST.md` pour minimiser les faux diagnostics.
- Les commandes sont mappées explicitement aux tickets P0 pour pilotage owner/reviewer.
- Les fallbacks restent conservateurs pour préserver la traçabilité runtime.

## Questions ouvertes
- Souhaite-t-on un pipeline unique automatisé ou une exécution manuelle par étape pour la première homologation ?
- Quel SLA de résolution applique-t-on si une étape critique échoue pendant hypercare ?
