# Phase 1 — Connaissance active (le savoir atteint les agents + sources liées)

**Dépend de :** Phase 0
**Débloque :** qualité et traçabilité de tout ce que les agents produisent (P2, P3).
**Effort :** L
**Objectif :** que le savoir métier réellement encodé (`analysis.md`, corpus MEFQ/NPP/CUSPAP) atteigne les LLM, et que chaque affirmation normative du rapport cite sa source. Couvre **A1** et **C**.

## Périmètre
**Inclus :** injection ciblée `analysis.md` (pipeline + assistant) ; rapatriement du corpus dans le dépôt ; RAG (pgvector) ; citations normatives dans le rapport ; outil assistant `search_knowledge`.
**Exclus :** calculs de valeur (P2), couverture mandats (P4).

---

## Tâches

### T1.1 — Injection immédiate de `analysis.md` (gain rapide, avant RAG)
- Étendre `engine/skills.py` : `load_skill_knowledge(skill_name)` qui lit les sections pertinentes de `analysis.md` (pas seulement `SKILL.md` 2/4).
- **Pipeline** : dans `runtime.py::_enrich_artifact_llm`, injecter, pour l'agent de l'étape, le savoir des `skills_allowed` (budget tokens ciblé par artefact).
- **Assistant** : étendre `api.py::_build_agent_full_prompt` pour préférer `analysis.md` (sections ciblées) au renvoi `SKILL.md`.
- **Fichiers :** `backend/engine/skills.py`, `backend/engine/runtime.py`, `backend/api.py`.
- **DoD :** un appel pipeline/assistant contient le contenu réel de `analysis.md` (vérifié par test sur le prompt construit) ; coût LLM mesuré.

### T1.2 — Rapatrier le corpus de connaissance dans le dépôt
Le corpus (`C:\Users\simon\knowledge(-source)`, pack v1 = 68 sources, evidence markdown + docling) est hors dépôt.
- Importer dans `backend/knowledge/` : evidence markdown + `source-catalog.json` + empreintes (pas les PDF originaux bruts si volumineux — garder les extractions markdown).
- Versionner ; documenter la provenance.
- **Fichiers :** `backend/knowledge/**`, `docs/KNOWLEDGE-BASE.md`.
- **DoD :** le savoir normatif est dans le dépôt, catalogué, avec empreintes.

### T1.3 — RAG normatif (pgvector)
- Chunking du corpus (MEFQ, NPP, CUSPAP, jurisprudence) → embeddings → Supabase `pgvector`.
- `engine/knowledge_rag.py` : `retrieve(query, top_k)` → chunks + métadonnées (document, partie/section, page).
- Brancher dans les agents `recherche-*` et `redaction` : requête contextuelle → injection des top-k.
- **Fichiers :** `backend/engine/knowledge_rag.py`, `supabase/migrations/006_knowledge_embeddings.sql`, intégration `runtime.py`.
- **DoD :** une question MEFQ renvoie les bons chunks avec référence partie/section ; latence acceptable ; cache embeddings.

### T1.4 — Citations normatives liées au rapport (C)
- Chaque section du rapport qui invoque une règle cite sa source (ex. « MEFQ Partie 3C », « NPP Règle 2.3 », « art. 42 LFM ») avec un identifiant pointant vers le catalogue.
- Étendre `annexe_sources.md` pour inclure les **sources normatives** (pas seulement les `source_id` de données).
- **Fichiers :** `runtime.py` (rédaction + `annexe_sources.md`), gabarits de rapport.
- **DoD :** un rapport généré contient des citations normatives traçables jusqu'au catalogue knowledge.

### T1.5 — Outil assistant `search_knowledge` (constat assistant)
L'assistant n'a que `fetch_artifact`.
- Ajouter l'outil `search_knowledge(query)` (utilise T1.3) au tool-calling de `llm_assistant_answer`.
- **Fichiers :** `backend/api.py` (`_FETCH_ARTIFACT_TOOL` + nouvel outil, boucle de résolution).
- **DoD :** l'assistant peut citer une règle MEFQ/NPP en réponse à une question, avec source.

---

## Risques
- Coût/latence LLM ↑ avec injection — mesurer, plafonner les budgets, mettre en cache.
- Qualité des chunks (découpage) — itérer sur la stratégie de chunking.

## Critère de done de la phase
Le savoir profond atteint pipeline + assistant ; corpus dans le dépôt ; RAG opérationnel avec citations partie/section ; rapport et assistant citent leurs sources normatives.
