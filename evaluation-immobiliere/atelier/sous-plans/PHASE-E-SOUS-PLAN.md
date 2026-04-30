# Sous-plan Phase E — Interface évaluateur professionnelle

## 1. Objectif phase
Permettre la revue humaine complète des dossiers avec justification, validation et historique auditable.

## 2. Pré-requis
- API produit stable
- File de revue opérationnelle

## 3. Tâches détaillées (orientées exécution rapide)
- Définir écrans clés: file dossiers, vue comparables, vue approches de valeur, conformité, validation finale.
- Implémenter capture obligatoire des justifications lors des overrides humains.
- Afficher provenance des données (source_index) pour chaque assertion importante.
- Ajouter statuts de workflow: brouillon, en revue, à corriger, validé, livré.

## 4. Livrables
- Documents et artefacts attendus:
  - `SPEC-UI-EVALUATEUR-V1.md`
  - `WORKFLOW-REVUE-HUMAINE-V1.md`
  - `MATRICE-TRAÇABILITE-UI-V1.md`

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
