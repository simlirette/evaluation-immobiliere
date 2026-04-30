# Sous-plan Phase B — Contrats d'intégration Aston réels

## 1. Objectif phase
Transformer les documents de spécification en contrats exécutables versionnés pour session, événements, artefacts et erreurs.

## 2. Pré-requis
- Matrice capabilités validée
- Schemas ops v0 disponibles

## 3. Tâches détaillées (orientées exécution rapide)
- Normaliser les contrats input/output par agent (data-facts, comps-market, valuation-draft, compliance-qa, redaction).
- Spécifier taxonomie d'erreurs: warning, blocking, retryable, fatal.
- Définir règles d'idempotence et reprise de session.
- Ajouter tests de compatibilité de contrats à exécuter en CI.

## 4. Livrables
- Documents et artefacts attendus:
  - `CONTRATS-INTEGRATION-ASTON-V1.yaml`
  - `MATRICE-ERREURS-RETRY-V1.md`
  - `TESTS-COMPAT-CONTRATS-V1.md`

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
