# State — eval-immo

_Updated: 2026-05-21 | HEAD: S12 — PLAN COMPLET_

## Current Goal

S12 COMPLÈTE ✅ — Roadmap bureau É.A. (docs/ROADMAP-BUREAU-EA.md)
Révision code ✅ — 4 findings corrigés (bloquant démo + pipeline log + distance score + B005/B006 tests)
PLAN COMPLET S1–S12 ✅ — 237 tests verts. Prêt pour démo bureau.

## Plan Status

### Phases antérieures (UI/pipeline)
Phase 1–15A ✅ (voir git log — HEAD antérieur à f7a5bc4)

### Plan d'exécution vers démo bureau É.A. (établi 2026-05-20)
Plan complet : `_audit/2026-05-20/05_PLAN-EXECUTION.md`

S1 ✅ (f7a5bc4) — Séparation Dossier/Session + Supabase schema
S2 ✅ (f7a5bc4) — Auth + comptes bureau/É.A.
S3 ✅ — Pipeline stoppable par checkpoint (4 gates + log horodaté)
S4 ✅ — Compliance Python pur (B001-B007)
S5 ✅ — Extraction PDF élargie (30 champs) + UI CHECKPOINT 1
S6 ✅ — Import CSV JLR + scoring comparables + CHECKPOINT 2
S7 ✅ — Lettre de mandat (20 tests, template §6.3, PDF, formulaire requis)
S8 ✅ — Routing LLM par tâche (36 tests, gpt-4o rapport, coût < $0.10, 3 templates OEAQ)
S9 ✅ — Approches conditionnelles + watermark proxy (22 tests)
S10 ✅ — Éditeur rapport + export propre (13 tests — PDF sans session_id/snapshot_hash/proxy)
S11 ✅ — Dossier démo D-DEMO-2026-LAV (Laval unifamiliale) + chrono + seed script (29 tests)
S12 ✅ — Roadmap bureau É.A. (docs/ROADMAP-BUREAU-EA.md) — tarif, chrono, roadmap 6 mois

## Decisions (S3)

- checkpoint_log.jsonl par session — 1 entrée JSONL par CP confirmé (checkpoint, label, confirmed_by, confirmed_at, snapshot_hash)
- Gate bloquant : assert_checkpoint_confirmed(session_dir, CP-1) → CheckpointRequiredError → HTTP 409 CHECKPOINT_REQUIRED
- steps_filter: list[str] | None — None = tous les steps ; liste vide = aucun step
- _run_pipeline_segment(session, case, checkpoint) — exécute le segment CPn dans un thread daemon
- POST /app/checkpoint/confirm — enregistre la confirmation (uid évaluateur via X-Evaluator-Id)
- POST /app/checkpoint/resume — gate check puis lance segment suivant async
- GET /app/checkpoint/log — retourne toutes les entrées du log
- resume checkpoint=1 invalide (doit être 2-4)
- Input file nommé d'après dossier_id (safe_path_id(dossier_id).input.json), pas session_id

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

- 237 tests verts (24 S1 + 11 S2 + 27 S3 + 37 S4 + 15 S6 + 20 S7 + 36 S8 + 22 S9 + 13 S10 + 32 S11) — test_s1..test_s11_demo.py
- tsc 0 erreurs post-S7
- Formulaire "Nouveau dossier" : honoraires + date_livraison + nom_evaluateur → requis (bloque soumission)
- python -c "import api; print('OK')" ✅

## Open Issues

- Migrations 002+003 à appliquer sur Supabase prod (après provisioning Railway+Vercel)
- A1 : avocat Loi 25 + §6.5 OEAQ (avant S2 prod)
- A2 : CSV JLR export format réel à valider avec l'É.A. (parse_jlr_csv implémenté, aliases configurables)
