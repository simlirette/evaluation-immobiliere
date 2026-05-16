"""
data_enrichment.py — enrichissement du case depuis sources données externes.

Sources actives V0 :
  - SCHL marché locatif  : StatCan WDS API, table 34-10-0133-01 (cache 24 h)
  - Rôle municipal Mtl   : CSV MAMH (~72 MB, si data_cache/role_mtl.csv présent)
  - Rôle municipal XML   : MAMH XML (Qc/Laval/Longueuil/Gatineau/Sherbrooke)
  - Zonage urbanisme     : GeoJSON open data + Nominatim geocoding + PiP lookup

Tout est non-bloquant : une exception n'interrompt jamais le pipeline.
"""
from __future__ import annotations

import csv
import json
import logging
import time
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger("data_enrichment")

_CACHE_TTL = 86_400  # 24 h
_HTTP_TIMEOUT = 8.0
_WDS_BASE = "https://www150.statcan.gc.ca/t1/wds/rest/"
_SCHL_TABLE = 3410013301  # CANSIM 34-10-0133-01 : loyers moyens CMHC


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Lowercase + remove accents + strip."""
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _read_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict) and time.time() - d.get("_ts", 0) < _CACHE_TTL:
            return d
    except Exception:
        pass
    return None


def _write_cache(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ── City detection ────────────────────────────────────────────────────────────

# Keyword → SCHL city code  (subset relevant to QC V0)
_CITY_KEYWORDS: list[tuple[str, str]] = [
    ("saguenay", "saguenay"),
    ("jonquiere", "saguenay"),
    ("chicoutimi", "saguenay"),
    ("drummondville", "drummondville"),
    ("sherbrooke", "sherbrooke"),
    ("trois-riviere", "trois-rivieres"),
    ("trois riviere", "trois-rivieres"),
    ("gatineau", "gatineau"),
    ("hull", "gatineau"),
    ("aylmer", "gatineau"),
    ("quebec", "quebec"),
    ("sainte-foy", "quebec"),
    ("levis", "quebec"),
    ("beauport", "quebec"),
    ("longueuil", "montreal"),
    ("laval", "montreal"),
    ("brossard", "montreal"),
    ("saint-lambert", "montreal"),
    ("westmount", "montreal"),
    ("outremont", "montreal"),
    ("montreal", "montreal"),
    ("mtl", "montreal"),
]

# SCHL city code → StatCan GEO label (table 34-10-0133-01)
_SCHL_TO_STATCAN_GEO: dict[str, str] = {
    "montreal": "Montréal, Quebec",
    "quebec": "Québec, Quebec",
    "gatineau": "Ottawa - Gatineau, Quebec part, Quebec",
    "sherbrooke": "Sherbrooke, Quebec",
    "saguenay": "Saguenay, Quebec",
    "trois-rivieres": "Trois-Rivières, Quebec",
    "drummondville": "Drummondville, Quebec",
}

_SCHL_TO_DISPLAY: dict[str, str] = {
    "montreal": "Montréal",
    "quebec": "Québec",
    "gatineau": "Gatineau",
    "sherbrooke": "Sherbrooke",
    "saguenay": "Saguenay",
    "trois-rivieres": "Trois-Rivières",
    "drummondville": "Drummondville",
}

# ── Taux d'inoccupation SCHL (StatCan 34-10-0131-01) ─────────────────────────
_VACANCE_TABLE = 3410013101  # 34-10-0131-01 : Rental vacancy rates (October survey)

# Same GEO labels as 34-10-0133-01 (same SCHL survey universe)
_VACANCE_UNIT_SEARCHES: dict[str, list[str]] = {
    "total":    ["total"],
    "bachelor": ["bachelor", "studio"],
    "1ch":      ["1 bedroom", "1 chambre"],
    "2ch":      ["2 bedroom", "2 chambre"],
    "3ch_plus": ["3 bedroom", "3 chambre", "3+"],
}

# ── Taux Bank of Canada (Valet API) ──────────────────────────────────────────
_BOC_VALET_BASE = "https://www.bankofcanada.ca/valet/observations"
_BOC_TTL = 86_400  # 24 h (taux changent peu souvent)

# Series IDs → field key  (Bank of Canada Valet series codes)
_BOC_SERIES: dict[str, str] = {
    "CAOVRNIGH":    "taux_directeur_pct",        # Overnight rate (taux directeur)
    "V80691311":    "taux_preferentiel_pct",      # Prime business loan rate
    "V122495":      "taux_hypo_5ans_conv_pct",    # 5-year conventional mortgage
    "V122496":      "taux_hypo_1an_pct",          # 1-year conventional mortgage
}

# ── Marché du travail CMA (StatCan 14-10-0096-01) ────────────────────────────
_TRAVAIL_TABLE = 1410009601  # 14-10-0096-01 : Labour force characteristics by CMA (SA)

# city_code → StatCan GEO labels (CMA, EN)
_TRAVAIL_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
}

# Labour force characteristics to extract (dim 1 member search terms)
_TRAVAIL_INDICATORS: dict[str, list[str]] = {
    "taux_chomage_pct":    ["Unemployment rate"],
    "taux_emploi_pct":     ["Employment rate"],
    "taux_participation_pct": ["Participation rate"],
}

# ── Population CMA (StatCan 17-10-0135-01) ───────────────────────────────────
_POP_TABLE = 1710013501  # 17-10-0135-01 : Estimations de population par CMA

# city_code → StatCan GEO labels (CMA level, EN)
_POP_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal", "Montreal"],
    "quebec":         ["Québec", "Quebec"],
    "gatineau":       ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":     ["Sherbrooke"],
    "saguenay":       ["Saguenay"],
    "trois-rivieres": ["Trois-Rivières", "Trois-Rivieres"],
    "drummondville":  ["Drummondville"],
    "laval":          ["Laval"],
}

# ── NHPI — New Housing Price Index (StatCan 18-10-0205-01) ───────────────────
_NHPI_TABLE = 1810020501  # table 18-10-0205-01

# city_code → StatCan GEO label for NHPI (CMA level)
_NHPI_GEO_LABELS: dict[str, list[str]] = {
    "montreal":      ["Montréal", "Montreal"],
    "quebec":        ["Québec", "Quebec city"],
    "gatineau":      ["Ottawa - Gatineau", "Gatineau"],
    "sherbrooke":    ["Sherbrooke"],
    "saguenay":      ["Saguenay"],
    "trois-rivieres":["Trois-Rivières", "Trois-Rivieres"],
    "drummondville": ["Drummondville"],
}

# NHPI type → field key
_NHPI_TYPE_SEARCHES: dict[str, list[str]] = {
    "total":    ["Total (house and land)", "Total"],
    "batiment": ["Building", "Bâtiment"],
    "terrain":  ["Land", "Terrain"],
}

# ── Permis de construction (StatCan 34-10-0066-01) ────────────────────────────
_PERMIS_TABLE = 3410006601  # 34-10-0066-01 : Building permits by type of structure and work

# city_code → StatCan GEO labels (CMA level, EN)
_PERMIS_GEO_LABELS: dict[str, list[str]] = {
    "montreal":       ["Montréal, Quebec", "Montréal"],
    "quebec":         ["Québec, Quebec", "Québec"],
    "gatineau":       ["Ottawa - Gatineau, Quebec part, Quebec", "Gatineau, Quebec part",
                       "Ottawa-Gatineau, Quebec part"],
    "sherbrooke":     ["Sherbrooke, Quebec", "Sherbrooke"],
    "saguenay":       ["Saguenay, Quebec", "Saguenay"],
    "trois-rivieres": ["Trois-Rivières, Quebec", "Trois-Rivières"],
    "drummondville":  ["Drummondville, Quebec", "Drummondville"],
    "laval":          ["Laval, Quebec", "Laval"],
}

_PERMIS_STRUCTURE_SEARCHES = ["Residential", "Résidentiel"]
_PERMIS_WORK_SEARCHES_NEW  = ["New construction", "Nouvelle construction"]
_PERMIS_WORK_SEARCHES_ALL  = ["All work", "Toutes catégories", "Total"]
_PERMIS_UNIT_SEARCHES      = ["Number of units", "Units", "Unités"]
_PERMIS_VALUE_SEARCHES     = ["Value of permits", "Value", "Valeur"]

# ── Census Profile 2021 (StatCan REST) ───────────────────────────────────────
_CENSUS_BASE = "https://www12.statcan.gc.ca/rest/census-recensement/CR2021/fr/json"
_CENSUS_TTL = 30 * 86_400  # 30 jours — données stables (recensement 2021)

# city_code → DGUID Census Subdivision (SDR/CSD) 2021
# Format: 2021A0005{SGC-7-digits}   A = CSD level
_CENSUS_DGUIDS: dict[str, str] = {
    "montreal":       "2021A000524462023",  # Montréal (Île-de-Montréal CD)
    "laval":          "2021A000524290",     # Laval
    "longueuil":      "2021A000524458227",  # Longueuil (Agglomération)
    "quebec":         "2021A000523305",     # Québec (Capitale-Nationale)
    "gatineau":       "2021A000524813",     # Gatineau
    "sherbrooke":     "2021A000245005",     # Sherbrooke
    "saguenay":       "2021A000224006",     # Saguenay
    "trois-rivieres": "2021A000237012",     # Trois-Rivières
    "levis":          "2021A000223023",     # Lévis
    "drummondville":  "2021A000220016",     # Drummondville
}

# Substring patterns to extract from CHARACTERISTIC_NAME (FR)
# topic → [(field_key, search_substring), ...]
_CENSUS_TOPICS: dict[str, list[tuple[str, str]]] = {
    "9": [  # Logements
        ("pct_proprietaires",      "Propriétaires"),
        ("pct_locataires",         "Locataires"),
        ("valeur_mediane_logement","Valeur médiane ($)"),
        ("frais_loyer_median",     "Frais mensuels médians ($)"),
    ],
    "5": [  # Revenu
        ("revenu_median_menage",   "Revenu total médian des ménages"),
    ],
}


def fetch_census_profile(city_code: str, cache_dir: Path) -> dict:
    """Fetch 2021 Census Profile for a given city (demographic + housing indicators).

    Returns dict with keys: pct_proprietaires, pct_locataires,
    valeur_mediane_logement, frais_loyer_median, revenu_median_menage, ville, source.
    Returns {} if city unsupported or data unavailable.
    """
    import urllib.request

    dguid = _CENSUS_DGUIDS.get(city_code)
    if not dguid:
        return {}

    cache_path = cache_dir / f"census_{city_code}.json"
    cached = _read_cache_ttl(cache_path, _CENSUS_TTL)
    if cached is not None:
        return cached

    result: dict = {"ville": city_code, "source": "StatCan Recensement 2021"}
    char_rows: list[dict] = []

    for topic_id in _CENSUS_TOPICS:
        url = (
            f"{_CENSUS_BASE}?dguid={dguid}&topic={topic_id}&notes=0&lang=F"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "eval-immo/1.0"})
            with urllib.request.urlopen(req, timeout=int(_HTTP_TIMEOUT)) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list):
                    char_rows.extend(data)
        except Exception as exc:
            logger.debug("census topic %s fetch error: %s", topic_id, exc)

    if not char_rows:
        return {}

    # Build lookup dict: characteristic_name → C1_COUNT_TOTAL value
    char_lookup: dict[str, str] = {}
    for row in char_rows:
        name = str(row.get("CHARACTERISTIC_NAME") or row.get("Caractéristique") or "")
        value = str(row.get("C1_COUNT_TOTAL") or row.get("C1_TOTAL") or "").strip()
        if name and value and value not in ("", "x", "...", "F", "..F"):
            char_lookup[name] = value

    # Extract fields by substring match
    for topic_id, fields in _CENSUS_TOPICS.items():
        for field_key, search_sub in fields:
            for name, value in char_lookup.items():
                if search_sub.lower() in name.lower():
                    try:
                        num = float(value.replace(",", "").replace(" ", ""))
                        result[field_key] = num
                    except ValueError:
                        pass
                    break  # first match wins

    _write_cache_ttl(cache_path, result, _CENSUS_TTL)
    logger.debug("census_profile injecté: %s (%d champs)", city_code, len(result) - 2)
    return result


def _read_cache_ttl(path: Path, ttl: int) -> dict | None:
    """Read JSON cache file if it exists and is within TTL. Returns None on miss."""
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(d, dict) and time.time() - d.get("_ts", 0) < ttl:
            return d
    except Exception:
        pass
    return None


def _write_cache_ttl(path: Path, data: dict, ttl: int) -> None:  # noqa: ARG001
    """Write data to JSON cache with current timestamp."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        out = dict(data)
        out["_ts"] = time.time()
        path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def detect_city(display_name: str, zone: str = "") -> str:
    """Return SCHL city code inferred from display_name + zone (default: 'montreal').

    Strategy: try the last comma-segment of the address first (most likely the city),
    then fall back to the zone field, then the full text.
    """
    # 1. Last segment of comma-separated address (usually the city)
    parts = display_name.split(",")
    candidates = [_norm(parts[-1])] if len(parts) > 1 else []
    # 2. Zone field
    if zone:
        candidates.append(_norm(zone))
    # 3. Full display name (fallback)
    candidates.append(_norm(display_name))

    for haystack in candidates:
        for kw, code in _CITY_KEYWORDS:
            if kw in haystack:
                return code
    return "montreal"


# ── SCHL rental market (StatCan WDS) ─────────────────────────────────────────

def _wds_post(endpoint: str, payload: Any, timeout: float = _HTTP_TIMEOUT) -> Any:
    import httpx  # type: ignore
    url = _WDS_BASE + endpoint
    r = httpx.post(url, json=payload, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _wds_get(endpoint: str, timeout: float = _HTTP_TIMEOUT) -> Any:
    import httpx  # type: ignore
    url = _WDS_BASE + endpoint
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _cube_metadata(pid: int, cache_dir: Path) -> dict:
    """Fetch cube metadata with member ordinals; cache 24 h."""
    cache_path = cache_dir / f"wds_meta_{pid}.json"
    cached = _read_cache(cache_path)
    if cached:
        return cached
    data = _wds_get(f"getCubeMetadata/{pid}")
    if not isinstance(data, dict) or data.get("status") != "SUCCESS":
        return {}
    obj = data.get("object", {})
    result = {"_ts": time.time(), "dims": obj.get("dimension", [])}
    _write_cache(cache_path, result)
    return result


def _find_member_ordinal(dims: list[dict], dim_idx: int, search_terms: list[str]) -> int | None:
    """Return ordinal of best-matching member in dimension dim_idx.

    Tries exact match first, then substring match — avoids false positives
    like "employment rate" matching inside "unemployment rate".
    """
    if dim_idx >= len(dims):
        return None
    members = dims[dim_idx].get("member", [])
    # Pass 1: exact match
    for term in search_terms:
        t = _norm(term)
        for m in members:
            if t == _norm(str(m.get("memberNameEn", ""))):
                return int(m["memberId"])
    # Pass 2: substring match (fallback)
    for term in search_terms:
        t = _norm(term)
        for m in members:
            if t in _norm(str(m.get("memberNameEn", ""))):
                return int(m["memberId"])
    return None


def _build_coordinate(*ordinals: int | None) -> str | None:
    if any(o is None for o in ordinals):
        return None
    return ".".join(str(o) for o in ordinals)  # type: ignore[arg-type]


def _fetch_series(pid: int, coordinate: str, cache_dir: Path) -> float | None:
    """Fetch latest scalar value for a series; cache 24 h."""
    cache_path = cache_dir / f"wds_{pid}_{coordinate.replace('.', '_')}.json"
    cached = _read_cache(cache_path)
    if cached:
        return cached.get("value")

    payload = [{"productId": pid, "coordinate": coordinate, "latestN": 1}]
    data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
    if not isinstance(data, list) or not data:
        return None
    item = data[0]
    if item.get("status") != "SUCCESS":
        return None
    points = item.get("object", {}).get("vectorDataPoint", [])
    if not points:
        return None
    raw_val = points[0].get("value")
    try:
        val = float(raw_val)
    except (TypeError, ValueError):
        return None
    result = {"_ts": time.time(), "value": val}
    _write_cache(cache_path, result)
    return val


def fetch_taux_boc(cache_dir: Path) -> dict:
    """
    Fetch current Bank of Canada key rates via Valet REST API.

    Returns dict with keys: taux_directeur_pct, taux_preferentiel_pct,
    taux_hypo_5ans_conv_pct, taux_hypo_1an_pct, date, source.
    Returns {} on any failure (non-blocking).
    """
    import urllib.request

    cache_path = cache_dir / "boc_rates.json"
    cached = _read_cache_ttl(cache_path, _BOC_TTL)
    if cached is not None:
        return cached

    result: dict = {"source": "bankofcanada-valet"}

    # Fetch all series in one call: /observations/S1,S2,...?recent=1
    series_ids = ",".join(_BOC_SERIES.keys())
    url = f"{_BOC_VALET_BASE}/{series_ids}/json?recent=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "eval-immo/1.0"})
        with urllib.request.urlopen(req, timeout=int(_HTTP_TIMEOUT)) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.debug("BOC Valet fetch error: %s", exc)
        return {}

    observations = data.get("observations", [])
    if not observations:
        return {}

    latest = observations[-1]
    result["date"] = str(latest.get("d", ""))[:10]

    for series_id, field_key in _BOC_SERIES.items():
        entry = latest.get(series_id, {})
        raw = entry.get("v") if isinstance(entry, dict) else None
        if raw is not None:
            try:
                result[field_key] = float(raw)
            except (TypeError, ValueError):
                pass

    if len(result) <= 2:  # only source + date
        return {}

    _write_cache_ttl(cache_path, result, _BOC_TTL)
    logger.debug("taux_boc injecté : directeur=%.2f%% hypo5=%.2f%%",
                 result.get("taux_directeur_pct", 0),
                 result.get("taux_hypo_5ans_conv_pct", 0))
    return result


def fetch_marche_travail(city_code: str, cache_dir: Path) -> dict:
    """
    Return labour market indicators for a QC CMA via StatCan WDS (14-10-0096-01).

    Returns dict with keys: taux_chomage_pct, taux_emploi_pct,
    taux_participation_pct, periode, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _TRAVAIL_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_TRAVAIL_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Optional dim 2 (sex) → Both sexes / Total
        sex_ord: int | None = None
        if len(dims) >= 3:
            sex_ord = _find_member_ordinal(dims, 2,
                                           ["Both sexes", "Total - sex", "Total"])
            if sex_ord is None:
                members = dims[2].get("member", [])
                if members:
                    sex_ord = int(members[0]["memberId"])

        result: dict = {
            "source": "statcan-14-10-0096-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        for field_key, searches in _TRAVAIL_INDICATORS.items():
            ind_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, ind_ord,
                                      *([] if sex_ord is None else [sex_ord]))
            if coord:
                # latestN=1 for current value
                payload = [{"productId": _TRAVAIL_TABLE,
                            "coordinate": coord, "latestN": 1}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if (isinstance(data, list) and data
                        and data[0].get("status") == "SUCCESS"):
                    pts = data[0].get("object", {}).get("vectorDataPoint", [])
                    if pts:
                        try:
                            result[field_key] = float(pts[0]["value"])
                            if "periode" not in result:
                                ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                                if ref:
                                    result["periode"] = str(ref)[:7]
                        except (TypeError, ValueError):
                            pass

        if len(result) <= 2:
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Marché travail fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_population_growth(city_code: str, cache_dir: Path) -> dict:
    """
    Return population estimate + annual growth for a QC CMA via StatCan WDS (17-10-0135-01).

    Returns dict with keys: population, variation_annuelle_pct, annee, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _POP_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_POP_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Dim 1 = Age group → Total / All ages
        age_ord = _find_member_ordinal(dims, 1,
                                       ["Total - all ages", "All ages", "Total"])

        # Dim 2 = Sex → Both sexes / Total
        sex_ord = _find_member_ordinal(dims, 2,
                                       ["Both sexes", "Total - sex", "Total"])

        # Optional dim 3 (estimate type: low/medium/high) → prefer medium or first member
        extra_ord: int | None = None
        if len(dims) >= 4:
            extra_ord = _find_member_ordinal(dims, 3,
                                             ["Medium", "medium projection", "Estimate"])
            if extra_ord is None:
                members = dims[3].get("member", [])
                if members:
                    extra_ord = int(members[0]["memberId"])

        coord = _build_coordinate(geo_ord, age_ord, sex_ord,
                                  *([] if extra_ord is None else [extra_ord]))
        if not coord:
            return {}

        # Fetch 2 years (latestN=2) to compute annual change
        payload = [{"productId": _POP_TABLE, "coordinate": coord, "latestN": 2}]
        data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
        if not isinstance(data, list) or not data or data[0].get("status") != "SUCCESS":
            return {}

        pts = data[0].get("object", {}).get("vectorDataPoint", [])
        if not pts:
            return {}

        try:
            latest_val = float(pts[0]["value"])
        except (TypeError, ValueError, KeyError):
            return {}

        result: dict = {
            "source": "statcan-17-10-0135-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
            "population": round(latest_val),
        }

        ref = pts[0].get("refPer") or pts[0].get("refper") or ""
        if ref:
            result["annee"] = str(ref)[:4]

        if len(pts) >= 2:
            try:
                prior_val = float(pts[1]["value"])
                if prior_val > 0:
                    result["variation_annuelle_pct"] = round(
                        (latest_val - prior_val) / prior_val * 100, 2
                    )
            except (TypeError, ValueError, KeyError):
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Population growth fetch failed for %s: %s", city_code, exc)
        return {}


_BEDROOM_SEARCHES: dict[str, list[str]] = {
    "bachelor": ["bachelor", "studio"],
    "1ch": ["1 bedroom", "1 chambre"],
    "2ch": ["2 bedroom", "2 chambre"],
    "3ch_plus": ["3 bedroom", "3 chambre", "3+"],
    "total": ["total"],
}


def fetch_rental_market(city_code: str, cache_dir: Path) -> dict:
    """
    Return SCHL rental market data for a QC city via StatCan WDS.

    Returns dict with keys: loyer_moyen_{bachelor,1ch,2ch,3ch_plus,total},
    taux_inoccupation_total, annee, ville, source.
    Returns {} on any failure.
    """
    geo_label = _SCHL_TO_STATCAN_GEO.get(city_code)
    if not geo_label:
        return {}

    try:
        meta = _cube_metadata(_SCHL_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # dim 0 = GEO, dim 1 = Type of unit
        geo_ord = _find_member_ordinal(dims, 0, [geo_label, city_code])
        if geo_ord is None:
            return {}

        result: dict = {
            "source": "statcan-34-10-0133-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Average Rent series (survey index 1 usually covers primary rental)
        # Table may have a 3rd dim for survey type; try dim 2 = 1 as default
        extra_ord: list[int] = []
        if len(dims) >= 3:
            # Try to find "Private apartments" or first member
            members = dims[2].get("member", [])
            if members:
                extra_ord = [int(members[0]["memberId"])]

        # Vacancy Rate uses a different table (SCHL 34-10-0031) — skip for V0
        # We only parse Average Rent here

        for field_key, searches in _BEDROOM_SEARCHES.items():
            unit_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, unit_ord, *extra_ord if extra_ord else [])
            if coord:
                val = _fetch_series(_SCHL_TABLE, coord, cache_dir)
                if val is not None:
                    result[f"loyer_moyen_{field_key}"] = val

        if len(result) <= 2:  # only source + ville
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("SCHL fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_vacancy_rate(city_code: str, cache_dir: Path) -> dict:
    """
    Return SCHL rental vacancy rates for a QC city via StatCan WDS (34-10-0131-01).

    Returns dict with keys: taux_total_pct, taux_bachelor_pct, taux_1ch_pct,
    taux_2ch_pct, taux_3ch_plus_pct, annee, ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_label = _SCHL_TO_STATCAN_GEO.get(city_code)
    if not geo_label:
        return {}

    try:
        meta = _cube_metadata(_VACANCE_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # dim 0 = GEO, dim 1 = Type of unit
        geo_ord = _find_member_ordinal(dims, 0, [geo_label, city_code])
        if geo_ord is None:
            return {}

        result: dict = {
            "source": "statcan-34-10-0131-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Optional dim 2 (survey type) — take first member if present
        extra_ord: list[int] = []
        if len(dims) >= 3:
            members = dims[2].get("member", [])
            if members:
                extra_ord = [int(members[0]["memberId"])]

        for field_key, searches in _VACANCE_UNIT_SEARCHES.items():
            unit_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, unit_ord, *extra_ord if extra_ord else [])
            if coord:
                val = _fetch_series(_VACANCE_TABLE, coord, cache_dir)
                if val is not None:
                    result[f"taux_{field_key}_pct"] = val

        if len(result) <= 2:
            return {}

        # Try to capture reference period (year) from first successful series fetch
        if "taux_total_pct" in result:
            try:
                coord_total = _build_coordinate(
                    geo_ord,
                    _find_member_ordinal(dims, 1, _VACANCE_UNIT_SEARCHES["total"]),
                    *extra_ord if extra_ord else [],
                )
                if coord_total:
                    payload = [{"productId": _VACANCE_TABLE, "coordinate": coord_total, "latestN": 1}]
                    data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                    if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                        pts = data[0].get("object", {}).get("vectorDataPoint", [])
                        if pts:
                            ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                            if ref:
                                result["annee"] = str(ref)[:4]
            except Exception:
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Vacancy rate fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_nhpi(city_code: str, cache_dir: Path) -> dict:
    """
    Return NHPI (New Housing Price Index) for a QC city via StatCan WDS.

    Returns dict with keys: indice_total, indice_batiment, indice_terrain,
    variation_annuelle_pct (if 12 prior periods available), ville, source.
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _NHPI_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_NHPI_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # dim 0 = GEO, dim 1 = Type of unit/structure
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        result: dict = {
            "source": "statcan-18-10-0205-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        for field_key, searches in _NHPI_TYPE_SEARCHES.items():
            type_ord = _find_member_ordinal(dims, 1, searches)
            coord = _build_coordinate(geo_ord, type_ord)
            if coord:
                val = _fetch_series(_NHPI_TABLE, coord, cache_dir)
                if val is not None:
                    result[f"indice_{field_key}"] = val

        if len(result) <= 2:
            return {}

        # Compute annual change using a second series fetch (latestN=13, compare first vs last)
        total_ord = _find_member_ordinal(dims, 1, _NHPI_TYPE_SEARCHES["total"])
        coord_total = _build_coordinate(geo_ord, total_ord)
        if coord_total:
            try:
                payload = [{"productId": _NHPI_TABLE, "coordinate": coord_total, "latestN": 13}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                    points = data[0].get("object", {}).get("vectorDataPoint", [])
                    if len(points) >= 13:
                        latest = float(points[0]["value"])
                        year_ago = float(points[12]["value"])
                        if year_ago > 0:
                            result["variation_annuelle_pct"] = round(
                                (latest - year_ago) / year_ago * 100, 1
                            )
            except Exception:
                pass

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("NHPI fetch failed for %s: %s", city_code, exc)
        return {}


def fetch_permis_construction(city_code: str, cache_dir: Path) -> dict:
    """
    Return building permit activity for a QC city via StatCan WDS (34-10-0066-01).

    Returns dict with keys:
      - unites_residentielles_mois  : latest month (new residential units)
      - unites_residentielles_12mois: rolling 12-month sum
      - variation_pct_6m            : (avg last 6m / avg prior 6m - 1) × 100
      - valeur_permis_k_mois        : latest month value (k$) if available
      - periode                     : YYYY-MM label of latest data point
      - ville, source
    Returns {} on any failure or unsupported city.
    """
    geo_labels = _PERMIS_GEO_LABELS.get(city_code)
    if not geo_labels:
        return {}

    try:
        meta = _cube_metadata(_PERMIS_TABLE, cache_dir)
        dims = meta.get("dims", [])
        if not dims:
            return {}

        # Dim 0 = GEO
        geo_ord = _find_member_ordinal(dims, 0, geo_labels)
        if geo_ord is None:
            return {}

        # Dim 1 = Type of structure  →  Residential
        struct_ord = _find_member_ordinal(dims, 1, _PERMIS_STRUCTURE_SEARCHES)
        if struct_ord is None:
            return {}

        # Dim 2 = Type of work  →  New construction (preferred) or All work
        work_ord_new = _find_member_ordinal(dims, 2, _PERMIS_WORK_SEARCHES_NEW)
        work_ord_all = _find_member_ordinal(dims, 2, _PERMIS_WORK_SEARCHES_ALL)
        work_ord = work_ord_new if work_ord_new is not None else work_ord_all
        if work_ord is None:
            return {}

        # Optional dim 3 = measure (units vs value)
        unit_ord: int | None = None
        value_ord: int | None = None
        if len(dims) >= 4:
            unit_ord  = _find_member_ordinal(dims, 3, _PERMIS_UNIT_SEARCHES)
            value_ord = _find_member_ordinal(dims, 3, _PERMIS_VALUE_SEARCHES)

        # Build coordinates
        coord_units = _build_coordinate(geo_ord, struct_ord, work_ord, unit_ord)
        coord_value = _build_coordinate(geo_ord, struct_ord, work_ord, value_ord)

        # Fallback: 3-dim coordinate if dim 3 not present
        if coord_units is None:
            coord_units = _build_coordinate(geo_ord, struct_ord, work_ord)
        if coord_value is None and value_ord is not None:
            coord_value = _build_coordinate(geo_ord, struct_ord, work_ord_all, value_ord)

        result: dict = {
            "source": "statcan-34-10-0066-01",
            "ville": _SCHL_TO_DISPLAY.get(city_code, city_code),
        }

        # Fetch 12-month series for units
        if coord_units:
            try:
                payload = [{"productId": _PERMIS_TABLE, "coordinate": coord_units, "latestN": 12}]
                data = _wds_post("getDataFromCubePidCoordAndLatestNPeriods", payload)
                if isinstance(data, list) and data and data[0].get("status") == "SUCCESS":
                    pts = data[0].get("object", {}).get("vectorDataPoint", [])
                    values = []
                    for pt in pts:
                        try:
                            values.append(float(pt["value"]))
                        except (TypeError, ValueError):
                            pass
                    if values:
                        result["unites_residentielles_mois"] = values[0]
                        result["unites_residentielles_12mois"] = round(sum(values), 0)
                        # Ref period label from first point
                        ref = pts[0].get("refPer") or pts[0].get("refper") or ""
                        if ref:
                            result["periode"] = str(ref)[:7]  # YYYY-MM
                        # 6-month variation
                        if len(values) >= 12:
                            avg_rec  = sum(values[:6]) / 6
                            avg_prev = sum(values[6:12]) / 6
                            if avg_prev > 0:
                                result["variation_pct_6m"] = round(
                                    (avg_rec - avg_prev) / avg_prev * 100, 1
                                )
            except Exception:
                pass

        # Fetch latest value of permits (k$)
        if coord_value:
            try:
                val = _fetch_series(_PERMIS_TABLE, coord_value, cache_dir)
                if val is not None:
                    result["valeur_permis_k_mois"] = val
            except Exception:
                pass

        if len(result) <= 2:
            return {}

        return result

    except Exception as exc:  # pragma: no cover
        logger.debug("Permis construction fetch failed for %s: %s", city_code, exc)
        return {}


# ── Rôle municipal Montréal CSV ───────────────────────────────────────────────

_ROLE_MTL_CSV_URL = (
    "https://donnees.montreal.ca/dataset/4ad6baea-4d2c-460f-a8bf-5d000db498f7"
    "/resource/2b9dfc3d-91d3-48de-b32c-a2a6d9417079/download/uniteevaluationfonciere.csv"
)
_ROLE_INDEX_CACHE: dict[str, dict] = {}  # module-level in-process cache


def download_role_mtl(cache_dir: Path, force: bool = False) -> Path:
    """Download the Montréal rôle CSV (~72 MB) once and cache it."""
    import httpx  # type: ignore
    csv_path = cache_dir / "role_mtl.csv"
    if csv_path.exists() and not force:
        return csv_path
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Téléchargement rôle Montréal CSV (~72 MB)…")
    with httpx.stream("GET", _ROLE_MTL_CSV_URL, timeout=300, follow_redirects=True) as r:
        r.raise_for_status()
        with csv_path.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=256 * 1024):
                fh.write(chunk)
    logger.info("Rôle Montréal téléchargé : %s", csv_path)
    return csv_path


def _load_role_index(csv_path: Path) -> dict[str, dict]:
    """Load CSV into module-level dict indexed by MATRICULE83 (lazy, once per process)."""
    global _ROLE_INDEX_CACHE
    key = str(csv_path)
    if key in _ROLE_INDEX_CACHE:
        return _ROLE_INDEX_CACHE[key]
    idx: dict[str, dict] = {}
    address_idx: dict[str, list[dict]] = {}
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mat = row.get("MATRICULE83", "").strip()
            if mat:
                idx[mat] = row
            # Secondary index: (civique_debut, nom_rue)
            civique = row.get("CIVIQUE_DEBUT", "").strip()
            rue = _norm(row.get("NOM_RUE", ""))
            addr_key = f"{civique}|{rue}"
            address_idx.setdefault(addr_key, []).append(row)
    _ROLE_INDEX_CACHE[key] = {"matricule": idx, "address": address_idx}
    return _ROLE_INDEX_CACHE[key]


def _parse_civic_from_display(display_name: str) -> tuple[str, str]:
    """Extract (civic_number, street_name) from a free-text address best-effort."""
    import re
    m = re.match(r"^\s*(\d+)\s+(.+?)(?:\s*,.*)?$", display_name.strip())
    if m:
        return m.group(1).strip(), _norm(m.group(2).strip())
    return "", _norm(display_name.strip())


def lookup_role_mtl(
    csv_path: Path,
    matricule: str | None = None,
    display_name: str = "",
) -> dict:
    """
    Look up a property in the Montréal rôle CSV.

    Attempts lookup by MATRICULE83 first; falls back to civic + street.
    Returns {} if not found or CSV absent.
    """
    if not csv_path.exists():
        return {}
    try:
        idx = _load_role_index(csv_path)
    except Exception as exc:
        logger.debug("Role CSV load failed: %s", exc)
        return {}

    row: dict | None = None

    # 1. By matricule
    if matricule:
        mat_norm = matricule.strip().upper()
        row = idx["matricule"].get(mat_norm)

    # 2. By civic + street from display_name
    if row is None and display_name:
        civic, street = _parse_civic_from_display(display_name)
        if civic and street:
            addr_key = f"{civic}|{street}"
            candidates = idx["address"].get(addr_key, [])
            if candidates:
                row = candidates[0]

    if row is None:
        return {}

    def _int(v: str) -> int | None:
        try:
            return int(v) if v and v.strip() not in ("0", "") else None
        except (ValueError, TypeError):
            return None

    def _float(v: str) -> float | None:
        try:
            return float(v) if v and v.strip() not in ("0", "0.0", "") else None
        except (ValueError, TypeError):
            return None

    return {
        "source": "role-mtl-csv",
        "matricule83": row.get("MATRICULE83", ""),
        "adresse_civique": row.get("CIVIQUE_DEBUT", ""),
        "nom_rue": row.get("NOM_RUE", ""),
        "annee_construction": _int(row.get("ANNEE_CONSTRUCTION", "")),
        "superficie_batiment_m2": _float(row.get("SUPERFICIE_BATIMENT", "")),
        "superficie_terrain_m2": _float(row.get("SUPERFICIE_TERRAIN", "")),
        "nb_logements": _int(row.get("NOMBRE_LOGEMENT", "")),
        "code_cubf": _int(row.get("CODE_UTILISATION", "")),
        "libelle_cubf": row.get("LIBELLE_UTILISATION", ""),
        "municipalite": row.get("MUNICIPALITE", ""),
        "etages": _int(row.get("ETAGE_HORS_SOL", "")),
    }


# ── Rôle municipal XML (autres villes — MAMH XML → JSON index) ───────────────

# city_code → (code_geo, display_name, xml_url)
_ROLE_XML_CITIES: dict[str, tuple[str, str, str]] = {
    "quebec":       ("23027", "Ville de Québec",
                     "https://donneesouvertes.affmunqc.net/role/RL23027_2026.xml"),
    "laval":        ("65005", "Laval",
                     "https://donneesouvertes.affmunqc.net/role/RL65005_2026.xml"),
    "longueuil":    ("58227", "Longueuil",
                     "https://donneesouvertes.affmunqc.net/role/RL58227_2026.xml"),
    "gatineau":     ("81017", "Gatineau",
                     "https://donneesouvertes.affmunqc.net/role/RL81017_2026.xml"),
    "sherbrooke":   ("43027", "Sherbrooke",
                     "https://donneesouvertes.affmunqc.net/role/RL43027_2026.xml"),
}

# in-process cache for loaded XML indexes
_XML_INDEX_CACHE: dict[str, dict] = {}


def download_role_xml(city_code: str, cache_dir: Path, force: bool = False) -> Path | None:
    """Download MAMH XML for a non-Montreal city (100–400 MB). Returns path or None."""
    import httpx  # type: ignore
    info = _ROLE_XML_CITIES.get(city_code)
    if not info:
        return None
    code_geo, city_name, url = info
    xml_path = cache_dir / f"role_{city_code}.xml"
    if xml_path.exists() and not force:
        return xml_path
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Téléchargement rôle %s XML…", city_name)
    with httpx.stream("GET", url, timeout=600, follow_redirects=True) as r:
        r.raise_for_status()
        with xml_path.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=256 * 1024):
                fh.write(chunk)
    logger.info("Rôle %s téléchargé : %s", city_name, xml_path)
    return xml_path


def _xml_text(elem, tag: str) -> str | None:
    """Extract text from a direct child tag; return None if absent/empty."""
    child = elem.find(tag)
    if child is None:
        return None
    t = (child.text or "").strip()
    return t or None


def _xml_int(elem, tag: str) -> int | None:
    t = _xml_text(elem, tag)
    if t is None:
        return None
    try:
        v = int(t)
        return v if v != 0 else None
    except ValueError:
        return None


def _xml_float(elem, tag: str) -> float | None:
    t = _xml_text(elem, tag)
    if t is None:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _xml_build_matricule(a: str | None, b: str | None, c: str | None, d: str | None,
                          e: str | None = None, f: str | None = None) -> str | None:
    if not all([a, b, c, d]):
        return None
    try:
        sub1 = int(e) if e else 0
        sub2 = int(f) if f else 0
        return f"{int(a):04d}-{int(b):02d}-{int(c):04d}-{d}-{sub1:03d}-{sub2:04d}"
    except (ValueError, TypeError):
        return None


def build_role_xml_index(xml_path: Path, index_path: Path, city_code: str = "") -> int:
    """
    Parse a MAMH XML file (iterparse) and write a compact JSON index.

    Index structure:
      {
        "by_matricule": {"XXXX-YY-ZZZZ-W-000-0000": {...record...}},
        "by_address":   {"1000|rue sherbrooke o": [{...record...}]},
        "city_code": "...",
        "_built_at": <timestamp>,
      }

    Returns the number of UEVs indexed.
    """
    from xml.etree import ElementTree as ET

    logger.info("Building XML index for %s → %s", xml_path.name, index_path.name)
    by_matricule: dict[str, dict] = {}
    by_address: dict[str, list[dict]] = {}
    count = 0

    for _event, elem in ET.iterparse(str(xml_path), events=("end",)):
        if elem.tag != "RLUEx":
            continue  # do NOT clear sub-elements before RLUEx is processed

        # Adresse
        addr_parent = elem.find("RL0101")
        addr = addr_parent.find("RL0101x") if addr_parent is not None else None
        civique = _xml_text(addr, "RL0101Ax") if addr is not None else None
        nom_voie = _xml_text(addr, "RL0101Gx") if addr is not None else None
        type_voie = _xml_text(addr, "RL0101Ex") if addr is not None else None

        # Matricule
        rl0104 = elem.find("RL0104")
        mat = _xml_build_matricule(
            _xml_text(rl0104, "RL0104A") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104B") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104C") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104D") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104E") if rl0104 is not None else None,
            _xml_text(rl0104, "RL0104F") if rl0104 is not None else None,
        ) if rl0104 is not None else None

        # Lot
        rl0103_parent = elem.find("RL0103")
        rl0103x = rl0103_parent.find("RL0103x") if rl0103_parent is not None else None

        rec: dict = {
            "source": "mamh-xml",
            "city_code": city_code,
            "matricule83": mat or "",
            "adresse_civique": civique or "",
            "nom_rue": f"{type_voie or ''} {nom_voie or ''}".strip(),
            "no_lot": _xml_int(rl0103x, "RL0103Ax") if rl0103x is not None else None,
            "annee_construction": _xml_int(elem, "RL0307A"),
            "superficie_batiment_m2": _xml_float(elem, "RL0308A"),
            "superficie_terrain_m2": _xml_float(elem, "RL0302A"),
            "nb_logements": _xml_int(elem, "RL0311A") or 0,
            "code_cubf": _xml_int(elem, "RL0105A"),
            "valeur_terrain": _xml_float(elem, "RL0402A"),
            "valeur_batiment": _xml_float(elem, "RL0403A"),
            "valeur_totale": _xml_float(elem, "RL0404A"),
            "valeur_imposable": _xml_float(elem, "RL0405A"),
        }

        if mat:
            by_matricule[mat.upper()] = rec

        if civique and nom_voie:
            addr_key = f"{civique}|{_norm(f'{type_voie or ''} {nom_voie}')}"
            by_address.setdefault(addr_key, []).append(rec)

        count += 1
        if count % 50_000 == 0:
            logger.info("  %d UEV indexées…", count)

        elem.clear()

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({
            "by_matricule": by_matricule,
            "by_address": by_address,
            "city_code": city_code,
            "_built_at": time.time(),
            "_count": count,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Index built: %d UEVs → %s (%.1f MB)",
                count, index_path.name, index_path.stat().st_size / 1e6)
    return count


def _load_xml_index(index_path: Path) -> dict:
    """Load XML JSON index; module-level cache (one load per process)."""
    key = str(index_path)
    if key in _XML_INDEX_CACHE:
        return _XML_INDEX_CACHE[key]
    data = json.loads(index_path.read_text(encoding="utf-8"))
    _XML_INDEX_CACHE[key] = data
    return data


def lookup_role_xml(
    index_path: Path,
    matricule: str | None = None,
    display_name: str = "",
) -> dict:
    """Look up a property in a MAMH XML index (JSON). Returns {} if not found."""
    if not index_path.exists():
        return {}
    try:
        idx = _load_xml_index(index_path)
    except Exception as exc:
        logger.debug("XML index load failed: %s", exc)
        return {}

    by_mat = idx.get("by_matricule", {})
    by_addr = idx.get("by_address", {})

    row: dict | None = None

    if matricule:
        row = by_mat.get(matricule.strip().upper())

    if row is None and display_name:
        civic, street = _parse_civic_from_display(display_name)
        if civic and street:
            addr_key = f"{civic}|{street}"
            candidates = by_addr.get(addr_key, [])
            if candidates:
                row = candidates[0]

    return row or {}


# ── Geocoding (Nominatim OSM) ─────────────────────────────────────────────────

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_GEOCODE_TTL = 7 * 86_400  # 7 days


def _geocode_cache_path(display_name: str, cache_dir: Path) -> Path:
    import hashlib
    key = hashlib.md5(display_name.encode("utf-8")).hexdigest()[:12]
    return cache_dir / f"geo_{key}.json"


def geocode_address(display_name: str, cache_dir: Path) -> tuple[float, float] | None:
    """
    Geocode via Nominatim OSM. Returns (lat, lng) or None. Cache 7 days.

    Appends ', Québec, Canada' when city not explicit, to bias results.
    Respects Nominatim's 1 req/s policy — caller must not hammer this.
    """
    import httpx  # type: ignore

    cp = _geocode_cache_path(display_name, cache_dir)
    if cp.exists():
        try:
            d = json.loads(cp.read_text(encoding="utf-8"))
            if time.time() - d.get("_ts", 0) < _GEOCODE_TTL:
                lat, lng = d.get("lat"), d.get("lng")
                if lat is not None and lng is not None:
                    return float(lat), float(lng)
                return None  # cached "not found"
        except Exception:
            pass

    query = display_name.strip()
    low = query.lower()
    if "québec" not in low and "quebec" not in low and "canada" not in low:
        query += ", Québec, Canada"

    try:
        r = httpx.get(
            _NOMINATIM_URL,
            params={"q": query, "format": "json", "limit": 1},
            headers={"User-Agent": "eval-immo/1.0 contact=eval-immo@example.com"},
            timeout=_HTTP_TIMEOUT,
            follow_redirects=True,
        )
        r.raise_for_status()
        results = r.json()
    except Exception as exc:
        logger.debug("geocode_address HTTP failed: %s", exc)
        return None

    if not results:
        # Cache negative result
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({"_ts": time.time(), "lat": None, "lng": None}),
                      encoding="utf-8")
        return None

    lat = float(results[0]["lat"])
    lng = float(results[0]["lon"])
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(json.dumps({"_ts": time.time(), "lat": lat, "lng": lng}),
                  encoding="utf-8")
    return lat, lng


# ── Zonage urbanisme (GeoJSON open data + PiP) ────────────────────────────────

# city_code → CKAN config + rough bounding box [minlng, minlat, maxlng, maxlat]
_ZONING_CITIES: dict[str, dict] = {
    "montreal": {
        "ckan_api": "https://donnees.montreal.ca/api/3/action",
        # Try multiple package IDs (open data slugs may change)
        "package_ids": ["zones-urbanistiques", "zonage", "plan-urbanisme-zones"],
        "bbox": [-74.05, 45.39, -73.45, 45.75],
    },
    "quebec": {
        # Ville de Québec — portail données ouvertes provincial
        "ckan_api": "https://www.donneesquebec.ca/api/3/action",
        "package_ids": [
            "vmqc-plan-zonage",
            "plan-de-zonage-ville-de-quebec",
            "zonage-ville-de-quebec",
            "plan-zonage",
        ],
        "bbox": [-71.55, 46.70, -71.10, 47.05],
    },
    "laval": {
        "ckan_api": "https://www.donneesouvertes.laval.ca/api/3/action",
        "package_ids": ["plan-urbanisme-zonage", "zonage-laval", "plan-zonage"],
        "bbox": [-73.92, 45.49, -73.58, 45.68],
    },
    "longueuil": {
        # Longueuil — portail propriétaire (URL directe, pas CKAN standardisé)
        "ckan_api": None,
        "package_ids": [],
        "direct_url": "https://donneesouvertes.longueuil.quebec/datasets/zonage.geojson",
        "bbox": [-73.60, 45.46, -73.41, 45.58],
    },
    "gatineau": {
        "ckan_api": "https://www.donneesouvertes.gatineau.ca/api/3/action",
        "package_ids": ["zonage-gatineau", "plan-urbanisme-zonage", "reglements-zonage"],
        "bbox": [-76.15, 45.38, -75.55, 45.65],
    },
    "sherbrooke": {
        "ckan_api": "https://www.donneesouvertes.sherbrooke.ca/api/3/action",
        "package_ids": ["plan-urbanisme-zones", "zonage-sherbrooke", "plan-zonage"],
        "bbox": [-72.00, 45.35, -71.78, 45.55],
    },
}

# module-level spatial index cache: city_code → list[zone_record]
_ZONING_INDEX_CACHE: dict[str, list] = {}


def _find_ckan_geojson(ckan_api: str, package_id: str) -> str | None:
    """Find first GeoJSON resource URL in a CKAN package."""
    import httpx  # type: ignore
    r = httpx.get(f"{ckan_api}/package_show",
                  params={"id": package_id}, timeout=10, follow_redirects=True)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return None
    for res in data["result"].get("resources", []):
        fmt = (res.get("format") or "").lower()
        url = res.get("url", "")
        if "geojson" in fmt or url.lower().endswith(".geojson"):
            return url
    return None


def download_zoning_geojson(city_code: str, cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download zoning GeoJSON for a city.

    Discovery order:
      1. CKAN API (package_ids list) — for cities with a CKAN portal
      2. direct_url — for cities with a stable direct GeoJSON endpoint
    Returns local path or None if unavailable.
    """
    import httpx  # type: ignore

    city = _ZONING_CITIES.get(city_code)
    if not city:
        return None

    geojson_path = cache_dir / f"zoning_{city_code}.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    # 1. CKAN discovery
    url: str | None = None
    ckan_api = city.get("ckan_api")
    if ckan_api:
        for pkg_id in city.get("package_ids", []):
            try:
                url = _find_ckan_geojson(ckan_api, pkg_id)
                if url:
                    break
            except Exception as exc:
                logger.debug("CKAN discovery %s / %s failed: %s", city_code, pkg_id, exc)

    # 2. Fallback: direct_url
    if not url:
        url = city.get("direct_url")

    if not url:
        logger.debug("No GeoJSON URL found for zoning %s", city_code)
        return None

    logger.info("Downloading zoning GeoJSON %s …", city_code)
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
            r.raise_for_status()
            with geojson_path.open("wb") as fh:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    fh.write(chunk)
    except Exception as exc:
        logger.debug("Zoning download failed: %s", exc)
        if geojson_path.exists():
            geojson_path.unlink()
        return None

    logger.info("Zoning %s downloaded: %.1f MB", city_code,
                geojson_path.stat().st_size / 1e6)
    return geojson_path


def _simplify_ring(ring: list, max_pts: int = 300) -> list:
    """Downsample a coordinate ring to at most max_pts vertices."""
    if len(ring) <= max_pts:
        return ring
    step = len(ring) / max_pts
    return [ring[int(i * step)] for i in range(max_pts)]


def _pip_exterior(lng: float, lat: float, ring: list) -> bool:
    """
    Ray casting point-in-polygon test.
    ring: list of [lng, lat] pairs (GeoJSON coordinate order).
    Exterior ring only — holes are ignored (acceptable for zoning lookups).
    """
    x, y = lng, lat
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y):
            denom = yj - yi
            if denom == 0.0:
                denom = 1e-15
            if x < (xj - xi) * (y - yi) / denom + xi:
                inside = not inside
        j = i
    return inside


def build_zoning_index(geojson_path: Path, index_path: Path) -> int:
    """
    Parse a GeoJSON zoning file and write a compact spatial index.

    Index structure (JSON):
      {
        "zones": [
          {
            "props": {<original GeoJSON properties>},
            "bbox":  [minlng, minlat, maxlng, maxlat],
            "ring":  [[lng, lat], ...],   # simplified exterior ring
          },
          ...
        ],
        "_built_at": <timestamp>,
        "_count": <int>,
      }

    Only Polygon / MultiPolygon geometries are indexed.
    Returns the number of zones indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")

        if gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            if len(exterior) < 3:
                continue
            xs = [p[0] for p in exterior]
            ys = [p[1] for p in exterior]
            bbox = [min(xs), min(ys), max(xs), max(ys)]
            zones.append({
                "props": props,
                "bbox": bbox,
                "ring": _simplify_ring(exterior),
            })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Zoning index built: %d zones → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def lookup_zoning_point(city_code: str, lat: float, lng: float, cache_dir: Path) -> dict:
    """
    Return zone properties for the point (lat, lng) in the given city.

    Auto-downloads GeoJSON and builds index if not cached.
    Returns {} if not found, city unsupported, or any failure.
    """
    if city_code not in _ZONING_CITIES:
        return {}

    index_path = cache_dir / f"zoning_{city_code}_index.json"

    # Build index from GeoJSON if needed
    if not index_path.exists():
        geojson_path = cache_dir / f"zoning_{city_code}.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_zoning_geojson(city_code, cache_dir)
            except Exception as exc:
                logger.debug("Zoning download skip: %s", exc)
                return {}
        if geojson_path and geojson_path.exists():
            try:
                build_zoning_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("Zoning index build skip: %s", exc)
                return {}

    if not index_path.exists():
        return {}

    # Load index into module-level cache
    global _ZONING_INDEX_CACHE
    key = str(index_path)
    if key not in _ZONING_INDEX_CACHE:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _ZONING_INDEX_CACHE[key] = data.get("zones", [])
        except Exception as exc:
            logger.debug("Zoning index load failed: %s", exc)
            return {}

    zones = _ZONING_INDEX_CACHE[key]

    # Spatial lookup: bbox pre-filter → PiP on exterior ring
    for zone in zones:
        bbox = zone["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        if _pip_exterior(lng, lat, zone["ring"]):
            return {"source": f"zonage-{city_code}", **zone["props"]}

    return {}


# ── CPTAQ zone agricole ───────────────────────────────────────────────────────

# GeoQuébec / données.gouv.qc.ca — Zone agricole CPTAQ (tout le Québec)
# File is large (~150 MB uncompressed) but indexes down to ~10 MB.
_CPTAQ_GEOJSON_URL = (
    "https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Theme-Series/"
    "Produits_geobase/Reglementaires/SHP_AQreseau%2B/"
    # Fallback: données.gouv.qc.ca canonical GeoJSON
)
_CPTAQ_GEOJSON_URLS: list[str] = [
    # données.gouv.qc.ca open data — zone agricole permanente CPTAQ
    "https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Theme-Series/"
    "Produits_geobase/Reglementaires/SHP_AQreseau%2B/",
    # Alternate: GeoQuébec WFS service (GeoJSON output)
    (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/zone_agricole.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:zone_agricole"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    ),
]

# module-level CPTAQ index cache
_CPTAQ_INDEX_CACHE: list | None = None


def _download_file(url: str, dest: Path, timeout: int = 600) -> None:
    """Stream-download url → dest."""
    import httpx  # type: ignore
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as r:
        r.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=256 * 1024):
                fh.write(chunk)


def download_cptaq(cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download the CPTAQ zone agricole GeoJSON (all of Québec, cached once).

    Tries the GeoQuébec WFS service first (direct GeoJSON), falls back to
    static file if known URL is configured. Returns local path or None.
    """
    geojson_path = cache_dir / "cptaq_zone_agricole.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Try WFS GeoJSON endpoint (direct, no parsing needed)
    wfs_url = (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/zone_agricole.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature&TYPENAME=ms:zone_agricole"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    )
    try:
        logger.info("Downloading CPTAQ zone agricole (WFS GeoJSON)…")
        _download_file(wfs_url, geojson_path, timeout=600)
        logger.info("CPTAQ downloaded: %.1f MB", geojson_path.stat().st_size / 1e6)
        return geojson_path
    except Exception as exc:
        logger.debug("CPTAQ WFS download failed: %s", exc)
        if geojson_path.exists():
            geojson_path.unlink()

    logger.debug("CPTAQ download unavailable — place cptaq_zone_agricole.geojson in data_cache/")
    return None


def build_cptaq_index(geojson_path: Path, index_path: Path) -> int:
    """
    Build compact spatial index from CPTAQ GeoJSON.

    Unlike zonage, we only keep bbox + simplified ring (props minimal).
    Returns count of polygons indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")

        if gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            if len(exterior) < 3:
                continue
            xs = [p[0] for p in exterior]
            ys = [p[1] for p in exterior]
            # Keep only relevant props (zone designation)
            keep = {k: v for k, v in props.items()
                    if k.upper() in ("NM_MRC", "NM_MUNIC", "NM_REGION", "TYPE_ZONE",
                                      "CATEGORIE", "STATUT", "NO_DECISION", "CODE")}
            zones.append({
                "props": keep,
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
                "ring": _simplify_ring(exterior, max_pts=200),
            })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("CPTAQ index built: %d zones → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def lookup_cptaq(lat: float, lng: float, cache_dir: Path) -> dict | None:
    """
    Return CPTAQ zone info if point (lat, lng) is inside the agricultural zone.

    Returns dict with source + props if inside, {} if outside, None if data unavailable.
    Auto-downloads and builds index if not cached.
    """
    global _CPTAQ_INDEX_CACHE

    index_path = cache_dir / "cptaq_index.json"

    # Build index if needed
    if not index_path.exists():
        geojson_path = cache_dir / "cptaq_zone_agricole.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_cptaq(cache_dir)
            except Exception as exc:
                logger.debug("CPTAQ download skip: %s", exc)
                return None
        if geojson_path and geojson_path.exists():
            try:
                build_cptaq_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("CPTAQ index build skip: %s", exc)
                return None

    if not index_path.exists():
        return None

    # Load into module-level cache
    key = str(index_path)
    if _CPTAQ_INDEX_CACHE is None:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _CPTAQ_INDEX_CACHE = data.get("zones", [])
        except Exception as exc:
            logger.debug("CPTAQ index load failed: %s", exc)
            return None

    for zone in _CPTAQ_INDEX_CACHE:
        bbox = zone["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        if _pip_exterior(lng, lat, zone["ring"]):
            return {"source": "cptaq", "en_zone_agricole": True, **zone["props"]}

    return {"source": "cptaq", "en_zone_agricole": False}


# ── Patrimoine culturel (Répertoire du patrimoine culturel du Québec) ─────────

# module-level cache
_PATRIMOINE_INDEX_CACHE: list | None = None

# Known WFS endpoint types for patrimoine culturel QC
_PATRIMOINE_WFS_URLS: list[str] = [
    # Immeubles patrimoniaux (bâtiments classés/cités/reconnus)
    (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/patrimoine.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature"
        "&TYPENAME=ms:immeuble_patrimonial"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    ),
    # Alternate: données.gouv.qc.ca package
]


def download_patrimoine(cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download the Répertoire du patrimoine culturel du Québec GeoJSON (WFS).

    Covers immeubles patrimoniaux (classés, cités, reconnus).
    Returns local path or None if unavailable.
    """
    geojson_path = cache_dir / "patrimoine_culturel.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    for url in _PATRIMOINE_WFS_URLS:
        try:
            logger.info("Downloading patrimoine culturel (WFS GeoJSON)…")
            _download_file(url, geojson_path, timeout=300)
            logger.info("Patrimoine culturel downloaded: %.1f MB",
                        geojson_path.stat().st_size / 1e6)
            return geojson_path
        except Exception as exc:
            logger.debug("Patrimoine WFS download failed: %s", exc)
            if geojson_path.exists():
                geojson_path.unlink()

    logger.debug("Patrimoine download unavailable — place patrimoine_culturel.geojson in data_cache/")
    return None


def build_patrimoine_index(geojson_path: Path, index_path: Path) -> int:
    """
    Build compact spatial index from patrimoine culturel GeoJSON.

    For Point geometries (common for individual buildings): store as tiny bbox.
    For Polygon/MultiPolygon: same as CPTAQ.
    Returns number of features indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    _KEEP_PROPS = {
        "NOM", "NM_BIEN", "STATUT", "CATEGORIE", "TYPE_BIEN",
        "COTE_PATRIMONIALE", "MUNICIPALITE", "MRC", "REGION",
        "NM_STATUT", "NM_CATEGORIE",
    }

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")
        keep = {k: v for k, v in props.items() if k.upper() in _KEEP_PROPS and v}

        if gtype == "Point":
            lng, lat = geom["coordinates"][0], geom["coordinates"][1]
            # Small buffer ~50m in degrees at QC latitude
            buf = 0.0005
            zones.append({
                "props": keep,
                "bbox": [lng - buf, lat - buf, lng + buf, lat + buf],
                "point": [lng, lat],
            })
        elif gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        if gtype in ("Polygon", "MultiPolygon"):
            for poly in polys:
                if not poly:
                    continue
                exterior = poly[0]
                if len(exterior) < 3:
                    continue
                xs = [p[0] for p in exterior]
                ys = [p[1] for p in exterior]
                zones.append({
                    "props": keep,
                    "bbox": [min(xs), min(ys), max(xs), max(ys)],
                    "ring": _simplify_ring(exterior, max_pts=100),
                })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Patrimoine index built: %d features → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def _point_near(lng: float, lat: float, feat_lng: float, feat_lat: float,
                threshold_deg: float = 0.0005) -> bool:
    """Return True if (lng, lat) is within threshold degrees of a point feature."""
    return abs(lng - feat_lng) <= threshold_deg and abs(lat - feat_lat) <= threshold_deg


def lookup_patrimoine(lat: float, lng: float, cache_dir: Path) -> dict | None:
    """
    Return first patrimoine culturel feature near/containing (lat, lng).

    Returns dict with source + props if found, {} if not found,
    None if data unavailable.
    """
    global _PATRIMOINE_INDEX_CACHE

    index_path = cache_dir / "patrimoine_index.json"

    if not index_path.exists():
        geojson_path = cache_dir / "patrimoine_culturel.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_patrimoine(cache_dir)
            except Exception as exc:
                logger.debug("Patrimoine download skip: %s", exc)
                return None
        if geojson_path and geojson_path.exists():
            try:
                build_patrimoine_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("Patrimoine index build skip: %s", exc)
                return None

    if not index_path.exists():
        return None

    if _PATRIMOINE_INDEX_CACHE is None:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _PATRIMOINE_INDEX_CACHE = data.get("zones", [])
        except Exception as exc:
            logger.debug("Patrimoine index load failed: %s", exc)
            return None

    for feat in _PATRIMOINE_INDEX_CACHE:
        bbox = feat["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        # Point feature: proximity check
        if "point" in feat:
            fl, flat = feat["point"]
            if _point_near(lng, lat, fl, flat):
                return {"source": "patrimoine-culturel", **feat["props"]}
        # Polygon feature: PiP
        elif "ring" in feat:
            if _pip_exterior(lng, lat, feat["ring"]):
                return {"source": "patrimoine-culturel", **feat["props"]}

    return {}


# ── Zones inondables (MELCC / GeoQuébec) ─────────────────────────────────────

# module-level cache
_INONDABLE_INDEX_CACHE: list | None = None

# MELCC WFS — zones de contrainte (inondation 0-20 ans, 20-100 ans)
# Source: Atlas des zones inondables du MELCC
_INONDABLE_WFS_URLS: list[str] = [
    (
        "https://geoegl.msp.gouv.qc.ca/apis/wss/complet.fcgi"
        "?SERVICE=WFS&REQUEST=GetFeature"
        "&TYPENAME=ms:igo_inondation"
        "&OUTPUTFORMAT=geojson&SRSNAME=EPSG:4326"
    ),
    # Alternate: direct MELCC GeoServer
    (
        "https://geoserver.environnement.gouv.qc.ca/geoserver/ows"
        "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
        "&TYPENAMES=MELCC:zone_inondable"
        "&OUTPUTFORMAT=application/json&SRSNAME=EPSG:4326"
    ),
]

# Récurrence → label FR
_RECURRENCE_LABELS: dict[str, str] = {
    "0_20": "0-20 ans (grand courant)",
    "20_100": "20-100 ans (crue centennale)",
    "100": "100+ ans",
    "2": "2 ans",
    "20": "20 ans",
    "100_500": "100-500 ans",
}


def download_inondable(cache_dir: Path, force: bool = False) -> Path | None:
    """
    Download MELCC zones inondables GeoJSON (tout le Québec, WFS).
    Returns local path or None if unavailable.
    """
    geojson_path = cache_dir / "zones_inondables.geojson"
    if geojson_path.exists() and not force:
        return geojson_path

    cache_dir.mkdir(parents=True, exist_ok=True)

    for url in _INONDABLE_WFS_URLS:
        try:
            logger.info("Downloading zones inondables MELCC (WFS GeoJSON)…")
            _download_file(url, geojson_path, timeout=600)
            logger.info("Zones inondables downloaded: %.1f MB",
                        geojson_path.stat().st_size / 1e6)
            return geojson_path
        except Exception as exc:
            logger.debug("Zones inondables WFS failed: %s", exc)
            if geojson_path.exists():
                geojson_path.unlink()

    logger.debug("Zones inondables unavailable — place zones_inondables.geojson in data_cache/")
    return None


def build_inondable_index(geojson_path: Path, index_path: Path) -> int:
    """
    Build compact spatial index from zones inondables GeoJSON.
    Keeps récurrence/type fields for risk classification.
    Returns number of polygons indexed.
    """
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features") or []
    zones: list[dict] = []

    _KEEP_PROPS = {
        "RECURRENCE", "TYPE_ZONE", "NM_ZONE", "DESCRIPTION",
        "CLASSE", "SOURCE", "MRC", "MUNICIPALITE",
        # alternate field names from different WFS schemas
        "RECURR", "TYPE", "STATUT",
    }

    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties") or {}
        gtype = geom.get("type", "")
        keep = {k: v for k, v in props.items() if k.upper() in _KEEP_PROPS and v}

        if gtype == "Polygon":
            polys = [geom["coordinates"]]
        elif gtype == "MultiPolygon":
            polys = geom["coordinates"]
        else:
            continue

        for poly in polys:
            if not poly:
                continue
            exterior = poly[0]
            if len(exterior) < 3:
                continue
            xs = [p[0] for p in exterior]
            ys = [p[1] for p in exterior]
            zones.append({
                "props": keep,
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
                "ring": _simplify_ring(exterior, max_pts=150),
            })

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"zones": zones, "_built_at": time.time(), "_count": len(zones)},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Zones inondables index built: %d zones → %s (%.1f MB)",
                len(zones), index_path.name, index_path.stat().st_size / 1e6)
    return len(zones)


def lookup_inondable(lat: float, lng: float, cache_dir: Path) -> dict | None:
    """
    Return first zone inondable containing (lat, lng).

    Returns dict with source + récurrence if in flood zone,
    {} if outside all zones, None if data unavailable.
    """
    global _INONDABLE_INDEX_CACHE

    index_path = cache_dir / "inondable_index.json"

    if not index_path.exists():
        geojson_path = cache_dir / "zones_inondables.geojson"
        if not geojson_path.exists():
            try:
                geojson_path = download_inondable(cache_dir)
            except Exception as exc:
                logger.debug("Zones inondables download skip: %s", exc)
                return None
        if geojson_path and geojson_path.exists():
            try:
                build_inondable_index(geojson_path, index_path)
            except Exception as exc:
                logger.debug("Inondable index build skip: %s", exc)
                return None

    if not index_path.exists():
        return None

    if _INONDABLE_INDEX_CACHE is None:
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
            _INONDABLE_INDEX_CACHE = data.get("zones", [])
        except Exception as exc:
            logger.debug("Inondable index load failed: %s", exc)
            return None

    # Return the most restrictive zone (smallest recurrence period = highest risk)
    hits: list[dict] = []
    for zone in _INONDABLE_INDEX_CACHE:
        bbox = zone["bbox"]
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue
        if _pip_exterior(lng, lat, zone["ring"]):
            hits.append(zone["props"])

    if not hits:
        return {}

    # Prefer zone with smallest recurrence number (highest risk)
    def _risk_key(props: dict) -> int:
        rec = str(props.get("RECURRENCE") or props.get("RECURR") or "999")
        try:
            return int(rec.split("_")[0].split("-")[0])
        except ValueError:
            return 999

    best = sorted(hits, key=_risk_key)[0]
    rec = best.get("RECURRENCE") or best.get("RECURR") or ""
    label = _RECURRENCE_LABELS.get(rec, rec)
    return {
        "source": "melcc-zones-inondables",
        "en_zone_inondable": True,
        "recurrence": rec,
        "recurrence_label": label,
        **{k: v for k, v in best.items() if k not in ("RECURRENCE", "RECURR")},
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def enrich_case(
    case: dict,
    display_name: str = "",
    cache_dir: Path | None = None,
) -> None:
    """
    Enrich case dict in-place with external data.

    Injects (when available) :
      - case["marche_locatif"]    : SCHL rental market data (StatCan WDS)
      - case["role_municipal"]    : building characteristics + valeurs foncières
      - case["zonage_urbanisme"]    : official zone code + description (open data GeoJSON)
      - case["zone_agricole"]       : CPTAQ agricultural zone status (bool + MRC info)
      - case["patrimoine_culturel"] : {} if not listed, dict with statut/nom if found
      - case["zone_inondable"]        : {} if outside, dict with recurrence if in flood zone
      - case["indice_prix_logement"]  : NHPI (indice + variation annuelle %) via StatCan WDS

    Never raises — all failures logged at DEBUG level.
    """
    if cache_dir is None:
        cache_dir = Path(__file__).resolve().parent.parent / "data_cache"

    zone = str(case.get("zone", ""))
    city_code = detect_city(display_name, zone)

    # ── Marché du travail CMA ─────────────────────────────────────────────────
    if not case.get("marche_travail"):
        try:
            travail = fetch_marche_travail(city_code, cache_dir)
            if travail:
                case["marche_travail"] = travail
                logger.debug("marche_travail injecté : %s chômage=%.1f%%",
                             city_code, travail.get("taux_chomage_pct", 0))
        except Exception as exc:
            logger.debug("marche_travail skip: %s", exc)

    # ── Croissance démographique CMA ──────────────────────────────────────────
    if not case.get("population_cma"):
        try:
            pop = fetch_population_growth(city_code, cache_dir)
            if pop:
                case["population_cma"] = pop
                logger.debug("population_cma injecté : %s pop=%d var=%.2f%%",
                             city_code, pop.get("population", 0),
                             pop.get("variation_annuelle_pct", 0))
        except Exception as exc:
            logger.debug("population_cma skip: %s", exc)

    # ── Taux Bank of Canada (nationaux, non spécifiques à la ville) ──────────
    if not case.get("taux_bancaires"):
        try:
            taux = fetch_taux_boc(cache_dir)
            if taux:
                case["taux_bancaires"] = taux
                logger.debug("taux_bancaires injecté : directeur=%.2f%%",
                             taux.get("taux_directeur_pct", 0))
        except Exception as exc:
            logger.debug("taux_boc skip: %s", exc)

    # ── SCHL rental market ────────────────────────────────────────────────────
    if not case.get("marche_locatif"):
        try:
            rental = fetch_rental_market(city_code, cache_dir)
            if rental:
                case["marche_locatif"] = rental
                logger.debug("marche_locatif injecté : %s", rental.get("ville"))
        except Exception as exc:
            logger.debug("marche_locatif skip: %s", exc)

    # ── Taux d'inoccupation SCHL ──────────────────────────────────────────────
    if not case.get("taux_inoccupation"):
        try:
            vacance = fetch_vacancy_rate(city_code, cache_dir)
            if vacance:
                case["taux_inoccupation"] = vacance
                logger.debug("taux_inoccupation injecté : %s total=%.1f%%",
                             city_code, vacance.get("taux_total_pct", 0))
        except Exception as exc:
            logger.debug("taux_inoccupation skip: %s", exc)

    # ── NHPI (indice prix logement neuf) ──────────────────────────────────────
    if not case.get("indice_prix_logement"):
        try:
            nhpi = fetch_nhpi(city_code, cache_dir)
            if nhpi:
                case["indice_prix_logement"] = nhpi
                logger.debug("indice_prix_logement injecté : %s indice=%.1f",
                             nhpi.get("ville"), nhpi.get("indice_total", 0))
        except Exception as exc:
            logger.debug("nhpi skip: %s", exc)

    # ── Census démographique (Recensement 2021) ───────────────────────────────
    if not case.get("donnees_sociodemographiques"):
        try:
            census = fetch_census_profile(city_code, cache_dir)
            if census:
                case["donnees_sociodemographiques"] = census
                logger.debug("donnees_sociodemographiques injecté : %s", city_code)
        except Exception as exc:
            logger.debug("census skip: %s", exc)

    # ── Permis de construction (StatCan 34-10-0066-01) ────────────────────────
    if not case.get("permis_construction"):
        try:
            permis = fetch_permis_construction(city_code, cache_dir)
            if permis:
                case["permis_construction"] = permis
                logger.debug("permis_construction injecté : %s unités/mois=%.0f",
                             city_code, permis.get("unites_residentielles_mois", 0))
        except Exception as exc:
            logger.debug("permis_construction skip: %s", exc)

    # ── Rôle municipal ────────────────────────────────────────────────────────
    if not case.get("role_municipal"):
        matricule = str(case.get("matricule") or "").strip() or None
        role: dict = {}

        if city_code == "montreal":
            # Montréal: CSV lookup
            csv_path = cache_dir / "role_mtl.csv"
            if csv_path.exists():
                try:
                    role = lookup_role_mtl(csv_path, matricule=matricule, display_name=display_name)
                except Exception as exc:
                    logger.debug("role_municipal (mtl csv) skip: %s", exc)
        elif city_code in _ROLE_XML_CITIES:
            # Autres villes: XML JSON index lookup
            index_path = cache_dir / f"role_{city_code}_index.json"
            if not index_path.exists():
                # Try to build index from XML if XML is cached
                xml_path = cache_dir / f"role_{city_code}.xml"
                if xml_path.exists():
                    try:
                        build_role_xml_index(xml_path, index_path, city_code)
                    except Exception as exc:
                        logger.debug("role XML index build skip: %s", exc)
            if index_path.exists():
                try:
                    role = lookup_role_xml(index_path, matricule=matricule, display_name=display_name)
                except Exception as exc:
                    logger.debug("role_municipal (xml) skip: %s", exc)

        if role:
            case["role_municipal"] = role
            if not case.get("annee_construction") and role.get("annee_construction"):
                case["annee_construction"] = role["annee_construction"]
            if not case.get("surface") and role.get("superficie_batiment_m2"):
                case["surface"] = role["superficie_batiment_m2"]
            # Backfill evaluation municipale from XML valeur_totale
            if not case.get("evaluation_municipale_totale") and role.get("valeur_totale"):
                case["evaluation_municipale_totale"] = role["valeur_totale"]
            logger.debug("role_municipal injecté : %s (%s)", role.get("matricule83"), city_code)

    # ── Geocode (shared by zonage + CPTAQ + patrimoine + inondable) ─────────
    _coords: tuple[float, float] | None = None
    if display_name and (
        not case.get("zonage_urbanisme")
        or not case.get("zone_agricole")
        or not case.get("patrimoine_culturel")
        or "zone_inondable" not in case
    ):
        try:
            _coords = geocode_address(display_name, cache_dir)
        except Exception as exc:
            logger.debug("geocode skip: %s", exc)

    # ── Zonage urbanisme ──────────────────────────────────────────────────────
    if not case.get("zonage_urbanisme") and _coords:
        try:
            lat, lng = _coords
            zone_info = lookup_zoning_point(city_code, lat, lng, cache_dir)
            if zone_info:
                case["zonage_urbanisme"] = zone_info
                logger.debug("zonage_urbanisme injecté : %s", zone_info)
        except Exception as exc:
            logger.debug("zonage skip: %s", exc)

    # ── CPTAQ zone agricole ───────────────────────────────────────────────────
    if not case.get("zone_agricole") and _coords:
        try:
            lat, lng = _coords
            cptaq = lookup_cptaq(lat, lng, cache_dir)
            if cptaq is not None:
                case["zone_agricole"] = cptaq
                logger.debug("zone_agricole injecté : en_zone=%s", cptaq.get("en_zone_agricole"))
        except Exception as exc:
            logger.debug("cptaq skip: %s", exc)

    # ── Patrimoine culturel ───────────────────────────────────────────────────
    if not case.get("patrimoine_culturel") and _coords:
        try:
            lat, lng = _coords
            pat = lookup_patrimoine(lat, lng, cache_dir)
            if pat is not None:
                case["patrimoine_culturel"] = pat  # {} = not listed, dict = found
                if pat:
                    logger.debug("patrimoine_culturel injecté : %s", pat.get("NOM") or pat.get("NM_BIEN"))
        except Exception as exc:
            logger.debug("patrimoine skip: %s", exc)

    # ── Zones inondables (MELCC) ──────────────────────────────────────────────
    if "zone_inondable" not in case and _coords:
        try:
            lat, lng = _coords
            inond = lookup_inondable(lat, lng, cache_dir)
            if inond is not None:
                case["zone_inondable"] = inond  # {} = hors zone, dict = en zone
                if inond:
                    logger.debug("zone_inondable injectée : récurrence=%s",
                                 inond.get("recurrence"))
        except Exception as exc:
            logger.debug("inondable skip: %s", exc)
