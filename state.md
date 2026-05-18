# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 5A COMPLÈTE ✅ — grille d'ajustements éditable dans AnalysePanel.

## Plan Status

Phase 1 ✅ · Phase 2 ✅ · Phase 4 ✅ (commits 5d4d488 → c20ca21)

Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.

Phase 5A COMPLÈTE ✅ (commit 9f023c3):
- [x] Backend: POST /app/adjustments — persiste ajustements manuels par session
- [x] Backend: app_adjustment_rows() lit override manuel en priorité (fallback fixture)
- [x] Frontend: saveRuntimeAdjustments() dans runtime-api.ts
- [x] AnalysePanel: mode édition inline — inputs surface/temps/condition/garage, prix ajusté recalculé live

## Decisions

- Ajustements manuels stockés dans SESSIONS_DIR/{session_id}/adjustments.json (flag manual: true).
- Fallback automatique vers fixture si pas de fichier manuel — rétrocompat totale.
- Édition inline dans AnalysePanel (pas de composant séparé) — couplage fort justifié.
- middleware.ts : AUTH_ENABLED = Supabase URL+key configurés ET non-placeholder → passthrough local sinon.
- BFF route.ts : /app/create et /app/state dans PIPELINE_PATHS (timeout 120s).

## Evidence

- `npx tsc --noEmit` 0 erreurs après Phase 5A.
- `python -c "import api; print('OK')"` OK.

## Open Issues

- Supabase credentials prod à configurer (Vercel env vars).
- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Phase 5B (pipeline progress streaming) et 5C (transcript UI) disponibles.
