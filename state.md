# State — eval-immo

_Updated: 2026-05-31 | HEAD: 2910d9a (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 1 — Connaissance active : T1.1 done, T1.2 next (rapatrier corpus normatif).

## Plan Status

Plan : `docs/plans/2026-05-31-phase-1-connaissance-active.md`

- [x] T1.1 — analysis.md injecté pipeline (`_enrich_artifact_llm`) + assistant (`_build_agent_full_prompt`)
- [ ] T1.2 — Corpus normatif dans `backend/knowledge/` (68 sources depuis `C:\Users\simon\knowledge(-source)`)
- [ ] T1.3 — RAG pgvector (`engine/knowledge_rag.py`, migration 006)
- [ ] T1.4 — Citations normatives liées dans le rapport
- [ ] T1.5 — Outil assistant `search_knowledge`

Phase 0 status (pour mémoire) :
- [x] T0.1–T0.4 (commit 3731404)
- [ ] T0.5 migrations Supabase prod 002–005 (accès requis)
- [ ] T0.6 Loi 25 / masquage PII SIRF (non-technique)

## Evidence

- 485 tests verts (2910d9a, 2026-05-31)
- `load_skill_knowledge` : analysis.md prioritaire, budget 3000 chars pipeline / 5000 chars assistant

## Open Issues

- T0.5 : migrations Supabase prod (002–005)
- T0.6 : masquage noms vendeur/acheteur `registre_foncier.py`
- T1.2 : décider quels fichiers de `knowledge-source/` importer (68 sources — markdown seulement, pas PDF bruts)
