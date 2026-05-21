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
