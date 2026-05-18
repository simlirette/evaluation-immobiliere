# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 4 COMPLÈTE ✅ — Phase 3 (RAG) bloquée en attente livres MEFQ + NPP 2025.

## Plan Status

Phase 1 COMPLÈTE ✅ (commits 5d4d488 → 08e4f71 → 39177e5)

Phase 2 COMPLÈTE ✅:
- [x] 2.1 Streaming SSE (commit 5134888)
- [x] 2.2 Tool calling fetch_artifact (commit af289bc)
- [x] 2.3 PDF ingestion + multi-tour (commit b5c5aaf)
- [x] 2.5+2.6 Tests + Export PDF (commit 61a30af)

Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.

Phase 4 COMPLÈTE ✅ (commit c20ca21):
- [x] 4.1 CI GitHub Actions — pytest tests/ + tsc + build
- [x] 4.2 PDF download button — RapportEditor ⬇ .pdf via backend _generate_pdf()
- [x] 4.3 RapportPanel → useAgentChat — streaming SSE + multi-tour history

## Decisions

- middleware.ts : AUTH_ENABLED = Supabase URL+key configurés ET non-placeholder → passthrough local sinon.
- BFF route.ts : /app/create ajouté à PIPELINE_PATHS (timeout 120s).
- RapportEditor : browser-print retiré, remplacé par téléchargement PDF backend.
- RapportPanel : useAgentChat(dossierId, 'redaction') — ChatReply[] avec curseur ▊ streaming.

## Evidence

- `npx tsc --noEmit` 0 erreurs après Phase 4 (vérifié).
- CI runs `pytest tests/` (couvre test_pure.py + test_phase2.py).

## Open Issues

- Supabase credentials prod à configurer (Vercel env vars).
- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
