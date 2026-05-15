# Batch 6 — Ingestion de documents

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extraire automatiquement les données des documents uploadés et les injecter silencieusement dans le `case` avant l'exécution du pipeline.

**Architecture:** Nouveau module `engine/ingestion.py` avec fonctions pures. Appelé depuis `start_runtime()` après `enrich_case()` et avant `run_case_data()`. PyMuPDF pour PDFs avec couche texte, GPT-4o Vision pour images et PDFs scannés. Un seul appel LLM (`response_format: json_object`) extrait les champs structurés. Les champs fixture ont priorité absolue (`not case.get(k)`). Le prompt LLM de `fiche_bien.json` (data-facts) inclut les textes extraits si `case["ingested_docs"]` est présent.

**Tech Stack:** Python 3.11, PyMuPDF (`fitz`), OpenAI (déjà utilisé), pytest

**Assumptions:**
- Assume `session["uploaded_documents"][n]["filename"]` est le nom de fichier disque (pas le chemin complet) — le chemin complet = `Path(session["session_dir"]) / "uploads" / doc["filename"]`. Will NOT work si `app_upload_document()` stocke les chemins différemment.
- Assume `openai` non installé en test env → mock via `sys.modules` patch (pattern Batch 5). Will NOT work si `openai` est installé globalement sans mock.
- Assume `gpt-4o` supporte `response_format: json_object` et Vision. Will NOT work avec `gpt-4o-mini` pour Vision.

---

## File Structure

| Fichier | Action | Responsabilité |
|---|---|---|
| `backend/engine/ingestion.py` | Créer | Extraction PDF/image, structured fields parsing |
| `backend/tests/test_pure.py` | Modifier | Tests TDD pour ingestion + fiche_bien prompt |
| `backend/api.py` | Modifier | Wiring ingestion dans `start_runtime()` |
| `backend/engine/runtime.py` | Modifier | `_build_enrichment_prompt` fiche_bien inclut ingested_docs |
| `backend/requirements.txt` | Modifier | Ajouter `pymupdf>=1.24.0` |

---

## Wave Plan

- **Wave 1 (parallel):** Task 1 (tests failing) + Task 4 (runtime.py prompt) — fichiers disjoints
- **Wave 2:** Task 2 (ingestion.py) — fait passer les tests Task 1
- **Wave 3:** Task 3 (api.py wiring)
- **Wave 4:** Task 5 (requirements + vérification finale)

---

### Task 1: Tests TDD — ingestion + fiche_bien prompt

**Files:**
- Modify: `backend/tests/test_pure.py`

**Security flag:** `none`

**Does NOT cover:** tests d'intégration bout-en-bout avec vrai pipeline ; test de re-extraction si doc déjà extrait.

- [x] **Step 1: Append test classes to test_pure.py**

```python
# ── TestIngestion_ExtractPDFText ──────────────────────────────────────────────

class TestIngestion_ExtractPDFText:
    def test_extracts_text_from_pdf_with_text_layer(self):
        import sys
        import unittest.mock
        mock_fitz = unittest.mock.MagicMock()
        mock_page = unittest.mock.MagicMock()
        mock_page.get_text.return_value = "Surface : 1200 pi²\nPrix : 350 000 $"
        mock_doc = unittest.mock.MagicMock()
        mock_doc.__iter__ = unittest.mock.Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        with unittest.mock.patch.dict(sys.modules, {"fitz": mock_fitz}):
            from engine.ingestion import extract_text_from_pdf
            text, has_text = extract_text_from_pdf(Path("/fake/doc.pdf"))
        assert has_text is True
        assert "1200" in text

    def test_returns_false_when_no_text(self):
        import sys
        import unittest.mock
        mock_fitz = unittest.mock.MagicMock()
        mock_page = unittest.mock.MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc = unittest.mock.MagicMock()
        mock_doc.__iter__ = unittest.mock.Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        with unittest.mock.patch.dict(sys.modules, {"fitz": mock_fitz}):
            from engine.ingestion import extract_text_from_pdf
            text, has_text = extract_text_from_pdf(Path("/fake/scan.pdf"))
        assert has_text is False
        assert text == ""


# ── TestIngestion_VisionFallback_PDF ─────────────────────────────────────────

class TestIngestion_VisionFallback_PDF:
    def test_vision_called_when_pdf_has_no_text(self):
        import unittest.mock
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = "Maison de plain-pied en brique"
        mock_client.chat.completions.create.return_value = mock_resp
        with unittest.mock.patch("engine.ingestion.extract_text_from_pdf", return_value=("", False)):
            with unittest.mock.patch("engine.ingestion.pdf_page_to_b64_image", return_value="fakeb64base64"):
                from engine.ingestion import extract_document
                result = extract_document(Path("/fake/scan.pdf"), "application/pdf", mock_client)
        assert result["method"] == "vision"
        assert "Maison" in result["extracted_text"]

    def test_skipped_when_pdf_has_no_text_and_no_client(self):
        import unittest.mock
        with unittest.mock.patch("engine.ingestion.extract_text_from_pdf", return_value=("", False)):
            from engine.ingestion import extract_document
            result = extract_document(Path("/fake/scan.pdf"), "application/pdf", None)
        assert result["method"] == "skipped"
        assert result["extracted_text"] == ""


# ── TestIngestion_VisionImage ─────────────────────────────────────────────────

class TestIngestion_VisionImage:
    def test_vision_called_for_jpeg(self):
        import unittest.mock
        import tempfile
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = "Belle maison en brique"
        mock_client.chat.completions.create.return_value = mock_resp
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
            tmp_path = Path(f.name)
        try:
            from engine.ingestion import extract_document
            result = extract_document(tmp_path, "image/jpeg", mock_client)
            assert result["method"] == "vision"
            assert "Belle maison" in result["extracted_text"]
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_skipped_for_jpeg_without_client(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 20)
            tmp_path = Path(f.name)
        try:
            from engine.ingestion import extract_document
            result = extract_document(tmp_path, "image/jpeg", None)
            assert result["method"] == "skipped"
            assert result["extracted_text"] == ""
        finally:
            tmp_path.unlink(missing_ok=True)


# ── TestIngestion_NoOpenAI ────────────────────────────────────────────────────

class TestIngestion_NoOpenAI:
    def test_no_crash_when_no_client_pdf(self):
        import sys
        import unittest.mock
        mock_fitz = unittest.mock.MagicMock()
        mock_page = unittest.mock.MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc = unittest.mock.MagicMock()
        mock_doc.__iter__ = unittest.mock.Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        with unittest.mock.patch.dict(sys.modules, {"fitz": mock_fitz}):
            from engine.ingestion import extract_document
            result = extract_document(Path("/fake/scan.pdf"), "application/pdf", None)
        assert result["extracted_text"] == ""
        assert result["method"] == "skipped"


# ── TestIngestion_StructuredFields ────────────────────────────────────────────

class TestIngestion_StructuredFields:
    def test_parse_structured_fields_returns_known_keys(self):
        import unittest.mock
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = (
            '{"prix_achat": 350000.0, "date_achat": "2025-03-15", "no_lot": null}'
        )
        mock_client.chat.completions.create.return_value = mock_resp
        from engine.ingestion import parse_structured_fields
        docs = [{"filename": "acte.pdf", "extracted_text": "Prix : 350 000 $"}]
        result = parse_structured_fields(docs, mock_client)
        assert result["prix_achat"] == 350000.0
        assert result["date_achat"] == "2025-03-15"
        assert "no_lot" not in result  # null excluded

    def test_returns_empty_when_no_client(self):
        from engine.ingestion import parse_structured_fields
        docs = [{"filename": "acte.pdf", "extracted_text": "Prix : 350 000 $"}]
        result = parse_structured_fields(docs, None)
        assert result == {}


# ── TestIngestion_NullFieldsSkipped ──────────────────────────────────────────

class TestIngestion_NullFieldsSkipped:
    def test_null_fields_not_in_result(self):
        import unittest.mock
        mock_client = unittest.mock.MagicMock()
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = '{"prix_achat": null, "date_achat": null}'
        mock_client.chat.completions.create.return_value = mock_resp
        from engine.ingestion import parse_structured_fields
        docs = [{"filename": "photo.jpg", "extracted_text": "Maison en briques"}]
        result = parse_structured_fields(docs, mock_client)
        assert result == {}


# ── TestIngestion_NoUpload ────────────────────────────────────────────────────

class TestIngestion_NoUpload:
    def test_empty_uploaded_docs_returns_empty_dict(self):
        from engine.ingestion import ingest_uploaded_documents
        session = {"session_dir": "/tmp/fake-session", "uploaded_documents": []}
        result = ingest_uploaded_documents(session, None)
        assert result == {}

    def test_missing_uploaded_docs_key_returns_empty_dict(self):
        from engine.ingestion import ingest_uploaded_documents
        session = {"session_dir": "/tmp/fake-session"}
        result = ingest_uploaded_documents(session, None)
        assert result == {}


# ── TestIngestion_ExistingFieldsNotOverwritten ────────────────────────────────

class TestIngestion_ExistingFieldsNotOverwritten:
    def test_fixture_field_wins_over_extracted_field(self):
        """The injection loop in start_runtime: 'not case.get(k)' — existing values win."""
        case = {"prix_achat": 450000.0}
        _fields = {"prix_achat": 350000.0, "date_achat": "2025-03-15"}
        for k, v in _fields.items():
            if v is not None and not case.get(k):
                case[k] = v
        assert case["prix_achat"] == 450000.0  # not overwritten
        assert case["date_achat"] == "2025-03-15"  # new field added

    def test_empty_string_case_field_is_overwritten(self):
        """Empty string is falsy — extraction fills the gap."""
        case = {"prix_achat": ""}
        _fields = {"prix_achat": 350000.0}
        for k, v in _fields.items():
            if v is not None and not case.get(k):
                case[k] = v
        assert case["prix_achat"] == 350000.0


# ── TestFicheBien_IngestedDocs ────────────────────────────────────────────────

class TestFicheBien_IngestedDocs:
    def test_ingested_docs_appended_to_fiche_bien_prompt(self):
        from engine.runtime import _build_enrichment_prompt
        case = {
            "dossier_id": "D-INGEST-TEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "zone": "Laval",
            "ingested_docs": [
                {
                    "filename": "acte_vente.pdf",
                    "extracted_text": "Prix : 350 000 $\nDate : 2025-03-15",
                },
            ],
        }
        payload = {
            "surface": {"value": 1200, "unit": "pi²"},
            "confidence": 0.85,
            "source_ids": ["SRC-001"],
        }
        prompt = _build_enrichment_prompt("data-facts", "fiche_bien.json", payload, case)
        assert "Documents" in prompt
        assert "acte_vente.pdf" in prompt
        assert "350 000" in prompt

    def test_fiche_bien_prompt_unchanged_without_ingested_docs(self):
        from engine.runtime import _build_enrichment_prompt
        case = {
            "dossier_id": "D-NO-INGEST",
            "type_bien": "residentiel_unifamilial",
            "date_reference": "2026-05-13",
            "zone": "Montreal",
        }
        payload = {
            "surface": {"value": 900, "unit": "pi²"},
            "confidence": 0.70,
            "source_ids": [],
        }
        prompt = _build_enrichment_prompt("data-facts", "fiche_bien.json", payload, case)
        # Should still produce a valid prompt, just without the documents section
        assert "DONNÉES DE LA FICHE BIEN" in prompt
        assert "acte_vente.pdf" not in prompt
```

- [x] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_pure.py -k "TestIngestion or TestFicheBien_IngestedDocs" -v 2>&1 | tail -20`

Expected: FAIL — `ModuleNotFoundError: No module named 'engine.ingestion'` for TestIngestion_* classes ; `TestFicheBien_IngestedDocs` fails because "Documents" not in prompt.

- [x] **Step 3: Commit failing tests**

```bash
git add backend/tests/test_pure.py
git commit -m "test(batch6): add failing TDD tests for ingestion module and fiche_bien prompt"
```

---

### Task 2: Implement engine/ingestion.py

**Files:**
- Create: `backend/engine/ingestion.py`

**Security flag:** `none`

**Does NOT cover:** re-extraction si doc déjà extrait dans la session ; multipage Vision (seulement page 0) ; PDF protégé par mot de passe.

- [x] **Step 1: Create backend/engine/ingestion.py**

```python
"""Document ingestion — extract text/descriptions from uploaded PDF/image files."""
from __future__ import annotations

import base64
import json
from pathlib import Path

_MAX_VISION_PAGES = 5  # cap Vision fallback pages per PDF

_STRUCTURED_FIELDS_SCHEMA = {
    "prix_achat": "float|null — prix d'acquisition ou de vente en dollars canadiens",
    "date_achat": "string ISO YYYY-MM-DD|null — date de la transaction",
    "no_lot": "string|null — numéro de lot cadastral",
    "matricule": "string|null — numéro de matricule municipal",
    "evaluation_municipale_totale": "float|null — valeur totale au rôle d'évaluation",
    "evaluation_municipale_batiment": "float|null — valeur du bâtiment au rôle",
    "evaluation_municipale_terrain": "float|null — valeur du terrain au rôle",
    "surface_habitable": "float|null — surface habitable en pieds carrés",
    "surface_terrain": "float|null — surface du terrain en pieds carrés",
    "annee_construction": "int|null — année de construction",
}

_VISION_PROMPT_DOC = (
    "Tu es un expert en évaluation immobilière québécoise. "
    "Analyse ce document et extrait tous les faits pertinents : "
    "adresse, type de bien, dimensions, prix, dates, parties impliquées, "
    "numéros de lot ou matricule, évaluation municipale. "
    "Réponds en français, de façon structurée."
)

_VISION_PROMPT_PHOTO = (
    "Tu es un expert en évaluation immobilière québécoise. "
    "Décris cette propriété : état général, type de construction, "
    "caractéristiques visibles, matériaux, éléments distinctifs, "
    "condition apparente. Réponds en français, de façon structurée."
)


def extract_text_from_pdf(path: Path) -> tuple[str, bool]:
    """Extract text layer from PDF. Returns (text, has_text). has_text=False means scanned PDF."""
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError:
        return "", False
    try:
        doc = fitz.open(str(path))
        pages_text = []
        for i, page in enumerate(doc):
            if i >= _MAX_VISION_PAGES:
                break
            pages_text.append(page.get_text())
        doc.close()
        text = "\n".join(pages_text).strip()
        return text, bool(text)
    except Exception:
        return "", False


def pdf_page_to_b64_image(path: Path, page_num: int = 0) -> str:
    """Convert a PDF page to base64 PNG for Vision API. Returns empty string on failure."""
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError:
        return ""
    try:
        doc = fitz.open(str(path))
        if page_num >= len(doc):
            doc.close()
            return ""
        page = doc[page_num]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for legibility
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        doc.close()
        return base64.b64encode(png_bytes).decode("ascii")
    except Exception:
        return ""


def describe_with_vision(b64_image: str, client, prompt: str = _VISION_PROMPT_DOC) -> str:
    """Call GPT-4o Vision with a base64 PNG image. Returns description text."""
    if not b64_image or client is None:
        return ""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                        },
                    ],
                }
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""


def _describe_image_file(path: Path, client) -> str:
    """Send JPG/PNG file to Vision API. Returns description text."""
    if client is None:
        return ""
    try:
        raw = path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        suffix = path.suffix.lower()
        mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _VISION_PROMPT_PHOTO},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""


def extract_document(path: Path, mime_type: str, client) -> dict:
    """Extract text/description from one document.

    Returns:
        {filename, mime_type, extracted_text, method}
        method: "pymupdf" | "vision" | "skipped"
    """
    result: dict = {
        "filename": path.name,
        "mime_type": mime_type,
        "extracted_text": "",
        "method": "skipped",
    }

    if mime_type == "application/pdf":
        text, has_text = extract_text_from_pdf(path)
        if has_text:
            result["extracted_text"] = text
            result["method"] = "pymupdf"
        elif client is not None:
            b64 = pdf_page_to_b64_image(path, page_num=0)
            if b64:
                desc = describe_with_vision(b64, client)
                result["extracted_text"] = desc
                result["method"] = "vision"
    elif mime_type in ("image/jpeg", "image/png"):
        if client is not None:
            desc = _describe_image_file(path, client)
            result["extracted_text"] = desc
            result["method"] = "vision"

    return result


def parse_structured_fields(docs: list[dict], client) -> dict:
    """Single LLM call on all extracted texts → structured case fields dict.

    Returns only non-null known fields. Returns {} if no client or no texts.
    """
    if not docs or client is None:
        return {}

    texts = []
    for doc in docs:
        text = (doc.get("extracted_text") or "").strip()
        if text:
            texts.append(f"=== {doc.get('filename', 'document')} ===\n{text}")

    if not texts:
        return {}

    combined = "\n\n".join(texts)
    schema_str = json.dumps(_STRUCTURED_FIELDS_SCHEMA, ensure_ascii=False, indent=2)
    prompt = (
        "Tu es un expert en évaluation immobilière québécoise. "
        "Voici des textes extraits de documents d'un dossier d'évaluation.\n\n"
        f"{combined}\n\n"
        f"Extrait les champs suivants selon ce schéma JSON :\n{schema_str}\n\n"
        "Retourne UNIQUEMENT un objet JSON valide avec ces clés exactes. "
        "Utilise null pour les champs non trouvés. "
        "Ne retourne aucun texte hors du JSON."
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=600,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        return {k: data[k] for k in _STRUCTURED_FIELDS_SCHEMA if data.get(k) is not None}
    except Exception:
        return {}


def ingest_uploaded_documents(session: dict, api_key: str | None) -> dict:
    """Main entry point. Extract text from uploaded documents, return structured case fields.

    Side-effect: updates session["uploaded_documents"][n] with "extracted_text" and
    "extraction_method" keys. Fixture fields have priority (caller decides merge policy).

    Returns:
        dict of structured case fields (non-null, from _STRUCTURED_FIELDS_SCHEMA).
        Returns {} if no uploaded documents or no content extracted.
    """
    uploaded = session.get("uploaded_documents", [])
    if not uploaded:
        return {}

    client = None
    if api_key:
        try:
            import openai as _openai  # type: ignore
            client = _openai.OpenAI(api_key=api_key)
        except Exception:
            pass

    session_dir = Path(session["session_dir"])
    uploads_dir = session_dir / "uploads"

    extracted_docs: list[dict] = []
    for doc in uploaded:
        filename = str(doc.get("filename") or "")
        mime_type = str(doc.get("mime_type") or "")
        if not filename:
            continue
        path = uploads_dir / filename
        if not path.exists():
            continue
        result = extract_document(path, mime_type, client)
        # Persist extraction results in session metadata
        doc["extracted_text"] = result["extracted_text"]
        doc["extraction_method"] = result["method"]
        if result["extracted_text"]:
            extracted_docs.append(result)

    return parse_structured_fields(extracted_docs, client)
```

- [x] **Step 2: Run the failing tests to verify they now pass**

Run: `cd backend && python -m pytest tests/test_pure.py -k "TestIngestion" -v 2>&1 | tail -30`

Expected: All `TestIngestion_*` tests PASS. `TestFicheBien_IngestedDocs` still fails (Task 4 not done yet).

- [x] **Step 3: Run full test suite to check no regressions**

Run: `cd backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -10`

Expected: 78 existing tests PASS, new TestIngestion tests PASS, TestFicheBien_IngestedDocs FAIL (expected — Task 4 pending).

- [x] **Step 4: Commit**

```bash
git add backend/engine/ingestion.py
git commit -m "feat(batch6): add engine/ingestion.py — PyMuPDF + GPT-4o Vision + structured fields"
```

---

### Task 3: Wire api.py — start_runtime() ingestion injection

**Files:**
- Modify: `backend/api.py`

**Security flag:** `none`

**Does NOT cover:** re-lancement de l'ingestion si pipeline relancé sur même session ; exposition des champs extraits dans `app_session_view`.

- [x] **Step 1: Locate injection point in start_runtime() and add wiring**

In `start_runtime()`, find the line `write_json(case_input_path, case)`. The injection block goes immediately after this line, before `steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)`.

```python
    write_json(case_input_path, case)

    # ── Ingestion documents uploadés (non-bloquant) ──────────────────────────
    if session.get("uploaded_documents"):
        try:
            from engine.ingestion import ingest_uploaded_documents as _ingest
            _fields = _ingest(session, os.environ.get("OPENAI_API_KEY"))
            for k, v in _fields.items():
                if v is not None and not case.get(k):
                    case[k] = v
            # Textes bruts disponibles pour enrichissement LLM de fiche_bien.json
            case["ingested_docs"] = [
                {
                    "filename": d.get("filename", ""),
                    "extracted_text": d.get("extracted_text", ""),
                }
                for d in session.get("uploaded_documents", [])
                if d.get("extracted_text")
            ]
        except Exception:
            pass  # ingestion is optional — never block pipeline

    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
```

- [x] **Step 2: Run full test suite**

Run: `cd backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -10`

Expected: All 78 existing tests PASS. TestIngestion_* PASS. TestFicheBien_IngestedDocs still FAIL (Task 4 pending).

- [x] **Step 3: Commit**

```bash
git add backend/api.py
git commit -m "feat(batch6): wire ingest_uploaded_documents into start_runtime() before pipeline"
```

---

### Task 4: runtime.py — extend _build_enrichment_prompt for fiche_bien.json

**Files:**
- Modify: `backend/engine/runtime.py`

**Security flag:** `none`

**Does NOT cover:** injection de ingested_docs dans les prompts des autres artifacts (amu_analyse.md, comparables, etc.).

- [x] **Step 1: Update the fiche_bien.json block in _build_enrichment_prompt**

Find the `if artifact == "fiche_bien.json":` block (lines ~202–213). Replace it with:

```python
    if artifact == "fiche_bien.json":
        surface = payload.get("surface", {})
        surface_str = f"{surface.get('value', '—')} {surface.get('unit', '')}" if isinstance(surface, dict) else str(surface)
        ingested_section = ""
        if case.get("ingested_docs"):
            doc_parts = []
            for d in case["ingested_docs"]:
                fname = str(d.get("filename", "document"))
                text = str(d.get("extracted_text", "")).strip()
                if text:
                    doc_parts.append(f"[{fname}]\n{text[:600]}")
            if doc_parts:
                ingested_section = "\n\n## Documents uploadés\n\n" + "\n\n".join(doc_parts)
        return base + (
            f"DONNÉES DE LA FICHE BIEN :\n"
            f"Surface : {surface_str}\n"
            f"Confiance : {payload.get('confidence', '—')}\n"
            f"Sources : {payload.get('source_ids', [])}"
            f"{ingested_section}\n\n"
            "Rédige en 2–3 paragraphes une analyse contextuelle professionnelle du bien identifié. "
            "Inclus : description physique probable, localisation et contexte de marché local. "
            "Sois factuel et n'invente aucune donnée absente du contexte fourni."
        )
```

- [x] **Step 2: Run TestFicheBien_IngestedDocs to verify it now passes**

Run: `cd backend && python -m pytest tests/test_pure.py -k "TestFicheBien_IngestedDocs" -v`

Expected: 2 tests PASS.

- [x] **Step 3: Run full test suite**

Run: `cd backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -10`

Expected: All tests PASS (78 existing + new ingestion + new fiche_bien).

- [x] **Step 4: Commit**

```bash
git add backend/engine/runtime.py
git commit -m "feat(batch6): include ingested_docs texts in fiche_bien.json LLM enrichment prompt"
```

---

### Task 5: requirements.txt + vérification finale

**Files:**
- Modify: `backend/requirements.txt`
- Verify: all tests pass, no regressions

**Security flag:** `none`

**Does NOT cover:** test d'installation de pymupdf dans le CI/CD.

- [x] **Step 1: Add pymupdf to requirements.txt**

Current content of `backend/requirements.txt`:
```
openai>=1.30.0
python-dotenv>=1.0.0
```

New content:
```
openai>=1.30.0
python-dotenv>=1.0.0
pymupdf>=1.24.0
```

- [x] **Step 2: Run complete test suite**

Run: `cd backend && python -m pytest tests/test_pure.py -v 2>&1 | tail -20`

Expected: All tests PASS, 0 failures. Count should be ≥ 78 + 12 new tests = ≥ 90 tests.

- [x] **Step 3: Verify ingestion module imports cleanly**

Run: `cd backend && python -c "from engine.ingestion import ingest_uploaded_documents; print('OK')"`

Expected: `OK`

- [x] **Step 4: Verify api.py imports cleanly**

Run: `cd backend && python -c "from api import start_runtime; print('OK')"`

Expected: `OK`

- [x] **Step 5: Update state.md**

Update `state.md` — set Batch 6 plan status to DONE ✓ and update test count.

- [x] **Step 6: Commit**

```bash
git add backend/requirements.txt state.md
git commit -m "feat(batch6): add pymupdf dependency + mark batch 6 complete"
```
