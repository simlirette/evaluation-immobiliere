# State — eval-immo

_Updated: 2026-05-31 | HEAD: 9580d99 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 2 — T2.1+T2.3+T2.5 done. Prochaine : T2.2 (unification source calcul) ou T2.6 (frontend diagnostics).

## Plan Status

Plan : `docs/plans/2026-05-31-phase-2-coeur-analytique.md`

- [x] T2.1 — Grille ajustements 7 lignes/comp, médiane, fourchette (bdf2630)
- [x] T2.3 — AMU réelle 4 critères déterministes (3fd9a0e)
- [x] T2.5 — TGA/coûts proxy marqués VALEUR PROXY, notes a_valider (9580d99)
- [ ] T2.2 — Unification source calcul TS/Python (Python = source vérité, frontend = affichage)
- [ ] T2.4 — Tables coûts certifiables (accès Altus requis — externe)
- [ ] T2.6 — Visibilité diagnostics sources (frontend MarchePanel/CheckpointComparablePanel)

## Evidence

- 36 tests P2 verts (9580d99)
- AVERTISSEMENT = "VALEUR PROXY" dans trace.defaults_used quand TGA/vacance/loyer = défaut
- _cost_uses_default + AVERTISSEMENT_COUT pour approche coût

## Open Issues

- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T2.2 : ~150 compute-*.ts frontend à auditer (usage réel?) avant décision
- T2.4 : accès Altus incertain — repli saisie manuelle É.A.
