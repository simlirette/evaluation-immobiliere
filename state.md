# State — eval-immo

_Updated: 2026-05-31 | HEAD: c0edc19 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 3 — T3.1+T3.2+T3.4 done. T3.3 (inspection) ou T3.5 (export) next.

## Plan Status

Plan : `docs/plans/2026-05-31-phase-3-rapport-expert.md`

- [x] T3.1 — 16 éléments vérifiés post-génération (`engine/report_check.py`, c0edc19)
- [x] T3.2 — Grille ajustements dans rapport (prompt LLM + repli déterministe, c0edc19)
- [x] T3.4 — Repli déterministe 16 sections, MODE DÉGRADÉ honnête (c0edc19)
- [ ] T3.3 — Capture inspection structurée (UI DossierPanel + `/app/inspection` + `inspection.json`)
- [ ] T3.5 — Export certifiable (n° permis OEAQ, retrait filigrane contrôlé, trace)
- [ ] T3.6 — Démo bureau (jalon — dossier réel anonymisé bout en bout)

Phase 2 restant :
- [ ] T2.2 — Unification TS/Python (architectural)
- [ ] T2.4 — Tables coûts (Altus — externe)

## Evidence

- 474 tests backend verts (c0edc19)
- report_check : 16 patterns, score 0.88 sur repli déterministe actuel (E2+E15 partiellement couverts)
- Repli déterministe : 16 sections, "À RÉDIGER PAR L'É.A.", "MODE DÉGRADÉ" distinct

## Open Issues

- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
- T3.3 : inspection.json schema + /app/inspection endpoint + UI DossierPanel
- T3.5 : report_export.py + bloc signature n° permis OEAQ depuis profil authentifié
