# State — eval-immo

_Updated: 2026-05-19_

## Current Goal

Phase 11B COMPLÈTE ✅ (1b17b28) — deploy config Railway + Vercel prête.

## Plan Status

Phase 1–10E ✅
Phase 11B ✅ (1b17b28) — vercel.json + DEPLOYMENT.md + BFF timeout fix
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025

## Decisions

- Tous panels lisent via runtime — Supabase non requis en dev.
- BFF timeout : 120s pour /app/create, /app/state, /app/package, /app/review/validate. 30s sinon.
- vercel.json : maxDuration 120s (Vercel Pro requis pour dépasser 60s).
- EVAL_RUNTIME_ALLOWED_ORIGIN doit correspondre exactement à l'URL Vercel (sans slash final).
- app_fact_chips overrides stockés dans session["app_fact_overrides"].
- Commanditaire stocké dans session["app_commanditaire"].

## Evidence

- tsc 0 erreurs. test_phase5 8/8. test_phase6 13/13. test_pure 16/16. test_phase9 15/15.

## Open Issues

- Mise en prod : Railway + Vercel à provisionner (guide complet dans DEPLOYMENT.md).
- Tests /app/facts endpoint (Phase 10E) — non écrits.
- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- rapport-versions (Supabase) — intentionnel, graceful fail.
