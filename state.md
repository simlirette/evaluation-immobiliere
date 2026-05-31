# State — eval-immo

_Updated: 2026-05-31 | HEAD: a commit après T2.6 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 2 — T2.1+T2.3+T2.5+T2.6 done. T2.2 (architectural) ou Phase 3 next.

## Plan Status

Plan : `docs/plans/2026-05-31-phase-2-coeur-analytique.md`

- [x] T2.1 — Grille ajustements 7 lignes/comp, médiane, fourchette
- [x] T2.3 — AMU réelle 4 critères déterministes
- [x] T2.5 — PROXY TGA/coûts marqués VALEUR PROXY
- [x] T2.6 — Diagnostics sources frontend (SourceDiagnosticPanel, MarchePanel, CheckpointComparablePanel)
- [ ] T2.2 — Unification TS/Python (~150 compute-*.ts audit + décision Python = source vérité)
- [ ] T2.4 — Tables coûts certifiables (Altus — accès externe requis)

Phase 3 — Rapport expert (prochaine priorité après T2.2 ou directement) :
Plan : `docs/plans/2026-05-31-phase-3-rapport-expert.md`
- T3.1 — 16 éléments garantis post-génération
- T3.2 — Grille ajustements dans le rapport
- T3.3 — Capture inspection (élément 14 NPP)
- T3.4 — Repli déterministe complet
- T3.5 — Export certifiable (signature, n° permis)

## Evidence

- 953 tests backend verts (3fd9a0e)
- 0 erreurs TS après T2.6 (npx tsc --noEmit)
- SourceDiagnosticPanel : compact/full, statuts colorés ok/partial/empty/failed/missing

## Open Issues

- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T2.2 : décision à prendre — Python source vérité, frontend = affichage (compute-*.ts = analytics only)
- T2.4 : accès Altus incertain — repli saisie manuelle É.A.
