# State — eval-immo

_Updated: 2026-05-31 | HEAD: 3d62846 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 6 ✅. Toutes phases P0–P6 couvertes. Prochaine : merger branche ou apicore/llm.py.

## Plan Status

### Phase 6 ✅

- [x] T6.1 — apicore/ : formatters, llm_config, storage, sessions (580 L extraites)
- [x] T6.2 — INCLUDE_INVESTMENT_CONTEXT flag
- [x] T6.3 — docs/CALCULS-SOURCE-OF-TRUTH.md (Python = vérité, TS = affichage)
- [x] T6.4 — CI hermétique + E2E happy path + conftest.py
- [x] T6.5 — Dead code ThemeToggle/TabBar supprimés
- [x] T6.6 — track_llm_usage branché rapport + assistant
- [ ] T6.1 complet — extraire apicore/llm.py + apicore/handler.py (api.py = ~6300L restantes)

### apicore/ état (T6.1 fondation)

```
apicore/
  __init__.py        — doc plan migration
  formatters.py      — app_money, utc_now_*, etc.
  llm_config.py      — _AGENT_TOOLS, constantes LLM
  storage.py         — atomic_write_text, write_json, read_json_dict
  sessions.py        — create_session, load_session, track_llm_usage, etc.
```

## Evidence

- 58 tests regression verts (3d62846)
- apicore.sessions : get_sessions_dir() via os.environ — patchable sans monkeypatch api.SESSIONS_DIR
- docs/CALCULS-SOURCE-OF-TRUTH.md : invariant "calcul TS ≠ rapport Python" documenté

## Open Issues

- T0.5 prod : migrations 002–008 Supabase
- T3.6 : démo bureau dossier réel
- T6.1 complet : apicore/llm.py (openai client, llm_assistant_answer, stream)
