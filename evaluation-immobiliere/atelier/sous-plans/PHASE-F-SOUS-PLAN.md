# Sous-plan Phase F — Sécurité, conformité, gouvernance

## 1. Objectif phase
Atteindre un niveau de sécurité et gouvernance compatible avec un usage professionnel et sensible.

## 2. Pré-requis
- Flux API/UI définis
- Données sensibles identifiées

## 3. Tâches détaillées (orientées exécution rapide)
- Mettre en place RBAC minimum (ops, évaluateur, superviseur).
- Gérer secrets et rotation; interdire hardcoding.
- Activer chiffrement transit/repos et politique de rétention.
- Établir journal d'accès et procédure d'audit de conformité.

## 4. Livrables
- Documents et artefacts attendus:
  - `SECURITY-BASELINE-V1.md`
  - `RBAC-MODEL-V1.md`
  - `POLITIQUE-RETENTION-AUDIT-V1.md`

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
