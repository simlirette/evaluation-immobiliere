# HANDOFF TERMINAL CHECKLIST (runtime réel / tests lourds)

## Prérequis environnement
- Python 3.11+ et dépendances projet installées.
- Accès aux sources de données externes (si activées).
- Variables d’environnement sécurité (secrets/token) injectées hors repo.
- Espace disque pour artefacts runtime/reports.

## Commandes uniques à exécuter (ordre recommandé)
1. `python evaluation-immobiliere/outils/verifier_coherence_runtime_v0.py`
2. `python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py`
3. `python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py`
4. `python evaluation-immobiliere/outils/analyser_qualite_runtime_v0.py`
5. `python -m unittest evaluation-immobiliere/tests/test_runtime_v0.py evaluation-immobiliere/tests/test_api_v0.py evaluation-immobiliere/tests/test_ops_professional_gates_v0.py`
6. `python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py` *(si données réelles disponibles)*
7. `python evaluation-immobiliere/outils/generer_rapport_pilote_runtime_v0.py`
8. `python evaluation-immobiliere/outils/preparer_handoff_ops_v0.py`

## Résultats attendus
- Rapports runtime générés sans erreur bloquante.
- Statuts qualité/cohérence/contrats compatibles Go phase courante.
- Artefacts handoff exploitables (manifest, delta, résumé).

## Signaux d’échec (stop immédiat)
- Échec schéma/contrat sur artefact critique.
- Incohérence unité/sources sur dossier nominal.
- Session runtime non reproductible sur même fixture.
- Régression des tests API/runtime/ops.

## Décisions prises
- Centraliser les commandes terminal dans un seul document pour futures sessions lourdes.
- Mettre les tests “réels” après les checks v0 pour diagnostiquer plus vite.

## Questions ouvertes
- Liste finale des variables d’environnement requises par runtime Aston réel? **À valider**.
- Seuil d’arrêt automatique (ex: % échecs) à implémenter dans CI? **À valider**.
