# Sous-plan Phase C — Branchement engine réel et outils runtime

## 1. Objectif phase
Connecter les AgentConfig immobiliers à un moteur d'exécution Aston-like réel au lieu d'un flux piloté uniquement par fixtures.

## 2. Pré-requis
- Contrats V1 approuvés
- Configs agents stabilisées

## 3. Tâches détaillées (orientées exécution rapide)
- Mapper chaque `tools_allowed` vers une implémentation réelle (lecture docs, écriture artefacts, audit).
- Brancher extraction texte/OCR avec journalisation complète des sources.
- Valider l'exécution bout en bout sur un dossier réel anonymisé.
- Tracer explicitement les écarts entre sortie simulation et sortie engine réel.

## 4. Livrables
- Documents et artefacts attendus:
  - `RAPPORT-BRANCHEMENT-ENGINE-V1.md`
  - `TOOL-MAPPING-ASTON-V1.md`
  - `CASE-REEL-E2E-RESULTATS-V1.md`

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
