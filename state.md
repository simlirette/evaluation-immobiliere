# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 6A COMPLÈTE ✅ — Formulaire de saisie dossier avec champs sujet.

## Plan Status

Phase 1 ✅ · Phase 2 ✅ · Phase 4 ✅
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.
Phase 5A ✅ (9f023c3) · Phase 5B ✅ (00addca) · Phase 5C ✅ (71c0aab)
Phase 6A ✅ (8cc94d4) — Formulaire saisie + pipeline launch immédiat

## Decisions

- app_create_dossier: construit case dict complet, lance start_runtime en thread daemon → retour immédiat.
- NewDossierForm: type_bien select structuré + superficie hab/terrain (pi²), année construction, nb chambres.
- Routing post-création: /dossier/${dossier.id} (dossier.id = session_id, pas de slug Supabase).
- Page dossier/[id]: fetchDossier (Supabase) → fetchRuntimeDossier (runtime-api).
- Pipeline polling déjà géré: status "CREATED" ≠ terminal → setIsRunning(true) automatique.

## Evidence

- tsc --noEmit 0 erreurs. python -c "import api" OK.

## Open Issues

- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Supabase credentials prod à configurer (Vercel env vars).
