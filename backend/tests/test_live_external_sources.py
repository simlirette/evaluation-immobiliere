from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _live_enabled() -> bool:
    return os.environ.get("EVAL_IMMO_LIVE_EXTERNALS") == "1"


def _require_live() -> None:
    if not _live_enabled():
        pytest.skip("set EVAL_IMMO_LIVE_EXTERNALS=1 to run live external-source smoke tests")


def _float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        pytest.fail(f"{name} must be a float, got {value!r}")


def _int_env(name: str) -> int:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"set {name} to run this live smoke test")
    try:
        return int(value)
    except ValueError:
        pytest.fail(f"{name} must be an integer lot number, got {value!r}")


def test_live_infolot_wfs_returns_cadastral_lots(tmp_path):
    _require_live()

    from engine.infolot import fetch_lots_in_radius

    lat = _float_env("EVAL_IMMO_INFOL0T_LAT", 45.5450)
    lon = _float_env("EVAL_IMMO_INFOL0T_LON", -73.7450)
    radius_km = _float_env("EVAL_IMMO_INFOL0T_RADIUS_KM", 0.5)
    diagnostics: list[dict] = []

    lots = fetch_lots_in_radius(lat, lon, radius_km, tmp_path, diagnostics=diagnostics)

    assert lots, f"Infolot returned no lots for ({lat}, {lon}) radius={radius_km} km"
    assert all(isinstance(item.get("no_lot"), int) and item["no_lot"] > 0 for item in lots)
    assert all(float(item.get("distance_km", 999)) <= radius_km for item in lots)
    assert any(d.get("source") == "infolot" and d.get("status") == "ok" for d in diagnostics)


def test_live_mamh_cache_has_index_and_optional_lookup():
    _require_live()

    from engine.data_enrichment import get_data_cache_dir, lookup_role_by_lot, lookup_role_mtl

    cache_dir = get_data_cache_dir()
    if not os.environ.get("DATA_CACHE_DIR"):
        pytest.skip("set DATA_CACHE_DIR to the provisioned MAMH cache directory")
    if not cache_dir.exists():
        pytest.fail(f"DATA_CACHE_DIR does not exist: {cache_dir}")

    city = os.environ.get("EVAL_IMMO_MAMH_CITY", "laval").strip().lower()
    if city == "montreal":
        csv_path = cache_dir / "role_mtl.csv"
        assert csv_path.exists(), f"missing Montreal role CSV: {csv_path}"
        assert csv_path.stat().st_size > 1_000_000, f"Montreal role CSV looks too small: {csv_path}"
        matricule = os.environ.get("EVAL_IMMO_MAMH_TEST_MATRICULE")
        address = os.environ.get("EVAL_IMMO_MAMH_TEST_ADDRESS", "")
        if matricule or address:
            record = lookup_role_mtl(csv_path, matricule=matricule, display_name=address)
            assert record, "MAMH Montreal lookup returned no record for supplied test input"
        return

    index_path = cache_dir / f"role_{city}_index.json"
    assert index_path.exists(), f"missing MAMH XML index: {index_path}"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert data.get("city_code") == city
    assert int(data.get("_count") or 0) > 0
    assert isinstance(data.get("by_lot"), dict) and data["by_lot"]

    lot = os.environ.get("EVAL_IMMO_MAMH_TEST_LOT")
    if lot:
        record = lookup_role_by_lot(index_path, int(lot))
        assert record, f"MAMH lookup by lot returned no record for {lot}"


def test_live_sirf_enriches_known_lot(tmp_path):
    _require_live()
    if os.environ.get("EVAL_IMMO_LIVE_SIRF") != "1":
        pytest.skip("set EVAL_IMMO_LIVE_SIRF=1 to run paid SIRF smoke test")
    if not os.environ.get("SIRF_USERNAME") or not os.environ.get("SIRF_PASSWORD"):
        pytest.skip("set SIRF_USERNAME and SIRF_PASSWORD to run SIRF smoke test")

    from engine.registre_foncier import enrich_pool_with_sirf

    no_lot = _int_env("SIRF_TEST_LOT")
    diagnostics: list[dict] = []
    pool = [
        {
            "comparable_id": f"SMOKE-SIRF-{no_lot}",
            "source_id": f"SMOKE-SIRF-{no_lot}",
            "source_type": "role_evaluation_municipale",
            "no_lot": no_lot,
            "prix_vente": 0.0,
            "date_vente": "",
            "surface": {"value": 100.0, "unit": "m2"},
            "distance_km": 0.1,
        }
    ]

    result = enrich_pool_with_sirf(
        pool,
        cache_dir=tmp_path,
        supabase_client=None,
        max_sirf_lookups=1,
        diagnostics=diagnostics,
    )

    sirf_diag = next((d for d in diagnostics if d.get("source") == "sirf"), None)
    assert sirf_diag is not None
    assert sirf_diag.get("status") in {"ok", "partial"}
    assert result[0]["source_type"] == "registre_foncier"
    assert float(result[0]["prix_vente"]) > 0
    assert result[0]["date_vente"]
