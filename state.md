# State — eval-immo

_Updated: 2026-05-31 | HEAD: 27e640b (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 1 ✅ COMPLÈTE. Prochaine : Phase 2 — Cœur analytique.

## Plan Status

### Phase 1 — Connaissance active ✅

- [x] T1.1 — analysis.md injecté pipeline + assistant (2910d9a)
- [x] T1.2 — Corpus 62 docs / 17MB dans `backend/knowledge/corpus/` (aef3dc1)
- [x] T1.3 — RAG pgvector : 8745 chunks, migration 006, `retrieve_context` dégradé-silencieux (e45b3a7)
- [x] T1.4 — Citations normatives dans `annexe_sources.md` + prompt rapport (27e640b)
- [x] T1.5 — Outil `search_knowledge` (fetch_artifact + search_knowledge = _AGENT_TOOLS) (27e640b)

### Phase 2 — Cœur analytique (prochaine)

Plan : `docs/plans/2026-05-31-phase-2-coeur-analytique.md`

- [ ] T2.1 — Grille d'ajustements moteur (runtime.py calcule les ajustements, pas seulement frontend)
- [ ] T2.2 — AMU réelle (zonage API + CPTAQ, sortir tampon hardcodé)
- [ ] T2.3 — TGA/coûts marché sourcés (tables certifiables)
- [ ] T2.4 — Visibilité diagnostics comparables
- [ ] T2.5 — Source de calcul unique TS/Python

### Phase 0 restant

- [ ] T0.5 migrations Supabase prod 002–006 (accès requis)
- [ ] T0.6 Loi 25 / masquage PII SIRF

## Evidence

- 31 tests P0+P1 verts (27e640b)
- 910 tests totaux verts (suite complète à 2910d9a)
- RAG prod : appliquer migrations 002–006 puis `index_corpus()` (~$0.07)

## Open Issues

- T0.5+T1.3 prod : migrations 002–006 à appliquer + index_corpus() à exécuter
- Phase 2 dépend de Phase 1 (✅) — peut démarrer immédiatement
