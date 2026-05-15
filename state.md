# State

## Current Goal
Phase B en cours. B1/B2/B3 (dossier lifecycle) DONE. Prochaines: upload robustness, sources données pipeline.

## Decisions
- Batch 9 spec : docs/specs/2026-05-15-batch9-pipeline-liveview-polish.md
- Pipeline live view : polling /app/state toutes les 2s via usePipelinePolling hook
- Rapport panel resize : DragHandle custom (no lib), localStorage persist, clamp 280px–80vw
- UX polish : PanelSkeleton (remplace PanelLoader), erreur pipeline explicite, badge tab Rapport

## Plan Status
- Batch 1 (AGENTCONFIG×5 + SKILL.md×20 + LLM enrichment): DONE ✓
- Batch 2 (classify_dossier + PLANS-MANDATS + PlanOrchestrator): DONE ✓
- Batch 3 (AMU agent + pipeline 5→6 + orchestrator wiring + build-eval-skill): DONE ✓
- Batch 4 (mandat-intake + FTA skill + frontend): DONE ✓
- Batch 5 (commanditaire form + LLM conflit + gate): DONE ✓
- Batch 6 (ingestion-docs): DONE ✓
- Batch 7 (comparables manuels): DONE ✓
- Batch 8a (rapport éditeur TipTap + LLM quality): DONE ✓
- Batch 8b (export docx/html + versioning Supabase): DONE ✓
- Batch 9 (pipeline live view + UX polish): DONE ✓

## Evidence
- 115 tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
- E2E validé 2026-05-15 : session f152408cb9f1, valeur 569 122 $, PRET_REVISION_FINALE, 0 blocking failures

## Phase B (2026-05-15) — IN PROGRESS
- B1 unique dossier_id par session (D-{8hex} UUID) ✓
- B2 pin persistant backend (POST /app/pin, session["pinned"]) ✓
- B3 archive persistant backend (POST /app/archive, session["archived"]) ✓
- localStorage helpers supprimés ✓
- B4 upload robustness: tests fetch-mock, BFF timeout 120s + maxDuration=120 ✓
- Commits: 29aa285, 4eb54dc

## Phase A (2026-05-15) — DONE
- Git aligné : master → origin/master + origin/main, GitHub default = main ✓
- Bug conflit gate fixé : faux positifs LLM (runtime.py + api.py), 115 tests pass ✓
- Pipeline E2E validé bout-en-bout ✓
- Auth decision : Option B local-only (middleware.ts LOCAL_ONLY=true, SidebarFooter caché) ✓

## Phase B (cont.)
- B5 sources données (data_enrichment.py) ✓
  - SCHL rental market via StatCan WDS API (34-10-0133-01, 24h cache)
  - Rôle municipal Montréal CSV (lookup by matricule/address, download_role_mtl())
  - enrich_case() wired into start_runtime() après ingestion
  - fiche_bien.json + amu_analyse.md + comparables_proposes.json enrichis
  - Commit: 880b5cf

## Open Issues
- Sources données : 10 autres sources (StatCan census, zonage, CPTAQ, centris, etc.) — prochaine phase
- Rôle municipal CSV : besoin de `python -m engine.data_enrichment download_role_mtl` pour activer
- Mobile/responsive : absent
- CI/CD : GitHub Actions + Playwright E2E non configurés
- Sources données : 15+ sources dans informations/ non connectées au pipeline
- Mobile/responsive : absent
- CI/CD : GitHub Actions + Playwright E2E non configurés
- DLC/JLR + Registre foncier : HOLD
