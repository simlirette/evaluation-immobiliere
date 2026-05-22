"""
comparables_builder.py — Pipeline Infolot + MAMH → pool de comparables.

Flux pour les villes XML (québec, laval, longueuil, gatineau, sherbrooke) :
  geocode_address() → Infolot WFS → lookup_role_by_lot() → pool

Flux Montréal (CSV, sans no_lot) :
  geocode_address() → lookup_role_mtl_by_civic() → pool (heuristique civique ±200)

Dans les deux cas, prix_vente=0 et date_vente="" jusqu'à l'intégration SIRF.
Non-bloquant : toute exception retourne [].
"""
from __future__ import annotations

import logging
import unicodedata
from pathlib import Path

from engine.source_diagnostics import append_source_diagnostic, make_source_diagnostic

logger = logging.getLogger("comparables_builder")

try:
    from engine.registre_foncier import enrich_pool_with_sirf as _enrich_sirf
    _SIRF_AVAILABLE = True
except ImportError:
    _SIRF_AVAILABLE = False

# Correspondance ville → city_code MAMH (sous-ensemble des cities supportées)
_CITY_KEYWORDS: list[tuple[str, str]] = [
    ("montreal", "montreal"),
    ("montréal", "montreal"),
    ("laval", "laval"),
    ("longueuil", "longueuil"),
    ("gatineau", "gatineau"),
    ("sherbrooke", "sherbrooke"),
    ("québec", "quebec"),
    ("quebec", "quebec"),
    ("lévis", "quebec"),
    ("levis", "quebec"),
]

# MAMH XML cities supportées pour lot-number matching
_XML_CITIES = {"quebec", "laval", "longueuil", "gatineau", "sherbrooke"}

# Filtres de surface : garder les comparables entre [subject * (1-tol), subject * (1+tol)]
_DEFAULT_SURFACE_TOLERANCE = 0.50   # ±50 %
_MIN_SURFACE_M2 = 30.0              # Ignorer les très petites superficies


def _norm(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _detect_city_code(address: str) -> str | None:
    """Détecte le city_code MAMH depuis une adresse textuelle."""
    norm = _norm(address)
    for keyword, code in _CITY_KEYWORDS:
        if keyword in norm:
            return code
    return None


def _pool_item_from_mamh_record(rec: dict, lot: dict) -> dict:
    """
    Formate un enregistrement MAMH + lot Infolot en dict compatible avec
    search_comparables() de tools.py.

    prix_vente et date_vente sont vides — seront remplis par le module SIRF (Phase 2).
    source_quality="role_evaluation_municipale" → score 0.85 dans tools.py SOURCE_QUALITY.
    """
    no_lot = lot.get("no_lot") or rec.get("no_lot", "")
    matricule = rec.get("matricule83", "") or rec.get("matricule", "")
    surface_m2 = float(rec.get("superficie_batiment_m2") or 0.0)
    adresse = f"{rec.get('adresse_civique', '')} {rec.get('nom_rue', '')}".strip()

    # Déduire le type_bien depuis le code CUBF (MEFQ)
    code_cubf = rec.get("code_cubf") or 0
    type_bien = _cubf_to_type_bien(int(code_cubf) if code_cubf else 0)

    return {
        "comparable_id": f"MAMH-{no_lot}",
        "source_id": f"MAMH-{no_lot}",
        "source_type": "role_evaluation_municipale",
        "adresse": adresse,
        "matricule": matricule,
        "no_lot": int(no_lot) if no_lot else None,
        "lat": lot.get("lat"),
        "lon": lot.get("lon"),
        "distance_km": float(lot.get("distance_km") or 0.0),
        "surface": {"value": surface_m2, "unit": "m2"},
        "surface_habitable": surface_m2,
        "surface_terrain": float(rec.get("superficie_terrain_m2") or 0.0),
        "annee_construction": rec.get("annee_construction"),
        "nb_logements": int(rec.get("nb_logements") or 0),
        "type_bien": type_bien,
        "code_cubf": code_cubf,
        "evaluation_municipale": float(rec.get("valeur_totale") or 0.0),
        # Vide jusqu'à intégration SIRF (Phase 2)
        "prix_vente": 0.0,
        "date_vente": "",
        "confidence": 0.65,
    }


def _cubf_to_type_bien(code_cubf: int) -> str:
    """Convertit un code CUBF MAMH en type_bien eval-immo."""
    if 1000 <= code_cubf <= 1099:
        return "unifamiliale"
    if 1100 <= code_cubf <= 1199:
        return "jumelé"
    if 1200 <= code_cubf <= 1299:
        return "duplex"
    if 1300 <= code_cubf <= 1399:
        return "triplex"
    if 1400 <= code_cubf <= 1999:
        return "immeuble_revenus"
    if 2000 <= code_cubf <= 2999:
        return "commercial"
    if 3000 <= code_cubf <= 3999:
        return "industriel"
    if 5000 <= code_cubf <= 5999:
        return "terrain"
    return "autre"


def _filter_by_type_and_surface(
    pool: list[dict],
    subject_surface_m2: float,
    subject_type_bien: str,
    surface_tolerance: float = _DEFAULT_SURFACE_TOLERANCE,
) -> list[dict]:
    """
    Garde les comparables avec :
    - surface dans [subject * (1-tol), subject * (1+tol)]

    Si subject_surface_m2 <= 0, le filtre surface est désactivé.
    """
    result = []
    for item in pool:
        surf = float((item.get("surface") or {}).get("value") or 0.0)
        if surf < _MIN_SURFACE_M2:
            continue
        if subject_surface_m2 > 0:
            lo = subject_surface_m2 * (1 - surface_tolerance)
            hi = subject_surface_m2 * (1 + surface_tolerance)
            if not (lo <= surf <= hi):
                continue
        if subject_type_bien and item.get("type_bien") != subject_type_bien:
            continue
        result.append(item)
    return result


def _diag(
    diagnostics: list[dict] | None,
    source: str,
    status: str,
    message: str,
    *,
    stage: str,
    severity: str = "info",
    details: dict | None = None,
) -> None:
    append_source_diagnostic(
        diagnostics,
        make_source_diagnostic(
            source,
            status,
            message,
            stage=stage,
            severity=severity,
            details=details,
        ),
    )


def build_comparable_pool(
    subject_address: str,
    subject_surface_m2: float = 0.0,
    subject_type_bien: str = "",
    subject_annee_construction: int = 0,
    radius_km: float = 2.0,
    cache_dir: Path | None = None,
    max_candidates: int = 50,
    diagnostics: list[dict] | None = None,
) -> list[dict]:
    """
    Point d'entrée principal. Retourne un pool de dicts prêts pour search_comparables().

    Flux XML (5 villes) : geocode → Infolot WFS → lookup_role_by_lot()
    Flux MTL            : geocode → lookup_role_mtl_by_civic() (heuristique)
    Fallback            : [] (non-bloquant)

    prix_vente=0 et date_vente="" dans tous les cas — Phase 2 (SIRF) les remplira.
    """
    if cache_dir is None:
        from engine.data_enrichment import get_data_cache_dir
        cache_dir = get_data_cache_dir()

    city_code = _detect_city_code(subject_address)
    if city_code is None:
        logger.info("Ville non reconnue dans '%s' — pool vide", subject_address)
        _diag(
            diagnostics,
            "mamh",
            "skipped",
            "Ville non supportee par le pipeline de comparables publics",
            stage="city_detection",
            details={"address": subject_address},
        )
        return []

    try:
        from engine.data_enrichment import geocode_address
        coords = geocode_address(subject_address, cache_dir)
    except Exception as exc:
        logger.warning("geocode_address failed: %s", exc)
        _diag(
            diagnostics,
            "geocoding",
            "failed",
            "Geocodage de l'adresse impossible",
            stage="comparables",
            severity="warning",
            details={"error": f"{type(exc).__name__}: {exc}"},
        )
        return []

    if coords is None:
        _diag(
            diagnostics,
            "geocoding",
            "empty",
            "Aucune coordonnee geocodee pour l'adresse",
            stage="comparables",
            details={"address": subject_address},
        )
        logger.info("Geocoding sans résultat pour '%s'", subject_address)
        return []

    subject_lat, subject_lon = coords
    _diag(
        diagnostics,
        "geocoding",
        "ok",
        "Adresse geocodee pour le bassin de comparables",
        stage="comparables",
        details={"city_code": city_code},
    )

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
            diagnostics=diagnostics,
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
            diagnostics=diagnostics,
        )
    else:
        _diag(
            diagnostics,
            "mamh",
            "skipped",
            "Ville sans source MAMH configuree",
            stage="comparables",
            details={"city_code": city_code},
        )
        logger.info("city_code '%s' sans MAMH configuré — pool vide", city_code)
        return []

    if _SIRF_AVAILABLE and pool:
        try:
            pool = _enrich_sirf(pool, cache_dir=cache_dir, diagnostics=diagnostics)
        except Exception as exc:
            logger.warning("enrich_pool_with_sirf failed (non-bloquant): %s", exc)
            _diag(
                diagnostics,
                "sirf",
                "failed",
                "Enrichissement SIRF interrompu",
                stage="comparables",
                severity="warning",
                details={"error": f"{type(exc).__name__}: {exc}"},
            )
    elif not _SIRF_AVAILABLE:
        _diag(
            diagnostics,
            "sirf",
            "skipped",
            "Module SIRF indisponible",
            stage="comparables",
            severity="warning",
        )
    elif not pool:
        _diag(
            diagnostics,
            "sirf",
            "skipped",
            "Aucun comparable avec lot a enrichir via SIRF",
            stage="comparables",
        )

    return pool


def _build_pool_xml(
    city_code: str,
    subject_lat: float,
    subject_lon: float,
    subject_surface_m2: float,
    subject_type_bien: str,
    radius_km: float,
    cache_dir: Path,
    max_candidates: int,
    diagnostics: list[dict] | None = None,
) -> list[dict]:
    """Pipeline pour les 5 villes XML : Infolot → by_lot → filtrage."""
    try:
        from engine.infolot import fetch_lots_in_radius
        from engine.data_enrichment import lookup_role_by_lot
    except Exception as exc:
        logger.warning("Import error dans _build_pool_xml: %s", exc)
        _diag(
            diagnostics,
            "mamh",
            "failed",
            "Import du pipeline Infolot/MAMH impossible",
            stage="comparables_xml",
            severity="warning",
            details={"error": f"{type(exc).__name__}: {exc}"},
        )
        return []

    index_path = cache_dir / f"role_{city_code}_index.json"
    if not index_path.exists():
        _diag(
            diagnostics,
            "mamh",
            "skipped",
            "Index MAMH absent pour la ville",
            stage="comparables_xml",
            details={"city_code": city_code, "index_path": str(index_path)},
        )
        logger.info("Index MAMH absent pour %s (%s) — pool vide", city_code, index_path)
        return []

    lots = fetch_lots_in_radius(subject_lat, subject_lon, radius_km, cache_dir, diagnostics=diagnostics)
    if not lots:
        _diag(
            diagnostics,
            "mamh",
            "skipped",
            "Aucun lot Infolot disponible pour joindre le role MAMH",
            stage="comparables_xml",
            details={"city_code": city_code},
        )
        return []

    pool: list[dict] = []
    matched_lots = 0
    for lot in lots[:max_candidates * 3]:   # Surcharger pour compenser les filtres
        rec = lookup_role_by_lot(index_path, no_lot=lot["no_lot"])
        if not rec:
            continue
        matched_lots += 1
        item = _pool_item_from_mamh_record(rec, lot)
        pool.append(item)

    pool = _filter_by_type_and_surface(pool, subject_surface_m2, subject_type_bien)
    pool.sort(key=lambda x: x["distance_km"])
    _diag(
        diagnostics,
        "mamh",
        "ok" if pool else ("partial" if matched_lots else "empty"),
        "Comparables MAMH joints aux lots Infolot" if pool else "Aucun comparable MAMH retenu apres jointure/filtres",
        stage="comparables_xml",
        details={
            "city_code": city_code,
            "lot_count": len(lots),
            "matched_lot_count": matched_lots,
            "pool_count": len(pool),
        },
    )
    return pool[:max_candidates]


def _build_pool_montreal(
    subject_address: str,
    subject_lat: float,
    subject_lon: float,
    subject_surface_m2: float,
    subject_type_bien: str,
    cache_dir: Path,
    max_candidates: int,
    diagnostics: list[dict] | None = None,
) -> list[dict]:
    """
    Pipeline Montréal : heuristique civic number ±200 sur même rue.
    Pas d'Infolot (CSV MTL sans no_lot).
    Les distances sont calculées via geocode_address par lot (limité à 20 pour perf).
    """
    try:
        from engine.data_enrichment import lookup_role_mtl_by_civic, geocode_address
    except Exception as exc:
        logger.warning("Import error dans _build_pool_montreal: %s", exc)
        _diag(
            diagnostics,
            "mamh",
            "failed",
            "Import du role municipal Montreal impossible",
            stage="comparables_montreal",
            severity="warning",
            details={"error": f"{type(exc).__name__}: {exc}"},
        )
        return []

    csv_path = cache_dir / "role_mtl.csv"
    if not csv_path.exists():
        _diag(
            diagnostics,
            "mamh",
            "skipped",
            "CSV du role municipal Montreal absent",
            stage="comparables_montreal",
            details={"csv_path": str(csv_path)},
        )
        return []

    # Extraire no_civique et nom_rue depuis l'adresse du sujet
    civic_ref, nom_rue = _parse_civic_address(subject_address)
    if civic_ref is None or not nom_rue:
        logger.info("Impossible d'extraire no_civique depuis '%s'", subject_address)
        _diag(
            diagnostics,
            "mamh",
            "empty",
            "Adresse non exploitable pour la recherche civique Montreal",
            stage="comparables_montreal",
            details={"address": subject_address},
        )
        return []

    rows = lookup_role_mtl_by_civic(csv_path, nom_rue_norm=nom_rue, civique_ref=civic_ref)
    if not rows:
        _diag(
            diagnostics,
            "mamh",
            "empty",
            "Aucune entree du role Montreal autour de l'adresse",
            stage="comparables_montreal",
            details={"street": nom_rue, "civic": civic_ref},
        )
        return []

    pool: list[dict] = []
    for row in rows[:max_candidates * 2]:
        # Distance approximative : geocoder l'adresse du comparable (cache 7j)
        comp_addr = f"{row.get('adresse_civique', '')} {row.get('nom_rue', '')}, Montréal, Québec"
        coords = geocode_address(comp_addr, cache_dir)
        if coords is None:
            # Fallback : distance inconnue = 0.5 km (neutre pour scoring)
            clat, clon, dist = subject_lat, subject_lon, 0.5
        else:
            clat, clon = coords
            from engine.infolot import _haversine_km
            dist = _haversine_km(subject_lat, subject_lon, clat, clon)

        lot = {"no_lot": None, "lat": clat, "lon": clon, "distance_km": dist}
        item = _pool_item_from_mamh_record(row, lot)
        pool.append(item)

    pool = _filter_by_type_and_surface(pool, subject_surface_m2, subject_type_bien)
    pool.sort(key=lambda x: x["distance_km"])
    _diag(
        diagnostics,
        "mamh",
        "ok" if pool else "empty",
        "Comparables MAMH Montreal retenus" if pool else "Aucun comparable MAMH Montreal retenu apres filtres",
        stage="comparables_montreal",
        details={"row_count": len(rows), "pool_count": len(pool)},
    )
    return pool[:max_candidates]


def _parse_civic_address(address: str) -> tuple[int | None, str]:
    """
    Extrait (no_civique, nom_rue_normalisé) depuis une adresse textuelle.
    Ex: "123 rue des Érables, Montréal" → (123, "rue des erables")
    Retourne (None, "") si parsing échoue.
    """
    import re
    address_clean = address.split(",")[0].strip()
    m = re.match(r"^(\d+)\s+(.+)$", address_clean)
    if not m:
        return None, ""
    try:
        civic = int(m.group(1))
    except ValueError:
        return None, ""
    rue = _norm(m.group(2))
    return civic, rue
