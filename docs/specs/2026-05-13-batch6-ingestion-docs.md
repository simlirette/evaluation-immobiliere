# Batch 6 — Ingestion de documents

## Scope

Permettre l'injection automatique de données extraites de documents uploadés (PDF, JPG, PNG) dans le `case` avant l'exécution du pipeline.

**In scope :**
- Extraction texte depuis PDFs avec couche texte (PyMuPDF)
- Fallback GPT-4o Vision pour PDFs scannés et images
- Extraction structurée en champs case via un appel LLM
- Injection silencieuse dans `case` — les champs existants (fixture) ont priorité
- Texte extrait disponible comme contexte LLM pour l'agent `data-facts`

**Non-goals :**
- UI extraction status / badges
- Tesseract OCR local
- Re-extraction si doc re-uploadé dans la même session
- Extraction de comparables depuis documents (Batch 8)
- Injection dans les steps post `data-facts`

## Architecture

### Nouveau module : `backend/engine/ingestion.py`

Point d'entrée : `ingest_uploaded_documents(session, api_key) -> dict`

Appel depuis `api.py:start_runtime()` après `enrich_case()`, avant `run_case_data()`.

```
ingest_uploaded_documents(session, api_key)
├── pour chaque doc dans session["uploaded_documents"]
│   ├── extract_document(path, mime_type, client)
│   │   ├── PDF → extract_text_from_pdf(path)
│   │   │   ├── text trouvé → {method: "pymupdf", extracted_text: ...}
│   │   │   └── texte vide → pdf_page_to_b64_image() → describe_with_vision()
│   │   └── JPG/PNG → describe_with_vision() directement
│   └── stocke extracted_text dans session["uploaded_documents"][n]
└── parse_structured_fields(docs, client) → dict champs case
```

### Fonctions publiques

```python
def extract_text_from_pdf(path: Path) -> tuple[str, bool]:
    """(text, has_text). has_text=False = PDF scanné."""

def pdf_page_to_b64_image(path: Path, page_num: int = 0) -> str:
    """Convertit une page PDF en image base64 PNG pour Vision API."""

def describe_with_vision(b64_image: str, client) -> str:
    """Appel GPT-4o vision-preview. Retourne description textuelle."""

def extract_document(path: Path, mime_type: str, client) -> dict:
    """Retourne {filename, mime_type, extracted_text, method}."""

def parse_structured_fields(docs: list[dict], client) -> dict:
    """Un seul appel LLM sur tous les textes extraits. Retourne champs case."""

def ingest_uploaded_documents(session: dict, api_key: str | None) -> dict:
    """Point d'entrée. Retourne champs à merger dans case."""
```

### Champs structurés extraits (schema LLM)

| Champ case | Type | Source typique |
|---|---|---|
| `prix_achat` | float | Acte de vente |
| `date_achat` | str ISO | Acte de vente |
| `no_lot` | str | Acte / éval. municipale |
| `matricule` | str | Éval. municipale |
| `evaluation_municipale_totale` | float | Rôle d'évaluation |
| `evaluation_municipale_batiment` | float | Rôle d'évaluation |
| `evaluation_municipale_terrain` | float | Rôle d'évaluation |
| `surface_habitable` | float | Tout document |
| `surface_terrain` | float | Certificat de localisation |
| `annee_construction` | int | Éval. municipale / fiche |

Le LLM retourne `null` pour les champs non trouvés. Seuls les champs non-null et absents du case (ou vides) sont injectés — **les champs fixture ont priorité absolue**.

### Modifications `api.py:start_runtime()`

```python
# Après enrich_case(), avant run_case_data()
if session.get("uploaded_documents"):
    from engine.ingestion import ingest_uploaded_documents
    _fields = ingest_uploaded_documents(session, os.environ.get("OPENAI_API_KEY"))
    for k, v in _fields.items():
        if v is not None and not case.get(k):
            case[k] = v
    # Textes bruts pour enrichissement data-facts
    case["ingested_docs"] = [
        {"filename": d.get("filename", ""), "extracted_text": d.get("extracted_text", "")}
        for d in session.get("uploaded_documents", [])
        if d.get("extracted_text")
    ]
```

### Modifications `runtime.py:_build_enrichment_prompt`

Bloc pour `fiche_bien.json` : si `case.get("ingested_docs")`, append les textes extraits au prompt de l'agent `data-facts` sous la section `## Documents uploadés`.

### Limites opérationnelles

- Vision fallback : **5 pages max** par PDF (coût + latence)
- Sans clé OpenAI : skip Vision silencieux, `extracted_text = ""`, structured fields = `{}`
- PyMuPDF non installé : `ImportError` → fallback Vision direct pour PDFs (non-bloquant)

## Flux de données

```
upload (existant)
  └─ session["uploaded_documents"] += {id, filename, mime_type, path, ...}

start_runtime() [nouveau]
  ├─ ingest_uploaded_documents(session, api_key)
  │   ├─ extract_document() × N docs
  │   └─ parse_structured_fields() — 1 appel LLM
  ├─ case.update(structured_fields)  ← fixture fields win
  └─ case["ingested_docs"] = [...]

run_case_data() [inchangé]
  ├─ mandat-intake — conflit_interets.json (ignore ingested_docs)
  ├─ data-facts — fiche_bien.json LLM prompt inclut ingested_docs textes
  └─ ... autres steps inchangés
```

## Tests

| Classe | Vérifie |
|---|---|
| `TestIngestion_ExtractPDFText` | mock fitz → texte retourné, method="pymupdf" |
| `TestIngestion_VisionFallback_PDF` | fitz retourne vide → Vision appelé, method="vision" |
| `TestIngestion_VisionImage` | JPG → Vision appelé directement |
| `TestIngestion_NoOpenAI` | pas de client → extracted_text="", pas de crash |
| `TestIngestion_StructuredFields` | mock LLM → champs extraits correctement |
| `TestIngestion_NullFieldsSkipped` | champ null LLM → non injecté dans case |
| `TestIngestion_NoUpload` | 0 doc → `{}`, pipeline intact |
| `TestIngestion_ExistingFieldsNotOverwritten` | case["prix_achat"] existant → non écrasé |

## Dépendances

- `pymupdf` (pip install pymupdf) — extraction texte PDF
- `openai` — déjà utilisé pour LLM enrichment
- Pas de Tesseract, pas de PIL/Pillow (PyMuPDF génère les images PNG nativement)

## Failure modes documentés

1. **PyMuPDF non installé** — ImportError capturé, fallback Vision pour PDFs (non-bloquant, dégradé)
2. **LLM hallucine un champ** — existing fixture fields win, pas d'écrasement
3. **PDF 200 pages** — cap 5 pages Vision, reste ignoré pour V0
4. **Pas de clé OpenAI** — skip complet Vision + structured fields, pipeline continue normalement
