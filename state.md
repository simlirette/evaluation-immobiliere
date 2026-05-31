# State — eval-immo

_Updated: 2026-05-31 | HEAD: d113692 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 6 T6.2+T6.4+T6.5+T6.6 done. T6.1 (api.py découpe) reste.

## Plan Status

### Phase 6 — Qualité & dette ✅ (partiel)

- [x] T6.2 — INCLUDE_INVESTMENT_CONTEXT flag (90016c4)
- [x] T6.4 — CI hermétique + E2E happy path + fix bug T3.3 case_dir (d113692)
- [x] T6.5 — Dead code ThemeToggle/TabBar supprimés (90016c4)
- [x] T6.6 — Observabilité tokens track_llm_usage (90016c4)
- [ ] T6.1 — Découper api.py 6000+ lignes en modules (~30 Ko max)
- [ ] T6.3 — Unification TS/Python doc (Python = source vérité)

### Fixes inclus

- Bug T3.3 : case_dir non défini dans _artifact_payload → inspection pré-chargée dans run_case_data

## Evidence

- 63 tests E2E+P3+P4 verts (d113692)
- conftest.py : block_network_calls autouse, fixture tmp_session
- CI : ignore live tests, EVAL_IMMO_LIVE_EXTERNALS=0

## Open Issues

- T6.1 : api.py 6000+ lignes — refactor majeur, risqué
- T0.5 prod : migrations 002–008 sur Supabase
- T3.6 : démo bureau dossier réel
