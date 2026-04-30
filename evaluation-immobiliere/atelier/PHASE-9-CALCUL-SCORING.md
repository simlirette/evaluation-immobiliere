# Phase 9 - Scoring explicable et calcul deterministe

## Objectif

Remplacer les valeurs v0 opaques par des scores de comparables explicables et
des traces de calcul auditables.

## Livrables ajoutes

- `engine/valuation.py`
- `mvp/SCORING-COMPARABLES-V0.yaml`
- `mvp/MOTEUR-CALCUL-VALEUR-V0.yaml`
- `tests/test_valuation_v0.py`

## Changements runtime

- `comparables_proposes.json` contient maintenant `score_details`.
- `calculs_approche_comparative.json` contient une trace:
  - comparables retenus;
  - poids utilises;
  - valeur de base;
  - ajustements valides appliques;
  - politique de calcul.
- Les approches cout et revenu restent des proxys v0 documentes jusqu'a
  obtention de tables metier et calibration evaluateur.

## Points a valider avec les evaluateurs

- Poids du scoring: distance, recence, similarite de surface, confiance, source.
- Penalites: vente future, unite incoherente, source manquante.
- Moment ou un warning doit devenir bloquant.
- Remplacement des proxys cout/revenu par des tables et formules metier.
