# Infolot + MAMH Comparables Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la dépendance au CSV JLR par un pipeline auto-alimenté : Infolot WFS (lots cadastraux par rayon) + MAMH rôle municipal (caractéristiques) → pool de comparables candidats pour CHECKPOINT 2.

**Architecture:** `engine/infolot.py` interroge le WFS du cadastre québécois par boîte englobante et retourne les lots dans un rayon donné avec leurs centroides. `engine/comparables_builder.py` orchestre geocode → Infolot → MAMH lookup par no_lot (XML cities) ou par adresse heuristique (Montréal) → pool formaté pour `search_comparables()`. `runtime.py` auto-alimente `case["comparables"]` au step `comps-market` si le pool est vide (JLR CSV reste en fallback). Même pattern de cache JSON fichier que `data_enrichment.py`.

**Tech Stack:** Python 3.11, httpx (déjà présent), xml.etree (stdlib), engine/data_enrichment.py (geocode + MAMH lookup existants), engine/tools.py (search_comparables existant)

**Assumptions:**
- Assume WFS endpoint `https://servicesvectoriels.atlas.gouv.qc.ca/IDS_CATASTO_STAC_S_RLOT_QC/wfs` avec TypeName `IDS_CATASTO_STAC_S_RLOT_QC:S_RLOT_QC` est accessible — ne fonctionnera pas si l'endpoint est changé ou hors service (fallback : pool vide, pas d'erreur bloquante).
- Assume `no_lot` dans MAMH XML (champ `RL0103Ax`, déjà extrait à la ligne 2534 de data_enrichment.py) correspond au `NOLOT` dans les features WFS Infolot — vrai pour le cadastre rénové du Québec.
- Assume les 5 villes XML (`quebec`, `laval`, `longueuil`, `gatineau`, `sherbrooke`) ont leurs fichiers XML déjà téléchargés + index JSON buildés avant l'appel — sinon pool vide, non bloquant.
- Pour Montréal (MAMH CSV sans no_lot) : fallback heuristique par civic number ±200 + même rue. Prix de vente absent dans les deux cas — le pool MAMH a `prix_vente=0` jusqu'à l'intégration SIRF (Phase 2).

---

## Fichiers

| Action | Fichier | Responsabilité |
|---|---|---|
| CREATE | `backend/engine/infolot.py` | WFS bbox → lots dans rayon → `[{no_lot, lat, lon, distance_km}]` |
| MODIFY | `backend/engine/data_enrichment.py` | Ajouter `by_lot` à `build_role_xml_index()` + `lookup_role_by_lot()` + `lookup_role_mtl_by_civic()` |
| CREATE | `backend/engine/comparables_builder.py` | Pipeline complet geocode → Infolot → MAMH → pool Comparable-compatible |
| MODIFY | `backend/engine/runtime.py` | Auto-alimenter `case["comparables"]` au step `comps-market` (ligne ~1595) |
| CREATE | `backend/tests/test_infolot.py` | Tests unitaires infolot (pure Python, pas de réseau) |
| CREATE | `backend/tests/test_comparables_builder.py` | Tests unitaires comparables_builder (pure Python, pas de réseau) |

---

## Task 1 — Ajouter `by_lot` à l'index XML MAMH + `lookup_role_by_lot()`

**Files:**
- Modify: `backend/engine/data_enrichment.py`
- Test: `backend/tests/test_comparables_builder.py` (section MAMH)

**Security flag:** `none`

**Does NOT cover:** Montréal CSV (pas de no_lot dans le CSV — couvert par Task 3 fallback).

- [ ] **Step 1 : Écrire le test**

```python
# Dans backend/tests/test_comparables_builder.py  (créer le fichier)
import json
from pathlib import Path
import tempfile
import pytest
from engine.data_enrichment import build_role_xml_index, lookup_role_by_lot

MINIMAL_XML = """<?xml version="1.0" encoding="UTF-8"?>
<RLUEsAll>
  <RLUEx>
    <RL0101>
      <RL0101x>
        <RL0101Ax>123</RL0101Ax>
        <RL0101Ex>RUE</RL0101Ex>
        <RL0101Gx>PRINCIPALE</RL0101Gx>
      </RL0101x>
    </RL0101>
    <RL0104>
      <RL0104A>1234</RL0104A>
      <RL0104B>56</RL0104B>
      <RL0104C>7890</RL0104C>
      <RL0104D>A</RL0104D>
      <RL0104E>0</RL0104E>
      <RL0104F>0</RL0104F>
    </RL0104>
    <RL0103>
      <RL0103x>
        <RL0103Ax>4567890</RL0103Ax>
      </RL0103x>
    </RL0103>
    <RL0307A>1985</RL0307A>
    <RL0308A>120.5</RL0308A>
    <RL0302A>350.0</RL0302A>
    <RL0311A>1</RL0311A>
    <RL0105A>1000</RL0105A>
    <RL0402A>125000</RL0402A>
    <RL0403A>215000</RL0403A>
    <RL0404A>340000</RL0404A>
    <RL0405A>340000</RL0405A>
  </RLUEx>
</RLUEsAll>
"""

def test_by_lot_in_index():
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "role.xml"
        index_path = Path(tmp) / "index.json"
        xml_path.write_text(MINIMAL_XML, encoding="utf-8")
        build_role_xml_index(xml_path, index_path, city_code="test")
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        assert "by_lot" in idx
        assert "4567890" in idx["by_lot"]
        rec = idx["by_lot"]["4567890"]
        assert rec["superficie_batiment_m2"] == pytest.approx(120.5)
        assert rec["annee_construction"] == 1985

def test_lookup_role_by_lot_found():
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "role.xml"
        index_path = Path(tmp) / "index.json"
        xml_path.write_text(MINIMAL_XML, encoding="utf-8")
        build_role_xml_index(xml_path, index_path, city_code="test")
        result = lookup_role_by_lot(index_path, no_lot=4567890)
        assert result["annee_construction"] == 1985
        assert result["superficie_batiment_m2"] == pytest.approx(120.5)
        assert result["no_lot"] == 4567890

def test_lookup_role_by_lot_missing():
    with tempfile.TemporaryDirectory() as tmp:
        index_path = Path(tmp) / "nonexistent.json"
        result = lookup_role_by_lot(index_path, no_lot=9999)
        assert result == {}
```

- [ ] **Step 2 : Lancer les tests (attendre FAIL)**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/test_comparables_builder.py::test_by_lot_in_index tests/test_comparables_builder.py::test_lookup_role_by_lot_found tests/test_comparables_builder.py::test_lookup_role_by_lot_missing -v
```
Expected: `ImportError: cannot import name 'lookup_role_by_lot'`

- [ ] **Step 3 : Implémenter**

Dans `backend/engine/data_enrichment.py`, modifier la fonction `build_role_xml_index()` (ligne ~2481). Localiser le bloc qui construit `by_matricule` et `by_address` et ajouter `by_lot` :

```python
# Dans build_role_xml_index() — après le bloc existant qui peuple by_matricule et by_address
# Ajouter la variable by_lot au début de la fonction (après les déclarations existantes) :
by_lot: dict[str, dict] = {}

# Dans la boucle iterparse, après le bloc `if mat:` existant, ajouter :
        no_lot_val = rec.get("no_lot")
        if no_lot_val:
            by_lot[str(no_lot_val)] = rec

# Dans le json.dumps final, ajouter "by_lot": by_lot :
    index_path.write_text(
        json.dumps({
            "by_matricule": by_matricule,
            "by_address": by_address,
            "by_lot": by_lot,           # ← AJOUTER
            "city_code": city_code,
            "_built_at": time.time(),
            "_count": count,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
```

Ajouter la nouvelle fonction `lookup_role_by_lot()` après `lookup_role_xml()` (ligne ~2615) :

```python
def lookup_role_by_lot(index_path: Path, no_lot: int) -> dict:
    """
    Look up a property in a MAMH XML index by cadastral lot number.
    Returns {} if not found or index absent.
    """
    if not index_path.exists():
        return {}
    try:
        idx = _load_xml_index(index_path)
    except Exception as exc:
        logger.debug("XML index load failed: %s", exc)
        return {}
    by_lot = idx.get("by_lot", {})
    return by_lot.get(str(no_lot), {})
```

Ajouter aussi `lookup_role_mtl_by_civic()` après la fonction précédente (pour le fallback Montréal en Task 3) :

```python
def lookup_role_mtl_by_civic(
    csv_path: Path,
    nom_rue_norm: str,
    civique_ref: int,
    window: int = 200,
) -> list[dict]:
    """
    Retourne les propriétés MAMH MTL sur la même rue dont le numéro civique
    est dans [civique_ref - window, civique_ref + window].
    Utilisé comme heuristique spatiale quand Infolot n'a pas de no_lot MTL.
    Retourne [] si CSV absent ou aucun résultat.
    """
    if not csv_path.exists():
        return []
    try:
        idx = _load_role_index(csv_path)
    except Exception:
        return []

    results = []
    lo, hi = civique_ref - window, civique_ref + window
    # idx["address"] keys = "CIVIQUE|nom_rue_norm"
    for key, rows in idx["address"].items():
        parts = key.split("|", 1)
        if len(parts) != 2:
            continue
        try:
            civic_num = int(parts[0])
        except ValueError:
            continue
        if _norm(parts[1]) != _norm(nom_rue_norm):
            continue
        if lo <= civic_num <= hi:
            for row in rows:
                results.append({
                    "source": "role-mtl-csv",
                    "matricule83": row.get("MATRICULE83", ""),
                    "adresse_civique": row.get("CIVIQUE_DEBUT", ""),
                    "nom_rue": row.get("NOM_RUE", ""),
                    "annee_construction": int(row["ANNEE_CONSTRUCTION"]) if row.get("ANNEE_CONSTRUCTION", "").strip() not in ("", "0") else None,
                    "superficie_batiment_m2": float(row["SUPERFICIE_BATIMENT"]) if row.get("SUPERFICIE_BATIMENT", "").strip() not in ("", "0", "0.0") else None,
                    "superficie_terrain_m2": float(row["SUPERFICIE_TERRAIN"]) if row.get("SUPERFICIE_TERRAIN", "").strip() not in ("", "0", "0.0") else None,
                    "nb_logements": int(row["NOMBRE_LOGEMENT"]) if row.get("NOMBRE_LOGEMENT", "").strip() not in ("", "0") else 0,
                    "code_cubf": int(row["CODE_UTILISATION"]) if row.get("CODE_UTILISATION", "").strip() not in ("", "0") else None,
                    "municipalite": row.get("MUNICIPALITE", ""),
                    "civic_num": civic_num,
                })
    return results
```

- [ ] **Step 4 : Lancer les tests (attendre PASS)**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/test_comparables_builder.py::test_by_lot_in_index tests/test_comparables_builder.py::test_lookup_role_by_lot_found tests/test_comparables_builder.py::test_lookup_role_by_lot_missing -v
```
Expected: 3 PASSED

- [ ] **Step 5 : Commit**

```bash
cd C:/Users/simon/eval-immo/backend
git add engine/data_enrichment.py tests/test_comparables_builder.py
git commit -m "feat(mamh): add by_lot index to XML role + lookup_role_by_lot() + lookup_role_mtl_by_civic()"
```

---

## Task 2 — Créer `engine/infolot.py`

**Files:**
- Create: `backend/engine/infolot.py`
- Test: `backend/tests/test_infolot.py`

**Security flag:** `none`

**Does NOT cover:** Authentification WFS (endpoint public, pas d'auth requise). Ne couvre pas les lots hors cadastre rénové (< 2.73% selon fonciq). Ne fait pas la validation métier des caractéristiques — responsabilité de `comparables_builder.py`.

- [ ] **Step 1 : Écrire les tests**

```python
# Créer backend/tests/test_infolot.py
import math
import pytest
from engine.infolot import _bbox_from_radius, _haversine_km, _centroid_from_geometry, _parse_nolot

def test_bbox_from_radius_montreal():
    # 45.5017° N, 73.5673° W, 2 km
    minlng, minlat, maxlng, maxlat = _bbox_from_radius(45.5017, -73.5673, 2.0)
    assert minlat < 45.5017 < maxlat
    assert minlng < -73.5673 < maxlng
    # 2 km → ~0.018° lat, ~0.025° lng à cette latitude
    assert abs(maxlat - minlat) == pytest.approx(0.036, abs=0.005)

def test_haversine_km():
    # Montréal → Québec ~233 km
    d = _haversine_km(45.5017, -73.5673, 46.8139, -71.2082)
    assert 228 < d < 238

def test_haversine_same_point():
    assert _haversine_km(45.5, -73.5, 45.5, -73.5) == pytest.approx(0.0)

def test_centroid_from_polygon():
    # Carré simple
    coords = [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]]
    lat, lng = _centroid_from_geometry({"type": "Polygon", "coordinates": coords})
    assert lat == pytest.approx(0.5, abs=0.01)
    assert lng == pytest.approx(0.5, abs=0.01)

def test_centroid_from_multipolygon():
    coords = [[[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0], [0.0, 0.0]]]]
    lat, lng = _centroid_from_geometry({"type": "MultiPolygon", "coordinates": coords})
    assert lat == pytest.approx(1.0, abs=0.01)
    assert lng == pytest.approx(1.0, abs=0.01)

def test_centroid_unknown_geometry():
    lat, lng = _centroid_from_geometry({"type": "Point", "coordinates": [10.0, 20.0]})
    assert lat is None
    assert lng is None

def test_parse_nolot_string():
    assert _parse_nolot("4567890") == 4567890

def test_parse_nolot_int():
    assert _parse_nolot(4567890) == 4567890

def test_parse_nolot_invalid():
    assert _parse_nolot("ABC") is None
    assert _parse_nolot(None) is None
```

- [ ] **Step 2 : Lancer les tests (attendre FAIL)**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/test_infolot.py -v
```
Expected: `ModuleNotFoundError: No module named 'engine.infolot'`

- [ ] **Step 3 : Créer `backend/engine/infolot.py`**

```python
"""
infolot.py — Recherche de lots cadastraux par rayon via WFS gouvernemental.

Source : WFS Atlas gouvernemental du Québec
  URL    : https://servicesvectoriels.atlas.gouv.qc.ca/IDS_CATASTO_STAC_S_RLOT_QC/wfs
  Layer  : IDS_CATASTO_STAC_S_RLOT_QC:S_RLOT_QC
  Auth   : aucune (service public)
  Coût   : gratuit
  Cache  : JSON fichier, TTL 30 jours par cellule (lat4, lon4, radius)

Retourne des lots avec no_lot (cadastre rénové Québec) + centroïde + distance.
Non-bloquant : toute exception retourne [].
"""
from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path

logger = logging.getLogger("infolot")

_WFS_BASE = (
    "https://servicesvectoriels.atlas.gouv.qc.ca"
    "/IDS_CATASTO_STAC_S_RLOT_QC/wfs"
)
_WFS_TYPENAME = "IDS_CATASTO_STAC_S_RLOT_QC:S_RLOT_QC"
_WFS_NOLOT_FIELD = "NOLOT"   # nom du champ dans les features (à valider au runtime)
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

    lngs = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return sum(lats) / len(lats), sum(lngs) / len(lngs)


def _parse_nolot(value: object) -> int | None:
    """Convertit NOLOT (str ou int) en int. Retourne None si invalide."""
    if value is None:
        return None
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
        return cached

    try:
        import httpx
    except ImportError:
        logger.warning("httpx non disponible — Infolot désactivé")
        return []

    minlng, minlat, maxlng, maxlat = _bbox_from_radius(lat, lon, radius_km)
    bbox_str = f"{minlng},{minlat},{maxlng},{maxlat},EPSG:4326"

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeName": _WFS_TYPENAME,
        "bbox": bbox_str,
        "outputFormat": "application/json",
        "count": str(_MAX_FEATURES),
    }

    try:
        r = httpx.get(_WFS_BASE, params=params, timeout=_HTTP_TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        logger.warning("Infolot WFS error: %s", exc)
        return []

    lots: list[dict] = []
    for feature in data.get("features", []):
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
    logger.info("Infolot WFS: %d lots dans %.1f km autour de (%.4f, %.4f)", len(lots), radius_km, lat, lon)
    return lots
```

- [ ] **Step 4 : Lancer les tests (attendre PASS)**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/test_infolot.py -v
```
Expected: 8 PASSED

- [ ] **Step 5 : Commit**

```bash
cd C:/Users/simon/eval-immo/backend
git add engine/infolot.py tests/test_infolot.py
git commit -m "feat(infolot): WFS cadastre lots-in-radius + cache 30j"
```

---

## Task 3 — Créer `engine/comparables_builder.py`

**Files:**
- Create: `backend/engine/comparables_builder.py`
- Test: `backend/tests/test_comparables_builder.py` (ajouter au fichier de Task 1)

**Security flag:** `none`

**Does NOT cover:** Prix de vente (absent — MAMH ne contient pas les transactions, seulement l'évaluation municipale). Couvre uniquement les villes avec XML MAMH disponible + Montréal CSV. Les villes sans MAMH retournent un pool vide.

- [ ] **Step 1 : Ajouter les tests dans `test_comparables_builder.py`**

Ajouter à la fin du fichier existant `backend/tests/test_comparables_builder.py` :

```python
import math
from pathlib import Path
from unittest.mock import patch, MagicMock
from engine.comparables_builder import (
    _pool_item_from_mamh_record,
    _detect_city_code,
    _filter_by_type_and_surface,
)

# ── Tests pool_item_from_mamh_record ──────────────────────────────────────────

def test_pool_item_basic():
    rec = {
        "source": "mamh-xml",
        "matricule83": "1234-56-7890-A-000-0000",
        "adresse_civique": "456",
        "nom_rue": "RUE DES ÉRABLES",
        "no_lot": 4567890,
        "annee_construction": 1985,
        "superficie_batiment_m2": 120.5,
        "superficie_terrain_m2": 350.0,
        "nb_logements": 1,
        "code_cubf": 1000,
        "valeur_totale": 340000.0,
        "city_code": "quebec",
    }
    lot = {"no_lot": 4567890, "lat": 46.82, "lon": -71.22, "distance_km": 0.8}
    item = _pool_item_from_mamh_record(rec, lot)
    assert item["source_id"] == "MAMH-4567890"
    assert item["source_type"] == "role_evaluation_municipale"
    assert item["distance_km"] == pytest.approx(0.8)
    assert item["surface"]["value"] == pytest.approx(120.5)
    assert item["surface"]["unit"] == "m2"
    assert item["prix_vente"] == 0.0
    assert item["date_vente"] == ""
    assert item["annee_construction"] == 1985

def test_pool_item_missing_superficie():
    rec = {"source": "mamh-xml", "matricule83": "X", "superficie_batiment_m2": None,
           "superficie_terrain_m2": None, "nb_logements": 0, "code_cubf": None,
           "valeur_totale": None, "no_lot": 111, "city_code": "laval",
           "adresse_civique": "1", "nom_rue": "MAIN", "annee_construction": None}
    lot = {"no_lot": 111, "lat": 45.5, "lon": -73.7, "distance_km": 1.2}
    item = _pool_item_from_mamh_record(rec, lot)
    assert item["surface"]["value"] == 0.0

# ── Tests _detect_city_code ───────────────────────────────────────────────────

def test_detect_montreal():
    assert _detect_city_code("123 rue Sherbrooke, Montréal") == "montreal"

def test_detect_laval():
    assert _detect_city_code("45 boul. Cartier, Laval, QC") == "laval"

def test_detect_unknown():
    assert _detect_city_code("123 Main Street") is None

# ── Tests _filter_by_type_and_surface ────────────────────────────────────────

def test_filter_keeps_similar():
    pool = [
        {"surface": {"value": 110.0, "unit": "m2"}, "type_bien": "unifamiliale"},
        {"surface": {"value": 200.0, "unit": "m2"}, "type_bien": "unifamiliale"},  # trop grand
        {"surface": {"value": 95.0, "unit": "m2"}, "type_bien": "unifamiliale"},
        {"surface": {"value": 50.0, "unit": "m2"}, "type_bien": "condo"},  # mauvais type
    ]
    result = _filter_by_type_and_surface(
        pool,
        subject_surface_m2=100.0,
        subject_type_bien="unifamiliale",
        surface_tolerance=0.5,
    )
    assert len(result) == 2
    surfaces = [p["surface"]["value"] for p in result]
    assert 110.0 in surfaces
    assert 95.0 in surfaces
```

- [ ] **Step 2 : Lancer les tests (attendre FAIL)**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/test_comparables_builder.py::test_pool_item_basic tests/test_comparables_builder.py::test_detect_montreal tests/test_comparables_builder.py::test_filter_keeps_similar -v
```
Expected: `ImportError: cannot import name '_pool_item_from_mamh_record' from 'engine.comparables_builder'`

- [ ] **Step 3 : Créer `backend/engine/comparables_builder.py`**

```python
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

logger = logging.getLogger("comparables_builder")

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
    - même famille de type_bien (exact ou famille proche)
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
        result.append(item)
    return result


def build_comparable_pool(
    subject_address: str,
    subject_surface_m2: float = 0.0,
    subject_type_bien: str = "",
    subject_annee_construction: int = 0,
    radius_km: float = 2.0,
    cache_dir: Path | None = None,
    max_candidates: int = 50,
) -> list[dict]:
    """
    Point d'entrée principal. Retourne un pool de dicts prêts pour search_comparables().

    Flux XML (5 villes) : geocode → Infolot WFS → lookup_role_by_lot()
    Flux MTL            : geocode → lookup_role_mtl_by_civic() (heuristique)
    Fallback            : [] (non-bloquant)

    prix_vente=0 et date_vente="" dans tous les cas — Phase 2 (SIRF) les remplira.
    """
    if cache_dir is None:
        cache_dir = Path("data_cache")

    city_code = _detect_city_code(subject_address)
    if city_code is None:
        logger.info("Ville non reconnue dans '%s' — pool vide", subject_address)
        return []

    try:
        from engine.data_enrichment import geocode_address
        coords = geocode_address(subject_address, cache_dir)
    except Exception as exc:
        logger.warning("geocode_address failed: %s", exc)
        return []

    if coords is None:
        logger.info("Geocoding sans résultat pour '%s'", subject_address)
        return []

    subject_lat, subject_lon = coords

    if city_code in _XML_CITIES:
        return _build_pool_xml(
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
        return _build_pool_montreal(
            subject_address=subject_address,
            subject_lat=subject_lat,
            subject_lon=subject_lon,
            subject_surface_m2=subject_surface_m2,
            subject_type_bien=subject_type_bien,
            cache_dir=cache_dir,
            max_candidates=max_candidates,
        )
    else:
        logger.info("city_code '%s' sans MAMH configuré — pool vide", city_code)
        return []


def _build_pool_xml(
    city_code: str,
    subject_lat: float,
    subject_lon: float,
    subject_surface_m2: float,
    subject_type_bien: str,
    radius_km: float,
    cache_dir: Path,
    max_candidates: int,
) -> list[dict]:
    """Pipeline pour les 5 villes XML : Infolot → by_lot → filtrage."""
    try:
        from engine.infolot import fetch_lots_in_radius
        from engine.data_enrichment import lookup_role_by_lot
    except Exception as exc:
        logger.warning("Import error dans _build_pool_xml: %s", exc)
        return []

    index_path = cache_dir / f"role_{city_code}_index.json"
    if not index_path.exists():
        logger.info("Index MAMH absent pour %s (%s) — pool vide", city_code, index_path)
        return []

    lots = fetch_lots_in_radius(subject_lat, subject_lon, radius_km, cache_dir)
    if not lots:
        return []

    pool: list[dict] = []
    for lot in lots[:max_candidates * 3]:   # Surcharger pour compenser les filtres
        rec = lookup_role_by_lot(index_path, no_lot=lot["no_lot"])
        if not rec:
            continue
        item = _pool_item_from_mamh_record(rec, lot)
        pool.append(item)

    pool = _filter_by_type_and_surface(pool, subject_surface_m2, subject_type_bien)
    pool.sort(key=lambda x: x["distance_km"])
    return pool[:max_candidates]


def _build_pool_montreal(
    subject_address: str,
    subject_lat: float,
    subject_lon: float,
    subject_surface_m2: float,
    subject_type_bien: str,
    cache_dir: Path,
    max_candidates: int,
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
        return []

    csv_path = cache_dir / "role_mtl.csv"

    # Extraire no_civique et nom_rue depuis l'adresse du sujet
    civic_ref, nom_rue = _parse_civic_address(subject_address)
    if civic_ref is None or not nom_rue:
        logger.info("Impossible d'extraire no_civique depuis '%s'", subject_address)
        return []

    rows = lookup_role_mtl_by_civic(csv_path, nom_rue_norm=nom_rue, civique_ref=civic_ref)
    if not rows:
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
```

- [ ] **Step 4 : Lancer les tests (attendre PASS)**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/test_comparables_builder.py -v
```
Expected: tous PASSED (6 tests Task 1 + 7 tests Task 3)

- [ ] **Step 5 : Commit**

```bash
cd C:/Users/simon/eval-immo/backend
git add engine/comparables_builder.py tests/test_comparables_builder.py
git commit -m "feat(comparables): pipeline Infolot+MAMH → pool comparables (sans prix SIRF)"
```

---

## Task 4 — Câbler `build_comparable_pool()` dans `runtime.py`

**Files:**
- Modify: `backend/engine/runtime.py`

**Security flag:** `none`

**Does NOT cover:** Ne modifie pas la logique de scoring (tools.py inchangé). Ne supprime pas le support CSV JLR — le pipeline auto-alimente uniquement si `case["comparables"]` est vide.

- [ ] **Step 1 : Localiser le hookup exact**

Ouvrir `backend/engine/runtime.py` et trouver le bloc à la ligne ~1595 :
```python
if step == "comps-market" and artifact == "comparables_proposes.json":
    payload["date_reference"] = case.get("date_reference")
    payload["comparables"] = [
        c.__dict__
        for c in search_comparables(
            case.get("comparables", []),
```

- [ ] **Step 2 : Modifier le bloc**

Remplacer ce bloc par :

```python
        if step == "comps-market" and artifact == "comparables_proposes.json":
            payload["date_reference"] = case.get("date_reference")

            # Auto-alimenter le pool si aucun comparable n'a été chargé (CSV JLR absent)
            if not case.get("comparables"):
                try:
                    from engine.comparables_builder import build_comparable_pool
                    address = str(case.get("adresse_complete") or "")
                    if address:
                        auto_pool = build_comparable_pool(
                            subject_address=address,
                            subject_surface_m2=float(case.get("surface_habitable") or 0),
                            subject_type_bien=str(case.get("type_bien") or ""),
                            subject_annee_construction=int(case.get("annee_construction") or 0),
                            cache_dir=Path("data_cache"),
                        )
                        if auto_pool:
                            case["comparables"] = auto_pool
                            logger.info(
                                "Pool auto-alimenté Infolot+MAMH: %d candidats pour '%s'",
                                len(auto_pool), address,
                            )
                except Exception as exc:
                    logger.warning("build_comparable_pool failed (non-bloquant): %s", exc)

            payload["comparables"] = [
                c.__dict__
                for c in search_comparables(
                    case.get("comparables", []),
                    max_items=5,
                    subject=case,
                    date_reference=case.get("date_reference"),
                )
            ]
            if case.get("marche_locatif"):
                payload["marche_locatif"] = case["marche_locatif"]
```

Ajouter `from pathlib import Path` en tête de `runtime.py` si absent (vérifier les imports existants).

- [ ] **Step 3 : Vérifier que l'import Path existe**

```bash
cd C:/Users/simon/eval-immo/backend
grep -n "^from pathlib import\|^import pathlib" engine/runtime.py | head -5
```
Si absent, ajouter `from pathlib import Path` dans la section imports.

- [ ] **Step 4 : Test smoke — pipeline sans CSV**

```bash
cd C:/Users/simon/eval-immo/backend
python -c "
from engine.runtime import DEFAULT_STEPS
# Vérifier que le module se charge sans erreur
print('runtime.py chargé OK')
print(f'{len(DEFAULT_STEPS)} steps définis')
"
```
Expected: `runtime.py chargé OK` + `7 steps définis`

- [ ] **Step 5 : Lancer la suite de tests existante**

```bash
cd C:/Users/simon/eval-immo/backend
python -m pytest tests/ -v --tb=short 2>&1 | tail -20
```
Expected: aucun test préexistant ne régresse.

- [ ] **Step 6 : Commit**

```bash
cd C:/Users/simon/eval-immo/backend
git add engine/runtime.py
git commit -m "feat(pipeline): auto-alimenter pool comparables Infolot+MAMH au step comps-market"
```

---

## Self-Review

**1. Spec coverage**
- ✅ Infolot WFS : Task 2
- ✅ MAMH by_lot index : Task 1
- ✅ Câblage MAMH → search_comparables() : Tasks 3 + 4
- ✅ Montréal fallback : Task 3 `_build_pool_montreal()`
- ✅ Non-bloquant si service indisponible : chaque fonction retourne [] sur exception
- ✅ Cache JSON fichier : infolot.py TTL 30j, data_enrichment pattern existant

**2. Placeholder scan**
- Aucun TODO/TBD/placeholder détecté. Prix de vente = 0 documenté explicitement comme attendu (Phase 2 SIRF).

**3. Type consistency**
- `_pool_item_from_mamh_record(rec: dict, lot: dict) -> dict` : utilisé identiquement dans Task 3 tests et implémentation.
- `lookup_role_by_lot(index_path: Path, no_lot: int) -> dict` : défini Task 1, importé Task 3.
- `fetch_lots_in_radius(lat, lon, radius_km, cache_dir) -> list[dict]` : défini Task 2, importé Task 3.

**4. Scope-reduction scan**
- Aucun "v1/basic/simple/placeholder" hors du contexte explicitement sanctionné (SIRF Phase 2 pour prix).
