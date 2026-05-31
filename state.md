# State — eval-immo

_Updated: 2026-05-31 | HEAD: 1f0ade0 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 4 ✅ complète. Prochaine : Phase 5 (multi-bureau) ou T3.6 (démo bureau).

## Plan Status

### Phase 4 ✅

- [x] T4.1–T4.4 Mandats spéciaux : succession/donation/contestation/expropriation/liquidation (7ba8671)
- [x] T4.5 Immeubles revenus : provision remplacement, baux, $/pi² (1f0ade0)
- [x] T4.6 Types spécialisés : indivise, agricole CPTAQ, patrimonial, RPA (1f0ade0)
- [x] T4.7 Outils assistant : search_comparables, run_calculation, rerun_step (8bac70e)

### Phase 5 — Multi-bureau & échelle (prochaine)

Plan : `docs/plans/2026-05-31-phase-5-multi-bureau-echelle.md`
- T5.1 — Modèle bureau_id (tenant) + colonne Supabase
- T5.2 — RLS par bureau (bureau_admin lit ses É.A.)
- T5.3 — Tableau directeur
- T5.4 — Crédits/facturation
- T5.5 — Scale (perf, pagination)

### T3.6 — Démo bureau (jalon)

Dossier résidentiel réel anonymisé bout en bout + chrono.

## Evidence

- 41 tests P4, 1002+ tests total verts (1f0ade0)
- specialized_valuation.py : 4 analyseurs (indivise/agricole/patrimonial/RPA)
- _income_inputs : provision_remplacement 3% défaut pour 7+ logements, baux_summary

## Open Issues

- Phase 5 dépend de P0 (migrations Supabase) — T0.5 à appliquer d'abord
- T3.6 : dossier réel anonymisé requis
- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
