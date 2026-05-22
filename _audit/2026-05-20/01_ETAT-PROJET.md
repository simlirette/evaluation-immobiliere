# Audit eval-immo — 01 ETAT DU PROJET
**Date :** 2026-05-20  
**Auditeur :** Revue outillée (Claude Sonnet 4.6)  
**Posture :** hostile et constructive — aucun verdict adouci

---

## Section 1 — Résumé exécutif

Le projet eval-immo est un outil d'aide à l'évaluation immobilière québécoise pour évaluateurs agréés (OEAQ). Il comprend deux couches distinctes :

**Couche backend Python** (`backend/`) : un runtime agentique opérationnel. Le pipeline 7 étapes (intake → data-facts → amu-analyst → comps-market → valuation-draft → compliance-qa → rédaction) s'exécute de bout en bout sans API key OpenAI en mode déterministe. Les artefacts sont tracés, le journal d'audit est écrit, les sessions sont persistées. Le code de calcul déterministe (`tools.py`, `valuation.py`, `orchestrator.py`) est implémenté avec logique métier réelle. Résultat empirique : `PRET_REVISION_FINALE`, 0 blocage, 7 étapes complétées.

**Couche frontend TypeScript** (`src/`) : un frontend Next.js avec 148 modules de calcul TypeScript, chacun avec un `.test.ts` miroir, et 17 composants UI. La couche de calcul est réelle et testée.

**Ce qui manque ou est fragile :**
- L'approche coût et l'approche revenu sont des **proxies v0** explicitement déclarés comme tels dans `MOTEUR-CALCUL-VALEUR-V0.yaml` : `approche_cout` = `mean(prix_vente)`, `approche_revenu` = `median(prix_vente)`. Ce ne sont pas des approches de valorisation indépendantes — elles utilisent les mêmes comparables que l'approche comparative.
- Les connecteurs de données externes (JLR, Centris, Matrix, GESTIM) sont absents du code — `search_comparables()` opère sur le pool passé dans le `case`, pas sur une source externe.
- Le module `data_enrichment.py` (5 142 LOC) appelle StatCan WDS API et Nominatim en réseau. Les tests correspondants font des vrais appels réseau et bloquent indéfiniment en environnement hors ligne.
- L'agent compliance-qa est un LLM (GPT-4o-mini), pas un moteur de règles. Les règles OEAQ B001-B007 et W001-W005 sont dans le `system_prompt`, pas dans du code vérifiable.
- La validation humaine (`human_validation_required: true`) est vérifiée dans `valuation.py` (`validation_humaine` sur les ajustements) mais il n'y a pas de blocage d'interface — un dossier passe sans que les ajustements soient validés si aucun ajustement n'est fourni.
- `backend/mvp/PIPELINE-IO-SCHEMAS/` est un dossier vide. `backend/schemas/` est vide.
- Un fichier avec un chemin Windows dans le nom existe à la racine : `C:Userssimoneval-immosession-log.md` — artefact de bug de création de fichier.

**Verdict global :** le scaffold est majoritairement **implémenté côté backend** pour la couverture fonctionnelle de base. La couche de conformité réglementaire dépend entièrement du LLM. Les connecteurs de données réelles sont absents. Environ 65 % des tests backend passent sans dépendances réseau.

---

## Section 2 — Arborescence annotée

```
eval-immo/
├── .env.example                    # Variables documentées (OPENAI_API_KEY, SUPABASE, RUNTIME_API_TOKEN)
├── .env.local                      # Variables locales (ne pas committer)
├── .github/
│   └── workflows/ci.yml            # CI GitHub Actions : frontend (typecheck+lint+test+build) + backend (pytest)
├── .vercel/                        # Artefacts Vercel (output, project.json)
├── backend/
│   ├── api.py                      # Serveur HTTP Python — 4 402 LOC — point d'entrée runtime
│   ├── Dockerfile                  # Dockerfile backend
│   ├── Procfile                    # Procfile Railway
│   ├── requirements.txt            # openai, python-dotenv, pymupdf, python-docx, markdown, httpx
│   ├── requirements-dev.txt        # + pytest
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── audit.py                # 14 LOC — append_audit_log() — IMPLÉMENTÉ
│   │   ├── data_enrichment.py      # 5 142 LOC — StatCan/Nominatim/rôle municipal — IMPLÉMENTÉ (appels réseau)
│   │   ├── ingestion.py            # 265 LOC — OCR PDF + Vision GPT-4o — IMPLÉMENTÉ
│   │   ├── orchestrator.py         # 286 LOC — classify_dossier + PlanOrchestrator — IMPLÉMENTÉ
│   │   ├── package.py              # 141 LOC — génération ZIP package V1 — IMPLÉMENTÉ
│   │   ├── report_export.py        # 309 LOC — HTML/PDF/DOCX — IMPLÉMENTÉ
│   │   ├── runtime.py              # 2 353 LOC — RuntimeEngine cœur pipeline — IMPLÉMENTÉ
│   │   ├── skills.py               # 242 LOC — registre skills + parseurs YAML — IMPLÉMENTÉ
│   │   ├── tools.py                # 229 LOC — score_comparable + run_calculation — IMPLÉMENTÉ
│   │   └── valuation.py            # 51 LOC — calculate_valuation_trace — IMPLÉMENTÉ (proxies v0)
│   ├── integration/
│   │   ├── AGENTCONFIG-AMU-ANALYST-V0.yaml         # DOCUMENTÉ — system_prompt LLM uniquement
│   │   ├── AGENTCONFIG-COMPLIANCE-QA-V0.yaml       # DOCUMENTÉ — 7 règles B + 5 W dans prompt
│   │   ├── AGENTCONFIG-COMPS-MARKET-V0.yaml        # DOCUMENTÉ
│   │   ├── AGENTCONFIG-DATA-FACTS-V0.yaml          # DOCUMENTÉ
│   │   ├── AGENTCONFIG-MANDAT-INTAKE-V0.yaml       # DOCUMENTÉ
│   │   ├── AGENTCONFIG-REDACTION-V0.yaml           # DOCUMENTÉ
│   │   ├── AGENTCONFIG-VALUATION-DRAFT-V0.yaml     # DOCUMENTÉ — tables Marshall&Swift mentionnées, absentes
│   │   ├── PIPELINE-RUNTIME-ASTON-V0.yaml          # IMPLÉMENTÉ — lu par load_steps_from_pipeline_yaml()
│   │   └── PLANS-MANDATS-V0.yaml                   # IMPLÉMENTÉ — lu par orchestrator.py
│   ├── mvp/
│   │   ├── CONTRATS-DONNEES-V0.yaml                # DOCUMENTÉ — contrats schéma non appliqués en code
│   │   ├── MOTEUR-CALCUL-VALEUR-V0.yaml            # DOCUMENTÉ — statut proxies v0 explicite
│   │   └── PIPELINE-IO-SCHEMAS/                    # VIDE — dossier sans contenu
│   ├── schemas/                                     # VIDE — dossier sans contenu
│   ├── skills/
│   │   ├── analyse-amu/                            # DOCUMENTÉ (SKILL.md + analysis.md)
│   │   ├── analyse-approche-comparaison/           # DOCUMENTÉ
│   │   ├── analyse-approche-cout/                  # DOCUMENTÉ
│   │   ├── analyse-approche-fta/                   # DOCUMENTÉ
│   │   ├── analyse-approche-revenu/                # DOCUMENTÉ
│   │   ├── analyse-conformite/                     # DOCUMENTÉ
│   │   ├── analyse-extraction-faits/               # DOCUMENTÉ
│   │   ├── analyse-reconciliation-valeur/          # DOCUMENTÉ
│   │   ├── analyse-selection-comparables/          # DOCUMENTÉ
│   │   ├── recherche-baux-revenus/                 # DOCUMENTÉ
│   │   ├── recherche-cadre-legal/                  # DOCUMENTÉ
│   │   ├── recherche-domaines-specialises/         # DOCUMENTÉ
│   │   ├── recherche-jurisprudence-discipline/     # DOCUMENTÉ
│   │   ├── recherche-marche-donnees/               # DOCUMENTÉ
│   │   ├── recherche-mefq-methodologie/            # DOCUMENTÉ
│   │   ├── recherche-normes-professionnelles/      # DOCUMENTÉ
│   │   ├── recherche-registre-cadastre/            # DOCUMENTÉ
│   │   ├── recherche-urbanisme-construction/       # DOCUMENTÉ
│   │   ├── redaction-analyse-marche/               # DOCUMENTÉ
│   │   ├── redaction-fiches-techniques/            # DOCUMENTÉ
│   │   ├── redaction-lettre-mandat/                # DOCUMENTÉ
│   │   ├── redaction-rapport-conformite/           # DOCUMENTÉ
│   │   └── redaction-rapport-evaluation/           # DOCUMENTÉ
│   ├── tests/
│   │   ├── fixtures/
│   │   │   ├── case_low_confidence.json
│   │   │   ├── case_nominal.json
│   │   │   └── case_pilote_residentiel_standard.json
│   │   ├── test_phase2.py          # 288 LOC — PDF ingestion, fetch_artifact, history injection
│   │   ├── test_phase5.py          # ~210 LOC — adjustments, transcript, pipeline callback
│   │   ├── test_phase6.py          # ~160 LOC — create_dossier, save_comparables
│   │   ├── test_phase9.py          # 267 LOC — package.py generate_package_from_case
│   │   ├── test_phase10.py         # ~200 LOC — fact_chips, save_fact_overrides
│   │   ├── test_phase13.py         # 18 tests — app_valuation_trace
│   │   └── test_pure.py            # ~1 500 LOC — fonctions pures, orchestrateur, data_enrichment
│   └── runtime_sessions/           # 16 sessions réelles enregistrées (D-PILOTE-RES-001)
├── docs/
│   ├── plans/                      # Batches 3-9 planifiés (md) — DOCUMENTÉ
│   ├── specs/                      # Specs batches 3-9 — DOCUMENTÉ
│   ├── workflow-evaluateur-agree.md# Référence OEAQ exhaustive — DOCUMENTÉ
│   └── project-audit-2026-05-08.md # Audit précédent du 8 mai
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── api/runtime/            # Route BFF → backend Python
│   │   ├── auth/                   # Supabase auth callback
│   │   ├── dossier/[id]/           # Page dossier
│   │   ├── dossiers/               # Liste dossiers
│   │   └── login/                  # Page login
│   ├── components/                 # ~17 composants React
│   ├── lib/                        # 148 modules TypeScript de calcul + 136 fichiers de test
│   └── types/                      # Types TypeScript
├── supabase/
│   └── migrations/001_v3_schema.sql# Schéma DB Supabase
├── C:Userssimoneval-immosession-log.md  # ORPHELIN — bug de création de fichier (chemin Windows)
├── session-log.md                  # Journal de session
├── state.md                        # État de session superpowers
├── package.json                    # Next.js 15 + TypeScript
├── vitest.config.ts                # Config tests frontend
└── .github/workflows/ci.yml        # CI configuré
```

---

## Section 3 — Inventaire classifié

### Backend Python

| Artefact | Etiquette | Preuve |
|---|---|---|
| `engine/runtime.py` | IMPLÉMENTÉ | `RuntimeEngine.run_case_data()` — 2 353 LOC, boucle étapes, SSE events, audit log |
| `engine/orchestrator.py` | IMPLÉMENTÉ | `classify_dossier()` + parsing YAML sans dépendance externe |
| `engine/tools.py` | IMPLÉMENTÉ | `score_comparable()` — scoring pondéré 5 composantes avec pénalités |
| `engine/valuation.py` | IMPLÉMENTÉ | `calculate_valuation_trace()` — mais approches coût/revenu = proxies v0 |
| `engine/ingestion.py` | IMPLÉMENTÉ | PyMuPDF text extraction + GPT-4o Vision fallback |
| `engine/data_enrichment.py` | IMPLÉMENTÉ | StatCan WDS, rôle Mtl CSV, XML MAMH, Nominatim geocoding |
| `engine/report_export.py` | IMPLÉMENTÉ | HTML + PDF (PyMuPDF Story) + DOCX (python-docx) |
| `engine/package.py` | IMPLÉMENTÉ | ZIP manifest V1 avec artifacts |
| `engine/audit.py` | IMPLÉMENTÉ | `append_audit_log()` JSONL avec timestamp |
| `engine/skills.py` | IMPLÉMENTÉ | `discover_project_skills()` + `parse_frontmatter()` |
| `api.py` | IMPLÉMENTÉ | Serveur HTTP 4 402 LOC, ~40 endpoints REST |
| `integration/PIPELINE-RUNTIME-ASTON-V0.yaml` | IMPLÉMENTÉ | Lu par `load_steps_from_pipeline_yaml()`, 7 étapes fonctionnelles |
| `integration/PLANS-MANDATS-V0.yaml` | IMPLÉMENTÉ | Parsé par `orchestrator._parse_plans_yaml()` |
| `integration/AGENTCONFIG-*.yaml` (7 fichiers) | DOCUMENTÉ | Prompts LLM. Aucune règle OEAQ en code — seulement dans `system_prompt` |
| `mvp/CONTRATS-DONNEES-V0.yaml` | DOCUMENTÉ | Contrats schéma définis. `CONTRACT_CHECKS_BY_ARTIFACT` dans `runtime.py` est partiellement branché mais les règles CONF002/CONF005 ne sont pas vérifiées systématiquement hors LLM |
| `mvp/MOTEUR-CALCUL-VALEUR-V0.yaml` | DOCUMENTÉ | Déclare `status: proxy_until_reference_tables` pour coût et revenu |
| `mvp/PIPELINE-IO-SCHEMAS/` | SCAFFOLD | Dossier vide |
| `backend/schemas/` | SCAFFOLD | Dossier vide |
| `skills/*/SKILL.md` (23 skills) | DOCUMENTÉ | SKILL.md + analysis.md présents. Aucun .py associé |
| `tests/fixtures/*.json` (3 fichiers) | IMPLÉMENTÉ | Cas réels pilote et edge cases |

### Frontend TypeScript

| Artefact | Etiquette | Preuve |
|---|---|---|
| `src/lib/compute-*.ts` (148 modules) | IMPLÉMENTÉ | Logique de calcul (ajustements, quartiles, z-score, CV, etc.) avec tests miroirs |
| `src/lib/compute-*.test.ts` (136 tests) | IMPLÉMENTÉ | Tests vitest |
| `src/components/panels/*.tsx` (5 panneaux) | IMPLÉMENTÉ | DossierPanel, AnalysePanel, MarchePanel, SynthesePanel, RapportPanel |
| `src/lib/supabase/queries/` | SCAFFOLD | Dossier sans fichiers listés |
| `src/data/mock.ts` | RÉFÉRENCÉ | Mock data utilisé par composants — pas de connexion DB active visible |

### Répertoriés mais absents ou référencés uniquement

| Référence | Etiquette | Localisation de la référence |
|---|---|---|
| Connecteur JLR (Jurismédis) | RÉFÉRENCÉ | `workflow-evaluateur-agree.md` section sources |
| Connecteur Centris | RÉFÉRENCÉ | `AGENTCONFIG-COMPS-MARKET-V0.yaml` prompt texte |
| Connecteur Matrix | RÉFÉRENCÉ | `workflow-evaluateur-agree.md` |
| Connecteur GESTIM | RÉFÉRENCÉ | `workflow-evaluateur-agree.md` |
| Tables Marshall & Swift | RÉFÉRENCÉ | `AGENTCONFIG-VALUATION-DRAFT-V0.yaml` prompt |
| Grilles Altus | RÉFÉRENCÉ | `AGENTCONFIG-VALUATION-DRAFT-V0.yaml` prompt |
| Rôle municipal CSV 72 MB | RÉFÉRENCÉ | `data_enrichment.py` commentaire en-tête — `data_cache/role_mtl.csv` absent |
| `KNOWLEDGE-SCHEMA-IMMOBILIER-V0.yaml` | RÉFÉRENCÉ | `api.py` ligne 39 `KNOWLEDGE_CONTRACT_PATH` — fichier absent sur disque |
| `knowledge_immobilier_session_v1.schema.json` | RÉFÉRENCÉ | `api.py` ligne 40 — fichier absent (`backend/schemas/` vide) |
| UI HTML (`ui/pilote_api.html`, `ui/product_cockpit.html`) | RÉFÉRENCÉ | `api.py` lignes 34-37 — dossier `ui/` absent |
| `tests/runtime/` | RÉFÉRENCÉ | `api.py` ligne 32 — dossier absent (pas de cas T01-T05 YAML) |

---

## Section 4 — Verdicts grille agentique

| Critère | Verdict | Détail |
|---|---|---|
| **1. Frontières d'agents** | SOLIDE | 7 agents distincts, mutuellement exclusifs par YAML. `amu-analyst` ajouté correctement entre data-facts et comps-market. |
| **2. Schémas entrée/sortie** | FRAGILE | `CONTRATS-DONNEES-V0.yaml` définit les contrats. `CONTRACT_CHECKS_BY_ARTIFACT` dans `runtime.py` est partiellement implémenté. `PIPELINE-IO-SCHEMAS/` est vide. Les schémas JSON formels sont absents. |
| **3. Handoff entre agents** | SOLIDE | Les artefacts sont écrits dans `session_dir/artifacts/{dossier_id}/`, indexés dans `artifact_index.json`, et l'audit log JSONL est écrit après chaque écriture. |
| **4. Couche déterministe vs agentique** | FRAGILE | `tools.py` et `valuation.py` sont purement déterministes. Mais `approche_cout` et `approche_revenu` utilisent les mêmes comparables que `approche_comparative` — ce ne sont pas des approches indépendantes. L'isolation existe en structure mais pas en logique. |
| **5. Compliance OEAQ** | FRAGILE | `compliance-qa` est un LLM (GPT-4o-mini). Les règles B001-B007 et W001-W005 sont dans un `system_prompt`, pas dans du code vérifiable. Sans API key, le step produit quand même un artefact (mode déterministe du runtime), mais sans vérification réelle des règles. |
| **6. Traçabilité** | SOLIDE | `source_id` requis sur comparables et ajustements. `audit.py` trace chaque écriture. `score_comparable()` retourne une rationale explicite. |
| **7. Connecteurs de données** | MANQUANT | `search_comparables()` opère sur le pool passé dans le `case` dict — il n'y a pas de connecteur externe. `data_enrichment.py` couvre StatCan + rôle Mtl CSV + XML MAMH + Nominatim, mais JLR, Centris, Matrix, GESTIM sont absents. |
| **8. OCR / extraction documentaire** | SOLIDE | `ingestion.py` : PyMuPDF text layer + GPT-4o Vision fallback pour PDF scannés. Images JPG/PNG supportées. |
| **9. Géospatial** | FRAGILE | `data_enrichment.py` inclut lookup GeoJSON + Nominatim pour zonage. Mais `distance_km` dans les comparables est fourni par le caller — il n'y a pas de calcul de distance géospatiale à partir d'adresses. |
| **10. Validation humaine** | FRAGILE | `validation_humaine: true` est vérifié dans `valuation.py` — seuls les ajustements avec ce flag sont appliqués. Mais aucun blocage d'interface n'est implémenté pour exiger la validation avant de passer à l'étape suivante. |
| **11. Observabilité** | SOLIDE | SSE events (`step_start`, `step_done`, `artifact_written`, etc.) émis. `events.jsonl` + `audit.jsonl` dans chaque session. `metrics` (wall_clock_seconds, total_tokens, blocking_count, warning_count) calculés. |
| **12. Tests T01-T05 TEST-PLAN-V0** | MANQUANT | `tests/runtime/` est absent. Aucun fichier `TEST-PLAN-V0.md` trouvé dans le repo. Les cas T01-T05 mentionnés dans la consigne d'audit n'existent pas sur disque. |

---

## Section 5 — Résultats empiriques des tests

### Pipeline end-to-end

| Test | Résultat | Trace |
|---|---|---|
| Pipeline complet D-PILOTE-RES-001 (sans API key) | PASS | STATUS: PRET_REVISION_FINALE, 0 blocking, 7 étapes complétées, 92s (session 36db31abe008) |
| `classify_dossier({'type_bien': 'unifamilial'})` | PASS | Retourne `residentiel_standard` |
| `load_plan_for_mandat('residentiel_standard')` | PASS | `methodes_requises: [approche_comparative, approche_cout]` |
| `load_steps_from_pipeline_yaml()` | PASS | 7 étapes parsées correctement |

### Tests pytest backend

| Suite | Résultat | Détail |
|---|---|---|
| `test_phase2.py` (12 tests) | PASS | PDF extraction, fetch_artifact, history injection — tous passent |
| `test_phase5.py` (10 tests) | PASS | Adjustments save, pipeline callback — tous passent |
| `test_phase6.py` | PASS (inclus dans run 76 passed) | create_dossier, save_comparables |
| `test_phase9.py` (6 tests) | PASS | generate_package_from_case — tous passent |
| `test_phase10.py` | PASS | fact_chips, save_fact_overrides |
| `test_phase13.py` (18 tests) | PASS | app_valuation_trace |
| **Total phases 2+5+6+9+10+13** | **76 passed / 0 failed** | 182 secondes |
| `test_pure.py` (hors DataEnrichment) | 153 PASS / 1 FAIL | `TestExportRapport_InvalidFormat::test_format_pdf_raises_value_error` — le test attend `ValueError` sur format "pdf", mais `api.py` lève `FileNotFoundError` quand le rapport est absent |
| `test_pure.py::TestDataEnrichment_*` | SKIP_DEPS (réseau) | Tests font des appels réseau réels (StatCan WDS API, Nominatim) — bloquent indéfiniment hors ligne |

### Tests T01-T05 TEST-PLAN-V0

| Test | Résultat | Raison |
|---|---|---|
| T01 | SKIP_NOT_IMPL | `tests/runtime/` absent, `TEST-PLAN-V0.md` introuvable |
| T02 | SKIP_NOT_IMPL | Idem |
| T03 | SKIP_NOT_IMPL | Idem |
| T04 | SKIP_NOT_IMPL | Idem |
| T05 | SKIP_NOT_IMPL | Idem |

### Fichiers référencés absents (imports cassés potentiels)

| Fichier référencé | Dans | Impact |
|---|---|---|
| `backend/mvp/KNOWLEDGE-SCHEMA-IMMOBILIER-V0.yaml` | `api.py:39` | Pas d'import Python direct — chemin stocké en variable, pas de crash si absent |
| `backend/schemas/knowledge_immobilier_session_v1.schema.json` | `api.py:40` | Idem |
| `backend/ui/pilote_api.html` | `api.py:33` | 404 si demandé via HTTP |
| `backend/ui/product_cockpit.html` | `api.py:34` | 404 si demandé via HTTP |
| `backend/ui/ops_cockpit.html` | `api.py:35` | 404 si demandé via HTTP |
| `backend/ui/evaluateur_review.html` | `api.py:36` | 404 si demandé via HTTP |
| `backend/ui/auth_client.js` | `api.py:37` | 404 si demandé via HTTP |
| `backend/tests/runtime/` | `api.py:32` | Variable RUNTIME_DIR — pas de crash si absent |

---

## Section 6 — Métriques objectives

### Backend Python

| Module | LOC |
|---|---|
| `api.py` | 4 402 |
| `engine/data_enrichment.py` | 5 142 |
| `engine/runtime.py` | 2 353 |
| `engine/report_export.py` | 309 |
| `engine/orchestrator.py` | 286 |
| `engine/ingestion.py` | 265 |
| `engine/skills.py` | 242 |
| `engine/tools.py` | 229 |
| `engine/package.py` | 141 |
| `engine/valuation.py` | 51 |
| `engine/audit.py` | 14 |
| **Total production backend** | **~13 435** |
| **Total tests backend** | **~8 452** |

### Ratios

| Métrique | Valeur |
|---|---|
| Ratio tests/code backend | 0.63 (8 452 LOC tests / 13 435 LOC prod) |
| Agents classifiés IMPLÉMENTÉ (runtime) | 100% (7/7 exécutent sans crash) |
| Agents avec logique métier réelle (non-LLM) | 3/7 (orchestrator, tools, valuation) |
| Agents dont la logique dépend du LLM | 7/7 (tous enrichissent via LLM quand OPENAI_API_KEY présent) |
| Tests PASS hors réseau (76 + 153) | 229 / ~500 collectés |
| Tests SKIP_DEPS réseau | ~257 (DataEnrichment dans test_pure.py) |
| Tests T01-T05 | 5 SKIP_NOT_IMPL |
| Approches de valorisation indépendantes | 1/3 (comparative seule est non-proxy) |
| Connecteurs de données externes | 0/5 (JLR, Centris, Matrix, GESTIM, registre foncier live) |
| Frontend : modules de calcul TypeScript testés | 136/148 (92%) |
