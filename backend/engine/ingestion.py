"""Document ingestion — extract text/descriptions from uploaded PDF/image files."""
from __future__ import annotations

import base64
import json
from pathlib import Path

from engine.llm_routing import get_llm_model

_MAX_VISION_PAGES = 5  # cap Vision fallback pages per PDF
_MAX_PDF_PAGES = 75
_MAX_EXTRACTED_TEXT_CHARS = 250_000
_MAX_STRUCTURED_PROMPT_CHARS = 120_000

_STRUCTURED_FIELDS_SCHEMA = {
    # ── Identification ────────────────────────────────────────────────────────
    "prix_achat":                    "float|null — prix d'acquisition ou de vente en dollars canadiens",
    "date_achat":                    "string ISO YYYY-MM-DD|null — date de la transaction",
    "no_lot":                        "string|null — numéro de lot cadastral",
    "matricule":                     "string|null — numéro de matricule municipal",
    # ── Localisation ──────────────────────────────────────────────────────────
    "adresse_complete":              "string|null — adresse civique complète",
    "ville":                         "string|null — municipalité ou arrondissement",
    "code_postal":                   "string|null — code postal (ex. J1G 2A1)",
    # ── Type et destination ───────────────────────────────────────────────────
    "type_bien":                     "string|null — type de propriété (ex. unifamiliale, condo, duplex)",
    "destination":                   "string|null — usage actuel (ex. résidentiel, commercial, mixte)",
    "zonage":                        "string|null — zonage municipal (ex. R-1, C-2)",
    # ── Surfaces et évaluation municipale ────────────────────────────────────
    "surface_habitable":             "float|null — surface habitable en pieds carrés",
    "surface_terrain":               "float|null — surface du terrain en pieds carrés",
    "evaluation_municipale_totale":  "float|null — valeur totale au rôle d'évaluation",
    "evaluation_municipale_batiment":"float|null — valeur du bâtiment au rôle",
    "evaluation_municipale_terrain": "float|null — valeur du terrain au rôle",
    # ── Caractéristiques physiques ────────────────────────────────────────────
    "annee_construction":            "int|null — année de construction",
    "annee_renovation":              "int|null — année de la dernière rénovation majeure",
    "nb_pieces":                     "int|null — nombre total de pièces",
    "nb_chambres":                   "int|null — nombre de chambres à coucher",
    "nb_salles_bain":                "int|null — nombre de salles de bain",
    "nb_stationnements":             "int|null — nombre de places de stationnement",
    "garage":                        "bool|null — présence d'un garage (true/false)",
    "piscine":                       "bool|null — présence d'une piscine (true/false)",
    "sous_sol_fini":                 "bool|null — sous-sol aménagé (true/false)",
    "etat_general":                  "string|null — état général (ex. excellent, bon, moyen, mauvais)",
    "vue":                           "string|null — type de vue (ex. dégagée, eau, parc, aucune)",
    "proximite_nuisances":           "string|null — nuisances à proximité (ex. voie ferrée, industrie, aucune)",
    # ── Parties et mandat ─────────────────────────────────────────────────────
    "nom_proprietaire":              "string|null — nom du propriétaire inscrit au titre",
    "nom_commanditaire":             "string|null — nom du commanditaire de l'évaluation",
    "objet_evaluation":              "string|null — objet déclaré de l'évaluation",
}

# Libellés français pour l'interface UI CHECKPOINT 1
_FIELD_LABELS_FR: dict[str, str] = {
    "prix_achat":                    "Prix d'achat",
    "date_achat":                    "Date de transaction",
    "no_lot":                        "No de lot",
    "matricule":                     "Matricule municipal",
    "adresse_complete":              "Adresse complète",
    "ville":                         "Ville / municipalité",
    "code_postal":                   "Code postal",
    "type_bien":                     "Type de bien",
    "destination":                   "Destination",
    "zonage":                        "Zonage",
    "surface_habitable":             "Surface habitable (pi²)",
    "surface_terrain":               "Surface du terrain (pi²)",
    "evaluation_municipale_totale":  "Éval. munic. totale ($)",
    "evaluation_municipale_batiment":"Éval. munic. bâtiment ($)",
    "evaluation_municipale_terrain": "Éval. munic. terrain ($)",
    "annee_construction":            "Année de construction",
    "annee_renovation":              "Année de rénovation",
    "nb_pieces":                     "Nombre de pièces",
    "nb_chambres":                   "Chambres à coucher",
    "nb_salles_bain":                "Salles de bain",
    "nb_stationnements":             "Stationnements",
    "garage":                        "Garage",
    "piscine":                       "Piscine",
    "sous_sol_fini":                 "Sous-sol fini",
    "etat_general":                  "État général",
    "vue":                           "Vue",
    "proximite_nuisances":           "Nuisances à proximité",
    "nom_proprietaire":              "Propriétaire inscrit",
    "nom_commanditaire":             "Commanditaire",
    "objet_evaluation":              "Objet de l'évaluation",
}

# Champs obligatoires pour la conformité B001 (subset)
_REQUIRED_INTAKE_FIELDS = {
    "adresse_complete", "type_bien", "surface_habitable",
    "evaluation_municipale_totale", "annee_construction",
}


def get_intake_review(case: dict) -> list[dict]:
    """Retourne la liste des champs d'intake pour UI CHECKPOINT 1.

    Chaque entrée : {key, label, value, missing, required}.
    missing=True si la valeur est None/absente.
    required=True si le champ est obligatoire (B001 étendu).
    """
    rows = []
    for key, label in _FIELD_LABELS_FR.items():
        value = case.get(key)
        # Normalise les booleans pour affichage
        if isinstance(value, bool):
            display = "Oui" if value else "Non"
        elif value is None:
            display = None
        else:
            display = str(value)
        rows.append({
            "key": key,
            "label": label,
            "value": display,
            "missing": value is None,
            "required": key in _REQUIRED_INTAKE_FIELDS,
        })
    return rows

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
    doc = None
    try:
        doc = fitz.open(str(path))
        if getattr(doc, "is_encrypted", False) is True:
            return "", False
        if len(doc) > _MAX_PDF_PAGES:
            return "", False
        pages_text = []
        total_chars = 0
        for i, page in enumerate(doc):
            if i >= _MAX_PDF_PAGES:
                break
            text = page.get_text()
            remaining = _MAX_EXTRACTED_TEXT_CHARS - total_chars
            if remaining <= 0:
                break
            if len(text) > remaining:
                text = text[:remaining]
            pages_text.append(text)
            total_chars += len(text)
        text = "\n".join(pages_text).strip()
        return text, bool(text)
    except Exception:
        return "", False
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass


def pdf_page_to_b64_image(path: Path, page_num: int = 0) -> str:
    """Convert a PDF page to base64 PNG for Vision API. Returns empty string on failure."""
    try:
        import fitz  # type: ignore  # PyMuPDF
    except ImportError:
        return ""
    doc = None
    try:
        doc = fitz.open(str(path))
        if getattr(doc, "is_encrypted", False) is True:
            return ""
        if len(doc) > _MAX_PDF_PAGES:
            return ""
        if page_num >= len(doc):
            return ""
        page = doc[page_num]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for legibility
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        return base64.b64encode(png_bytes).decode("ascii")
    except Exception:
        return ""
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass


def describe_with_vision(b64_image: str, client, prompt: str = _VISION_PROMPT_DOC) -> str:
    """Call GPT-4o Vision with a base64 PNG image. Returns description text."""
    if not b64_image or client is None:
        return ""
    try:
        resp = client.chat.completions.create(
            model=get_llm_model("extraction_pdf"),
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
            model=get_llm_model("extraction_pdf"),
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
    if len(combined) > _MAX_STRUCTURED_PROMPT_CHARS:
        combined = combined[:_MAX_STRUCTURED_PROMPT_CHARS] + "\n\n[TRONQUE]"
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
            model=get_llm_model("parse_structured"),
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


# ── JLR CSV ───────────────────────────────────────────────────────────────────

# Colonnes JLR connues (aliases acceptés)
_JLR_COL_ALIASES: dict[str, list[str]] = {
    "adresse":            ["adresse", "address", "adresse_propriete"],
    "prix_vente":         ["prix_vente", "prix_transaction", "price", "prix"],
    "date_vente":         ["date_vente", "date_transaction", "date_contrat", "date"],
    "surface_habitable":  ["surface_habitable", "superficie_habitable", "sf_habitable", "superficie", "area_sqft"],
    "surface_terrain":    ["surface_terrain", "superficie_terrain", "terrain_sqft"],
    "nb_pieces":          ["nb_pieces", "pieces", "rooms", "nombre_pieces"],
    "nb_chambres":        ["nb_chambres", "chambres", "bedrooms", "nombre_chambres"],
    "nb_stationnements":  ["nb_stationnements", "stationnements", "parking"],
    "annee_construction": ["annee_construction", "annee", "year_built", "an_construction"],
    "type_bien":          ["type_bien", "type_propriete", "property_type", "type"],
    "source_id":          ["no_fiche", "fiche", "fiche_jlr", "source_id", "numero_fiche", "ref"],
    "latitude":           ["latitude", "lat"],
    "longitude":          ["longitude", "lon", "lng"],
    "distance_km":        ["distance_km", "distance"],
}


def _jlr_resolve_col(header: list[str]) -> dict[str, str]:
    """Retourne {champ_cible: col_csv} pour chaque alias trouvé dans le header."""
    header_lower = {h.strip().lower(): h for h in header}
    mapping: dict[str, str] = {}
    for field, aliases in _JLR_COL_ALIASES.items():
        for alias in aliases:
            if alias in header_lower:
                mapping[field] = header_lower[alias]
                break
    return mapping


def _jlr_float(val: str) -> float | None:
    """Parse float from JLR CSV cell (handles spaces, commas as thousands sep)."""
    if not val or not val.strip():
        return None
    cleaned = val.strip().replace("\u00a0", "").replace(",", "").replace(" ", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _jlr_int(val: str) -> int | None:
    f = _jlr_float(val)
    return int(f) if f is not None else None


def parse_jlr_csv(path: Path) -> list[dict]:
    """Parse un export CSV JLR et retourne une liste de comparables normalisés.

    Chaque comparable contient les champs cibles de _JLR_COL_ALIASES
    ainsi qu'un ``source_id`` auto-généré si absent.

    Raises:
        ValueError: si le fichier ne peut pas être lu ou si aucune ligne valide n'est trouvée.
    """
    import csv as _csv

    if not path.exists():
        raise ValueError(f"Fichier CSV introuvable : {path}")

    try:
        raw = path.read_bytes()
        # Détection BOM UTF-8 (fréquent dans les exports JLR)
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except Exception as exc:
            raise ValueError(f"Encodage CSV non supporté : {exc}") from exc

    lines = text.splitlines()
    if not lines:
        raise ValueError("CSV vide")

    # Détection auto du séparateur (virgule ou point-virgule)
    sample = lines[0]
    sep = ";" if sample.count(";") > sample.count(",") else ","

    reader = _csv.DictReader(lines, delimiter=sep)
    header = reader.fieldnames or []
    if not header:
        raise ValueError("CSV sans en-têtes")

    col_map = _jlr_resolve_col(list(header))
    if not col_map.get("prix_vente") and not col_map.get("adresse"):
        raise ValueError(
            "Le CSV ne contient aucune colonne reconnue. "
            "Colonnes attendues : adresse, prix_vente, date_vente, surface_habitable, …"
        )

    rows: list[dict] = []
    for i, row in enumerate(reader):
        def _get(field: str) -> str:
            col = col_map.get(field)
            return row.get(col, "").strip() if col else ""

        prix = _jlr_float(_get("prix_vente"))
        if prix is None or prix <= 0:
            continue  # ligne sans prix valide ignorée

        adresse = _get("adresse") or f"Comparable JLR {i + 1}"
        source_id = _get("source_id") or f"JLR-{i + 1:04d}"

        comp: dict = {
            "comparable_id": source_id,
            "source_id":     source_id,
            "adresse":       adresse,
            "prix_vente":    prix,
            "date_vente":    _get("date_vente") or "",
        }

        surf_hab = _jlr_float(_get("surface_habitable"))
        if surf_hab is not None:
            comp["surface_habitable"] = surf_hab
            # Stockage au format attendu par tools.score_comparable
            comp["surface"] = {"value": surf_hab, "unit": "pi2"}

        surf_terrain = _jlr_float(_get("surface_terrain"))
        if surf_terrain is not None:
            comp["surface_terrain"] = surf_terrain

        nb_pieces = _jlr_int(_get("nb_pieces"))
        if nb_pieces is not None:
            comp["nb_pieces"] = nb_pieces

        nb_chambres = _jlr_int(_get("nb_chambres"))
        if nb_chambres is not None:
            comp["nb_chambres"] = nb_chambres

        nb_stat = _jlr_int(_get("nb_stationnements"))
        if nb_stat is not None:
            comp["nb_stationnements"] = nb_stat

        annee = _jlr_int(_get("annee_construction"))
        if annee is not None:
            comp["annee_construction"] = annee

        type_bien = _get("type_bien")
        if type_bien:
            comp["type_bien"] = type_bien.lower().strip()

        lat = _jlr_float(_get("latitude"))
        lon = _jlr_float(_get("longitude"))
        if lat is not None and lon is not None:
            comp["latitude"] = lat
            comp["longitude"] = lon

        dist = _jlr_float(_get("distance_km"))
        if dist is not None:
            comp["distance_km"] = dist

        # Source quality tag for scoring
        comp["source_type"] = "mls_centris"

        rows.append(comp)

    if not rows:
        raise ValueError(
            "Aucune ligne valide dans le CSV JLR. "
            "Vérifiez que la colonne prix_vente contient des montants numériques."
        )

    return rows


class IngestionError(Exception):
    """Levée quand l'extraction PDF échoue de façon critique (visible dans l'UI)."""


def _resolve_uploaded_file(uploads_dir: Path, filename: str) -> Path | None:
    if not filename or "/" in filename or "\\" in filename:
        return None
    root = uploads_dir.resolve()
    candidate = (uploads_dir / filename).resolve()
    if not candidate.is_relative_to(root):
        return None
    return candidate


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

    Raises:
        IngestionError: si des documents sont présents mais qu'aucun texte n'a pu être extrait.
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
    skipped_files: list[str] = []

    for doc in uploaded:
        filename = str(doc.get("filename") or "")
        mime_type = str(doc.get("mime_type") or "")
        if not filename:
            continue
        path = _resolve_uploaded_file(uploads_dir, filename)
        if path is None:
            doc["extraction_status"] = "error"
            doc["extraction_error"] = "Chemin de document invalide."
            skipped_files.append(filename or "?")
            continue
        if not path.exists():
            doc["extraction_status"] = "error"
            doc["extraction_error"] = "Document introuvable sur disque."
            skipped_files.append(filename)
            continue
        result = extract_document(path, mime_type, client)
        # Persist extraction results in session metadata in-place
        doc["extracted_text"] = result["extracted_text"]
        doc["extraction_method"] = result["method"]
        if result["extracted_text"]:
            doc["extraction_status"] = "extracted"
            doc.pop("extraction_error", None)
            extracted_docs.append(result)
        elif result["method"] == "skipped":
            doc["extraction_status"] = "skipped"
            doc["extraction_error"] = (
                "Extraction PDF incomplete - aucun texte extrait. "
                "Verifiez que le document n'est pas protege par mot de passe ou illisible."
            )
            skipped_files.append(filename)

    # Raise if documents were uploaded but no text could be extracted
    if uploaded and not extracted_docs:
        filenames = [d.get("filename", "?") for d in uploaded]
        raise IngestionError(
            f"Extraction PDF incomplète — aucun texte extrait de : {', '.join(filenames)}. "
            "Vérifiez que le document n'est pas protégé par mot de passe ou illisible."
        )

    return parse_structured_fields(extracted_docs, client)
