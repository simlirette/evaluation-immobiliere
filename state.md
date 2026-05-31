# State — eval-immo

_Updated: 2026-05-31 | HEAD: 7ba8671 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 4 Vague 4A done. Vague 4B (biens spécialisés) ou 4C (assistant actif) next.

## Plan Status

Plan : `docs/plans/2026-05-31-phase-4-couverture-metier.md`

### Vague 4A ✅

- [x] T4.1 — Date rétrospective : classify_dossier depuis but_evaluation (7ba8671)
- [x] T4.2 — JVM/valeur réelle/liquidation : _mandat_special_lines + PLANS-MANDATS-V0 (7ba8671)
- [x] T4.3 — Expropriation avant-après : calculate_expropriation (7ba8671)
- [x] T4.4 — Liquidation : calculate_liquidation_value + proxy-warning (7ba8671)

### Vague 4B (prochaine)

- [ ] T4.5 — Immeubles à revenus 7+ / commercial / industriel (normalisation complète)
- [ ] T4.6 — Biens spécialisés (RPA, indivise, patrimonial, agricole)

### Vague 4C

- [ ] T4.7 — Outils assistant d'action (search_comparables, run_calculation, rerun_step)

## Evidence

- 28 tests P4 verts + 46 total (7ba8671)
- 6 nouveaux types de mandats dans PLANS-MANDATS-V0.yaml
- calculate_expropriation : avant − après + préjudices; calculate_liquidation_value : VM × (1-décote)

## Open Issues

- T3.6 : démo bureau (dossier réel anonymisé)
- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T2.2 : unification TS/Python (architectural)
