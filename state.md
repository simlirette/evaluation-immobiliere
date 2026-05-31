# State — eval-immo

_Updated: 2026-05-31 | HEAD: 8bac70e (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 4 Vague 4A+4C done. Vague 4B next (T4.5 immeubles revenus + T4.6 spécialisés).

## Plan Status

Plan : `docs/plans/2026-05-31-phase-4-couverture-metier.md`

### Vague 4A ✅

- [x] T4.1–T4.2 — Routing mandats spéciaux + JVM/valeur réelle/liquidation (7ba8671)
- [x] T4.3 — Expropriation avant-après (7ba8671)
- [x] T4.4 — Liquidation avec décote (7ba8671)

### Vague 4C ✅

- [x] T4.7 — Outils assistant : search_comparables, run_calculation, rerun_step (8bac70e)

### Vague 4B (prochaine)

- [ ] T4.5 — Immeubles à revenus 7+ / commercial : normalisation RBP→RBE→RNE complète, baux, vacance historique
- [ ] T4.6 — Biens spécialisés (RPA, indivise, patrimonial, agricole)

## Evidence

- 29 tests P4 verts (8bac70e)
- _AGENT_TOOLS : 5 outils (fetch_artifact, search_knowledge, search_comparables, run_calculation, rerun_step)
- rerun_step : gate checkpoint vérifié, déclenche _run_pipeline_segment en thread

## Open Issues

- T3.6 : démo bureau (dossier réel anonymisé bout en bout)
- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T2.2 : unification TS/Python (architectural)
