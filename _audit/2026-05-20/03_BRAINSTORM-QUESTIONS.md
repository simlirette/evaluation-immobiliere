# Audit eval-immo — 03 BRAINSTORM QUESTIONS
**Date :** 2026-05-20

Questions ouvertes, groupées par thème. Chaque question cite la ligne de code ou le document qui crée la tension.

---

## Thème 1 — Vision produit et proposition de valeur

### Q1 — L'outil est-il un assistant ou un générateur de rapport ?

**Contexte :** Le pipeline génère `brouillon_rapport.md` de bout en bout (`runtime_sessions/36db31abe008/result.json` confirme `PRET_REVISION_FINALE` sans OPENAI_API_KEY). Mais les artefacts intermédiaires (comparables, calculs) sont des placeholders déterministes basés sur le fixture.

Si l'outil génère le rapport complet (y compris les comparables et les calculs), la proposition de valeur est "automatisation de la rédaction". Si l'outil assiste l'évaluateur qui saisit lui-même les données, la proposition de valeur est "organisation et conformité". Ces deux produits ont des roadmaps radicalement différentes. Lequel est eval-immo ?

### Q2 — Comment justifies-tu à l'OEAQ que l'IA "propose" les comparables ?

**Contexte :** `AGENTCONFIG-COMPS-MARKET-V0.yaml` indique que l'agent propose les comparables, mais `search_comparables()` dans `tools.py` filtre un pool fourni par le caller — il ne fetch rien. L'OEAQ exige que l'évaluateur sélectionne et justifie chaque comparable.

Tu as choisi que l'agent "propose" les comparables, mais le code démontre que c'est l'évaluateur qui les saisit manuellement dans le JSON. Quelle est la réalité opérationnelle et quel est le risque disciplinaire si l'OEAQ considère que l'IA "choisit" les comparables ?

---

## Thème 2 — Frontière humain/machine

### Q3 — Le flag `human_validation_required: true` est-il une protection ou une illusion ?

**Contexte :** `engine/valuation.py` ligne 11 : `sum(float(a.get("montant", 0) or 0) for a in case.get("ajustements", []) if a.get("validation_humaine", False))`. Si `ajustements` est une liste vide (aucun ajustement fourni), le calcul passe avec `adjustment_total = 0.0` et aucun blocage.

Un dossier résidentiel standard sans aucun ajustement traverse le pipeline complet et atteint `PRET_REVISION_FINALE`. L'évaluateur qui reçoit ce rapport a-t-il validé quelque chose, ou a-t-il simplement reçu un document généré depuis le fixture ?

### Q4 — Quel est le protocole quand l'évaluateur désactive la suggestion LLM ?

**Contexte :** `OPENAI_API_KEY` est optionnelle selon `.env.example`. Sans elle, tous les agents fonctionnent en mode déterministe — ils produisent des artefacts structurés mais sans contenu analytique réel (commentaires vides ou génériques dans `_LLM_TEXT_FIELD_BY_ARTIFACT`).

Tu as documenté que le système fonctionne sans API key, mais les AGENTCONFIG décrivent des analyses sophistiquées (AMU, réconciliation, conformité). Sans LLM, ces analyses sont des templates vides. Est-ce qu'un rapport produit sans LLM est certifiable, et si oui, pourquoi payer pour l'API ?

---

## Thème 3 — Choix architecturaux

### Q5 — Pourquoi `compliance-qa` est-il un LLM et non un moteur de règles ?

**Contexte :** `AGENTCONFIG-COMPLIANCE-QA-V0.yaml` liste 7 règles bloquantes (B001-B007) et 5 avertissements (W001-W005). B001 (données manquantes), B002 (source_id absent), B003 (date future), B004 (unités incohérentes), B005 (ajustement sans validation) sont toutes vérifiables en code Python pur sans LLM.

Tu as choisi de mettre ces règles dans un `system_prompt` au lieu de les coder. Un LLM peut ignorer B003 si la date est ambiguë. Un LLM peut halluciner une source_id. Un moteur de règles ne peut pas. Quelle est la justification architecturale pour ce choix, et es-tu prêt à défendre une non-conformité B002 devant l'OEAQ en disant "le LLM n'a pas détecté" ?

### Q6 — `data_enrichment.py` fait 5 142 LOC mais aucun test ne passe sans réseau. C'est un module central ou un module périphérique ?

**Contexte :** `data_enrichment.py` est le deuxième plus gros fichier du projet (5 142 LOC), plus gros que `runtime.py` (2 353 LOC). Il couvre StatCan WDS, rôle municipal CSV, XML MAMH, Nominatim, zonage GeoJSON. Mais ses tests (`TestDataEnrichment_*`) font des appels HTTP réels et ne terminent jamais en mode hors ligne.

Tu as investi massivement dans l'enrichissement de données, mais ces données (loyers SCHL, zonage Nominatim) ne sont pas utilisées dans les calculs de valeur (`valuation.py`) — elles sont injectées dans le `case` mais aucun test ne vérifie qu'elles influencent le résultat final. Enrichissement pour quoi ?

### Q7 — Le modèle de sessions (16+ sessions pour D-PILOTE-RES-001) est-il intentionnel ?

**Contexte :** `backend/runtime_sessions/` contient 16 sessions avec le même input `D-PILOTE-RES-001.input.json`. Chaque run crée une nouvelle session. Il n'y a pas de déduplication ou d'invalidation des anciennes sessions.

En production, si un évaluateur relance le pipeline 10 fois sur le même dossier, tu as 10 sets d'artefacts avec potentiellement 10 valeurs différentes. Quelle session est la "vraie" ? Comment le frontend sait-il quelle session afficher ? L'audit trail OEAQ exige que la version finale soit identifiable.

---

## Thème 4 — Données et connecteurs

### Q8 — Comment les comparables entrent-ils dans le système en production réelle ?

**Contexte :** `engine/tools.py::search_comparables()` prend `pool: list[dict]` — un pool de comparables pré-chargé dans le `case`. En production, cela signifie que l'évaluateur doit saisir chaque comparable avec `comparable_id`, `prix_vente`, `date_vente`, `distance_km`, `surface`, `source_id`, `confidence` dans un JSON avant de lancer le pipeline.

Ce n'est pas un workflow d'évaluateur — c'est un workflow de développeur. Comment est-ce que l'évaluateur saisit ces données en pratique ? Y a-t-il une interface de saisie ? Un import CSV ? Un scraping Centris intégré ? Si la réponse est "manuellement dans le JSON", quel est le gain par rapport à Word + Excel ?

### Q9 — L'approche coût sans tables de coûts de construction — quelle est l'intention à 6 mois ?

**Contexte :** `mvp/MOTEUR-CALCUL-VALEUR-V0.yaml` déclare `status: proxy_until_reference_tables` pour `approche_cout`. `engine/valuation.py::calculate_valuation_trace()` utilise `mean(prix_vente)` pour l'approche coût.

Tu sais que c'est un proxy. Mais ce proxy est présenté comme "approche coût" dans les artefacts que l'évaluateur va lire. Est-ce qu'il y a un watermark ou un avertissement explicite dans `calculs_approche_cout.json` indiquant que c'est un proxy ? Et quel est le plan concret pour remplacer ce proxy — acheter les données Altus, scraper MAMH, ou autre ?

---

## Thème 5 — Conformité et risque disciplinaire

### Q10 — L'OEAQ est-il au courant de ce projet, et si non, quel est le plan de divulgation ?

**Contexte :** `workflow-evaluateur-agree.md` cite le Code de déontologie C-26 r. 123 et la Norme de pratique professionnelle (mars 2025). Le projet génère automatiquement des "lettres de mandat" et des "brouillons de rapport".

L'article §6.5 du Code interdit à l'évaluateur de laisser son nom être utilisé pour cautionner un travail qu'il n'a pas réellement effectué. Si eval-immo génère 80% du rapport et que l'évaluateur le relit en 20 minutes, est-ce que c'est conforme ? A-t-on consulté l'OEAQ ou un juriste spécialisé sur la frontière entre "outil d'assistance" et "délégation d'acte professionnel" ?

### Q11 — La lettre de mandat générée automatiquement est-elle légalement valide ?

**Contexte :** `AGENTCONFIG-MANDAT-INTAKE-V0.yaml` : "Ton rôle est de produire... La lettre de mandat professionnelle (lettre_mandat.md) — document obligatoire §6.3 du Code de déontologie". La lettre est générée par GPT-4o-mini avec `temperature: 0.1`.

§6.3 exige 10 éléments obligatoires dont les honoraires et les signatures. La lettre générée met `[À CONFIRMER]` pour les honoraires et `[COMMANDITAIRE]` si le commanditaire n'est pas dans le dossier. Une lettre avec des placeholders non remplis est-elle un document légal valide que l'évaluateur peut remettre au commanditaire ?

---

## Thème 6 — Modèle d'affaires

### Q12 — Quel est le coût LLM par dossier et comment le justifies-tu ?

**Contexte :** `runtime.py` collecte `total_tokens` dans `metrics`. La session `36db31abe008` montre `total_tokens: 0` — le pipeline a tourné sans LLM. En production avec LLM, chaque étape fait un appel GPT-4o-mini. 7 étapes × ~2 000 tokens = ~14 000 tokens par dossier.

GPT-4o-mini : ~$0.15/M tokens input, $0.60/M tokens output. Coût estimé ~$0.02 par dossier. Un évaluateur fait ~100-200 dossiers/an. Coût LLM : $2-4/an. C'est négligeable. Mais si tu passes à GPT-4o full pour la qualité, c'est ~$0.50 par dossier, soit $50-100/an/évaluateur. Est-ce qu'il y a une analyse du point de rupture tarifaire ?

### Q13 — Vercel + Railway + Supabase : quel est le coût infrastructure à 50 évaluateurs ?

**Contexte :** `.vercel/project.json` et `backend/railway.json` confirment le déploiement actuel. `supabase/migrations/001_v3_schema.sql` est présent.

16 sessions pilotes génèrent chacune ~7 fichiers JSON + 1 JSONL + artefacts markdown = ~50KB par session. 50 évaluateurs × 150 dossiers × 10 runs = 75 000 sessions = ~3.75 GB de sessions. Railway volume persistant + Supabase Pro : quel est le budget mensuel projeté, et y a-t-il une politique d'archivage des sessions ?

### Q14 — Quel est le plan pour la première vente payante ?

**Contexte :** Le projet a un frontend Vercel, un backend Railway, un Supabase, une CI GitHub Actions, 16 sessions pilotes avec un seul dossier anonymisé (`D-PILOTE-RES-001`). Il n'y a pas de dossier réel de production, pas de compte évaluateur réel, pas de workflow de facturation.

La roadmap (batches 3-9 dans `docs/plans/`) couvre des features techniques (AMU, ingestion, comparables, rapport éditeur, export). Aucun batch ne porte sur "onboarding premier évaluateur payant". Quelle est la métrique de succès à 3 mois — nombre de dossiers certifiés avec eval-immo, ou nombre de features implémentées ?
