# State — eval-immo

_Updated: 2026-05-31 | HEAD: 7bf30d8 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 5 T5.1–T5.4 done. T5.5/T5.6 ou Phase 6 next.

## Plan Status

### Phase 5 — Multi-bureau ✅ (partiel)

- [x] T5.1 — migration 007_bureaux_tenant.sql : bureaux + bureau_membres + helpers RLS (7bf30d8)
- [x] T5.2 — migration 008_rls_tenant.sql + session_access_allowed bureau-aware (7bf30d8)
- [x] T5.3 — bureau_dashboard_summary + GET /bureau/dashboard (7bf30d8)
- [x] T5.4 — create_session usage init + track_llm_usage (7bf30d8)
- [ ] T5.5 — Observabilité/audit étendu (métriques bureau)
- [ ] T5.6 — Doc migration cloud SCALE-MIGRATION.md

### Phase 6 — Qualité & dette (prochaine priorité)

Plan : `docs/plans/2026-05-31-phase-6-qualite-dette.md`
- T6.1 — Découper api.py 256 Ko en modules
- T6.2 — CI mocks réseau + tests E2E
- T6.3 — Dead code (ThemeToggle, TabBar)
- T6.4 — Unification calculs TS/Python
- T6.5 — Observabilité tokens LLM

## Evidence

- 15 tests P5 verts, 1002+ tests total (7bf30d8)
- sessions_access_allowed bureau-aware (bureau_id param)
- track_llm_usage incrémentiel silencieux

## Open Issues

- T0.5 : appliquer migrations 002–008 sur Supabase prod
- T1.3 prod : index_corpus() après migrations
- T3.6 : démo bureau dossier réel
