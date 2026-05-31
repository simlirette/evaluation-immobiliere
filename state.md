# State — eval-immo

_Updated: 2026-05-31 | HEAD: 9760cea (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 3 — T3.1–T3.4 done. T3.5 (export certifiable) next.

## Plan Status

Plan : `docs/plans/2026-05-31-phase-3-rapport-expert.md`

- [x] T3.1 — 16 éléments vérifiés post-génération (c0edc19)
- [x] T3.2 — Grille ajustements dans rapport (c0edc19)
- [x] T3.3 — Capture inspection : /app/inspection GET+POST, InspectionForm, DossierPanel (9760cea)
- [x] T3.4 — Repli déterministe 16 sections MODE DÉGRADÉ (c0edc19)
- [ ] T3.5 — Export certifiable : n° permis OEAQ, retrait filigrane contrôlé, trace horodatée
- [ ] T3.6 — Démo bureau (jalon)

## Evidence

- 34 tests P3 + P0 + P1 verts (9760cea)
- 0 erreurs TS (npx tsc --noEmit)
- InspectionForm : date/type/étendue/observations/accès, POST /app/inspection
- inspection.json injecté dans rapport section 14 (réel ou "À compléter")

## Open Issues

- T3.5 : report_export.py — bloc signature n° permis OEAQ depuis profil auth, retrait filigrane CP4
- T3.6 : dossier réel anonymisé bout en bout, chrono mesuré
- T2.2 : décision TS/Python source de vérité (architectural, différable)
