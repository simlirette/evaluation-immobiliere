# State — eval-immo

_Updated: 2026-05-31 | HEAD: e45b3a7 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 1 — Connaissance active : T1.1–T1.3 done, T1.4 next (citations normatives rapport).

## Plan Status

Plan : `docs/plans/2026-05-31-phase-1-connaissance-active.md`

- [x] T1.1 — analysis.md injecté pipeline + assistant (commit 2910d9a)
- [x] T1.2 — Corpus 62 docs / 17MB dans `backend/knowledge/corpus/` (commit aef3dc1)
- [x] T1.3 — RAG pgvector : `knowledge_rag.py`, migration 006, 8745 chunks, intégré `_enrich_artifact_llm` (commit e45b3a7)
- [ ] T1.4 — Citations normatives dans rapport + `annexe_sources.md` (sources normatives pas juste données)
- [ ] T1.5 — Outil assistant `search_knowledge` (tool-calling via RAG)

Phase 0 (pour mémoire) :
- [x] T0.1–T0.4 (commit 3731404)
- [ ] T0.5 migrations Supabase prod 002–006 (accès requis — T0.5 + T1.3 se font ensemble)
- [ ] T0.6 Loi 25 / masquage PII SIRF

## Evidence

- 27 tests P0+P1 verts (e45b3a7)
- 910 tests totaux verts (2910d9a)
- RAG dégradé-silencieux : '' si SUPABASE_URL/OPENAI_API_KEY absents
- index_corpus() : ~8745 chunks, coût estimé ~$0.07 (text-embedding-3-small)

## Open Issues

- T0.5+T1.3 prod : appliquer migrations 002–006 + exécuter index_corpus() une fois
- T1.4 : `annexe_sources.md` builder à étendre pour sources normatives (source_id du catalog)
- T1.5 : ajouter tool `search_knowledge` à `_FETCH_ARTIFACT_TOOL` dans api.py
