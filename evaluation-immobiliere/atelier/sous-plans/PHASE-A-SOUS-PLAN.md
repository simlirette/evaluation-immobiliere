# Sous-plan Phase A — Baseline et cadrage d'exécution

## 1. Objectif phase
Figer la baseline technique et métier à partir du commit 85555aa, et verrouiller les indicateurs qui servent de référence de progression.

## 2. Pré-requis
- Accès au dépôt + historique git
- Rapports runtime existants générés
- Référents technique/métier identifiés

## 3. Tâches détaillées (orientées exécution rapide)
- Créer un snapshot baseline: tests pass/fail, rapports runtime, endpoints API disponibles.
- Établir une matrice “capabilité actuelle vs capabilité cible Aston”.
- Définir KPI minimaux de pilotage: taux de dossiers sans blocage, couverture contrats, taux de revue humaine.
- Formaliser critères de priorité P0/P1/P2 utilisés pour trancher les arbitrages.

## 4. Livrables
- Documents et artefacts attendus:
  - `BASELINE-85555aa.md`
  - `MATRICE-CAPABILITES-ASTON-V1.md`
  - `KPI-PILOTAGE-V1.md`

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
