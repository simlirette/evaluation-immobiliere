# State

## Current Goal
Batch 9 DONE. Prêt pour test end-to-end pipeline É.A.

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

## Open Issues
- DLC/JLR + Registre foncier : HOLD — rôle d'évaluation foncière municipal envisagé Batch 10+
- Pipeline jamais testé bout-en-bout — validation qualité É.A. à faire après Batch 9
- Pipeline à tester end-to-end avec dossier réel avant démo É.A.
