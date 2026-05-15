# State

## Current Goal
Phase A complète. En attente décision auth (Option A: Supabase enforced / Option B: local-only).

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

## Phase A (2026-05-15) — DONE
- Git aligné : master → origin/master + origin/main, GitHub default = main ✓
- Bug conflit gate fixé : faux positifs LLM (runtime.py + api.py), 115 tests pass ✓
- Pipeline E2E validé bout-en-bout ✓
- Auth decision : Option B local-only (middleware.ts LOCAL_ONLY=true, SidebarFooter caché) ✓

## Open Issues
- Auth model : décision requise avant Phase B
- Dossier lifecycle réel : create/delete/pin persistants (P0)
- Sources données : 15+ sources dans informations/ non connectées au pipeline
- Mobile/responsive : absent
- CI/CD : GitHub Actions + Playwright E2E non configurés
- DLC/JLR + Registre foncier : HOLD
