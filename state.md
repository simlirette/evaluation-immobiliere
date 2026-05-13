# State

## Current Goal
Batch 6 plan écrit. En attente lancement subagent-driven-development.

## Decisions
- Batch 6 design : extraction lazy (pipeline launch), PyMuPDF + GPT-4o Vision fallback, structured fields injection, fixture fields win
- Spec : docs/specs/2026-05-13-batch6-ingestion-docs.md

## Plan Status
- Batch 1 (AGENTCONFIG×5 + SKILL.md×20 + LLM enrichment): DONE ✓
- Batch 2 (classify_dossier + PLANS-MANDATS + PlanOrchestrator): DONE ✓
- Batch 3 (AMU agent + pipeline 5→6 + orchestrator wiring + build-eval-skill): DONE ✓
- Batch 4 (mandat-intake + FTA skill + frontend): DONE ✓
- Batch 5 (commanditaire form + LLM conflit + gate): DONE ✓
- Batch 6 (ingestion-docs): DONE ✓

## Evidence
- 94 tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
- Gate conflit actif après mandat-intake : PipelineConflitError → status CONFLIT_DETECTE

## Open Issues
- APIs Batch 7 (DLC, Centris, MRNF) — user travaille à les obtenir
