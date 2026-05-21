"""
registre_foncier.py — Intégration SIRF (Registre foncier du Québec).

Mécanisme (validé 2026-05-21, compte client occasionnel + Network tab) :
  1. Login SIRF via POST sur pf_14_06_01_reglr.asp (champs txtVaCodeUtils / txtMotPasse)
  2. Recherche par no_lot via POST sur pf_13_01_11_02_indx_immbl.asp → 4 redirects
  3. Parse table HTML de la page index → colonne "Remarques" de la ligne "Vente"
  4. Cache disque local (JSON, 90 jours) + Supabase sirf_cache (partagé, 90 jours)

Coût BNRQ : 1,50 $/lot consulté (tarif avril 2026). Cache 90 jours évite répétition.
Prix de vente est dans le HTML — aucun PDF, aucun OCR requis.

Non-bloquant : toute exception retourne {} / pool intact.
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
# Constantes SIRF — toutes validées 2026-05-21 (inspection DOM + Network tab)
# ---------------------------------------------------------------------------
_SIRF_BASE       = "https://www.registrefoncier.gouv.qc.ca"

# Login — validé par inspection DOM de la page de connexion
_SIRF_LOGIN_URL  = f"{_SIRF_BASE}/Sirf/Script/14_06_01-02/pf_14_06_01_reglr.asp"
_SIRF_LOGIN_FIELDS = {
    "txtVaCodeUtils":            None,       # code d'utilisateur — rempli au runtime
    "txtMotPasse":               None,       # mot de passe — rempli au runtime
    "txtEtat":                   "valdr",
    "txtBoutn":                  "btnSoumt",
    "txtInAfichQuestIdentPersn": "N",
}

# Recherche index immeubles — validé par Network tab POST payload 2026-05-21
_SIRF_SEARCH_URL = f"{_SIRF_BASE}/Sirf/Script/13_01_11/pf_13_01_11_02_indx_immbl.asp"
_SIRF_SEARCH_FIELDS = {
    "txtEtat":       "valdr",
    "selCircnFoncr": "NULL",
    "selCadst":      "000001",   # Cadastre du Québec rénové (tous lots ≥ 7 chiffres)
    "txtNumrtLot":   None,       # Format " X XXX XXX" (espace initial) — rempli au runtime
    "selDesgnSecnd": "A",
    "rdModltConsl":  "NULL",
    "rdOrdreAffch":  "C",        # C = ordre chronologique
    "txtPerd":       "",
    "btnSoumt":      "Soumettre",
}

_SIRF_CACHE_TTL_DAYS = 90

# Regex pour extraire le prix depuis la cellule "Remarques" de la table SIRF
_PRIX_CELL_RE = re.compile(r"([\d\s\xa0]{3,}(?:,\d{2})?)\s*\$")


# ---------------------------------------------------------------------------
# 1. Formatage numéro de lot
# ---------------------------------------------------------------------------

def _format_lot_number(no_lot: int) -> str:
    """
    Formate un no_lot entier pour le champ txtNumrtLot du formulaire SIRF.

    Format requis : espace initial + groupes de 3 séparés par espaces.
    Exemple : 2274178 → " 2 274 178"

    Validé 2026-05-21 — POST payload Network tab : txtNumrtLot = " 2 274 178".
    """
    return " " + f"{no_lot:,}".replace(",", " ")


# ---------------------------------------------------------------------------
# 2. Parse table HTML SIRF
# ---------------------------------------------------------------------------

def _parse_index_html(html: str) -> dict:
    """
    Extrait la transaction de vente la plus récente de la page index SIRF.

    La table SIRF contient des colonnes :
      Date de présentation | Numéro d'inscription | Nature de l'acte |
      Qualité | Nom des parties | Remarques | Avis d'adresse | Radiations

    Le prix de vente est dans "Remarques" pour les lignes "Vente".
    Les inscriptions multi-parties utilisent des rowspans — le parseur
    cherche aussi la ligne suivante pour trouver Vendeur/Acheteur.

    Retourne {} si aucune vente trouvée.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Trouver tous les <td> dont le texte exact est "Vente"
    vente_trs: list = []
    for td in soup.find_all("td"):
        if td.get_text(strip=True) == "Vente":
            vente_trs.append(td.parent)

    if not vente_trs:
        return {}

    # SIRF affiche en ordre chronologique (rdOrdreAffch=C) → dernier = plus récent
    vente_tr = vente_trs[-1]

    # --- Prix ---
    prix_vente = 0.0
    row_text = vente_tr.get_text(" ", strip=True)
    for m in _PRIX_CELL_RE.finditer(row_text):
        raw = m.group(1).replace(" ", "").replace("\xa0", "").replace(",", ".")
        try:
            val = float(raw)
            if val >= 1000:          # ignorer montants parasites (ex: "1,00 $")
                prix_vente = val
                break
        except ValueError:
            continue

    # --- Date ---
    date_vente = ""
    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", row_text)
    if m_date:
        date_vente = m_date.group(1)

    # --- Numéro d'inscription (source_doc) ---
    source_doc = ""
    for a in vente_tr.find_all("a"):
        txt = a.get_text(strip=True).replace(" ", "").replace("\xa0", "")
        if txt.isdigit() and len(txt) >= 5:
            source_doc = txt
            break

    # --- Vendeur / Acheteur ---
    # Structure : Qualité | Nom des parties (parfois sur 2 rangées via rowspan)
    vendeur, acheteur = _extract_parties(vente_tr)

    return {
        "prix_vente": prix_vente,
        "date_vente": date_vente,
        "vendeur":    vendeur,
        "acheteur":   acheteur,
        "source_doc": source_doc,
        "raw_text":   "",
    }


def _extract_parties(vente_tr) -> tuple[str, str]:
    """
    Cherche les labels Vendeur/Acheteur dans vente_tr et la ligne suivante (rowspan).
    Retourne (vendeur, acheteur).
    """
    vendeur = ""
    acheteur = ""

    def scan_row(tr) -> None:
        nonlocal vendeur, acheteur
        cells = tr.find_all("td")
        for i, cell in enumerate(cells):
            txt = cell.get_text(strip=True)
            if txt == "Vendeur" and i + 1 < len(cells):
                vendeur = cells[i + 1].get_text(" ", strip=True)[:150]
            elif txt == "Acheteur" and i + 1 < len(cells):
                acheteur = cells[i + 1].get_text(" ", strip=True)[:150]

    scan_row(vente_tr)

    # Rowspan : la 2e partie est dans la rangée suivante
    if not vendeur or not acheteur:
        next_tr = vente_tr.find_next_sibling("tr")
        if next_tr:
            scan_row(next_tr)

    return vendeur, acheteur


# ---------------------------------------------------------------------------
# 3. Cache disque local (JSON, 90 jours)
# ---------------------------------------------------------------------------

def _local_cache_path(no_lot: int, cache_dir: Path) -> Path:
    sirf_dir = cache_dir / "sirf"
    sirf_dir.mkdir(parents=True, exist_ok=True)
    return sirf_dir / f"{no_lot}.json"


def _local_cache_get(no_lot: int, cache_dir: Path) -> dict | None:
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


def _local_cache_set(
    no_lot: int,
    data: dict,
    cache_dir: Path,
    ttl_days: int = _SIRF_CACHE_TTL_DAYS,
) -> None:
    path = _local_cache_path(no_lot, cache_dir)
    payload = dict(data)
    payload["_expires"] = (date.today() + timedelta(days=ttl_days)).isoformat()
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("sirf local cache write failed for no_lot=%s: %s", no_lot, exc)


# ---------------------------------------------------------------------------
# 4. Cache Supabase (production, partagé entre évaluateurs)
# ---------------------------------------------------------------------------

def _supabase_cache_get(no_lot: int, supabase_client) -> dict | None:
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
            "raw_text":   "",
        }).execute()
    except Exception as exc:
        logger.warning("supabase sirf_cache set failed: %s", exc)


# ---------------------------------------------------------------------------
# 5. SIRF HTTP — session, recherche, fetch HTML index
# ---------------------------------------------------------------------------

def _build_supabase_client():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
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
    Lève RuntimeError si SIRF_USERNAME / SIRF_PASSWORD sont absents.

    Login validé 2026-05-21 — champs txtVaCodeUtils + txtMotPasse confirmés.
    """
    import httpx
    username = os.environ.get("SIRF_USERNAME", "")
    password = os.environ.get("SIRF_PASSWORD", "")
    if not username or not password:
        raise RuntimeError("SIRF_USERNAME / SIRF_PASSWORD manquants dans l'environnement")

    client = httpx.Client(follow_redirects=True, timeout=30.0)
    client.get(_SIRF_LOGIN_URL).raise_for_status()

    payload = dict(_SIRF_LOGIN_FIELDS)
    payload["txtVaCodeUtils"] = username
    payload["txtMotPasse"]    = password
    client.post(_SIRF_LOGIN_URL, data=payload).raise_for_status()
    return client


def _fetch_sirf_index_html(no_lot: int, session) -> str:
    """
    POST le formulaire de recherche par lot, suit la chaîne de 4 redirects,
    retourne le HTML de la page index.

    Paramètres POST validés 2026-05-21 — payload Network tab confirmé.
    """
    fields = dict(_SIRF_SEARCH_FIELDS)
    fields["txtNumrtLot"] = _format_lot_number(no_lot)
    resp = session.post(_SIRF_SEARCH_URL, data=fields)
    resp.raise_for_status()
    return resp.text


def _fetch_sirf_transaction(no_lot: int, session) -> dict:
    """
    Cherche la dernière vente pour un lot via l'index HTML.
    Retourne {} si aucune vente trouvée ou si l'accès échoue.
    """
    html = _fetch_sirf_index_html(no_lot, session)
    return _parse_index_html(html)


# ---------------------------------------------------------------------------
# 6. Point d'entrée public
# ---------------------------------------------------------------------------

def enrich_pool_with_sirf(
    pool: list[dict],
    cache_dir: Path | None = None,
    supabase_client=None,
    max_sirf_lookups: int = 10,
) -> list[dict]:
    """
    Remplace prix_vente=0 / date_vente="" dans les items du pool via SIRF.

    Priorité pour chaque lot :
      1. Cache disque local  (cache_dir/sirf/{no_lot}.json, 90 jours)
      2. Cache Supabase      (sirf_cache table, 90 jours, partagé)
      3. Requête live SIRF   (plafonnée à max_sirf_lookups, 1,50 $/lot)

    Items sans no_lot ou avec prix_vente > 0 sont ignorés.
    Non-bloquant : toute exception retourne le pool intact.
    """
    if cache_dir is None:
        cache_dir = Path("data_cache")

    if supabase_client is None:
        supabase_client = _build_supabase_client()

    live_lookups = 0
    sirf_session_obj = None

    enriched = []
    for item in pool:
        no_lot = item.get("no_lot")
        item = dict(item)  # copie shallow — ne pas muter le pool original

        if not no_lot or item.get("prix_vente", 0) > 0:
            enriched.append(item)
            continue

        # 1. Cache disque
        cached = _local_cache_get(int(no_lot), cache_dir)
        if cached is None:
            # 2. Cache Supabase
            cached = _supabase_cache_get(int(no_lot), supabase_client)
            if cached:
                _local_cache_set(int(no_lot), cached, cache_dir)

        if cached:
            item["prix_vente"]  = float(cached.get("prix_vente") or 0)
            item["date_vente"]  = cached.get("date_vente") or ""
            item["vendeur"]     = cached.get("vendeur") or ""
            item["acheteur"]    = cached.get("acheteur") or ""
            if item["prix_vente"] > 0:
                item["source_type"] = "registre_foncier"
            enriched.append(item)
            continue

        # 3. Live SIRF (si quota non atteint)
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
                item["prix_vente"] = float(transaction.get("prix_vente") or 0)
                item["date_vente"] = transaction.get("date_vente") or ""
                item["vendeur"]    = transaction.get("vendeur") or ""
                item["acheteur"]   = transaction.get("acheteur") or ""
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
