# State — eval-immo

_Updated: 2026-05-31 | HEAD: 1ed16b1 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 3 ✅ (sauf T3.6 jalon démo). Prochaine : Phase 4 ou T3.6.

## Plan Status

### Phase 3 — Rapport expert ✅

- [x] T3.1 — 16 éléments vérifiés post-génération (c0edc19)
- [x] T3.2 — Grille ajustements dans rapport (c0edc19)
- [x] T3.3 — Capture inspection /app/inspection, InspectionForm (9760cea)
- [x] T3.4 — Repli déterministe 16 sections MODE DÉGRADÉ (c0edc19)
- [x] T3.5 — Export certifiable : signature É.A., retrait filigrane, SignatureForm (1ed16b1)
- [ ] T3.6 — Démo bureau (jalon opérationnel — dossier réel anonymisé bout en bout)

### Phase 4 — Couverture métier (prochaine)

Plan : `docs/plans/2026-05-31-phase-4-couverture-metier.md`
- T4.1 — Mandat succession (date rétrospective/JVM)
- T4.2 — Contestation LFM (date triennale)
- T4.3 — Expropriation avant-après
- T4.4 — Liquidation
- T4.5 — Types de biens spécialisés

## Evidence

- 18 tests P3 verts, 0 TS errors (1ed16b1)
- generate_certified_html/pdf/docx : sans filigrane, bloc signature complet
- SignatureForm : signe + génère HTML/PDF certifié via /app/signature + /app/signature/export

## Open Issues

- T3.6 : dossier réel anonymisé requis — jalon opérationnel
- T2.2 : unification TS/Python (architectural, différable)
- T0.5+T1.3 prod : migrations 002–006 + index_corpus()
