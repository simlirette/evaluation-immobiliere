# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 5 COMPLÈTE ✅ (5A + 5B + 5C).

## Plan Status

Phase 1 ✅ · Phase 2 ✅ · Phase 4 ✅
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.
Phase 5A ✅ (9f023c3) — Grille d'ajustements éditable
Phase 5B ✅ (00addca) — Pipeline progress streaming
Phase 5C ✅ (71c0aab) — Conversation transcript UI

## Decisions

- GET /app/transcript?session_id&agent — lit assistant_messages.jsonl, filtre par agent optionnel.
- useAgentChat charge transcript au mount (restaure historique entre navigations); userMessage par ChatReply.
- History multi-tour inclut maintenant les tours user (pas seulement assistant).
- pipeline_progress.json écrit dans session_dir après chaque étape.
- Ajustements manuels dans SESSIONS_DIR/{id}/adjustments.json.
- middleware.ts: AUTH_ENABLED auto-detect placeholder.

## Evidence

- tsc --noEmit 0 erreurs. python import api OK.

## Open Issues

- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Supabase credentials prod à configurer (Vercel env vars).
