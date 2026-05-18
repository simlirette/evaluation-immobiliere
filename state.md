# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 5B COMPLÈTE ✅ — pipeline progress streaming step-by-step.

## Plan Status

Phase 1 ✅ · Phase 2 ✅ · Phase 4 ✅
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.

Phase 5A ✅ (commit 9f023c3) — Grille d'ajustements éditable
Phase 5B ✅ (commit 00addca) — Pipeline progress streaming

## Decisions

- pipeline_progress.json écrit dans session_dir après chaque step (non-bloquant).
- on_step_done callback dans run_case_data — exception silencieuse, jamais bloquant.
- usePipelinePolling utilise pipeline_progress (7 étapes agents) si dispo, fallback workflow steps.
- Ajustements manuels stockés dans SESSIONS_DIR/{session_id}/adjustments.json.
- middleware.ts : AUTH_ENABLED auto-detect placeholder → passthrough local.

## Evidence

- `npx tsc --noEmit` 0 erreurs.
- `python -c "import api"` OK.

## Open Issues

- Phase 5C (transcript UI) disponible.
- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Supabase credentials prod à configurer.
