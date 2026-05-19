# State — eval-immo

_Updated: 2026-05-18_

## Current Goal

Phase 9A COMPLÈTE ✅ — mandat_type + date_reference dans NewDossierForm.

## Plan Status

Phase 1 ✅ · Phase 2 ✅ · Phase 4 ✅
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025.
Phase 5A ✅ · Phase 5B ✅ · Phase 5C ✅
Phase 6A ✅ · Phase 6B ✅ · Phase 6C ✅
Phase 7 ✅ — Infra deploy
Phase 8A ✅ — Tests 6A+6C (13/13)
Phase 8B ✅ — DossierPanel → runtime (ingestion PDF)
Phase 8C ✅ — Package V1 ZIP + download (engine/package.py)
Phase 8D ✅ — MarchePanel + AnalysePanel → runtime
Phase 9A ✅ — mandat_type select + date_reference date dans NewDossierForm (Step 2)

## Decisions

- Tous les panels (Dossier/Marche/Analyse) lisent comparables/adjustments/docs via runtime — Supabase non requis en dev.
- engine/package.py: generate_package_from_case → rapport.md + PDF + artifacts + manifest + ZIP.
- BFF route.ts: passe application/zip en binaire (évite corruption).
- DossierPanel: fetchRuntimeDocuments+uploadRuntimeDocument — ingestion PDF fonctionnelle.
- Railway backend: libgomp1 requis (PyMuPDF OpenMP), volume /data/sessions.
- NewDossierForm Step 2: mandat_type (défaut residentiel_standard) + date_reference (défaut today) envoyés au backend.

## Evidence

- tsc --noEmit 0 erreurs. test_phase5.py 8/8. test_phase6.py 13/13. test_pure.py ingestion 16/16.

## Open Issues

- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Mise en prod effective : Railway + Vercel non encore provisionnés.
- rapport-versions (Supabase) — intentionnel, graceful fail.
- Tests engine/package.py (Phase 9C) — non démarrés.
