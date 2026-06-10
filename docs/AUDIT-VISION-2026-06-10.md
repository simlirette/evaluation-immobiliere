# Audit complet — eval-immo vs VISION-PROJET.md + design handoff frontend

**Date :** 2026-06-10 · **HEAD :** `84fe160` (master)
**Références :** `VISION-PROJET.md` (2026-06-10), `frontend/design_handoff_eval_immo/` (Claude Design, 2026-06-10), `docs/workflow-evaluateur-agree.md`, `docs/ANALYSE-ECARTS-PRODUIT-FINAL-2026-05-31.md`

---

## 0. Verdict

**Le backend reflète la vision à ~85 %. Le frontend implémenté diverge structurellement du nouveau design handoff.**

Depuis l'analyse du 2026-05-31 (HEAD `07b0f45`), 81 commits ont exécuté l'intégralité du plan P0→P6 + waves A-D. Les 5 écarts structurels identifiés alors sont **fermés** :

| Écart 05-31 | Statut 06-10 | Preuve |
|---|---|---|
| A1 Savoir inerte (analysis.md jamais injecté) | ✅ Fermé | `2910d9a` injection pipeline+assistant ; RAG pgvector prod 8745 chunks, threshold 0.35 (`e45b3a7`, `5250204`) ; citations normatives + `search_knowledge` (`27e640b`) |
| A2 Grille d'ajustements absente du moteur | ✅ Fermé | `engine/adjustments.py` (date, superficies, garage, état, sous-sol, localisation ; seuil 25 % brut) `bdf2630` ; grille dans le rapport `c0edc19` |
| A3 AMU tampon hardcodé | ✅ Fermé | `engine/amu.py` — 4 critères déterministes (légalement permis / physiquement possible / financièrement faisable / maximalement productif) `3fd9a0e` |
| A4 Mandats spéciaux non gérés | ✅ Fermé (1ʳᵉ vague) | `PLANS-MANDATS-V0.yaml` : 14 plans dont succession, donation, contestation_role, expropriation, liquidation, financement (`7ba8671`) ; `specialized_valuation.py` : indivise, agricole, patrimonial, RPA (`1f0ade0`) |
| C Sources normatives hors dépôt | ✅ Fermé | `backend/knowledge/` (corpus + catalogue + KNOWLEDGE-BASE.md) `aef3dc1` |

Également fermés depuis : 16 éléments NPP vérifiés mécaniquement (`report_check.py`), capture d'inspection élément 14 (`/app/inspection`, `InspectionForm`), export certifiable avec signature É.A. et retrait contrôlé du filigrane, conflit d'intérêts déterministe, lettre de mandat chemin unique Jinja, fail-closed auth, multi-bureau tenant (migrations 007/008 + dashboard `/bureau`), assainissement AMU (contexte investissement derrière `INCLUDE_INVESTMENT_CONTEXT`), masquage PII SIRF (SHA256), CI hermétique + E2E happy path, apicore extrait de api.py, migrations 001-008 **appliquées en prod**.

**Santé technique au 06-10 :** typecheck ✅ · vitest **1188/1188** ✅ · pytest backend : voir §5.

---

## 1. Vision (5 étapes) vs implémentation

### 1.1 Dossier — récolte + identification ⚠️ écart UX principal vs vision

| Exigence vision | Statut |
|---|---|
| Drag & drop mandat / adresse / cadastre | ✅ `DropZone` + `/app/upload`, extraction PyMuPDF + Vision (~30 champs), CP1 |
| Agent **propose** type de mandat → É.A. confirme | ⚠️ Inversé : l'É.A. **choisit** le type dans `NewDossierForm` ; `classify_dossier()` route ensuite automatiquement. Pas de flux « suggestion agent → confirmation » |
| Agent propose type de propriété | ⚠️ Même inversion (champ de formulaire) |
| Agent propose **type de rapport OEAQ** (Complet / Restreint / Sommaire — Arbre 3 du workflow) | ❌ Non modélisé. `type_rapport` = string hardcodée `"evaluation_residentielle_v0"` (api.py:3553). Aucun gabarit restreint/sommaire/examen/consultation (3 gabarits rapport seulement) |

**Écart vision 1.2 :** le cœur du flux d'entrée voulu (dépôt de 3 documents → l'agent déduit et propose les 3 variables → l'É.A. confirme ou corrige) n'existe pas. Aujourd'hui c'est un formulaire manuel suivi d'un routage automatique non confirmé.

### 1.2 Marché — inspection + recherche

| Exigence | Statut |
|---|---|
| Inspection (photos, notes, croquis) | ✅ partiel : `InspectionForm` (élément 14 NPP — date, étendue, observations, état composantes) mais montée dans **DossierPanel**, pas à l'étape Marché comme la vision le place. Croquis non gérés |
| Drag & drop de nouveaux documents à l'étape Marché | ❌ `DropZone` uniquement à l'étape Dossier |
| Recherche de données par l'agent | ✅ Fort : géocodage → Infolot WFS → rôle MAMH → prix SIRF (cache 90 j, PII masquée) ; import JLR CSV ; scoring justifié FR ; diagnostics sources visibles UI (T2.6) |

### 1.3 AMU ✅
4 critères déterministes croisant zonage/CPTAQ/patrimoine/inondable, vérifiable par l'É.A. (checkpoint). Conforme vision.

### 1.4 Analyse — approches ✅ (avec proxys assumés)
- Comparaison : grille d'ajustements moteur + réconciliation + ~150 modules d'analyse frontend.
- Coût : MEFQ + saisie manuelle É.A. (Wave D), marqué PROXY si défauts ; Altus absent (non bloquant, décision actée).
- Revenu + FTA : complets ; TGA/vacance par défaut marqués « VALEUR PROXY » (T2.5).
- 4 checkpoints humains bloquants (CP1 faits, CP2 comparables, CP3 réconciliation, CP4 rapport) — conforme « étapes clés de vérification ».

### 1.5 Rapport ✅
Gabarits + 16 éléments vérifiés mécaniquement (`report_check.py`) + grille d'ajustements dans le livrable + repli déterministe complet + éditeur TipTap + versions + export PDF/DOCX + signature É.A. (profil OEAQ Supabase) + retrait contrôlé du filigrane.

### 1.6 Transversal vision
- « Sources officielles connectées » : ✅ cadastre/rôle/registre foncier publics ; MLS/Centris = import CSV JLR seulement (pas d'API live — limite externe, pas un défaut).
- « Agents/skills bâtis sur la connaissance théorique » : ✅ 26 skills + analysis.md injectés + RAG normatif cité dans le rapport.

---

## 2. Frontend implémenté vs design handoff (`frontend/design_handoff_eval_immo/`)

### 2.1 Ce qui est aligné
- **Design tokens : identiques à 100 %** (palette paper/ink/navy/verdigris/ochre/oxblood, dark mode, radii, shadows, Source Serif 4). `globals.css` reproduit le handoff token pour token, dark inclus.
- Shell sidebar 260px + main pane, stepper 5 étapes, panels par étape (Dossier/Marché/Analyse/Synthèse/Rapport), side cards, design « paper » sur toutes les routes.
- Routes existantes pour 9 des 10 écrans (login, dossiers, dossier/[id], bibliothèque, modèles, archives, paramètres, aide).

### 2.2 Divergence structurelle n° 1 — le workspace dossier
**Le design handoff est document-first ; l'implémentation actuelle est chat-first.**

| Design handoff (vision actuelle) | Implémentation (`src/`) |
|---|---|
| Body grid `1fr 340px` : panels KV riches par étape (Identification 6 KV, Caractéristiques 9 KV, table comparables 7 col, hero synthèse 56px, cover rapport) | Conversation centrée `max-w-[900px]` style Claude : messages agent + chips + corrections inline (sessions UI du 01-02/06) |
| Aside sticky 340px : Faits saillants (11 rows) / Mandat & client / Activité / Documents | SideCard 300px (sous-ensemble) |
| Chat = **capsule compacte fixe** en bas (suggestions + input, max-w 760px) | Chat = **le contenu principal** du panel |
| Topbar : adresse + ID inline, méta ville·type·année·superficie | Adresse + quartier·type (partiel) |

Ce n'est pas un bug — deux philosophies. Mais si `frontend/` est la vision de référence, le workspace dossier est à **rebâtir en panel-first** en conservant le streaming/checkpoints déjà câblés (le chat redevient une capsule).

### 2.3 Divergence n° 2 — Nouveau dossier
Design : route dédiée wizard 4 étapes (Point de départ → Propriété avec recherche+préview → Mandat → Confirmation), footer sticky, validation par étape.
Implémenté : `dossier/nouveau` inline → `NewDossierForm` simple dans le panel. **Wizard absent.**

### 2.4 Divergence n° 3 — pages sur mocks (aucun endpoint backend)
| Page | Implémentation | Backend |
|---|---|---|
| Bibliothèque (Ventes/Marchés/Coûts/Taux) | `bibliotheque-mock.ts` | ❌ aucun endpoint (les ventes JLR/SIRF existent en données mais ne sont pas exposées en bibliothèque) |
| Modèles | `modeles-mock.ts` | ❌ (gabarits réels dans `backend/templates/` non exposés) |
| Archives | `archives-mock.ts` | ⚠️ `/app/archive` existe (archiver) mais la page liste des mocks |

### 2.5 Écrans / éléments du design non implémentés
- Login : design 2 colonnes (quotes rotatives, seal OEAQ, SSO Microsoft, flux sign-up « Vérifier auprès de l'OEAQ », état « Vérification en cours ») — implémentation actuelle plus simple (à vérifier visuellement, mais sign-up OEAQ absent ; invitation via `/admin/inviter`).
- Dossiers : pin/épinglés sidebar (`/app/pin` existe côté backend ; vérifier câblage), vue grid/rows + tri + états (loading shimmer/empty/error/partial) — partiellement présents.
- Paramètres : design 7 sections (Profil, Cabinet, Membres, Intégrations, Utilisation, Sécurité, Préférences) — implémentation à inventorier section par section ; Intégrations/Utilisation probablement absents.
- Hors design (extra dans src/) : `/bureau` (dashboard directeur) et `/admin/inviter` — à intégrer au design (le handoff les ignore ; « Membres » dans Paramètres recouvre partiellement).

### 2.6 Reco frontend (ordre)
1. **Décision produit : panel-first (design) avec chat en capsule** — c'est la divergence qui conditionne tout le reste.
2. Wizard Nouveau dossier 4 étapes (le flux « suggestion agent → confirmation » de la vision 1.2 s'y loge naturellement à l'étape Mandat).
3. Brancher Bibliothèque/Modèles/Archives sur des endpoints réels (exposer ventes scorées, gabarits, dossiers archivés).
4. Login complet (SSO + sign-up OEAQ) + sections Paramètres manquantes.
5. Drag & drop à l'étape Marché + déplacer l'inspection à Marché.

---

## 3. Écarts backend restants (vers « É.A. complet »)

1. **Arbre 3 OEAQ non modélisé** : pas de choix Complet/Restreint/Sommaire/Examen/Consultation/Mise à jour ; 3 gabarits rapport seulement. Impact : tous les livrables sont des rapports complets résidentiel/revenus/commercial.
2. **Flux suggestion→confirmation des 3 variables** (mandat/propriété/rapport) côté API : `classify_dossier` route sans étape de confirmation É.A. dédiée.
3. **Types de biens spécialisés non couverts** : hôtel, station-service (Phase I/II), marina/golf/camping/ski, institutionnel, pré-construction (« as-if-complete »), chalet/riverain. Couverts : indivise, agricole, patrimonial, RPA.
4. Mandats spéciaux : implémentés en plans + logique (dates rétrospectives, avant-après, valeur réelle LFM, décote liquidation) — **profondeur à valider sur un vrai dossier** (T3.6 jamais fait).
5. Croquis d'inspection (vision 2.1) non gérés.
6. Examen / consultation (2 des 3 actes OEAQ) : hors périmètre actuel.

## 4. Risques / dettes ouvertes (inchangés depuis 05-31, hors code)

- **T3.6 — vrai dossier É.A. de bout en bout** : jamais exécuté. C'est LE test de vérité avant tout usage réel.
- **Loi 25** : masquage PII fait + doc `CONFORMITE-LOI25.md` ; l'**avis juridique** externe reste à obtenir. Supabase région Canada en open.
- **OEAQ §6.5** : thèse human-in-the-loop non validée auprès de l'Ordre.
- **Facturation Stripe** : absente (open depuis session-log).
- **Altus/Marshall Swift** : absents (repli MEFQ + saisie manuelle — accepté pour démo, requis si coût certifiable).
- Duplication calculs TS/Python : tranchée par doc « compute display-only » (Wave B) — les compute-* frontend sont décoratifs, le moteur Python est la source de vérité. À surveiller.

## 5. Santé technique

| Check | Résultat |
|---|---|
| `tsc --noEmit` | ✅ 0 erreur |
| vitest | ✅ 1188 tests / 140 fichiers |
| pytest backend | ✅ 1037 passed, 3 skipped (2 min 43) |
| CI | ✅ hermétique (mocks réseau) + E2E happy path (`d113692`) |
| Migrations prod | ✅ 001-008 appliquées (session-log 05-31) ; 009 profiles_ea_fields à vérifier |

## 6. Complétude estimée par axe

| Axe | % | Note |
|---|---|---|
| Pipeline backend résidentiel standard (vision 5 étapes) | ~90 % | Manque arbre 3 + flux confirmation intake |
| Mandats spéciaux | ~70 % | Implémentés, non éprouvés sur dossier réel |
| Types de biens | ~60 % | Standard + 4 spécialisés ; hôtel/essence/etc. absents |
| Connaissance / RAG / citations | ~85 % | En prod ; profondeur corpus à enrichir en continu |
| Frontend vs design handoff | ~55 % | Tokens 100 %, shell ok ; workspace divergent, wizard absent, 3 pages mockées |
| Prêt premier client réel | ~60 % | Bloqueurs : T3.6, avis Loi 25, OEAQ, facturation |

## 7. Plan recommandé (ordre)

1. **T3.6 — dossier réel de bout en bout avec un É.A.** (révèle les vrais écarts avant d'investir plus).
2. **Refonte workspace dossier panel-first** selon `frontend/` + chat capsule (conserver streaming/checkpoints).
3. **Wizard Nouveau dossier** intégrant le flux vision 1.2 : dépôt 3 docs → suggestions agent (mandat/propriété/rapport OEAQ) → confirmation É.A. — inclut la modélisation de l'Arbre 3 côté backend (types de rapport + gabarits restreint/sommaire).
4. Brancher Bibliothèque/Modèles/Archives sur endpoints réels.
5. Drag & drop Marché + inspection déplacée à Marché + croquis.
6. Loi 25 (avis juridique) + contact OEAQ + Stripe — en parallèle, non techniques.

---

## 8. Vérification approfondie (2026-06-10, 2ᵉ passe) — workflow, sources, knowledge

### 8.1 Workflow complet — acceptance É.A. exécutée localement : **PASS**

```
python scripts/run_ea_acceptance.py tests/fixtures/acceptance/ea_acceptance_anonymized_residential.json
→ status PASS : anonymization ✓ runtime_ready ✓ review_valide ✓
  certifiability_gate ✓ package_ready ✓ no_external_evaluator_answers ✓
→ paquet V1 (9 fichiers), requires_human_validation=true
```

Le pipeline bout en bout (intake → checkpoints → approches → revue → paquet) fonctionne en mode strict sur dossier anonymisé. Les plans de mandat encodent déjà `format_rapport: abrege | narratif_complet` + méthodes requises/prépondérantes par CUSPAP/NPP — l'Arbre 3 est donc **partiellement** modélisé (il manque le choix É.A. Complet/Restreint/Sommaire et les gabarits correspondants).

Restes workflow (inchangés §1) : flux suggestion→confirmation à l'intake, inspection/drag-drop à l'étape Marché, croquis, et **T3.6 dossier réel**.

### 8.2 Sources de données — ⚠️ 1 cassée, 2 non vérifiables d'ici

| Source | Test | Résultat |
|---|---|---|
| **Infolot WFS (cadastre)** | live, gratuit | ❌ **404 — service retiré**. `servicesvectoriels.atlas.gouv.qc.ca/IDS_CATASTO_STAC_S_RLOT_QC/wfs` n'existe plus (hôte répond, service absent ; variantes `_WFS/service.svc/get` aussi 404). **La chaîne comparables publics (Infolot→MAMH→SIRF) est brisée à la racine.** Candidats de remplacement à investiguer : `geo.environnement.gouv.qc.ca/donnees/rest/services/Reference/Cadastre_allege/MapServer` (ArcGIS REST), Données Québec « cadastre du Québec ». |
| MAMH (rôle) | cache local | ⚠️ `C:\data\eval-immo\data_cache` vide — non provisionné sur cette machine. Prod = volume Railway `/data/data_cache` (checklist DEPLOYMENT.md non cochée — état prod à confirmer via `provision_mamh_cache.py`). |
| SIRF (Registre foncier) | non lancé | ⚠️ Payant (1,50 $/lot) — pas de creds en local, test à faire avec approbation facturation (`EVAL_IMMO_LIVE_SIRF=1`). Scraping validé 2026-05-21, fragile par nature. |
| JLR CSV | n/a | ✅ Import local, pas de dépendance réseau. |
| Géocodage | non testé | À couvrir par le smoke live. |

### 8.3 Knowledge — câblage ✅, couverture corpus ⚠️ incomplète

**Câblage vérifié :** 26/26 skills ont `analysis.md` ; `engine/skills.py` charge en priorité `analysis.md` complet (sinon SKILL.md sections 2+4) ; RAG prod 8745 chunks (threshold 0.35) ; citations normatives via `source_id` du catalogue.

**Corpus (`backend/knowledge/`, 62 sources, ~17 MB) :** CUSPAP 2026, MEFQ 2025 complet (5 parties + guide + 8 compléments), LFM + 2 règlements, NPP mars 2025 + 11 docs normes, 17 règlements OEAQ (déonto C-26 r.123 incl.), AIC, 7 jurisprudences disciplinaires.

**Manques vs `workflow-evaluateur-agree.md`** (domaines requis par les mandats/biens couverts par le moteur) :

| Manque | Mandats affectés |
|---|---|
| Loi sur l'expropriation (refonte 2023) | expropriation (plan existe, savoir normatif absent) |
| LIR / guides ARC (JVM fiscale, dons P113, roulement art. 85) | succession, donation, roulement |
| Code civil (copropriété divise/indivise, servitudes, emphytéose 1195-1211, superficie 1110-1118) | indivise, condo, droits réels |
| Loi 141 (certificat syndicat) | condo divise |
| LPTAA / CPTAQ | agricole |
| `facteurs-de-rajustement/` (existait dans `C:\Users\simon\knowledge`, non rapatrié) | grille d'ajustements — sourçage des taux |
| Rapports précédents réels (D-REEL) + domaines 14-27 de `knowledge-source` (28 domaines → 10 rapatriés) | profondeur générale |

### 8.4 Actions issues de la vérification

1. **P0 — Réparer Infolot** : trouver le nouvel endpoint cadastre (ArcGIS REST Cadastre_allege ou Données Québec), adapter `engine/infolot.py`, re-passer le smoke. Sans ça, zéro comparable public.
2. P1 — Provisionner/confirmer le cache MAMH en prod + smoke SIRF avec approbation facturation (1 lot connu).
3. P1 — Rapatrier les corpus manquants (expropriation, LIR/ARC, CCQ, Loi 141, LPTAA, facteurs de rajustement) + réindexer le RAG.
4. P2 — Ajouter le smoke géocodage.
