# Analyse exhaustive — eval-immo vers le produit final É.A.

**Date :** 2026-05-31
**Portée :** `C:\Users\simon\eval-immo` (HEAD `07b0f45`) + base de connaissances `C:\Users\simon\knowledge(-source)`
**Dépôt :** https://github.com/simlirette/evaluation-immobiliere (branche `main`)
**Objectif de la cible :** un assistant capable d'exécuter toutes les tâches d'un évaluateur agréé, produisant un résultat identique à celui d'un É.A. expert, l'É.A. ne faisant que diriger les agents et confirmer les points clés. Toutes les sources utilisées par un É.A. doivent être liées au dossier ; toute la connaissance métier doit vivre dans le projet.

> **Méthode.** Analyse fondée sur lecture directe du code (`backend/engine/*`, `backend/integration/*`, `backend/skills/*`, `src/`), des docs (`docs/*`, `_audit/2026-05-20/*`), de l'état (`state.md`) et de l'inventaire de `knowledge/`. Les fichiers très volumineux non lus intégralement sont signalés « à vérifier » : `backend/api.py` (256 Ko), `backend/engine/runtime.py` (2 499 l., lu 1-1302), `backend/engine/data_enrichment.py` (5 353 l., lu 1-1302).

---

## 0. Verdict en une page

L'écart par rapport à l'audit du 18 mai est énorme : le plan S1→S12 du 20 mai a été **exécuté**. Le système n'est plus un prototype. On a aujourd'hui :

- un pipeline 7 étapes routé par type de mandat (`orchestrator.py` + `PLANS-MANDATS-V0.yaml`) ;
- 4 checkpoints humains bloquants horodatés avec hash d'instantané (`checkpoints.py`) ;
- un moteur de conformité **déterministe** B001–B008 + avertissements W (`compliance.py`) ;
- des approches de valeur conditionnelles par type de bien, comparaison/coût/revenu/FTA (`valuation.py`) ;
- un parseur CSV JLR + un pipeline de comparables publics réel (Infolot WFS cadastre → rôle MAMH → **prix de vente via scraping du Registre foncier SIRF**, avec cache 90 j) ;
- un routage LLM par tâche (GPT-4o pour la rédaction et la vision, GPT-4o-mini ailleurs) ;
- gabarits de lettre de mandat et de rapport (résidentiel / revenus / commercial) ;
- export PDF + DOCX filigranés « BROUILLON NON CERTIFIÉ », paquet ZIP V1 + manifeste ;
- une suite de tests substantielle (253 tests backend, ~150 modules `compute-*` frontend testés) ;
- BFF proxy (`/api/runtime/[...path]`), middleware d'auth, design system « paper » complet sur 13 routes.

**Mais** l'écart vers « résultat identique à un É.A. expert » et « toutes les sources / toute la connaissance dans le projet » reste réel et structurel. Les cinq écarts qui comptent :

1. **La connaissance des skills n'atteint jamais le LLM.** Les `analysis.md` (le vrai savoir métier) ne sont injectés dans **aucun** appel LLM. Les skills servent de métadonnées de traçabilité, pas de contexte actif. Aucun RAG, aucune citation normative source→rapport.
2. **La grille d'ajustements — le cœur de l'approche par comparaison — n'est pas calculée par le moteur.** Le backend fait une moyenne pondérée des prix bruts + somme des ajustements saisis à la main. Les ~150 fonctions d'analyse fines vivent côté frontend et ne nourrissent pas le rapport exporté.
3. **L'AMU est un tampon, pas une analyse.** `umpp_conclusion.json` met les 4 critères et `conformite_zonage` à `True` en dur ; le zonage récupéré n'entre pas dans la logique.
4. **Couverture métier partielle.** Le résidentiel standard est solide ; les mandats spécialisés richement documentés (succession rétrospective, expropriation avant-après, contestation de rôle LFM, JVM fiscale, liquidation) ne sont pas exécutés par le moteur.
5. **Pré-requis « premier client » non levés :** Loi 25 (avis juridique), application des migrations Supabase prod, isolation tenant/RLS, et capture d'inspection (élément 14 NPP) absente.

Le reste de ce document détaille (A) l'écart produit/ingénierie, (B) l'analyse « dans la peau d'un É.A. », (C) le diagnostic spécifique connaissances/sources, puis une feuille de route priorisée.

---

## PARTIE A — Écarts vers le produit final (par domaine)

### A1. Injection de la connaissance métier dans les agents — *écart n° 1*

**Constat (code).** `engine/runtime.py::RuntimeEngine._enrich_artifact_llm()` charge uniquement `load_agent_system_prompt(AGENTCONFIG)` comme message système, puis un prompt utilisateur construit par `_build_enrichment_prompt()`. À aucun moment le contenu de `SKILL.md` ni de `analysis.md` n'est lu ni injecté. `engine/skills.py` découvre les skills et construit un registre `skills_by_agent`, mais ce registre n'est propagé que dans les **événements/artefacts** (traçabilité), jamais dans le contexte d'un appel LLM.

**Conséquence.** Toute la richesse encodée — ex. `recherche-mefq-methodologie/analysis.md` (13 principes, formules MRB/TGA/coût, seuils 15 %/30 obs., base 1er juillet 1997…), `analyse-amu/analysis.md` (4 critères, terrain vacant vs amélioration) — **n'influence pas** ce que l'agent produit. Les system prompts AGENTCONFIG (~40 lignes) sont la seule connaissance active. C'est exactement le « gap critique » de l'audit du 18 mai, toujours non résolu.

**Pour atteindre la cible.**
- Injecter, par étape, les sections pertinentes des `analysis.md` des skills `skills_allowed` de l'agent (troncature intelligente, budget tokens).
- À terme : RAG sur la base de connaissances (voir C) pour aller au-delà des résumés `analysis.md`.
- Vérifier le même point dans l'assistant conversationnel (`api.py::llm_assistant_answer`, non lu — 256 Ko) : la mémoire indiquait un dict `_AGENT_SYSTEM_PROMPTS` simplifié au lieu des AGENTCONFIG. **À confirmer / corriger.**

### A2. Approche par comparaison — grille d'ajustements absente du moteur

**Constat.** `valuation.py::_calculate_comparative_approach()` : valeur = `weighted_mean(prix_vente, poids=score)` + `somme(ajustements où validation_humaine==True)`. Les ajustements ne sont **pas calculés** par le moteur ; ils doivent être fournis dans `case["ajustements"]`. Il n'y a pas de calcul d'ajustements par paires (terrain, surface habitable, âge/vétusté, garage, stationnement, sous-sol fini, localisation), ni de taux $/unité dérivés du marché.

Or un rapport d'É.A. **est** une grille d'ajustements par comparable, avec prix ajustés, fourchette resserrée et valeur indiquée. Les ~150 modules `src/lib/compute-*.ts` (paired sales, time-adjusted price, bracketing OEAQ, $/m², z-score, sensibilité…) sont **côté frontend** et testés par vitest, mais ils ne nourrissent pas l'artefact `calculs_approche_comparative.json` ni le rapport exporté.

**Risque produit.** « Cerveau dédoublé » : l'É.A. voit des analyses riches dans les panneaux Marché/Analyse, mais le `brouillon_rapport.md` exporté est généré par un seul appel LLM à partir d'artefacts qui **ne contiennent pas** la grille fine. Le résultat exporté n'égale pas le rendu d'un É.A. tant que la grille n'est pas calculée côté moteur (déterministe) et reprise dans le rapport.

**Pour atteindre la cible.**
- Porter la logique d'ajustements (au moins paires/$ par caractéristique) dans `engine/valuation.py`, produire une vraie grille dans `calculs_approche_comparative.json`.
- Faire en sorte que la rédaction consomme cette grille (tableau d'ajustements dans le rapport).
- Décider de la source de vérité des calculs : aujourd'hui dupliqués TS (frontend) / Python (backend) avec des logiques différentes — risque d'incohérence à l'export.

### A3. AMU (analyse du meilleur usage) — conclusion en dur

**Constat.** `runtime.py` (bloc `amu-analyst`/`umpp_conclusion.json`) : `usage_retenu = usage_map[type_bien]`, `conformite_zonage = True`, les 4 critères tous `True`, `umpp_differe_usage_actuel = (usage_retenu != type_bien)`. Le narratif `amu_analyse.md` est enrichi par LLM et **affiche** le zonage récupéré, mais la **conclusion structurée** ne raisonne pas sur le zonage, ni sur « légalement permis / physiquement possible / financièrement faisable / maximalement productif ». Confirme le gap brainstorm Q6.1.

**Conséquence.** L'AMU ne peut jamais conclure un usage optimal différent de l'usage actuel sur une vraie base (sauf via le narratif LLM non contraint). Pour un terrain en zone commerciale avec vieille maison, le système ne produira pas l'analyse de transition attendue.

**Pour atteindre la cible.** Implémenter une logique AMU réelle : croiser `zonage_urbanisme` (déjà récupéré), `zone_agricole` (CPTAQ), `patrimoine_culturel`, `zone_inondable` avec les 4 critères ; produire une conclusion défendable et alimenter le choix des approches.

### A4. Couverture des mandats et types de biens

**Constat.** `PLANS-MANDATS-V0.yaml` couvre 8 plans : résidentiel standard, multifamilial, immeuble à revenus, commercial, industriel, terrain, mise à jour, assurance. `classify_dossier()` ne route `but_evaluation` que pour « assurance ». Le `docs/workflow-evaluateur-agree.md` (très complet : ~11 types de mandat, ~20 types de propriété) décrit des logiques **non implémentées** :

- **Succession / donation / roulement** : date d'évaluation **rétrospective** imposée (décès, don) → toutes les données doivent être contemporaines/antérieures ; JVM fiscale (LIR) ≠ valeur marchande. Aucune gestion de date rétrospective ni de définition de valeur fiscale dans le moteur.
- **Contestation du rôle municipal (LFM)** : « valeur réelle » art. 42, **date de référence triennale** (≈ 18 mois avant l'entrée en vigueur). Non géré.
- **Expropriation** : méthode **avant-après**, préjudices accessoires, défense au TAQ. Non géré.
- **Liquidation/faillite** : valeur de liquidation ordonnée/forcée avec décote justifiée. Non géré.
- Types de biens spécialisés (RPA, hôtel, station-service/contamination, marina/golf, patrimonial, copropriété indivise…) : richement documentés (workflow) mais non opérationnalisés (going concern, FF&E, Phase I/II, décote d'illiquidité, etc.).

**Lecture.** C'est cohérent avec la portée démo (« résidentiel unifamilial seulement »). Mais par rapport à la **cible** « toutes les tâches d'un É.A. », c'est l'écart fonctionnel le plus large. À planifier explicitement par vagues post-démo.

### A5. Approches coût et revenu — non certifiables sans tables

**Coût (`valuation.py::calculate_cost_approach`).** Formule correcte (coût neuf × facteurs − dépréciation + terrain ; mandat assurance = remplacement neuf sans terrain ni dépréciation). Mais les coûts unitaires défaut (`_DEFAULT_COST_PER_M2` 2 400/2 600/3 000/2 200 $/m²) ne servent que si `allow_default_cost_reference=True`, sinon `INSUFFICIENT_COST_DATA`. **Aucune table Altus / Marshall Swift / barème MEFQ (base 1997 + 5 facteurs).** Décision actée : proxy + filigrane « VALEUR PROXY — non certifiable OEAQ ». Conforme à la décision, mais c'est un écart vers le produit final (approche coût certifiable).

**Revenu (`calculate_income_approach` + `calculate_fta_approach`).** RBP→RBE→RNE→capitalisation et un DCF/FTA complets et propres. Mais défauts : vacance 5 %, ratio dépenses 35 %, **TGA par défaut par type** (`_DEFAULT_CAP_RATE`). Un É.A. doit dériver le TGA de transactions réelles ; les défauts sont des béquilles de brouillon, à signaler comme tels et idéalement remplacés par un TGA marché.

### A6. Comparables — chaîne de données

**Acquis (fort).** Deux chemins réels :
- **JLR CSV** (`ingestion.py::parse_jlr_csv`) avec alias de colonnes, détection séparateur/BOM, `source_type="mls_centris"`.
- **Public** (`comparables_builder.py`) : géocodage → Infolot WFS (lots cadastraux gratuits) → rôle MAMH (XML 5 villes + CSV Montréal) → **enrichissement prix via SIRF** (`registre_foncier.py`, scraping validé 2026-05-21, 1,50 $/lot, cache disque + Supabase 90 j). Scoring métier explicable (`tools.py::score_comparable`, pondérations + pénalités + justification FR).

**Écarts.**
- MAMH ne fournit pas de prix (rôle) ; sans SIRF (ou hors quota de 10 lookups), `prix_vente=0` → comparable inutilisable (`is_usable_comparable` exige prix>0 + date ISO). La couverture publique réelle dépend donc fortement de SIRF (identifiants `SIRF_USERNAME/PASSWORD`, coût, fragilité du scraping HTML).
- Le scraping SIRF est un point de fragilité (changement de DOM = casse silencieuse, non-bloquante mais comparables vides).
- Champs cadastraux MAMH → `type_bien` via CUBF heuristique ; risque de mismatch.

### A7. Sécurité, multi-tenant, conformité Loi 25

- **Middleware** présent (`src/middleware.ts`), **BFF proxy** présent (`src/app/api/runtime/[...path]/route.ts`) — les deux P0 de l'audit du 8 mai sont adressés.
- **Open issue (state.md) :** migrations Supabase **002+003+004 non appliquées en prod**. Tant qu'elles ne le sont pas, persistance/auth prod incertaines.
- **Isolation tenant / RLS multi-bureau :** non vérifiée ; multi-bureau = roadmap automne 2026. À confirmer que les dossiers d'un bureau ne sont pas accessibles à un autre.
- **Loi 25 :** action A1 (avis juridique + inventaire des données personnelles + politique de rétention) **non faite** — bloquant légal avant premier client payant (dossiers contiennent adresses, propriétaires, valeurs).
- **§6.5 OEAQ / divulgation :** aucun contact OEAQ ; thèse human-in-the-loop défendable mais non validée juridiquement.
- **CORS backend** en prod : à confirmer restreint (l'audit notait `*`).

### A8. Inspection / visite — élément NPP manquant

Le workflow et le SKILL rédaction exigent l'**information sur l'inspection** (élément 14) et l'attestation (« inspection conforme aux normes »). Le système ingère des photos (description Vision) mais **n'a pas de capture d'inspection structurée** (date de visite, étendue, observations, état des composantes). Sans cela, l'attestation ne peut être véridique et le rapport n'est pas certifiable. Écart pour la certifiabilité réelle.

### A9. Rapport final — complétude des 16 éléments

- Gabarits présents : `templates/rapport_residentiel_unifamilial.md`, `rapport_immeuble_revenus.md`, `rapport_commercial.md`, `lettre_mandat_residentiels.md`.
- **À vérifier :** que `generate_brouillon_rapport` (dans la partie non lue de `runtime.py`/`api.py`) **utilise** réellement ces gabarits et garantit la présence des 16 éléments CUSPAP/NPP avec données réelles (pas un seul prompt libre). Le SKILL `redaction-rapport-evaluation` documente parfaitement la structure ; reste à garantir que la génération la respecte mécaniquement.
- Export PDF/DOCX (`report_export.py`) correct, filigrane « BROUILLON NON CERTIFIÉ », paquet V1 (`package.py`) `requires_human_validation=True`. Bon. La **signature/certification finale** (n° de membre OEAQ, sceau, signature) n'est pas un flux implémenté — volontaire (l'É.A. signe hors outil), mais à clarifier pour le produit final.

### A10. Checkpoints — solides, à finir de câbler

`checkpoints.py` : CP1 faits / CP2 comparables / CP3 réconciliation / CP4 rapport, log JSONL horodaté + `confirmed_by` (UUID Supabase) + `snapshot_hash` SHA-256, gate `assert_checkpoint_confirmed` → `CheckpointRequiredError` (HTTP 409). Conforme à la thèse de conformité. **À vérifier :** que **toutes** les voies d'avancement passent par les gates (aucune route API ne contourne), et que l'auth réelle alimente `confirmed_by` (pas une string libre).

### A11. Données d'enrichissement — sur-ingénierie hors périmètre OEAQ

`data_enrichment.py` fait **5 353 lignes**. WDS StatCan est désactivé (stubs `return None`, conforme à la décision), mais le module conserve un volume considérable de sources tangentielles injectées dans `fiche_bien` : climat (Open-Meteo), criminalité, indices qualité de vie, **score d'investissement**, **score de risque**, ratio prix/loyer, abordabilité, projection de valeur à 5 ans, etc.

**Problème.** Un rapport d'É.A. n'a pas besoin de « score d'investissement » ni d'« indice de qualité de vie » ; pire, ce contenu non professionnel risque de fuiter dans la fiche/rapport. C'est du scope creep par rapport au workflow OEAQ (qui cite Altus, Marshall Swift, SCHL, zonage, rôle). Recommandation : isoler strictement les enrichissements **utilisés par le rapport** (zonage→AMU, SCHL conditionnel locatif, rôle municipal cross-check) et mettre le reste derrière un flag/hors rapport. Réduit la surface de maintenance et le risque de contenu non conforme.

### A12. Maintenabilité

- `api.py` = **256 Ko** (handler HTTP natif monolithique). Difficile à tester/faire évoluer. Candidat à découpage par domaine.
- `runtime.py` = 2 499 l. ; le constructeur `fiche_bien` (≈ 800 lignes de blocs `if case.get(...)`) est très lourd — lié à A11.
- Doublons de logique frontend (TS) / backend (Python) pour calculs de valeur — risque de divergence.
- Dead code connu (`ThemeToggle.tsx`, `TabBar.tsx`).

### A13. Tests / CI / observabilité

- 253 tests backend (vs 0 au 8 mai) — gros progrès ; ~150 modules `compute-*` testés côté frontend.
- **À vérifier :** workflow GitHub Actions (`.github/workflows/`) exécute bien backend + frontend en CI. L'audit notait tests d'intégration HTTP réels dans `DataEnrichment` (brainstorm 6.3) → risque de flakiness hors-ligne ; vérifier qu'ils sont mockés.
- Pas de couverture E2E « happy path » runtime+frontend mentionnée.

---

## PARTIE B — Analyse « dans la peau d'un É.A. qui l'utilise »

Parcours d'un dossier réel, friction par friction.

**1. Ouverture du dossier / lettre de mandat.** Je saisis client, adresse, objet, honoraires, délai → lettre PDF. *Bien.* Mais : l'objet de mandat « succession » me donnera-t-il une date d'évaluation **rétrospective** et une JVM fiscale ? Non — le routing ne distingue pas (A4). Je devrai corriger à la main, ce qui contredit « l'agent fait le travail ».

**2. Dépôt des documents / faits.** J'uploade contrat, acte, photos. Extraction PyMuPDF + Vision, ~30 champs (`_STRUCTURED_FIELDS_SCHEMA`), écran CHECKPOINT 1 « voici ce que j'ai extrait » avec champs manquants en orange. *Très bon.* Friction : si OpenAI est indisponible, l'extraction Vision tombe ; `ingest_uploaded_documents` lève désormais une erreur visible (bien). Mais la **visite/inspection** n'est nulle part : je ne peux pas consigner ma visite, alors que l'attestation l'exige (A8).

**3. AMU.** L'outil conclut « usage actuel = meilleur usage » presque toujours, zonage « conforme » par défaut (A3). Pour un dossier standard ça passe ; dès que le zonage diverge, l'AMU est fausse et je ne peux pas m'y fier. Je dois la refaire — donc l'outil ne « fait » pas l'AMU, il la mime.

**4. Comparables (CHECKPOINT 2).** J'importe mon CSV JLR ou je laisse le pipeline public. Scoring + justification FR par comparable, sélection ≥ 3. *Excellent et défendable §6.5.* Friction : sans JLR ni SIRF, les comparables publics ont `prix_vente=0` et disparaissent ; je me retrouve sans comparables exploitables sans comprendre pourquoi (diagnostic source existe mais est-il visible dans l'UI ?).

**5. Calculs / réconciliation (CHECKPOINT 3).** Là où un É.A. attend **sa grille d'ajustements** (par comparable, par caractéristique, prix ajusté, fourchette), le moteur me donne une moyenne pondérée + mes ajustements saisis (A2). Les analyses fines existent à l'écran (panneaux) mais ne sont pas la base de la valeur retenue ni du rapport. Sentiment : « jolis graphiques, mais ce n'est pas mon dossier de preuve ». Coût = proxy filigrané ; revenu sur défauts 35 %/5 %/TGA type. Je dois retravailler les chiffres.

**6. Rapport (CHECKPOINT 4).** Brouillon LLM, éditeur en ligne (TipTap), export PDF/DOCX filigrané. *Bon flux.* Risque : le rapport doit contenir les 16 éléments avec mes vraies données et **citer mes sources** ; aujourd'hui les sources normatives (quel article MEFQ, quelle règle NPP) ne sont pas liées (C). Je signe ma responsabilité sur un texte dont je ne vois pas la chaîne de justification normative.

**7. Confiance / responsabilité.** Les checkpoints horodatés + filigrane me protègent (bien). Mais : (a) Loi 25 non réglée — je traite des données personnelles de clients dans un outil dont la conformité n'est pas attestée ; (b) si l'OEAQ me questionne, je dois pouvoir montrer d'où vient chaque chiffre et chaque règle — la traçabilité **données** existe (source_index, diagnostics), la traçabilité **normative** non.

**Synthèse É.A. :** l'outil est un excellent **accélérateur de dossier résidentiel standard** (intake, comparables, mise en forme, conformité formelle). Il n'est pas encore un **substitut de mon jugement analytique** : AMU mimée, grille d'ajustements non produite, mandats spéciaux non gérés, sources normatives non liées. Donc « je dirige et je confirme » est vrai pour la plomberie, pas encore pour l'analyse de valeur.

---

## PARTIE C — « Toutes les sources » et « toute la connaissance dans le projet » (exigences explicites)

### C1. Où est la connaissance aujourd'hui

| Emplacement | Contenu | Dans le dépôt ? | Utilisé au runtime ? |
|---|---|---|---|
| `backend/skills/*/analysis.md` | Résumés métier denses (MEFQ, AMU, approches, conformité…) | **Oui** | **Non** — jamais injecté dans un LLM (A1) |
| `backend/skills/*/SKILL.md` | Rôle, sources déclarées, règles, checklists | Oui | Métadonnées seulement |
| `backend/integration/AGENTCONFIG-*.yaml` | System prompts (~40 l.) | Oui | **Oui** (seule connaissance active) |
| `C:\Users\simon\knowledge\` | `indexed/` (104), `packs/quebec-real-estate-knowledge-pack-v1/` (110, 68 sources, evidence markdown + docling), `facteurs-de-rajustement/`, `repertoire-des-renseignements-prescrits/` | **Non (hors dépôt)** | Non (aucun RAG) |
| `C:\Users\simon\knowledge-source\` | 28 domaines (00-cuspap, 01-mefq, 04-oeaq-normes, 09-jurisprudence, 10-rapports-precedents/D-REEL, 14-27 spécialisés…) | **Non (hors dépôt)** | Non |

**Diagnostic.** « Toute la connaissance dans le projet » est **partiellement** vrai : les résumés `analysis.md` sont dans le dépôt mais inertes ; le corpus normatif complet (MEFQ, CUSPAP/NUPPEC, NPP, jurisprudence, rapports précédents réels) est **hors dépôt** et non interrogeable. Le « knowledge pack v1 » (Aston-like, evidence markdown + docling JSON, empreinte SHA-256) est exactement le matériau d'un RAG — mais il n'est ni dans le backend ni branché.

### C2. Liaison des sources

- **Sources de données :** bien traçées — `source_index.json`, `source_diagnostics`/`source_coverage` (geocoding, infolot, mamh, sirf), `source_id`/`source_type` sur chaque comparable, `annexe_sources.md`. ✔
- **Sources normatives :** **non liées.** Le rapport ne cite pas « MEFQ Partie 3C », « NPP Règle 2.3 », « art. 42 LFM » avec un lien vers le document source. Le SKILL MEFQ exige pourtant ce niveau de citation. Pour atteindre « toutes les sources liées », il faut un RAG citant page/section.

### C3. Ce qu'il faut faire (cible)

1. **Rapatrier le knowledge pack dans le dépôt** (ou un stockage versionné référencé) : `backend/knowledge/` avec evidence markdown + catalogue de sources + empreintes.
2. **Brancher un RAG** (Phase 3 du plan) : chunking MEFQ/NPP/CUSPAP → embeddings (Supabase pgvector déjà prévu) → top-k injecté dans le contexte des agents, avec **citations page/section** rattachées aux sections du rapport.
3. **Injection immédiate (sans RAG)** : à court terme, injecter les `analysis.md` des skills de l'agent dans son contexte (A1) — gain rapide avant le RAG complet.
4. **Lier les sources normatives au rapport** : chaque affirmation réglementaire → référence cliquable vers la source (catalogue knowledge pack).

---

## PARTIE D — Feuille de route priorisée des pièces manquantes

### P0 — Crédibilité analytique et conformité (avant tout usage réel)
1. **Injecter la connaissance des skills dans les agents** (A1) — corrige le décalage « savoir présent mais inerte ». Inclure l'assistant `api.py`.
2. **Grille d'ajustements calculée côté moteur** + reprise dans le rapport (A2) — sans elle, le résultat n'égale pas un É.A.
3. **AMU réelle** croisant zonage/CPTAQ/patrimoine/inondable (A3).
4. **Loi 25** : avis juridique, inventaire données, rétention (A7). **Bloquant légal.**
5. **Appliquer les migrations Supabase 002-004 en prod** + vérifier RLS/isolation tenant (A7).
6. **Capture d'inspection structurée** (A8) pour une attestation véridique.

### P1 — Sources et complétude du livrable
7. **RAG knowledge base + citations normatives** (C) ; à défaut immédiat, rapatrier le knowledge pack dans le dépôt.
8. **Garantir mécaniquement les 16 éléments** via gabarits (A9) ; vérifier `generate_brouillon_rapport`.
9. **TGA / coûts marché** : remplacer les défauts par des valeurs sourcées (Altus/MEFQ/marché) ou afficher clairement le statut « brouillon » (A5).
10. **Visibilité UI des diagnostics de sources** (pourquoi 0 comparable, SIRF indisponible, etc.) (A6/B4).

### P2 — Élargissement métier (post-démo)
11. **Mandats spécialisés** : succession (date rétrospective + JVM), contestation LFM (date triennale, valeur réelle), expropriation (avant-après), liquidation (A4).
12. **Types de biens spécialisés** : revenus 7+/commercial/industriel d'abord, puis RPA/hôtel/contamination/indivision/patrimonial.
13. **Multi-bureau / tableau de bord directeur / facturation** (roadmap automne 2026).

### P3 — Dette technique / qualité
14. **Réduire `data_enrichment.py`** au périmètre OEAQ ; sortir scores investissement/qualité de vie/climat du rapport (A11).
15. **Découper `api.py`** (256 Ko) (A12).
16. **Unifier la logique de calcul** TS/Python (source de vérité unique) (A12).
17. **CI** : mocker les appels HTTP réseau des tests ; ajouter un E2E happy path (A13).
18. **Supprimer le dead code** (`ThemeToggle`, `TabBar`).

---

## Addendum — Vérification approfondie (2026-05-31, 2ᵉ passe)

Lecture ciblée de `api.py`, `runtime.py` (réécriture rapport + AMU), CI, migrations. **Corrige et précise** plusieurs points de la 1ʳᵉ passe.

### Correctif A1 — l'injection de connaissance est *asymétrique* (pas absente partout)
- **Assistant conversationnel (`api.py`, l.4530-4578)** : le prompt système = `load_agent_system_prompt(AGENTCONFIG)` **+ injection des sections 2 (« Connaissances encodées ») et 4 (« Règles critiques ») des `SKILL.md`** autorisés ; fallback `_AGENT_SYSTEM_PROMPTS` (dict simplifié, l.4491). Donc le chat n'utilise PAS des prompts de 3 lignes — c'est corrigé côté assistant.
- **Pipeline (`runtime.py::_enrich_artifact_llm`)** : AGENTCONFIG system_prompt **seulement**. Ni `SKILL.md`, ni `analysis.md`.
- **`analysis.md` (le savoir profond — MEFQ, AMU, approches) n'est injecté nulle part.** Et pour les skills `recherche-*`, la section 2 du `SKILL.md` n'est qu'un **renvoi** vers `analysis.md` (« toutes tes connaissances sont encodées dans analysis.md ») — donc même l'assistant ne reçoit qu'une table des matières, pas le contenu.
- **Conclusion affinée :** le gap n'est pas « skills inertes » mais « profondeur inerte » : le savoir réellement actionnable (`analysis.md`) n'atteint aucun LLM ; le pipeline n'a même pas les `SKILL.md`. Cible : injecter `analysis.md` (tronqué/ciblé) dans le pipeline **et** l'assistant, puis RAG.

### Confirmation A3 + A11 — l'« AMU » est en réalité un tableau de bord d'investissement
`runtime.py` (bloc `amu_analyse.md`, l.1506-1558) : les 4 critères sont du texte fixe (« L'usage de type X est conforme au zonage… Aucune restriction légale identifiée » ; « Critère 4… l'usage actuel constitue l'UMPP »), **toujours** la même conclusion. Entre les critères 3 et 4 sont insérées ~25 sections **hors périmètre OEAQ** : score global + grade, score d'investissement, score de marché, rendement locatif, ratio prix/loyer, coûts de possession, taxes, projection de valeur à 5 ans, indice de qualité de vie, score de risque, criminalité, climat, alertes 🔴🟡🔵… Le document « Analyse du meilleur usage » livré à l'É.A. ressemble à un rapport d'agent immobilier d'investissement, **pas** à une AMU normative. C'est le risque de fuite de contenu non professionnel le plus concret du projet.

### conflit_interets — détection LLM seulement
`runtime.py` l.1560-1566 : artefact déterministe V0 = `conflit_detecte: False` **toujours**. La détection réelle n'existe que si `OPENAI_API_KEY` est présent (override LLM dans `_enrich_artifact_llm`, avec garde anti-faux-positif). Sans clé : aucun contrôle de conflit. Pour un acte OEAQ, le conflit d'intérêts ne devrait pas dépendre de la disponibilité d'OpenAI.

### Lettre de mandat — deux chemins, dont un LLM (contredit la décision Q11)
- Artefact pipeline `lettre_mandat.md` (l.1568-1599) : gabarit inline avec **placeholder « Honoraires : à confirmer »**, et comme `lettre_mandat.md → _raw_md` est une cible d'enrichissement LLM, il est **réécrit par le LLM** (MANDAT-INTAKE) quand la clé est présente. Or la décision du 20 mai était « formulaire + template fixe, **pas LLM** ».
- Chemin séparé : endpoint `/app/mandat/lettre` + `templates/lettre_mandat_residentiels.md` (probable PDF téléchargeable réel). **À confirmer** que c'est bien le template Jinja fixe et que c'est lui qui est livré au commanditaire (la lecture du template est en file d'attente).

### Rapport — gabarits + repli déterministe présents (bon point)
`runtime.py` l.2142-2305 : `_TEMPLATES_DIR`, mapping type_bien → gabarit (`rapport_residentiel_unifamilial.md` couvre condo/duplex/triplex/quadruplex/terrain ; `rapport_immeuble_revenus.md` ; `rapport_commercial.md`), **repli déterministe « avec vraies données » si aucun LLM** (l.2305), et `generate_brouillon_rapport()` (l.2423) appelé en rédaction (l.1704-1706). Les prompts de rédaction (l.2090-2131) exigent explicitement « les 16 éléments obligatoires CUSPAP » + « BROUILLON NON CERTIFIÉ ». **Reste à vérifier** (lecture en file) que la génération **garantit mécaniquement** la présence des 16 éléments (vs simple consigne au LLM) et que le gabarit déterministe est complet.

### Pipeline par segments — gates réellement câblées
`api.py` : `/app/checkpoint/confirm` (l.5714→`app_confirm_checkpoint`), `/app/checkpoint/resume` (l.5721) avec `assert_checkpoint_confirmed` (l.2523) → `CheckpointRequiredError` → **HTTP 409 CHECKPOINT_REQUIRED** (l.5858-5861). `run_case_data(steps_filter=…)` exécute un segment précis (l.1736-1761). `/app/checkpoint/comparables` auto-confirme le CP2 (l.2825). **Reste à confirmer** (en file) que `/start` n'exécute pas les 7 étapes d'un coup en contournant les gates, et que `confirmed_by` vient bien de l'auth Supabase et non d'une string libre.

### Sécurité — CORS + token présents (corrige l'audit du 8 mai)
`api.py` : `Access-Control-Allow-Origin` = origine configurée `EVAL_RUNTIME_ALLOWED_ORIGIN` (pas `*`), en-têtes `Authorization/X-API-Key/X-Evaluator-Id`, vérification **Bearer `EVAL_RUNTIME_API_TOKEN`** (l.5940-5955), et **checks de readiness de déploiement** qui refusent wildcard/origine locale en prod (l.181-207, 321). **Reste à confirmer** (en file) que le token est **exigé** (bloquant) sur les routes privilégiées, pas seulement vérifié.

### Migrations & RLS — le SQL existe (001→005)
`supabase/migrations/` : `001_v3_schema`, `002_sessions`, `003_profiles_roles`, `004_sirf_cache`, **`005_storage_rls_and_rapport_versions.sql`** (RLS storage + versions de rapport). Donc l'isolation par RLS et les rôles bureau/É.A. sont **écrits**. **Mais** `state.md` indique que **002+003+004 ne sont pas appliquées en prod** → l'isolation n'est pas active tant que ce n'est pas fait. **Reste à lire** (en file) le contenu exact des policies RLS de 003/005 pour confirmer l'isolation multi-bureau (tenant) correcte.

### CI
`.github/workflows/ci.yml` présent (1,3 Ko, 18 mai). **Contenu en file de lecture** — vérifier qu'il exécute pytest backend + vitest frontend et qu'il mocke les appels réseau (`data_enrichment`).

### Réévaluation des priorités après cette passe
- A1 reste P0 mais reformulé : **injecter `analysis.md`** (pas seulement « brancher les skills »).
- **Nouveau P0 :** assainir `amu_analyse.md` — sortir les ~25 sections d'investissement/QdV/risque hors du document AMU (et hors rapport). Risque de conformité immédiat.
- **Nouveau P1 :** détection de conflit d'intérêts déterministe (ne pas dépendre du LLM).
- **Nouveau P1 :** aligner la lettre de mandat sur la décision (template fixe, pas LLM) et confirmer le chemin livré.
- Sécurité/CORS/checkpoints : **rétrogradés** de « manquant » à « présent, à durcir/vérifier ».

---

## Clôture — Vérification finale (2026-05-31, 3ᵉ passe, les 5 points fermés)

### 1. Assistant conversationnel — sophistiqué, mais savoir profond toujours absent
`api.py::_build_agent_full_prompt` (l.4557) + `llm_assistant_answer` (l.4830) : prompt = AGENTCONFIG + **sections 2/4 des `SKILL.md`** (budget 3500 car., 900/skill) + bloc contexte + limites ; **tool calling** `fetch_artifact` (boucle multi-tours `_TOOL_MAX_ROUNDS`) ; multi-tour ; modèle `assistant_qa` (gpt-4o-mini). Bien au-delà des « 3 lignes » supposées.
- **Mais** : (a) `analysis.md` jamais injecté (le savoir profond) ; pour les `recherche-*`, la section 2 du `SKILL.md` n'est qu'un renvoi vers `analysis.md` → l'assistant reçoit une table des matières. (b) Le **seul outil** est `fetch_artifact` — pas de `search_comparables`, pas de `search_knowledge`, pas de ré-exécution d'étape. L'assistant **lit** les artefacts, il n'**agit** pas (confirme le gap brainstorm Q1.5 « Q&A ≠ ordonner les prochaines étapes »).

### 2. Génération du rapport — les 16 éléments sont une *consigne*, pas une *garantie* (important)
`runtime.py` l.2085-2444 :
- `generate_brouillon_rapport` → `_build_rapport_prompt_v2` (vraies données : identification, valeurs d'approches, comparables, hypothèses, statut) **+ injection des 3000 premiers car. du gabarit** comme structure à respecter → LLM `redaction_rapport` (gpt-4o). Sinon repli déterministe.
- **Aucune validation post-génération** que les 16 éléments / l'attestation (7 déclarations) / l'UMPP sont présents : tout repose sur l'obéissance du LLM au prompt système (l.2087-2139). Un rapport non conforme peut sortir sans être détecté.
- **La grille d'ajustements n'est pas alimentée :** le prompt passe les comparables (source, adresse, prix, date, score) et les valeurs d'approches, **mais aucun ajustement par caractéristique**. Or le gabarit `rapport_residentiel_unifamilial.md` contient bien une table « Grille d'ajustements » avec des `[ADJ] $` (l.86-97). Le LLM n'a donc rien pour la remplir → soit il laisse les placeholders (rapport incomplet), soit il **invente** des ajustements (interdit par le prompt et dangereux pour la responsabilité É.A.). C'est la manifestation, au niveau du livrable, de l'écart A2.
- **Le repli déterministe (`_generate_rapport_deterministic`, l.2304) est un stub minimal de 6 sections** : pas les 16 éléments, pas d'attestation à 7 déclarations, pas d'UMPP, et il écrit « Aucune inspection physique du bien n'a été effectuée ». Donc si OpenAI est indisponible, le rapport exporté est très loin du standard CUSPAP. Le mode dégradé n'est pas un vrai rapport.

### 3. CI — réelle, à durcir
`.github/workflows/ci.yml` : job **frontend** (typecheck + lint + `npm test` + build, Node 22) et job **backend** (`pytest tests/ -v`, Python 3.12, `requirements-dev.txt`), sur push `main/master` + PR. Bon socle. Manques : aucun mock réseau visible (si les tests `data_enrichment` font des appels HTTP réels → flaky en CI, gap brainstorm 6.3) ; pas d'E2E runtime+frontend ; CI ne déploie pas (pas de gate de déploiement).

### 4. RLS — isolation **par utilisateur**, pas **par bureau** (gap multi-tenant réel)
- 002 : RLS `sessions` via `dossiers.created_by = auth.uid()` + archivage 30 j. 003 : `profiles` (rôles `bureau_admin`/`evaluateur`), trigger de création de profil, `sessions.confirmed_by → auth.users`. 005 : RLS storage par chemin `{uid}/{dossier}/{file}`, `documents`, `pins`, table `rapport_versions` + RLS.
- **Toutes les policies isolent par `created_by = auth.uid()` (utilisateur), il n'existe aucune colonne `bureau_id`/`org_id`.** Conséquence : un `bureau_admin` peut lire tous les **profils** mais **pas** les dossiers de ses évaluateurs. Le modèle de données **multi-bureau** (tableau de bord directeur, attribution, historique centralisé — roadmap automne 2026) **n'a aucune fondation** : il faudra introduire la notion de bureau/tenant et réécrire les policies.
- **De plus :** la source de vérité des dossiers est le **système de fichiers** runtime (`runtime_sessions/…`), Supabase étant un shim (README). L'accès runtime est filtré par `session_access_allowed(session, evaluator_id)` + en-tête `X-Evaluator-Id` (`api.py` l.5981-5997). La RLS Supabase ne protège donc que ce qui est réellement écrit en base — à confirmer que les dossiers/sessions y sont persistés (sinon la RLS est en grande partie théorique). Et `X-Evaluator-Id` doit être posé par le BFF à partir d'une session **authentifiée** (sinon contournable). Migrations 002-005 **non appliquées en prod** (state.md) → rien de tout cela n'est actif aujourd'hui.

### 5. Lettre de mandat — le bon chemin existe, mais en double
`templates/lettre_mandat_residentiels.md` **est** un vrai gabarit Jinja2 (10 sections §6.3, n° de permis, signatures, pas de `[À CONFIRMER]` si champs fournis) — conforme à la décision « template fixe, pas LLM », servi par `/app/mandat/lettre`. **Mais** l'artefact pipeline `lettre_mandat.md` (généré + réécrit par LLM, avec placeholder honoraires) coexiste et le contredit. Cleanup : supprimer/neutraliser l'artefact pipeline LLM et ne garder que le chemin Jinja.

### Auth runtime — token + RBAC présents (corrige davantage l'audit du 8 mai)
`api.py` l.5939-5997 : `_auth_context` (Bearer `EVAL_RUNTIME_API_TOKEN`, `X-API-Key`, token ops superviseur), `_require_permission` (RBAC via `ROLE_PERMISSIONS` → 401/403), `_require_session_access` (→ 403 `SESSION_FORBIDDEN`). **Faille de conception à noter :** si `EVAL_RUNTIME_API_TOKEN` n'est **pas** défini, `_auth_context` retourne `authorized:True, role:local_dev` → **runtime entièrement ouvert**. Acceptable en dev, dangereux si déployé sans la variable ; le check de readiness existe (`_deploy_status_for_required_secret`) mais n'empêche pas le démarrage. À rendre *fail-closed* en prod.

### Bilan de la clôture
Les **5 écarts structurels** (A1 savoir inerte, A2 grille d'ajustements, A3 AMU tampon, A4 mandats spéciaux, C sources normatives) sont **confirmés et inchangés**. La 3ᵉ passe ajoute trois constats nets pour le plan :
- **Rapport :** 16 éléments non garantis mécaniquement + grille d'ajustements non alimentée + repli déterministe = stub. → la qualité du livrable n'égale pas encore un É.A.
- **Multi-bureau :** la RLS est mono-utilisateur ; le tenant bureau est à concevoir de zéro.
- **Sécurité :** fail-closed manquant si le token n'est pas configuré ; rendre obligatoire en prod.

Sécurité de base (CORS, token, RBAC, gates checkpoint, RLS par utilisateur) et CI sont **présents** — il s'agit de durcissement, pas de création. L'analyse est close ; prêt pour la rédaction des plans.

## Annexe — Points à vérifier (non lus intégralement cette session)
- `backend/api.py` (256 Ko) : l'assistant conversationnel charge-t-il les AGENTCONFIG ou un dict simplifié ? Les routes respectent-elles toutes les gates checkpoint ? CORS prod restreint ?
- `backend/engine/runtime.py` 1303-2499 : `generate_brouillon_rapport` utilise-t-il les gabarits et garantit-il les 16 éléments ?
- `backend/engine/data_enrichment.py` 1303-5353 : périmètre réel des sources encore actives.
- `.github/workflows/` : portée CI (backend + frontend), mocks réseau.
- Schéma Supabase (`supabase/migrations/`) : RLS / isolation tenant.
