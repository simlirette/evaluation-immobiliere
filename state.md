# State

## Current Goal
Phase B en cours. B1/B2/B3 (dossier lifecycle) DONE. Prochaines: upload robustness, sources données pipeline.

## Decisions
- Batch 9 spec : docs/specs/2026-05-15-batch9-pipeline-liveview-polish.md
- Pipeline live view : polling /app/state toutes les 2s via usePipelinePolling hook
- Rapport panel resize : DragHandle custom (no lib), localStorage persist, clamp 280px–80vw
- UX polish : PanelSkeleton (remplace PanelLoader), erreur pipeline explicite, badge tab Rapport

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
- Batch 9 (pipeline live view + UX polish): DONE ✓

## Evidence
- 115 tests pass
- Pipeline : mandat-intake(1) → data-facts(2) → amu-analyst(3) → comps-market(4) → valuation-draft(5) → compliance-qa(6) → redaction(7)
- E2E validé 2026-05-15 : session f152408cb9f1, valeur 569 122 $, PRET_REVISION_FINALE, 0 blocking failures

## Phase B (2026-05-15) — IN PROGRESS
- B1 unique dossier_id par session (D-{8hex} UUID) ✓
- B2 pin persistant backend (POST /app/pin, session["pinned"]) ✓
- B3 archive persistant backend (POST /app/archive, session["archived"]) ✓
- localStorage helpers supprimés ✓
- B4 upload robustness: tests fetch-mock, BFF timeout 120s + maxDuration=120 ✓
- Commits: 29aa285, 4eb54dc

## Phase A (2026-05-15) — DONE
- Git aligné : master → origin/master + origin/main, GitHub default = main ✓
- Bug conflit gate fixé : faux positifs LLM (runtime.py + api.py), 115 tests pass ✓
- Pipeline E2E validé bout-en-bout ✓
- Auth decision : Option B local-only (middleware.ts LOCAL_ONLY=true, SidebarFooter caché) ✓

## Phase B (cont.)
- B5 sources données (data_enrichment.py) ✓
  - SCHL rental market via StatCan WDS API (34-10-0133-01, 24h cache)
  - Rôle municipal Montréal CSV (lookup by matricule/address, download_role_mtl())
  - enrich_case() wired into start_runtime() après ingestion
  - fiche_bien.json + amu_analyse.md + comparables_proposes.json enrichis
  - Commit: 880b5cf

- B5b rôle municipal autres villes (MAMH XML iterparse — QC/Laval/Longueuil/Gatineau/Sherbrooke) ✓
  - build_role_xml_index() + lookup_role_xml() + download_role_xml()
  - valeur_totale → evaluation_municipale_totale (absent du CSV Montréal)
  - Commit: 3b07e3e
- B6 zonage urbanisme (Nominatim geocoding + GeoJSON open data + PiP) ✓
  - geocode_address(): Nominatim OSM, cache 7j
  - download_zoning_geojson(): CKAN discovery (Montréal open data)
  - build_zoning_index(): GeoJSON → compact JSON (bbox + ring simplifié 300pts)
  - _pip_exterior(): ray casting pur Python, pas de dépendance shapely
  - lookup_zoning_point(): bbox pre-filter + PiP, module-level cache
  - enrich_case() → case["zonage_urbanisme"] → fiche_bien.json + amu_analyse.md
  - Commit: 10653c4
- B7 CPTAQ zone agricole (WFS GeoJSON + PiP + index) ✓
  - download_cptaq(): WFS GeoJSON endpoint (geoegl.msp.gouv.qc.ca)
  - build_cptaq_index(): GeoJSON → compact bbox+ring index
  - lookup_cptaq(): {en_zone_agricole: bool, NM_MRC, ...} ou None si données absentes
  - Géocodage partagé zonage+CPTAQ (1 seul appel Nominatim par enrich_case)
  - fiche_bien.json + section amu_analyse.md (statut + note légale si en zone)
  - Commit: 59203c5
- B8 patrimoine culturel (WFS GeoJSON Point+Polygon + 50m buffer PiP) ✓
  - download_patrimoine() + build_patrimoine_index() + lookup_patrimoine()
  - {} = non répertorié, dict = trouvé, None = données absentes
  - Section AMU "ATTENTION" si bien répertorié (statut + note légale Ministre Culture)
  - Commit: 2b375d4
- B9 zones inondables MELCC (WFS PiP + sélection zone la plus restrictive) ✓
  - download_inondable() + build_inondable_index() + lookup_inondable()
  - Récurrence: 0_20 / 20_100 / 100 ans — libellés FR + sélection plus restrictive si chevauchement
  - {} = hors zone, dict = en zone (en_zone_inondable: True + recurrence_label)
  - Section AMU "ATTENTION" si en zone (impact financement hypothécaire + assurabilité)
  - Commit: eba96e3
- B10 NHPI StatCan 18-10-0205-01 (indice prix logement neuf + variation annuelle %) ✓
  - fetch_nhpi(): 7 villes QC, indice total/bâtiment/terrain + 13 périodes → variation %
  - Section marché AMU unifiée (SCHL loyers + NHPI indice/variation)
  - Commit: 5a07135
- 170 tests pass

## Open Issues
- Sources données actives : zonage autres villes (QC/Laval/etc.) — CKAN discovery pas encore configuré
- Sources données actives : 6 autres (StatCan census, centris, indice prix logement, etc.) — prochaines phases
- Pour activer rôle municipal : download_role_mtl() (Mtl CSV) ou download_role_xml('quebec') etc.
- Mobile/responsive : absent
- CI/CD : GitHub Actions + Playwright E2E non configurés
- Mobile/responsive : absent
- CI/CD : GitHub Actions + Playwright E2E non configurés
- Sources données : 15+ sources dans informations/ non connectées au pipeline
- Mobile/responsive : absent
- CI/CD : GitHub Actions + Playwright E2E non configurés
- DLC/JLR + Registre foncier : HOLD
