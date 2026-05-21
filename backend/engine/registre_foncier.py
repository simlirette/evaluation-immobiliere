"""
registre_foncier.py — Intégration SIRF (Registre foncier du Québec).

Responsabilités :
  1. OCR parsing  — extrait prix_vente / date_vente / parties depuis texte brut (pur, testable)
  2. Cache disque — JSON par no_lot dans cache_dir/sirf/ (90 jours)
  3. SIRF HTTP    — session auth, recherche par no_lot, téléchargement PDF
  4. enrichissement — enrich_pool_with_sirf() → remplace prix_vente=0 dans le pool MAMH

Non-bloquant : toute exception retourne {} / [] sans lever vers l'appelant.

CONSTANTS À VALIDER CONTRE LE PORTAIL SIRF AVANT MISE EN PRODUCTION :
  _SIRF_LOGIN_URL, _SIRF_SEARCH_URL, _SIRF_LOGIN_FIELDS, _SIRF_RESULT_SELECTOR
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, timedelta
from pathlib import Path

logger = logging.getLogger("registre_foncier")

# ---------------------------------------------------------------------------
# SIRF portal constants — MUST validate against live portal before production
# ---------------------------------------------------------------------------
_SIRF_BASE           = "https://www.registrefoncier.gouv.qc.ca"
_SIRF_LOGIN_URL      = f"{_SIRF_BASE}/sirf/index.do"
_SIRF_SEARCH_URL     = f"{_SIRF_BASE}/sirf/requetes/RequeteLotDesignCadastrale.do"
_SIRF_LOGIN_FIELDS   = {"j_username": None, "j_password": None}   # None = filled at runtime
_SIRF_RESULT_SELECTOR = "table.resultatRecherche tr[data-href]"   # CSS for actes rows
_SIRF_PDF_URL_ATTR   = "data-href"                                 # attr on result row
_SIRF_SEARCH_FIELD   = "noLot"                                     # POST field for lot number

# ---------------------------------------------------------------------------
# OCR regex patterns — French Quebec legal documents
# ---------------------------------------------------------------------------
_PRIX_RE: list[re.Pattern] = [
    re.compile(r"pour\s+la\s+somme\s+de\s+([\d\s]+(?:,\d{2})?)\s*\$", re.IGNORECASE),
    re.compile(r"somme\s+de\s+([\d\s]+(?:,\d{2})?)\s*\$", re.IGNORECASE),
    re.compile(r"prix\s+de\s+vente\s*[:\-]?\s*([\d\s]+(?:,\d{2})?)\s*\$", re.IGNORECASE),
    re.compile(r"contrepartie\s+de\s+([\d\s]+(?:,\d{2})?)\s*\$", re.IGNORECASE),
    re.compile(r"\$\s*([\d\s]{3,}(?:,\d{2})?)\s*\n?\s*\(", re.IGNORECASE),
]
_DATE_TEXTUELLE_RE = re.compile(
    r"(?:le|signé\s+le|en\s+date\s+du|date\s+de\s+la\s+vente\s*[:\-]?\s*le)\s+"
    r"(\d{1,2})\s+(\w+)\s+(\d{4})",
    re.IGNORECASE,
)
_DATE_ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_VENDEUR_RE  = re.compile(r"(?:vendeur|v)\s*[:\-]\s*(.+)", re.IGNORECASE)
_ACHETEUR_RE = re.compile(r"(?:acheteur|a)\s*[:\-]\s*(.+)", re.IGNORECASE)

_MOIS_FR: dict[str, int] = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}

_SIRF_CACHE_TTL_DAYS = 90


# ---------------------------------------------------------------------------
# 1. OCR parsing — pure functions, no I/O
# ---------------------------------------------------------------------------

def _parse_prix(text: str) -> float:
    """Extrait le premier montant en dollars trouvé dans le texte OCR."""
    for pattern in _PRIX_RE:
        m = pattern.search(text)
        if m:
            raw = m.group(1).replace("\xa0", "").replace(" ", "").replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
    return 0.0


def _parse_date(text: str) -> str:
    """Extrait la première date de vente trouvée. Retourne '' si introuvable."""
    # Priorité 1 : date textuelle française ("le 15 mars 2024")
    m = _DATE_TEXTUELLE_RE.search(text)
    if m:
        jour, mois_str, annee = m.group(1), m.group(2).lower().strip(), m.group(3)
        mois = _MOIS_FR.get(mois_str)
        if mois:
            try:
                return date(int(annee), mois, int(jour)).isoformat()
            except ValueError:
                pass

    # Priorité 2 : format ISO (2022-11-28)
    m2 = _DATE_ISO_RE.search(text)
    if m2:
        try:
            return date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3))).isoformat()
        except ValueError:
            pass

    return ""


def _parse_partie(text: str, pattern: re.Pattern) -> str:
    """Extrait vendeur ou acheteur depuis le texte OCR (première ligne après le label)."""
    m = pattern.search(text)
    if m:
        return m.group(1).strip()[:120]
    return ""


def _parse_transaction_text(text: str) -> dict[str, object]:
    """
    Extrait prix_vente, date_vente, vendeur, acheteur depuis le texte OCR brut.
    Retourne toujours un dict complet (valeurs vides si non trouvé).
    """
    return {
        "prix_vente": _parse_prix(text),
        "date_vente": _parse_date(text),
        "vendeur":    _parse_partie(text, _VENDEUR_RE),
        "acheteur":   _parse_partie(text, _ACHETEUR_RE),
    }


# ---------------------------------------------------------------------------
# 2. Cache disque local (JSON, 90 jours)
# ---------------------------------------------------------------------------

def _local_cache_path(no_lot: int, cache_dir: Path) -> Path:
    sirf_dir = cache_dir / "sirf"
    sirf_dir.mkdir(parents=True, exist_ok=True)
    return sirf_dir / f"{no_lot}.json"


def _local_cache_get(no_lot: int, cache_dir: Path) -> dict | None:
    """Retourne le dict mis en cache si encore valide, None sinon."""
    path = _local_cache_path(no_lot, cache_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        expires_str = data.get("_expires", "")
        if expires_str and date.fromisoformat(expires_str) < date.today():
            path.unlink(missing_ok=True)
            return None
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception:
        return None


def _local_cache_set(no_lot: int, data: dict, cache_dir: Path, ttl_days: int = _SIRF_CACHE_TTL_DAYS) -> None:
    path = _local_cache_path(no_lot, cache_dir)
    payload = dict(data)
    payload["_expires"] = (date.today() + timedelta(days=ttl_days)).isoformat()
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("sirf local cache write failed for no_lot=%s: %s", no_lot, exc)


# ---------------------------------------------------------------------------
# 3. Supabase cache (production)
# ---------------------------------------------------------------------------

def _supabase_cache_get(no_lot: int, supabase_client) -> dict | None:
    """Lit le cache Supabase sirf_cache pour no_lot. Retourne None si absent/expiré."""
    if supabase_client is None:
        return None
    try:
        resp = (
            supabase_client.table("sirf_cache")
            .select("prix_vente,date_vente,vendeur,acheteur,source_doc,raw_text")
            .eq("no_lot", no_lot)
            .gt("expires_at", date.today().isoformat())
            .order("fetched_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0] if rows else None
    except Exception as exc:
        logger.warning("supabase sirf_cache get failed: %s", exc)
        return None


def _supabase_cache_set(no_lot: int, data: dict, supabase_client) -> None:
    if supabase_client is None:
        return
    try:
        supabase_client.table("sirf_cache").upsert({
            "no_lot":     no_lot,
            "prix_vente": data.get("prix_vente", 0),
            "date_vente": data.get("date_vente", ""),
            "vendeur":    data.get("vendeur", ""),
            "acheteur":   data.get("acheteur", ""),
            "source_doc": data.get("source_doc", ""),
            "raw_text":   data.get("raw_text", "")[:4000],
        }).execute()
    except Exception as exc:
        logger.warning("supabase sirf_cache set failed: %s", exc)


# ---------------------------------------------------------------------------
# 4. SIRF HTTP session — auth, search, PDF download
# ---------------------------------------------------------------------------

def _build_supabase_client():
    """Construit un client Supabase depuis les variables d'environnement, ou None."""
    url  = os.environ.get("SUPABASE_URL", "")
    key  = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception as exc:
        logger.warning("Supabase client init failed: %s", exc)
        return None


def _sirf_session():
    """
    Retourne un httpx.Client authentifié sur le portail SIRF.
    Lève RuntimeError si les credentials sont absents.
    Lève httpx.HTTPError si le login échoue.

    NOTE: Les constantes _SIRF_LOGIN_URL / _SIRF_LOGIN_FIELDS DOIVENT être
    validées contre le portail SIRF en production (inspecter Network tab).
    """
    import httpx
    username = os.environ.get("SIRF_USERNAME", "")
    password = os.environ.get("SIRF_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("SIRF_USERNAME / SIRF_PASSWORD manquants dans l'environnement")

    client = httpx.Client(follow_redirects=True, timeout=30.0)
    # Récupérer la page de login pour obtenir les cookies / token CSRF si nécessaire
    login_page = client.get(_SIRF_LOGIN_URL)
    login_page.raise_for_status()

    # POST credentials
    payload = dict(_SIRF_LOGIN_FIELDS)
    payload["j_username"] = username
    payload["j_password"] = password
    resp = client.post(_SIRF_LOGIN_URL, data=payload)
    resp.raise_for_status()
    return client


def _sirf_search_lot(no_lot: int, session) -> list[dict]:
    """
    Recherche les actes SIRF pour un lot. Retourne liste de {doc_id, pdf_url}.

    NOTE: _SIRF_SEARCH_URL, _SIRF_SEARCH_FIELD, _SIRF_RESULT_SELECTOR et
    _SIRF_PDF_URL_ATTR DOIVENT être validés contre le portail SIRF en production.
    """
    from bs4 import BeautifulSoup
    import httpx
    resp = session.post(_SIRF_SEARCH_URL, data={_SIRF_SEARCH_FIELD: str(no_lot)})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for row in soup.select(_SIRF_RESULT_SELECTOR):
        href = row.get(_SIRF_PDF_URL_ATTR, "")
        if href:
            pdf_url = href if href.startswith("http") else f"{_SIRF_BASE}{href}"
            # Extraire identifiant acte depuis l'URL (dernier segment sans extension)
            doc_id = href.rstrip("/").split("/")[-1].replace(".pdf", "")
            results.append({"doc_id": doc_id, "pdf_url": pdf_url})
    return results


def _download_sirf_pdf(pdf_url: str, session) -> bytes:
    """Télécharge le PDF d'un acte SIRF. Retourne les bytes bruts."""
    resp = session.get(pdf_url)
    resp.raise_for_status()
    return resp.content


def _ocr_pdf_bytes(pdf_bytes: bytes) -> str:
    """Convertit un PDF en texte via pytesseract (langue française)."""
    from pdf2image import convert_from_bytes
    import pytesseract
    images = convert_from_bytes(pdf_bytes, dpi=300)
    return "\n".join(pytesseract.image_to_string(img, lang="fra") for img in images)


def _fetch_sirf_transaction(no_lot: int, session) -> dict:
    """
    Cherche le dernier acte de vente pour un lot et extrait la transaction.
    Retourne {} si aucun acte trouvé ou si l'extraction échoue.
    """
    actes = _sirf_search_lot(no_lot, session)
    if not actes:
        return {}
    # Prendre le premier acte (le plus récent selon l'ordre SIRF)
    acte = actes[0]
    pdf_bytes = _download_sirf_pdf(acte["pdf_url"], session)
    raw_text = _ocr_pdf_bytes(pdf_bytes)
    parsed = _parse_transaction_text(raw_text)
    return {**parsed, "source_doc": acte["doc_id"], "raw_text": raw_text}


# ---------------------------------------------------------------------------
# 5. Point d'entrée public
# ---------------------------------------------------------------------------

def enrich_pool_with_sirf(
    pool: list[dict],
    cache_dir: Path | None = None,
    supabase_client=None,
    max_sirf_lookups: int = 10,
) -> list[dict]:
    """
    Remplace prix_vente=0 / date_vente="" dans les items du pool via SIRF.

    Ordre de priorité pour chaque lot :
      1. Cache disque local (cache_dir/sirf/{no_lot}.json)
      2. Cache Supabase (sirf_cache table)
      3. Requête live SIRF (plafonnée à max_sirf_lookups par appel)

    Items sans no_lot ou avec prix_vente déjà renseigné sont ignorés.
    Non-bloquant : toute exception retourne le pool intact.
    """
    if cache_dir is None:
        cache_dir = Path("data_cache")

    if supabase_client is None:
        supabase_client = _build_supabase_client()

    live_lookups = 0
    sirf_session_obj = None  # ouvert seulement si nécessaire

    enriched = []
    for item in pool:
        no_lot = item.get("no_lot")
        # Copie shallow pour ne pas muter le pool original
        item = dict(item)

        if not no_lot or item.get("prix_vente", 0) > 0:
            enriched.append(item)
            continue

        # 1. Cache disque
        cached = _local_cache_get(int(no_lot), cache_dir)
        if cached is None:
            # 2. Cache Supabase
            cached = _supabase_cache_get(int(no_lot), supabase_client)
            if cached:
                # Répercuter dans le cache disque pour éviter futur appel Supabase
                _local_cache_set(int(no_lot), cached, cache_dir)

        if cached:
            item["prix_vente"]  = float(cached.get("prix_vente") or 0)
            item["date_vente"]  = cached.get("date_vente") or ""
            item["vendeur"]     = cached.get("vendeur") or ""
            item["acheteur"]    = cached.get("acheteur") or ""
            item["source_type"] = "registre_foncier"
            enriched.append(item)
            continue

        # 3. Requête SIRF live (si quota non atteint)
        if live_lookups >= max_sirf_lookups:
            enriched.append(item)
            continue

        try:
            if sirf_session_obj is None:
                sirf_session_obj = _sirf_session()
            transaction = _fetch_sirf_transaction(int(no_lot), sirf_session_obj)
            if transaction:
                _local_cache_set(int(no_lot), transaction, cache_dir)
                _supabase_cache_set(int(no_lot), transaction, supabase_client)
                item["prix_vente"]  = float(transaction.get("prix_vente") or 0)
                item["date_vente"]  = transaction.get("date_vente") or ""
                item["vendeur"]     = transaction.get("vendeur") or ""
                item["acheteur"]    = transaction.get("acheteur") or ""
                if item["prix_vente"] > 0:
                    item["source_type"] = "registre_foncier"
            live_lookups += 1
        except Exception as exc:
            logger.warning("SIRF lookup failed for no_lot=%s: %s", no_lot, exc)
            live_lookups += 1

        enriched.append(item)

    if sirf_session_obj is not None:
        try:
            sirf_session_obj.close()
        except Exception:
            pass

    return enriched
