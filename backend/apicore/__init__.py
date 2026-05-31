"""apicore/ — Package modulaire du runtime d'évaluation (T6.1).

Extraction progressive de api.py (6877 lignes / ~260 KB).
Objectif : < 30 Ko par module. api.py re-pointe vers ces modules lors de la migration.

Modules extraits :
  apicore.formatters — fonctions de formatage pures (app_money, app_float, etc.)
  apicore.llm_config  — constantes LLM et tool definitions (_AGENT_TOOLS, etc.)

Modules prévus (prochaines sessions) :
  apicore.sessions    — session I/O (create_session, load_session, etc.)
  apicore.llm         — LLM client + llm_assistant_answer/stream
  apicore.bureau      — bureau_dashboard_summary, track_llm_usage
  apicore.handler     — RuntimeApiHandler (HTTP routing)
"""
