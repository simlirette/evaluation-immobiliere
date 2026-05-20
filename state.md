# State — eval-immo

_Updated: 2026-05-20 | HEAD: f7a5bc4_

## Current Goal

S1+S2 COMPLÈTES ✅ — Séparation Dossier/Session + Auth bureau/É.A.
Prochaine : S3 — Pipeline stoppable par checkpoint (ouvrir nouvelle session).

## Plan Status

### Phases antérieures (UI/pipeline)
Phase 1–15A ✅ (voir git log — HEAD antérieur à f7a5bc4)

### Plan d'exécution vers démo bureau É.A. (établi 2026-05-20)
Plan complet : `_audit/2026-05-20/05_PLAN-EXECUTION.md`

S1 ✅ (f7a5bc4) — Séparation Dossier/Session + Supabase schema
S2 ✅ (f7a5bc4) — Auth + comptes bureau/É.A.
S3 ⏳ — Pipeline stoppable par checkpoint (4 gates + log horodaté) — Effort L
S4 — Compliance Python pur (B001-B007)
S5 — Extraction PDF élargie + UI CHECKPOINT 1
S6 — Import CSV JLR + CHECKPOINT 2
S7 — Lettre de mandat
S8 — Modèles rapport + routing LLM
S9 — Approches conditionnelles + watermark proxy
S10 — Éditeur rapport + export
S11 — Dossier démo anonymisé
S12 — Roadmap bureau

## Decisions (S1+S2)

- Dossier slug = dossier_id (D-USR-XXXXXXXX), jamais le session UUID hex12
- load_session() résout dossier_id → session_id via scan filesystem (fallback)
- app_state() déduplique par dossier_id — une card par dossier même si N sessions
- Sessions > 30 jours non-validées → archivées au démarrage (_archive_stale_sessions)
- confirmed_by = UUID Supabase (via X-Evaluator-Id BFF header), persiste dans review.json
- Middleware AUTH_ENABLED guard — passthrough si Supabase non configuré (dev local)
- /admin/* réservé bureau_admin (check profiles table en middleware)
- inviteUserByEmail via service role key (SUPABASE_SERVICE_ROLE_KEY, server-only)

## Evidence

- 35 tests verts (24 S1 + 11 S2) — test_s1_dossier_session.py, test_s2_auth.py
- tsc 0 erreurs post-S2
- python -c "import api; print('OK')" ✅

## Open Issues

- S3 à démarrer (nouvelle session) : run_pipeline_until + resume_from_checkpoint + gates 409
- Migrations 002+003 à appliquer sur Supabase prod (après provisioning Railway+Vercel)
- A1 : avocat Loi 25 + §6.5 OEAQ (avant S2 prod)
- A2 : CSV JLR export (avant S6)
