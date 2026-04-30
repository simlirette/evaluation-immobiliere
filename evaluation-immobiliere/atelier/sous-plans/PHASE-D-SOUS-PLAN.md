# Sous-plan Phase D — Persistance, streaming et API produit

## 1. Objectif phase
Mettre en place sessions persistées, événements streamables et API cohérente pour usage produit.

## 2. Pré-requis
- Engine réel branché
- Taxonomie événements validée

## 3. Tâches détaillées (orientées exécution rapide)
- Créer le modèle de persistance sessions/artifacts/events/knowledge snapshots.
- Implémenter endpoints sessions/start/stream/status/artefacts/review.
- Ajouter garanties de reprise après incident (resume session).
- Tester intégrité: chaque événement doit référencer session + étape + artefact lié.

## 4. Livrables
- Documents et artefacts attendus:
  - `MODELE-PERSISTENCE-V1.md`
  - `API-PRODUIT-CONTRATS-V1.md`
  - `TEST-RESUME-SESSION-V1.md`

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
