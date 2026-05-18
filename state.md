# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 6 COMPLÈTE ✅ (6A + 6B + 6C).

## Plan Status

Phase 1 ✅ · Phase 2 ✅ · Phase 4 ✅
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.
Phase 5A ✅ · Phase 5B ✅ · Phase 5C ✅
Phase 6A ✅ (8cc94d4) — Formulaire saisie + pipeline launch
Phase 6B ✅ (bd36415) — PDF export en-tête/pied/pagination
Phase 6C ✅ (cdc29e6) — Grille comparables éditable

## Decisions

- app_create_dossier: case dict inline → start_runtime thread daemon, retour immédiat.
- _generate_pdf: fitz two-pass (story → post-process pages) pour header/footer/pagination.
- app_comparable_rows(knowledge, session_id): comparables.json manuel prioritaire.
- Comparable.source_id + score optionnels (rétrocompat mocks).
- fetchDossier (Supabase) → fetchRuntimeDossier dans page dossier/[id].

## Evidence

- tsc --noEmit 0 erreurs. python import api OK. test_phase5.py 8/8.

## Open Issues

- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Supabase credentials prod à configurer (Vercel env vars).
- Tests 6A+6C à écrire (app_create_dossier inline, app_save_comparables).
