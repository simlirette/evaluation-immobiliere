# State — eval-immo

_Updated: 2026-05-19_

## Current Goal

Phase 10 COMPLÈTE ✅ (2dfc858) — valuation card + fact chips editor.

## Plan Status

Phase 1–9B ✅
Phase 10B ✅ (déjà fait — RapportEditor)
Phase 10C ✅ (déjà fait — AnalysePanel)
Phase 10D ✅ (2dfc858) — valuation card dans RapportPanel
Phase 10E ✅ (2dfc858) — fact chips editor inline + /app/facts POST
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025

## Decisions

- Tous panels lisent via runtime — Supabase non requis en dev.
- engine/package.py: ZIP V1 = rapport.md + PDF + artifacts + manifest.
- BFF: application/zip passé en binaire (évite corruption).
- Commanditaire sauvé dans session["app_commanditaire"] à la création.
- app_fact_chips accepte overrides={surface_pi2, zone, date_reference} depuis session["app_fact_overrides"].
- Fact overrides: patch target est engine.report_export._generate_pdf (lazy import).

## Evidence

- tsc 0 erreurs. test_phase5 8/8. test_phase6 13/13. test_pure 16/16. test_phase9 15/15.

## Open Issues

- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Mise en prod Railway + Vercel non encore provisionnés.
- rapport-versions (Supabase) — intentionnel, graceful fail.
- Tests pour /app/facts endpoint (10E) — non écrits.
