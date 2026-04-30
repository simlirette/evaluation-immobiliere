# Sous-plan Phase K — Déploiement production

## 1. Objectif phase
Déployer de façon progressive et contrôlée, avec capacité de retour arrière immédiat.

## 2. Pré-requis
- Homologation signée
- Plan support prêt

## 3. Tâches détaillées (orientées exécution rapide)
- Déployer canary sur périmètre limité de dossiers/équipes.
- Surveiller indicateurs critiques (qualité, latence, erreurs, sécurité).
- Activer playbooks incident + rollback instantané si seuil dépassé.
- Étendre progressivement le périmètre après validation stabilité.

## 4. Livrables
- Documents et artefacts attendus:
  - `PLAN-DEPLOIEMENT-CANARY-V1.md`
  - `TABLEAU-BORD-PROD-V1.md`
  - `RAPPORT-STABILISATION-J7.md`

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
