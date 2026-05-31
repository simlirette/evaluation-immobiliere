# State — eval-immo

_Updated: 2026-05-31 | HEAD: 3fd9a0e (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 2 — Cœur analytique : T2.1+T2.3 done, T2.5 next (TGA défauts marqués).

## Plan Status

Plan : `docs/plans/2026-05-31-phase-2-coeur-analytique.md`

- [x] T2.1 — Grille ajustements moteur (bdf2630)
- [x] T2.3 — AMU réelle, 4 critères déterministes, conformite_zonage réel (3fd9a0e)
- [ ] T2.5 — TGA/loyers marché : `_DEFAULT_CAP_RATE` → marqué "défaut à valider" quand utilisé
- [ ] T2.2 — Unification source calcul TS/Python
- [ ] T2.4 — Approche coût certifiable (tables Altus/MEFQ)
- [ ] T2.6 — Visibilité diagnostics sources (frontend)

## Evidence

- 953 tests verts (3fd9a0e, 2026-05-31)
- AMU : conformite_zonage = True|False|None selon données réelles (jamais True en dur)
- Grille : 7 lignes/comparable, statuts calcule|a_valider|donnees_manquantes

## Open Issues

- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T2.5 : `_DEFAULT_CAP_RATE`, `_DEFAULT_GRM`, `_DEFAULT_VACANCY_RATE` dans valuation.py
- T2.4 : accès tables Altus incertain — prévoir saisie manuelle É.A. comme repli
