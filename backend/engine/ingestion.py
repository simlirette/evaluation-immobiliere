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
    """Send JPG/PNG file to Vision API as base64. Returns description text."""
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
        dict with keys: filename, mime_type, extracted_text, method
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

    Returns only non-null known fields from _STRUCTURED_FIELDS_SCHEMA.
    Returns {} if no client or no extracted texts.
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

    Reads uploaded documents from session["uploaded_documents"], extracts text/descriptions,
    and returns structured case fields to merge (fixture fields have priority — caller decides).

    Side-effect: updates each doc in session["uploaded_documents"] with:
        "extracted_text": str
        "extraction_method": "pymupdf" | "vision" | "skipped"

    Args:
        session: session dict with "session_dir" and optional "uploaded_documents"
        api_key: OpenAI API key (None = skip Vision and structured fields)

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
        # Persist extraction results in session metadata in-place
        doc["extracted_text"] = result["extracted_text"]
        doc["extraction_method"] = result["method"]
        if result["extracted_text"]:
            extracted_docs.append(result)

    return parse_structured_fields(extracted_docs, client)
