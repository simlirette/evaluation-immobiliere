# State

## Current Goal
Batch 8b DONE. Prêt pour Batch 9 ou présentation É.A.

## Decisions
- Batch 8b spec : docs/specs/2026-05-15-batch8b-export-versioning.md
- Export .docx : python-docx + parser MD custom, watermark toujours injecté
- Export HTML/PDF : markdown lib → template CSS print A4, browser Ctrl+P
- Versioning : 100% frontend (Supabase JS) — pas de supabase-py backend
- Versions : 1ère auto (is_initial=true) + max 5 manuelles = 6 total par session
- Schéma SQL à exécuter manuellement dans Supabase avant implémentation

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

## Evidence
- 115 tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)

## Open Issues
- DLC/JLR + Registre foncier : HOLD jusqu'à présentation à évaluateur agréé
