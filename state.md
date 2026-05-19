# State — eval-immo

_Updated: 2026-05-19_

## Current Goal

Phase 10 en attente de choix utilisateur (10A–10E proposées).

## Plan Status

Phase 1–8D ✅
Phase 9A ✅ (da056d2) — mandat_type + date_reference dans NewDossierForm
Phase 9B ✅ (da056d2) — commanditaire display + tests engine/package.py (15/15) + sidebar search
Phase 3 BLOQUÉE — attente livres MEFQ + NPP 2025

Phase 10 options proposées :
- 10A : Deploy prod Railway + Vercel (opérationnel pur)
- 10B : Export rapport DOCX/PDF bouton UI
- 10C : Comparable/Adjustment editor inline
- 10D : Valuation card synthèse
- 10E : Fact chips editor manuel

## Decisions

- Tous panels lisent via runtime — Supabase non requis en dev.
- engine/package.py: ZIP V1 = rapport.md + PDF + artifacts + manifest.
- BFF: application/zip passé en binaire (évite corruption).
- Commanditaire sauvé dans session["app_commanditaire"] à la création, lu dans app_session_view.
- SidebarRecent: recherche client-side (filtre dossiers, apparaît >3 dossiers).

## Evidence

- tsc 0 erreurs. test_phase5 8/8. test_phase6 13/13. test_pure 16/16. test_phase9 15/15.

## Open Issues

- Phase 3 bloquée : attente livres MEFQ + NPP 2025.
- Mise en prod Railway + Vercel non encore provisionnés (Phase 10A).
- rapport-versions (Supabase) — intentionnel, graceful fail.
