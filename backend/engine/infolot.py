"""
infolot.py — Recherche de lots cadastraux par rayon via service gouvernemental.

Source : ArcGIS REST « Cadastre_allege » (MELCCFP/MRNF, registre Cadastre Québec)
  URL    : https://geo.environnement.gouv.qc.ca/donnees/rest/services/Reference/Cadastre_allege/MapServer/0/query
  Layer  : 0 — Lots du cadastre rénové (champ NO_LOT, MAJ aux 2 mois)
  Auth   : aucune (service public)
  Coût   : gratuit
  Cache  : JSON fichier, TTL 30 jours par cellule (lat4, lon4, radius)

Remplace l'ancien WFS Atlas (servicesvectoriels.atlas.gouv.qc.ca/IDS_CATASTO_
STAC_S_RLOT_QC) retiré par le gouvernement — 404 constaté le 2026-06-10.

Retourne des lots avec no_lot (cadastre rénové Québec) + centroïde + distance.
Non-bloquant : toute exception retourne [].
"""
from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path

from engine.source_diagnostics import append_source_diagnostic, make_source_diagnostic

logger = logging.getLogger("infolot")

_WFS_BASE = (
    "https://geo.environnement.gouv.qc.ca"
    "/donnees/rest/services/Reference/Cadastre_allege/MapServer/0/query"
)
_WFS_NOLOT_FIELD = "NO_LOT"  # format service : "6 259 953" (espaces de groupement)
_HTTP_TIMEOUT = 15.0
_CACHE_TTL = 30 * 86_400     # 30 jours
_MAX_FEATURES = 500


# ── Géométrie ─────────────────────────────────────────────────────────────────

def _bbox_from_radius(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    """Retourne (minLng, minLat, maxLng, maxLat) pour un rayon donné."""
    lat_deg = radius_km / 111.32
    lon_deg = radius_km / (111.32 * math.cos(math.radians(lat)))
    return (lon - lon_deg, lat - lat_deg, lon + lon_deg, lat + lat_deg)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance Haversine en km entre deux points WGS84."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _centroid_from_geometry(geom: dict) -> tuple[float | None, float | None]:
    """
    Calcule le centroïde approximatif d'un Polygon ou MultiPolygon GeoJSON.
    Retourne (lat, lon) ou (None, None) si type non supporté.
    Note : les coordonnées GeoJSON sont [longitude, latitude].
    """
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return None, None

    if gtype == "Polygon":
        ring = coords[0]  # anneau extérieur
    elif gtype == "MultiPolygon":
        ring = coords[0][0]  # premier anneau du premier polygone
    else:
        return None, None

    if not ring:
        return None, None

    # GeoJSON rings close back to the first point — exclude it for proper centroid
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring = ring[:-1]

    lngs = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


def _parse_nolot(value: object) -> int | None:
    """Convertit NO_LOT (str ou int) en int. Retourne None si invalide.

    Le service Cadastre_allege formate les numéros avec des espaces de
    groupement (ex. "6 259 953") — espaces ordinaires et insécables retirés.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace(" ", "").replace(" ", "")
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# ── Cache ─────────────────────────────────────────────────────────────────────

def _cache_path(lat: float, lon: float, radius_km: float, cache_dir: Path) -> Path:
    key = f"infolot_{lat:.4f}_{lon:.4f}_{radius_km:.1f}"
    return cache_dir / f"{key}.json"


def _read_cache(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - d.get("_ts", 0) < _CACHE_TTL:
            return d.get("lots", [])
    except Exception:
        pass
    return None


def _write_cache(path: Path, lots: list[dict]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"_ts": time.time(), "lots": lots}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


# ── WFS Query ─────────────────────────────────────────────────────────────────

def fetch_lots_in_radius(
    lat: float,
    lon: float,
    radius_km: float,
    cache_dir: Path,
    diagnostics: list[dict] | None = None,
) -> list[dict]:
    """
    Retourne les lots cadastraux dans un rayon autour d'un point.

    Chaque lot : {no_lot: int, lat: float, lon: float, distance_km: float}

    Non-bloquant : retourne [] si WFS inaccessible ou erreur réseau.
    Cache 30 jours par cellule (lat4, lon4, radius).
    """
    cp = _cache_path(lat, lon, radius_km, cache_dir)
    cached = _read_cache(cp)
    if cached is not None:
        append_source_diagnostic(
            diagnostics,
            make_source_diagnostic(
                "infolot",
                "ok" if cached else "empty",
                "Cache Infolot utilise",
                stage="wfs",
                cached=True,
                details={"lot_count": len(cached), "radius_km": radius_km},
            ),
        )
        return cached

    try:
        import httpx
    except ImportError:
        logger.warning("httpx non disponible — Infolot désactivé")
        append_source_diagnostic(
            diagnostics,
            make_source_diagnostic(
                "infolot",
                "failed",
                "httpx non disponible",
                stage="wfs",
                severity="warning",
            ),
        )
        return []

    minlng, minlat, maxlng, maxlat = _bbox_from_radius(lat, lon, radius_km)

    params = {
        "geometry": f"{minlng},{minlat},{maxlng},{maxlat}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": _WFS_NOLOT_FIELD,
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
        "resultRecordCount": str(_MAX_FEATURES),
    }

    try:
        r = httpx.get(_WFS_BASE, params=params, timeout=_HTTP_TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        data = r.json()
        # ArcGIS REST renvoie ses erreurs en HTTP 200 avec un corps {"error": …}
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(f"ArcGIS error: {data['error']}")
    except Exception as exc:
        logger.warning("Infolot WFS error: %s", exc)
        append_source_diagnostic(
            diagnostics,
            make_source_diagnostic(
                "infolot",
                "failed",
                "Erreur WFS Infolot",
                stage="wfs",
                severity="warning",
                details={"error": f"{type(exc).__name__}: {exc}"},
            ),
        )
        return []

    raw_features = data.get("features", []) if isinstance(data, dict) else []
    features = raw_features if isinstance(raw_features, list) else []
    lots: list[dict] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}

        no_lot = _parse_nolot(props.get(_WFS_NOLOT_FIELD))
        if no_lot is None:
            # Essayer des variantes de noms de champ
            for alt in ("NO_LOT", "LOT_NO", "NOLOT", "nolot", "no_lot"):
                no_lot = _parse_nolot(props.get(alt))
                if no_lot is not None:
                    break
        if no_lot is None:
            continue

        clat, clon = _centroid_from_geometry(geom)
        if clat is None or clon is None:
            continue

        dist = _haversine_km(lat, lon, clat, clon)
        if dist > radius_km:
            continue  # Exclusion des coins de la bbox

        lots.append({
            "no_lot": no_lot,
            "lat": clat,
            "lon": clon,
            "distance_km": round(dist, 4),
        })

    lots.sort(key=lambda x: x["distance_km"])
    _write_cache(cp, lots)
    append_source_diagnostic(
        diagnostics,
        make_source_diagnostic(
            "infolot",
            "ok" if lots else "empty",
            "Lots cadastraux Infolot recuperes" if lots else "Aucun lot Infolot dans le rayon",
            stage="wfs",
            details={"lot_count": len(lots), "feature_count": len(features), "radius_km": radius_km},
        ),
    )
    logger.info("Infolot WFS: %d lots dans %.1f km autour de (%.4f, %.4f)", len(lots), radius_km, lat, lon)
    return lots
