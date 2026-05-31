# State — eval-immo

_Updated: 2026-05-31 | HEAD: bdf2630 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 2 — Cœur analytique : T2.1 done, T2.3 next (AMU réelle).

## Plan Status

Plan : `docs/plans/2026-05-31-phase-2-coeur-analytique.md`

- [x] T2.1 — Grille ajustements moteur : `engine/adjustments.py`, 7 lignes/comp, médiane, fourchette, alertes 25% (bdf2630)
- [ ] T2.3 — AMU réelle (`engine/amu.py`, 4 critères avec données réelles, conclusion pouvant différer usage actuel)
- [ ] T2.2 — Unification source calcul TS/Python (après T2.3)
- [ ] T2.4 — Approche coût certifiable (tables Altus/MEFQ)
- [ ] T2.5 — TGA/loyers marché sourcés ou marqués "défaut à valider"
- [ ] T2.6 — Visibilité diagnostics sources (frontend)

## Evidence

- 435 tests verts (bdf2630)
- Grille: AdjustmentRates (7 taux MEFQ/APCIQ), statut calcule|a_valider|donnees_manquantes
- Valeur indiquée = médiane prix ajustés; alerte si ajustements bruts > 25%

## Open Issues

- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T2.3 : `conformite_zonage` hardcodé True dans runtime.py ~l.1517 à remplacer
- T2.5 : `_DEFAULT_CAP_RATE` dans valuation.py → marquer "défaut à valider" quand utilisé
