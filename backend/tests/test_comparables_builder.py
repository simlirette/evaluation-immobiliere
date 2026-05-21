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


import math
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
