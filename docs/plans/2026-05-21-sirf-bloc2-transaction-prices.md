# SIRF Bloc 2 — Transaction Prices from Registre Foncier

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the Infolot+MAMH comparable pool with actual transaction prices (prix_vente, date_vente) by scraping Registre foncier SIRF PDFs and extracting values via pytesseract OCR.

**Architecture:** New module `engine/registre_foncier.py` handles SIRF session auth, lot search, PDF download, and pytesseract OCR extraction. Cache hierarchy: local disk (dev/test, 90-day JSON files) → Supabase `sirf_cache` table (production, shared across evaluators, 90-day TTL). New public function `enrich_pool_with_sirf()` is called after `build_comparable_pool()` in `comparables_builder.py` with a cost cap (`max_sirf_lookups`, default 10). Non-blocking: if SIRF fails or `prix_vente` cannot be parsed, the comparable stays in the pool with its MAMH score and prix_vente=0.

**Tech Stack:** Python 3.11, httpx (async-capable sync session), BeautifulSoup4 (HTML parsing), pdf2image + pytesseract + tesseract-ocr + poppler (OCR pipeline), supabase-py (Supabase client), PostgreSQL (Supabase)

**Assumptions:**
- Assumes env vars `SIRF_USERNAME` and `SIRF_PASSWORD` hold valid compte client SIRF credentials — will NOT work without a paid SIRF account
- Assumes SIRF portal HTML structure matches the `_SIRF_*` URL/selector constants at top of `registre_foncier.py` — MUST validate these constants against the live portal before first production use (they are centralised for easy update)
- Assumes pool items have `no_lot: int | None` field (set by `comparables_builder._pool_item_from_mamh_record`) — items with `no_lot=None` are skipped silently
- Assumes pytesseract, tesseract-ocr (with `fra` language pack), pdf2image, and poppler are installed in the runtime environment
- Assumes Supabase migration 004 is applied before production use; module degrades to local-disk-only cache if `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` env vars are absent
- Assumes `no_lot` integer from Infolot WFS maps directly to SIRF cadastral designation string (format `str(no_lot)`) — will NOT work if SIRF requires canton prefix format like `"07-1234567"`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `supabase/migrations/004_sirf_cache.sql` | Create | `sirf_cache` table + RLS + TTL index |
| `backend/engine/registre_foncier.py` | Create | SIRF scraper, OCR parser, cache layer, public `enrich_pool_with_sirf()` |
| `backend/engine/comparables_builder.py` | Modify | Call `enrich_pool_with_sirf()` after pool build |
| `backend/tests/test_registre_foncier.py` | Create | Unit tests for OCR parsing + cache logic (no live SIRF calls) |

---

### Task 1: Supabase migration — sirf_cache table

**Files:**
- Create: `supabase/migrations/004_sirf_cache.sql`

**Security flag:** `none`

**Does NOT cover:** RLS policies for multi-tenant access beyond service role; index on `expires_at` covers TTL cleanup only.

- [ ] **Step 1: Write the migration SQL**

```sql
-- supabase/migrations/004_sirf_cache.sql
-- Cache des transactions SIRF (Registre foncier).
-- Durée de vie : 90 jours. Partagé entre tous les évaluateurs (service-role only).

create table if not exists sirf_cache (
  id           uuid primary key default gen_random_uuid(),
  no_lot       bigint not null,
  prix_vente   numeric not null default 0,
  date_vente   text    not null default '',
  vendeur      text    not null default '',
  acheteur     text    not null default '',
  source_doc   text    not null default '',   -- identifiant acte SIRF (ex: "2024-12345")
  raw_text     text    not null default '',   -- texte OCR brut pour audit
  fetched_at   timestamptz not null default now(),
  expires_at   timestamptz not null default now() + interval '90 days'
);

-- Lookup rapide par lot + validité
create index if not exists sirf_cache_no_lot_expires
  on sirf_cache (no_lot, expires_at desc);

-- Service-role only — les évaluateurs ne lisent/écrivent pas directement
alter table sirf_cache enable row level security;

create policy "service role full access"
  on sirf_cache for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');
```

- [ ] **Step 2: Verify file exists**

Run: `ls supabase/migrations/004_sirf_cache.sql`
Expected: file present, no error

- [ ] **Step 3: Apply migration locally (if Supabase CLI available)**

Run: `supabase db push --local 2>/dev/null || echo "SKIP — apply manually via Supabase dashboard"`
Expected: either "Finished supabase db push" or "SKIP"

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/004_sirf_cache.sql
git commit -m "feat(db): add sirf_cache table for SIRF transaction price caching"
```

---

### Task 2: OCR parsing — pure functions, fully testable

**Files:**
- Create: `backend/engine/registre_foncier.py` (OCR section only — Tasks 3 and 4 will append to this file)
- Create: `backend/tests/test_registre_foncier.py`

**Security flag:** `none`

**Does NOT cover:** Network calls, SIRF auth, or cache — those are in Tasks 3 and 4. This task produces only the pure text-parsing functions.

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_registre_foncier.py
"""Tests pour le module registre_foncier — OCR parsing, cache, scraping (mocké)."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures texte OCR synthétiques
# ---------------------------------------------------------------------------

ACTE_SIMPLE = """
ACTE DE VENTE

Les soussignés déclarent avoir procédé à la vente et cession
de l'immeuble ci-après désigné pour la somme de 485 000,00 $
(quatre cent quatre-vingt-cinq mille dollars).

Date de la vente : le 15 mars 2024

VENDEUR : TREMBLAY, Jean-Pierre
ACHETEUR : GAGNON, Marie-Andrée

DÉSIGNATION CADASTRALE : 1 234 567
"""

ACTE_PRIX_EN_CHIFFRES = """
CONTRAT DE VENTE

Prix de vente : 735 500 $
Signé le 3 juin 2023

Vendeur: DUMONT, Robert
Acheteur: LAPOINTE, Sylvie
"""

ACTE_CONTREPARTIE = """
CESSION D'IMMEUBLE

Moyennant une contrepartie de 1 200 000,00 $
En date du 2022-11-28

V: INVEST-NORD INC.
A: PLACEMENTS CÔTÉ INC.
"""

ACTE_PRIX_INTROUVABLE = """
ACTE DIVERS
Aucune mention de prix.
Date inconnue.
"""


# ---------------------------------------------------------------------------
# Tests parse_transaction_text
# ---------------------------------------------------------------------------

class TestParseTransactionText:
    """Tests pour _parse_transaction_text() — extraction prix/date/parties depuis texte OCR."""

    def test_prix_somme_de(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_SIMPLE)
        assert result["prix_vente"] == 485000.0

    def test_date_textuelle_mars(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_SIMPLE)
        assert result["date_vente"] == "2024-03-15"

    def test_vendeur_acheteur(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_SIMPLE)
        assert "TREMBLAY" in result["vendeur"]
        assert "GAGNON" in result["acheteur"]

    def test_prix_label_direct(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_PRIX_EN_CHIFFRES)
        assert result["prix_vente"] == 735500.0

    def test_date_iso_format(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_CONTREPARTIE)
        assert result["date_vente"] == "2022-11-28"

    def test_contrepartie_pattern(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_CONTREPARTIE)
        assert result["prix_vente"] == 1200000.0

    def test_prix_introuvable_returns_zero(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_PRIX_INTROUVABLE)
        assert result["prix_vente"] == 0.0

    def test_date_introuvable_returns_empty(self):
        from engine.registre_foncier import _parse_transaction_text
        result = _parse_transaction_text(ACTE_PRIX_INTROUVABLE)
        assert result["date_vente"] == ""


# ---------------------------------------------------------------------------
# Tests cache local disque
# ---------------------------------------------------------------------------

class TestLocalCache:
    def test_miss_returns_none(self, tmp_path):
        from engine.registre_foncier import _local_cache_get
        assert _local_cache_get(9999999, tmp_path) is None

    def test_store_then_get(self, tmp_path):
        from engine.registre_foncier import _local_cache_get, _local_cache_set
        data = {"prix_vente": 350000.0, "date_vente": "2023-06-01", "vendeur": "X", "acheteur": "Y", "source_doc": "abc", "raw_text": "..."}
        _local_cache_set(1234567, data, tmp_path)
        result = _local_cache_get(1234567, tmp_path)
        assert result is not None
        assert result["prix_vente"] == 350000.0

    def test_expired_entry_returns_none(self, tmp_path):
        from engine.registre_foncier import _local_cache_get, _local_cache_set
        data = {"prix_vente": 100.0, "date_vente": "2020-01-01", "vendeur": "", "acheteur": "", "source_doc": "", "raw_text": ""}
        _local_cache_set(7777777, data, tmp_path, ttl_days=-1)  # ttl_days=-1 → already expired
        assert _local_cache_get(7777777, tmp_path) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:/Users/simon/eval-immo && python -m pytest backend/tests/test_registre_foncier.py -x -q 2>&1 | head -20`
Expected: FAIL — `ModuleNotFoundError: No module named 'engine.registre_foncier'`

- [ ] **Step 3: Implement OCR parsing functions**

Create `backend/engine/registre_foncier.py` with the following content:

```python
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
```

- [ ] **Step 4: Run OCR parsing + cache tests**

Run: `cd C:/Users/simon/eval-immo && python -m pytest backend/tests/test_registre_foncier.py -x -q -k "ParseTransaction or LocalCache" 2>&1 | tail -10`
Expected: PASS — all 10 tests green

- [ ] **Step 5: Commit**

```bash
git add backend/engine/registre_foncier.py backend/tests/test_registre_foncier.py
git commit -m "feat(sirf): add OCR parsing and local disk cache for SIRF transactions"
```

---

### Task 3: SIRF integration into comparables_builder + Supabase cache tests

**Files:**
- Modify: `backend/engine/comparables_builder.py`
- Modify: `backend/tests/test_registre_foncier.py` (add Supabase cache + integration tests)

**Security flag:** `none`

**Does NOT cover:** Live SIRF HTTP calls — those are mocked in all tests. Supabase upsert conflict resolution (duplicate no_lot rows within TTL are acceptable; the query uses `order(fetched_at, desc=True).limit(1)`).

- [ ] **Step 1: Add Supabase cache tests and enrich_pool integration test**

Append to `backend/tests/test_registre_foncier.py`:

```python
# ---------------------------------------------------------------------------
# Tests cache Supabase (mock)
# ---------------------------------------------------------------------------

class TestSupabaseCache:
    def _mock_supabase(self, rows: list[dict]):
        """Construit un faux client Supabase retournant rows."""
        sb = MagicMock()
        chain = sb.table.return_value.select.return_value.eq.return_value.gt.return_value.order.return_value.limit.return_value
        chain.execute.return_value = MagicMock(data=rows)
        return sb

    def test_miss_returns_none(self):
        from engine.registre_foncier import _supabase_cache_get
        sb = self._mock_supabase([])
        assert _supabase_cache_get(9999999, sb) is None

    def test_hit_returns_dict(self):
        from engine.registre_foncier import _supabase_cache_get
        row = {"prix_vente": 400000.0, "date_vente": "2023-04-10", "vendeur": "X", "acheteur": "Y", "source_doc": "z", "raw_text": ""}
        sb = self._mock_supabase([row])
        result = _supabase_cache_get(1234567, sb)
        assert result is not None
        assert result["prix_vente"] == 400000.0

    def test_none_client_returns_none(self):
        from engine.registre_foncier import _supabase_cache_get
        assert _supabase_cache_get(1234567, None) is None

    def test_set_with_none_client_no_error(self):
        from engine.registre_foncier import _supabase_cache_set
        # Should not raise
        _supabase_cache_set(1234567, {"prix_vente": 100.0, "date_vente": "", "vendeur": "", "acheteur": "", "source_doc": "", "raw_text": ""}, None)


# ---------------------------------------------------------------------------
# Tests enrich_pool_with_sirf
# ---------------------------------------------------------------------------

class TestEnrichPoolWithSirf:
    def _make_pool_item(self, no_lot: int, prix_vente: float = 0.0) -> dict:
        return {
            "comparable_id": f"MAMH-{no_lot}",
            "source_id":     f"MAMH-{no_lot}",
            "source_type":   "role_evaluation_municipale",
            "no_lot":        no_lot,
            "prix_vente":    prix_vente,
            "date_vente":    "",
            "surface":       {"value": 120.0, "unit": "m2"},
            "distance_km":   0.5,
        }

    def test_item_with_prix_already_set_not_touched(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        pool = [self._make_pool_item(111, prix_vente=350000.0)]
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        assert result[0]["prix_vente"] == 350000.0
        assert result[0]["source_type"] == "role_evaluation_municipale"  # unchanged

    def test_item_without_no_lot_not_touched(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        item = self._make_pool_item(0)
        item["no_lot"] = None
        result = enrich_pool_with_sirf([item], cache_dir=tmp_path, supabase_client=None)
        assert result[0]["no_lot"] is None

    def test_cache_hit_enriches_item(self, tmp_path):
        from engine.registre_foncier import _local_cache_set, enrich_pool_with_sirf
        no_lot = 9876543
        cached = {"prix_vente": 520000.0, "date_vente": "2024-01-20", "vendeur": "A", "acheteur": "B", "source_doc": "doc1", "raw_text": ""}
        _local_cache_set(no_lot, cached, tmp_path)
        pool = [self._make_pool_item(no_lot)]
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        assert result[0]["prix_vente"] == 520000.0
        assert result[0]["date_vente"] == "2024-01-20"
        assert result[0]["source_type"] == "registre_foncier"

    def test_sirf_error_returns_pool_intact(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        pool = [self._make_pool_item(1111111)]
        # No cache, no SIRF credentials → _sirf_session() will raise RuntimeError
        # enrich_pool_with_sirf must NOT raise
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        assert len(result) == 1
        assert result[0]["prix_vente"] == 0.0  # unchanged

    def test_max_sirf_lookups_respected(self, tmp_path):
        from engine.registre_foncier import enrich_pool_with_sirf
        pool = [self._make_pool_item(i) for i in range(1000001, 1000016)]  # 15 items
        # With max_sirf_lookups=3, should not try more than 3 live lookups
        # (all will fail due to missing credentials → non-blocking)
        result = enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None, max_sirf_lookups=3)
        assert len(result) == 15  # all items preserved

    def test_pool_not_mutated(self, tmp_path):
        from engine.registre_foncier import _local_cache_set, enrich_pool_with_sirf
        no_lot = 2222222
        _local_cache_set(no_lot, {"prix_vente": 300000.0, "date_vente": "2023-05-01", "vendeur": "", "acheteur": "", "source_doc": "", "raw_text": ""}, tmp_path)
        original_item = self._make_pool_item(no_lot)
        pool = [original_item]
        enrich_pool_with_sirf(pool, cache_dir=tmp_path, supabase_client=None)
        # Original item in pool must not have been mutated
        assert original_item["prix_vente"] == 0.0
```

- [ ] **Step 2: Run new tests to verify they fail (enrich_pool tests already pass partially from Task 2)**

Run: `cd C:/Users/simon/eval-immo && python -m pytest backend/tests/test_registre_foncier.py -x -q 2>&1 | tail -10`
Expected: PASS — all tests green (enrich_pool functions already in registre_foncier.py from Task 2 Step 3)

- [ ] **Step 3: Wire enrich_pool_with_sirf into build_comparable_pool**

In `backend/engine/comparables_builder.py`, add the import at the top after the existing imports:

```python
# À ajouter après les imports existants (ligne ~19, après `logger = ...`)
```

Find the line `logger = logging.getLogger("comparables_builder")` and add after it:

```python
try:
    from engine.registre_foncier import enrich_pool_with_sirf as _enrich_sirf
    _SIRF_AVAILABLE = True
except ImportError:
    _SIRF_AVAILABLE = False
```

Then in `build_comparable_pool()`, find the return statements at the end (the function returns from `_build_pool_xml()` or `_build_pool_montreal()`) and wrap them with enrichment. The function currently ends with:

```python
    if city_code in _XML_CITIES:
        return _build_pool_xml(...)
    elif city_code == "montreal":
        return _build_pool_montreal(...)
    return []
```

Replace those return statements with:

```python
    if city_code in _XML_CITIES:
        pool = _build_pool_xml(
            city_code=city_code,
            subject_lat=subject_lat,
            subject_lon=subject_lon,
            subject_surface_m2=subject_surface_m2,
            subject_type_bien=subject_type_bien,
            radius_km=radius_km,
            cache_dir=cache_dir,
            max_candidates=max_candidates,
        )
    elif city_code == "montreal":
        pool = _build_pool_montreal(
            subject_address=subject_address,
            subject_lat=subject_lat,
            subject_lon=subject_lon,
            subject_surface_m2=subject_surface_m2,
            subject_type_bien=subject_type_bien,
            cache_dir=cache_dir,
            max_candidates=max_candidates,
        )
    else:
        return []

    if _SIRF_AVAILABLE and pool:
        try:
            pool = _enrich_sirf(pool, cache_dir=cache_dir)
        except Exception as exc:
            logger.warning("enrich_pool_with_sirf failed (non-bloquant): %s", exc)

    return pool
```

- [ ] **Step 4: Run full test suite to verify no regression**

Run: `cd C:/Users/simon/eval-immo && python -m pytest backend/tests/ -x -q 2>&1 | tail -15`
Expected: All tests pass (including existing 73+ tests from previous session)

- [ ] **Step 5: Commit**

```bash
git add backend/engine/registre_foncier.py backend/engine/comparables_builder.py backend/tests/test_registre_foncier.py
git commit -m "feat(sirf): wire enrich_pool_with_sirf into build_comparable_pool + full test suite"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ SIRF session auth (`_sirf_session()`)
- ✅ Search by NOLOT (`_sirf_search_lot()`)
- ✅ PDF download (`_download_sirf_pdf()`)
- ✅ pytesseract OCR (`_ocr_pdf_bytes()` + `_parse_transaction_text()`)
- ✅ Supabase `sirf_cache` table (Task 1 migration)
- ✅ Local disk cache (90-day TTL)
- ✅ Cost cap via `max_sirf_lookups`
- ✅ Non-blocking: any exception returns pool intact
- ✅ `source_type` upgraded to `"registre_foncier"` (score 1.0) when price extracted
- ✅ Integration in `comparables_builder.build_comparable_pool()`

**2. Placeholder scan:** No TBD/TODO in implementation code. SIRF URL constants flagged clearly as needing validation. No "add error handling" — all handlers are explicit.

**3. Type consistency:**
- `enrich_pool_with_sirf(pool: list[dict]) -> list[dict]` — consistent across Task 2 and 3
- `_parse_transaction_text(text: str) -> dict[str, object]` — used only in Task 2
- `_local_cache_get/set(no_lot: int, ...)` — `int` consistent; `item["no_lot"]` cast to `int` in `enrich_pool_with_sirf`

**4. Scope-reduction scan:** No "v1/basic/simple/placeholder" in implementation. The SIRF constants flagged as needing validation are an explicit assumption, not a scope downgrade.
