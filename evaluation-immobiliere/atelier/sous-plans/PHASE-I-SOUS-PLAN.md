# Sous-plan Phase I — Industrialisation CI/CD et environnements

## 1. Objectif phase
Automatiser build/test/release avec environnements dev/staging/prod et gates bloquants.

## 2. Pré-requis
- Tests critiques définis
- Artefacts versionnés

## 3. Tâches détaillées (orientées exécution rapide)
- Créer pipeline CI: tests unitaires/intégration/contrats/sécurité/docs.
- Créer pipeline CD avec promotions contrôlées et approbations.
- Implémenter stratégie de rollback version applicative et contrats.
- Versionner migrations et compatibilité des données de session.

## 4. Livrables
- Documents et artefacts attendus:
  - `PIPELINE-CI-V1.md`
  - `PIPELINE-CD-V1.md`
  - `RUNBOOK-ROLLBACK-V1.md`

## 5. Tests / validation
- Vérifier que les livrables sont produits et exploitables.
- Exécuter la suite de tests pertinente à la phase (runtime/ops/API/UI/sécurité).
- Valider les critères de passage en revue croisée technique + métier.

## 6. Risques et mitigation
- **Dépendance externe**: source de données ou outil indisponible.
  - *Mitigation*: fallback documenté + re-run contrôlé.
- **Risque qualité**: outputs techniquement valides mais métier insuffisants.
  - *Mitigation*: revue évaluateur systématique sur échantillon critique.
- **Risque délai**: dérive de périmètre.
  - *Mitigation*: arbitrage strict P0/P1/P2 à chaque gate.

## 7. Critères de done
- Objectif de phase atteint sur cas de référence définis.
- Livrables versionnés et relus.
- Aucun blocage critique ouvert pour la phase suivante.
- Décision formelle Go/No-Go de fin de phase.

## 8. Estimation charge / délai
- Estimation macro conforme au plan directeur (à ajuster selon capacité équipe).
- Charge pilotée par priorité P0 puis P1; P2 seulement si capacité restante.
