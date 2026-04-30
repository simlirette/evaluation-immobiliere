# Sous-plan Phase H — Validation métier terrain et calibration

## 1. Objectif phase
Obtenir une validation crédible par évaluateurs sur dossiers réels et calibrer les règles finales.

## 2. Pré-requis
- UI revue disponible
- Sécurité minimale active

## 3. Tâches détaillées (orientées exécution rapide)
- Conduire une campagne d'évaluation sur panel représentatif de dossiers.
- Comparer sorties IA vs avis évaluateurs et tracer les écarts.
- Ajuster règles/seuils uniquement avec justification métier explicite.
- Signer des critères d'acceptation métier (go/no-go commercial).

## 4. Livrables
- Documents et artefacts attendus:
  - `RAPPORT-CAMPAGNE-TERRAIN-V1.md`
  - `MATRICE-ECARTS-EVALUATEURS-V1.csv`
  - `CRITERES-ACCEPTATION-METIER-V1.md`

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
