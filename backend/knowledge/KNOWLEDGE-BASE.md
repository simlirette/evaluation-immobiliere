# Base de connaissance normative — eval-immo

**Rapatrié :** 2026-05-31  
**Sources :** `C:\Users\simon\knowledge\indexed\` (pipeline docling/pypdf)  
**Catalogue :** `source-catalog.json` (62 entrées)  
**Corpus total :** ~17 MB markdown

## Structure

```
knowledge/
  corpus/            ← markdown extrait des PDF normatifs
    00-cuspap-nuppec-2026/
    01-mefq-manuel-2025/
    02-mefq-complements-et-outils/
    03-loi-fiscalite-municipale/
    04-oeaq-normes-pratique/
    05-oeaq-reglements/
    06-aic-gouvernance/
    07-aic-practice-notes/
    08-oeaq-guides-lignes-directrices/
    09-jurisprudence-discipline/
  source-catalog.json  ← métadonnées + source_id par fichier
  KNOWLEDGE-BASE.md    ← ce fichier
```

## Domaines couverts

| Domaine | Dossier | Fichiers |
|---|---|---|
| `cuspap_nuppec_professional_standards` | 00 | 1 |
| `municipal_assessment_manual` | 01 | 6 |
| `municipal_assessment_tools` | 02 | 8 |
| `municipal_statute_regulation` | 03 | 3 |
| `oeaq_professional_standards` | 04 | 11 |
| `oeaq_regulation` | 05 | 17 |
| `aic_governance` | 06 | 5 |
| `aic_cuspap_practice_notes` | 07–08 | 4 |
| `oeaq_discipline` | 09 | 7 |

## Sources clés pour le RAG

- **NPP OEAQ** : `04-oeaq-normes-pratique/npp-24-mars-2025.md` — normes obligatoires
- **CUSPAP 2026** : `00-cuspap-nuppec-2026/2026-cuspap.md` — standards AIC
- **MEFQ 2025** : `01-mefq-manuel-2025/mefq-partie-*.md` — méthodologie foncière
- **LFM** : `03-loi-fiscalite-municipale/f-2-1.md` — Loi sur la fiscalité municipale

## Usage

Utilisé par `engine/knowledge_rag.py` (T1.3) pour le RAG pgvector.  
`source_id` dans `source-catalog.json` sert d'identifiant de citation normative dans les rapports.

## Note sur les fichiers volumineux

`gui-manuel-evaluation-fonciere-2025.md` (~7 MB) et `mefq-partie-2/3-2025.md` (~3 MB)  
seront chunké à 1000–1500 tokens par le pipeline RAG (T1.3) avant indexation pgvector.
