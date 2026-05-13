# State

## Current Goal
Batch 5 terminé. En attente review utilisateur avant Batch 6.

## Decisions
- Batch 5 livré : commanditaire 2-step form + LLM conflit + gate pipeline
- Roadmap : Batch 6 (ingestion-docs) → 7 (registre) → 8 (enrichissement) → 9 (frontend pipeline view) → 10 (admin-package PDF)

## Plan Status
- Batch 1 (AGENTCONFIG×5 + SKILL.md×20 + LLM enrichment): DONE ✓
- Batch 2 (classify_dossier + PLANS-MANDATS + PlanOrchestrator): DONE ✓
- Batch 3 (AMU agent + pipeline 5→6 + orchestrator wiring + build-eval-skill): DONE ✓
- Batch 4 (mandat-intake + FTA skill + frontend): DONE ✓
- Batch 5 (commanditaire form + LLM conflit + gate): DONE ✓
- Batch 6: plan NON encore écrit

## Evidence
- 78 tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
- Gate conflit actif après mandat-intake : PipelineConflitError → status CONFLIT_DETECTE

## Open Issues
- APIs Batch 7 (DLC, Centris, MRNF) — user travaille à les obtenir
