# Analyse honnête du projet et de l'adaptation Aston → évaluation immobilière

## D'abord, la vérité sur "infrastructure quasi-parfaite"

Tu as raison **à moitié**, et c'est important de bien découper pour éviter de se faire surprendre plus tard.

L'infrastructure Aston se sépare en **deux couches très différentes** :

**La couche "moteur" (vraiment réutilisable, ~quasi-parfaite)** : `engine/loop.py`, `AgentConfig`, `AgentState`, anti-loop, recovery, continuation, streaming SSE, persistance Postgres, pipeline de contexte (snip → compact → collapse → summarize → restore), validate_and_repair. Ça, c'est de l'orchestration générique multi-agents, agnostique au métier. Tu peux le copier presque tel quel.

**La couche "métier" (très spécialisée juridique, à ~70% à refaire)** : le schéma de `knowledge.json` (identity/facts/legal/strategy avec parties, tribunal, prescription...), les extracteurs Haiku qui peuplent ce schéma, tout le RAG (court boost CSC×1.30, treatment penalty REVERSED×0.3, citation_edges), tous les outils légaux (`search_caselaw`, `get_decision_text`, `check_prescription`, `verify_citation`...), les checklists de vérification (citation_format, principles_attributed, no_fabricated_citations), et le système de SKILL.md de rédaction.

Donc « quasi-parfaite » oui pour le moteur, **non pour le métier**. Quand tu dis « adaptation directe d'Aston », tu décris en fait :

- ~30 % de réutilisation telle quelle (engine, streaming, persistance, contexte)
- ~30 % de réutilisation avec adaptation (patterns de configs, frontend hooks, file tools)
- ~40 % à réécrire complètement (knowledge schema, RAG, tous les tools métier, vérification, prompts, RAG)

Ce n'est pas grave — c'est même la bonne stratégie — mais il faut nommer la chose : **tu fais un fork avec moteur réutilisé et couche métier reconstruite à neuf**.

---

## Trois agents que tu présentes comme "adaptations" sont en réalité des agents NEUFS

Ton plan dans `DEMARRAGE-ADAPTATION-EVALUATION-IMMOBILIERE.md` parle d'Intake, Comps & Market, Valuation Draft, Compliance QA. **Aucun de ces 4 n'a d'équivalent direct dans Aston**. Conséquence concrète : tu n'as pas un AgentConfig de référence à copier-coller pour eux. Tu pars d'un patron vide.

| Ton agent immobilier | Équivalent Aston | Coût réel |
|---|---|---|
| Intake | aucun | 100 % neuf |
| Data/Facts | Facts (proche dans l'esprit) | adaptation prompts + outils |
| Comps & Market | aucun | 100 % neuf |
| Valuation Draft | aucun | 100 % neuf — et c'est l'agent le plus délicat car il fait des **calculs numériques**, ce qu'Aston ne fait jamais |
| Compliance QA | partiellement la verification post-agent | partiel (Aston a des checklists post-tour mais pas un agent gate dédié) |
| Redaction | Redaction | adaptation SKILL.md + prompt |

Le piège à éviter : Aston fait du RAG textuel sur des décisions de jurisprudence. Comps & Market doit faire de la **recherche structurée numérique** (filtres géo, surface, date) avec un **scoring quantitatif** (distance × récence × similarité d'attributs). Tu ne peux pas réutiliser le pipeline `pgvector + ZeroEntropy rerank` tel quel — la signature du problème est différente.

---

## Knowledge base : à redesigner intégralement, c'est non négociable

Le `cases.knowledge` JSONB d'Aston est hardcodé sur des notions juridiques (`parties[].role`, `prescription`, `tribunal`, `applicable_articles`, `holdings`, `key_decisions`, `adverse_authority`, `theory`, `weaknesses`...). Le `render_knowledge_for_agent()` formate spécifiquement pour ces sections. Les extracteurs Haiku sont prompted pour produire ce schéma exact.

Pour l'immobilier il te faut un schéma totalement différent, par exemple :

```json
{
  "subject_property": { "adresse": "...", "type": "...", "zoning": "...", "surface": "...", "attributs": "...", "contraintes_titre": "..." },
  "mandate": { "type_rapport": "...", "date_reference": "...", "finalite": "...", "portee": "...", "limites": "..." },
  "comparables": [],
  "adjustments": [],
  "approaches": { "comparative": "...", "cost": "...", "income": "..." },
  "reconciliation": { "weights": "...", "conclusion_value": "...", "confidence_band": "..." },
  "compliance": { "npp_checks": "...", "blocking": "...", "warnings": "..." },
  "audit": { "sources": "...", "human_decisions": "...", "timestamps": "..." }
}
```

Tu vas devoir réécrire :

1. Le schéma `knowledge.json`
2. Les profils par agent (`AGENT_CONTEXT_PROFILES`)
3. Les prompts d'extraction Haiku (`update_knowledge_from_facts`, `update_knowledge_from_research`)
4. La fonction `render_knowledge_for_agent` (markdown formatting par audience)

C'est ~3-5 fichiers à refaire, pas hyper compliqué, mais à ne pas sous-estimer.

---

## Connaissances à fournir, par agent

C'est la partie où tu m'as demandé d'être précis. Voici ce que chaque agent a besoin que tu prépares **avant** son implémentation.

### Agent Intake (nouveau)

**À fournir** :

- Typologie des mandats acceptés en v1 (tu as déjà ciblé résidentiel 1-4 logements, c'est bien — formalise-le)
- Liste des documents requis par type de mandat (checklist d'admission)
- Règles de refus de mandat (hors compétence, conflit d'intérêts, données insuffisantes)
- Schéma `dossier_normalise.json` cible

**Format** : YAML de configuration + 1 prompt système. Pas besoin de gros corpus.

### Agent Data-Facts

**À fournir** :

- **Taxonomie d'attributs immobiliers** (résidentiel) : surface habitable vs brute, nb pièces, sous-sol fini/non, garage, terrain, année construction, rénovations, état général, etc. — avec définitions exactes pour éviter les ambiguïtés d'extraction.
- **Liste des documents-sources et leur niveau de fiabilité** : registre foncier (autorité), rôle d'évaluation municipale (indicatif), certificat de localisation (autorité technique), inspection préachat (avec auteur), photos (faible probative), MLS (commerciale).
- **Règles de OCR/extraction** : quand est-ce qu'une valeur extraite est jugée fiable (cap de confidence, présence de la même valeur dans 2 sources, etc.).
- **Schéma `fiche_bien.json`** précis avec types et unités obligatoires.
- **Section pertinente des NPP** (OEAQ) sur la collecte d'information.

**Format** : un document de référence "Taxonomie & sources" (~10-15 pages) + le schéma JSON.

### Agent Comps-Market (le plus exigeant en données métier)

**À fournir** :

- **Critères de sélection** : rayon géographique max par densité de marché, fenêtre temporelle, type de propriété, exclusions obligatoires (vente entre apparentés, succession, vente forcée, reprise de finance).
- **Rubrique d'ajustements** standardisée : localisation, surface, état, terrain, garage/stationnement, temps écoulé depuis la vente. Chaque catégorie avec sa méthode (paired sales, % du prix, $ par m²...).
- **Sources de données de ventes accessibles légalement** (point critique avant tout dev) : registre foncier, JLR, Centris si licence, IGIF, etc.
- **Scoring rubric** : comment classer la qualité d'un comparable. Par exemple : score = w1·(1/distance) + w2·(récence) + w3·(similarité_attributs) − pénalités. Il faut que tu fasses calibrer les poids par les évaluateurs.
- **Exemples de cas anonymisés** : 5-10 dossiers complets avec les comparables qu'un évaluateur expert aurait choisis (ground truth pour valider l'agent).

**Format** : le rubric en YAML + un guide écrit + le jeu de cas.

### Agent Valuation-Draft (le plus exigeant techniquement)

C'est ici qu'il faut être très prudent — un agent qui fait des **calculs** doit produire des résultats reproductibles. Il vaut mieux que l'agent **génère une trace de calcul JSON structurée**, et qu'un module Python pur exécute les formules. Sinon tu risques des erreurs arithmétiques incohérentes d'un dossier à l'autre.

**À fournir** :

- **Trois approches détaillées** : comparative (méthode et formule de réconciliation des comparables ajustés), coût (coût de remplacement neuf − dépréciation physique − dépréciation fonctionnelle − dépréciation économique + valeur du terrain), revenu (DCF ou capitalisation directe avec taux de cap par segment).
- **Tables de référence** : taux de cap par sous-marché et par type, coûts de construction de référence (Marshall & Swift Québec ou équivalent), taux de dépréciation par âge.
- **Logique de réconciliation** : quelle approche pondérer dans quel cas, comment justifier les poids.
- **Tests de cohérence mathématique** : le total des ajustements ne dépasse pas X % du prix, le RNE est positif, etc.
- **Hypothèses qui DOIVENT être validées par humain** (ajustements > seuil $, taux de cap atypique, vacance prolongée).

**Format** : un document méthodologique + des tables de référence en CSV/YAML + un module de calcul Python séparé que l'agent appelle via un outil `run_calculation`.

### Agent Compliance-QA

**À fournir** :

- **Checklist NPP/OEAQ complète et exécutable** : chaque item devient une règle (regex sur structure, présence de section, validation de format de date, contrôle d'unité). Tu as déjà commencé avec `RULES-CONFORMITE-V0.yaml` et les codes B001-B005, W001-W003 — c'est la bonne approche, il faut juste compléter.
- **Sections obligatoires par type de rapport** (formulaire, abrégé, narratif).
- **Règles de traçabilité** : tout chiffre dans le rapport doit être lié à au moins une source dans `source_index.json`.
- **Seuils** : quel écart entre approches déclenche un `A_REVOIR`, quel niveau de confidence force une validation humaine.
- **Cas tests d'erreur** : 10-20 dossiers volontairement non conformes pour valider que les règles attrapent bien les fautes.

**Format** : un YAML exécutable des règles + le jeu de cas tests négatifs.

### Agent Redaction

**À fournir** :

- **Gabarits de rapport** par type (l'équivalent du SKILL.md de Redaction Aston) — c'est ton nouvel équivalent de `aston/skills/`.
- **Formulations standardisées** OEAQ-conformes (clauses limitatives, certifications, hypothèses extraordinaires).
- **Style guide** : ton, vouvoiement, formats de date, formats numériques, unités SI obligatoires.
- **Exemples de rapports anonymisés** (idéalement 3-5 par type) — c'est ce qui donnera à l'agent la "voix" attendue.

**Format** : un fichier `SKILL_REPORT_<type>.md` par type de rapport + un dossier `templates/` + des exemples.

---

## Ce qui manque dans ton plan actuel et qui t'éviterait des bugs douloureux

**1. Pas de stratégie pour les calculs numériques**. Aston fait du texte. L'évaluation immobilière fait des chiffres. Tu dois décider très tôt : est-ce que les approches sont calculées par un module Python déterministe (recommandé) ou laissées au LLM (risqué) ? Mon avis honnête : déterministe, et l'agent ne fait que poser les hypothèses.

**2. Pas de plan OCR/extraction documents**. Aston lit des PDFs juridiques déjà nettoyés. Tu vas devoir gérer des certificats de localisation scannés à 200 dpi, des photos de plans, des baux PDF. L'outil `extract_text` est marqué "à brancher selon infra OCR" dans ton mapping — c'est un projet en soi, prévois-le.

**3. La verification post-agent d'Aston ne suffit pas**. Aston a `MAX_FIX_CYCLES = 2` et auto-fix uniquement si severity != high. Pour de l'évaluation immobilière, certaines erreurs (ex. ajustement non justifié) doivent **bloquer dur** sans tentative de fix LLM, et basculer en file d'attente humaine. Ça veut dire que ton Compliance-QA doit avoir une logique de gate plus stricte que la verification Aston actuelle.

**4. Pas de mention de la responsabilité professionnelle**. L'évaluateur signe et engage sa responsabilité. Tu dois prévoir un mécanisme de **scellement** de la version validée par humain (hash, signature, log immuable). Ce n'est pas dans Aston.

**5. Données géographiques**. Comparables → distance → tu auras besoin de PostGIS ou équivalent. Aston ne l'utilise pas.

---

## Ordre d'attaque recommandé

1. **Geler le schéma `knowledge.json` immobilier** (1-2 jours) — sans ça rien ne tient en aval.
2. **Construire le module de calcul déterministe** des trois approches en Python pur, testé avec 5 cas connus (1 semaine). Ça te débloque l'agent Valuation-Draft.
3. **Reproduire l'engine Aston** dans ton repo (copie minimale : `engine/`, `streaming/`, `persistence/`, `context/`) avec tests qui passent (3-5 jours).
4. **Implémenter Data-Facts en premier** (le plus proche de Facts Aston) sur fixtures synthétiques pour valider le shell (1 semaine).
5. **Implémenter Compliance-QA** ensuite (ça te donne tes garde-fous avant Comps qui est plus dur).
6. **Implémenter Comps-Market** avec un connecteur de données simulé d'abord, vrai connecteur ensuite.
7. **Brancher Valuation-Draft** sur le module de calcul.
8. **Implémenter Redaction** en dernier.
9. **Workshop évaluateurs** seulement après que le pipeline tourne sur fixtures — sinon les questions seront trop abstraites.

---

## Verdict direct sur la phrase de départ

> "je crois est quasi-parfaite pour ce projet"

- **Le moteur (engine + streaming + persistence + context) : oui, quasi-parfait, garde-le.**
- **La couche métier (knowledge schema + RAG + tools + verification + skills) : non, c'est une réécriture, pas une adaptation.**
- **Trois de tes six agents (Intake, Comps-Market, Valuation-Draft) sont neufs, pas adaptés.**
- **Tu sous-estimes deux choses : la calculabilité numérique et l'OCR documentaire.**

Si tu acceptes ces vérités au lieu de te raconter "c'est presque tout réutilisable", tu vas livrer un produit solide. Si tu pars en mode "swap juridique → immobilier en 4 semaines", tu vas mur dans 3 mois.
