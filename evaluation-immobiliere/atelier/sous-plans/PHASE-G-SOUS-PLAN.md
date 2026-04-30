# Sous-plan Phase G — Performance, fiabilité, coût

## 1. Objectif phase
Rendre le système stable et économiquement soutenable en charge réaliste.

## 2. Pré-requis
- Stack technique stabilisée
- Observabilité de base active

## 3. Tâches détaillées (orientées exécution rapide)
- Mesurer latence et coût par étape agent sur lots de dossiers.
- Définir et suivre SLO/SLA (temps traitement, taux échec, taux reprise).
- Optimiser prompts/outils/parallélisme sans perdre qualité de justification.
- Installer alertes sur régression qualité, latence et coûts.

## 4. Livrables
- Documents et artefacts attendus:
  - `BENCH-PERF-COUT-V1.md`
  - `SLO-SLA-V1.md`
  - `PLAN-OPTIMISATION-V1.md`

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
