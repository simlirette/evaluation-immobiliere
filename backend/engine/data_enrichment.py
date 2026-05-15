"""
data_enrichment.py — enrichissement du case depuis sources données externes.

Sources actives V0 :
  - SCHL marché locatif  : StatCan WDS API, table 34-10-0133-01 (cache 24 h)
  - Rôle municipal Mtl   : CSV MAMH (~72 MB, si data_cache/role_mtl.csv présent)

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
    """Return ordinal of best-matching member in dimension dim_idx."""
    if dim_idx >= len(dims):
        return None
    members = dims[dim_idx].get("member", [])
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


# ── Main entry point ──────────────────────────────────────────────────────────

def enrich_case(
    case: dict,
    display_name: str = "",
    cache_dir: Path | None = None,
) -> None:
    """
    Enrich case dict in-place with external data.

    Injects (when available) :
      - case["marche_locatif"]  : SCHL rental market data (StatCan WDS)
      - case["role_municipal"]  : building characteristics (Montréal CSV)

    Never raises — all failures logged at DEBUG level.
    """
    if cache_dir is None:
        cache_dir = Path(__file__).resolve().parent.parent / "data_cache"

    zone = str(case.get("zone", ""))
    city_code = detect_city(display_name, zone)

    # ── SCHL rental market ────────────────────────────────────────────────────
    if not case.get("marche_locatif"):
        try:
            rental = fetch_rental_market(city_code, cache_dir)
            if rental:
                case["marche_locatif"] = rental
                logger.debug("marche_locatif injecté : %s", rental.get("ville"))
        except Exception as exc:
            logger.debug("marche_locatif skip: %s", exc)

    # ── Rôle municipal Montréal ───────────────────────────────────────────────
    if not case.get("role_municipal"):
        csv_path = cache_dir / "role_mtl.csv"
        if csv_path.exists():
            try:
                matricule = str(case.get("matricule") or "").strip() or None
                role = lookup_role_mtl(csv_path, matricule=matricule, display_name=display_name)
                if role:
                    case["role_municipal"] = role
                    # Backfill case fields that fixture may have left empty
                    if not case.get("annee_construction") and role.get("annee_construction"):
                        case["annee_construction"] = role["annee_construction"]
                    if not case.get("surface") and role.get("superficie_batiment_m2"):
                        case["surface"] = role["superficie_batiment_m2"]
                    logger.debug("role_municipal injecté : %s", role.get("matricule83"))
            except Exception as exc:
                logger.debug("role_municipal skip: %s", exc)
