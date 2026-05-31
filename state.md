# State — eval-immo

_Updated: 2026-05-31 | HEAD: cedc06a (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 6 quasi-complète. T6.1 fondation posée, migration complète prochaines sessions.

## Plan Status

### Phase 6 ✅ (partiel)

- [x] T6.1 — apicore/ fondation : formatters.py + llm_config.py extraits de api.py (cedc06a)
       Note : api.py reste intact ; migration complète = sessions.py/llm.py/bureau.py/handler.py
- [x] T6.2 — INCLUDE_INVESTMENT_CONTEXT flag (90016c4)
- [x] T6.4 — CI hermétique + E2E happy path + fix bug T3.3 case_dir (d113692)
- [x] T6.5 — Dead code ThemeToggle/TabBar (90016c4)
- [x] T6.6 — track_llm_usage branché (90016c4)
- [ ] T6.1 (complet) — Extraire sessions.py, llm.py, bureau.py, handler.py depuis api.py
- [ ] T6.3 — Unification TS/Python doc (Python = source vérité)

### Toutes phases P0–P5 ✅

Voir session-log.md pour détails.

## Evidence

- 58 tests regression verts (cedc06a)
- apicore.formatters : app_money, utc_now_iso, etc. — importables sans circular deps
- apicore.llm_config : AGENT_TOOLS (5 outils), constantes LLM
- Nom 'apicore' (pas 'api') pour éviter de masquer api.py

## Open Issues

- T6.1 complet : api.py 6877L → apicore/ — migration complète prochaine session
- T0.5 prod : migrations 002–008 Supabase
- T3.6 : démo bureau dossier réel
