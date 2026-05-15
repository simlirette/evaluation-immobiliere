# State

## Current Goal
Batch 8a DONE. Prêt pour Batch 8b (export Word/PDF + versioning) ou Batch 9.

## Decisions
- Batch 7 : saisie manuelle (option A) — pas de scraping ni DB externe pour V0
- Comparables passent via case["comparables"] (déjà câblé dans runtime.py + tools.py)
- Step 3 ajouté au wizard DossierPanel (step1: bien, step2: commanditaire, step3: comparables)
- Spec : docs/specs/2026-05-14-batch7-comparables.md

## Plan Status
- Batch 1 (AGENTCONFIG×5 + SKILL.md×20 + LLM enrichment): DONE ✓
- Batch 2 (classify_dossier + PLANS-MANDATS + PlanOrchestrator): DONE ✓
- Batch 3 (AMU agent + pipeline 5→6 + orchestrator wiring + build-eval-skill): DONE ✓
- Batch 4 (mandat-intake + FTA skill + frontend): DONE ✓
- Batch 5 (commanditaire form + LLM conflit + gate): DONE ✓
- Batch 6 (ingestion-docs): DONE ✓
- Batch 7 (comparables manuels): DONE ✓
- Batch 8a (rapport éditeur TipTap + LLM quality): DONE ✓

## Evidence
- 108+ tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
- runtime.py ligne 624 : search_comparables(case.get("comparables", [])) — déjà câblé
- CONF002 : 0 comparables → A_REVOIR (blocking, non-crash) — pipeline complète

## Open Issues
- DLC/JLR + Registre foncier : HOLD jusqu'à présentation à évaluateur agréé
