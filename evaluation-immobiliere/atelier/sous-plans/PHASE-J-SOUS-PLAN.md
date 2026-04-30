# Sous-plan Phase J — Pré-production et homologation

## 1. Objectif phase
Vérifier en environnement pré-prod que le système est exploitable, sûr et acceptable métier.

## 2. Pré-requis
- CI/CD actif
- Observabilité + sécurité en place

## 3. Tâches détaillées (orientées exécution rapide)
- Réaliser un dress rehearsal complet avec incidents simulés.
- Exécuter tests de charge, tests reprise et tests conformité.
- Clôturer écarts bloquants avant décision Go/No-Go.
- Formaliser procès-verbal d'homologation multi-parties.

## 4. Livrables
- Documents et artefacts attendus:
  - `RAPPORT-DRESS-REHEARSAL-V1.md`
  - `PV-HOMOLOGATION-V1.md`
  - `REGISTRE-ECARTS-PREPROD-V1.md`

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
