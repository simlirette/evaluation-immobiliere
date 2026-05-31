# State — eval-immo

_Updated: 2026-05-31 | HEAD: 90016c4 (branch: docs/audit-et-plans-2026-05-31)_

## Current Goal

Phase 6 partielle done. T6.1 (api.py découpe) ou T6.4 (CI mocks) next.

## Plan Status

### Phase 6 — Qualité & dette (partiel)

- [x] T6.2 — data_enrichment : INCLUDE_INVESTMENT_CONTEXT flag (scores hors OEAQ gérés) (90016c4)
- [x] T6.5 — Dead code : ThemeToggle.tsx + TabBar.tsx supprimés (90016c4)
- [x] T6.6 — Observabilité tokens réels : track_llm_usage branché rapport + assistant (90016c4)
- [ ] T6.1 — Découper api.py 6000+ lignes en modules (~30 Ko max)
- [ ] T6.3 — Unification TS/Python (Python = source vérité, frontend = affichage)
- [ ] T6.4 — CI durcie + E2E happy path

### Phases antérieures ✅

P0–P5 : voir session-log.md pour détails.

## Evidence

- 78 tests P3+P4+P5+valuation verts (90016c4)
- 0 TS errors après suppression dead code (npx tsc --noEmit avant suppression)
- INCLUDE_INVESTMENT_CONTEXT=0 (défaut) : enrich_case ne calcule plus 8 scores hors périmètre

## Open Issues

- T6.1 : api.py 6000+ lignes — refactor risqué, tester chaque route après
- T6.4 : CI sans accès réseau (data_enrichment, SIRF, Infolot) + E2E fixture
- T0.5 prod : appliquer migrations 002–008 sur Supabase
- T3.6 : démo bureau dossier réel
