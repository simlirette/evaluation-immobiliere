# Sous-plan Phase L — Hypercare et amélioration continue

## 1. Objectif phase
Stabiliser l'usage réel, traiter les retours terrain, et préparer la feuille de route v2.

## 2. Pré-requis
- Production active
- Canary élargi

## 3. Tâches détaillées (orientées exécution rapide)
- Mettre en place cellule hypercare (support rapide incidents critiques).
- Classer retours bureaux d'évaluateurs en correctifs court terme vs roadmap.
- Piloter métriques d'adoption et de satisfaction utilisateur.
- Basculer en mode run standard avec gouvernance produit trimestrielle.

## 4. Livrables
- Documents et artefacts attendus:
  - `PLAN-HYPERCARE-V1.md`
  - `BACKLOG-AMELIORATION-V2.md`
  - `RAPPORT-ADOPTION-V1.md`

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
