from __future__ import annotations

from unittest.mock import MagicMock


def test_source_coverage_reports_degraded_when_source_fails():
    from engine.source_diagnostics import build_source_coverage, make_source_diagnostic

    diagnostics = [
        make_source_diagnostic("geocoding", "ok", "ok", stage="test"),
        make_source_diagnostic("infolot", "failed", "timeout", stage="test"),
    ]

    coverage = build_source_coverage(diagnostics)

    assert coverage["status"] == "degraded"
    assert coverage["available_count"] == 1
    assert coverage["failed_count"] == 1
    assert coverage["source_statuses"]["infolot"] == "failed"


def test_infolot_records_wfs_timeout(tmp_path, monkeypatch):
    import httpx
    from engine.infolot import fetch_lots_in_radius

    def fail_get(*_args, **_kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "get", fail_get)
    diagnostics: list[dict] = []

    lots = fetch_lots_in_radius(45.5, -73.6, 1.0, tmp_path, diagnostics=diagnostics)

    assert lots == []
    assert diagnostics[-1]["source"] == "infolot"
    assert diagnostics[-1]["status"] == "failed"
    assert "TimeoutException" in diagnostics[-1]["details"]["error"]


def test_infolot_records_empty_when_wfs_features_cannot_be_used(tmp_path, monkeypatch):
    import httpx
    from engine.infolot import fetch_lots_in_radius

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "features": [
            {
                "properties": {"NOLOT": "1234567"},
                "geometry": {"type": "Point", "coordinates": [-73.6, 45.5]},
            }
        ]
    }
    monkeypatch.setattr(httpx, "get", lambda *_args, **_kwargs: response)
    diagnostics: list[dict] = []

    lots = fetch_lots_in_radius(45.5, -73.6, 1.0, tmp_path, diagnostics=diagnostics)

    assert lots == []
    assert diagnostics[-1]["source"] == "infolot"
    assert diagnostics[-1]["status"] == "empty"
    assert diagnostics[-1]["details"]["feature_count"] == 1


def test_comparable_builder_records_missing_mamh_index(tmp_path, monkeypatch):
    from engine import data_enrichment
    from engine.comparables_builder import build_comparable_pool

    monkeypatch.setattr(data_enrichment, "geocode_address", lambda *_args, **_kwargs: (45.5, -73.6))
    diagnostics: list[dict] = []

    pool = build_comparable_pool(
        "123 rue Principale, Laval",
        cache_dir=tmp_path,
        diagnostics=diagnostics,
    )

    assert pool == []
    assert any(
        d["source"] == "mamh"
        and d["status"] == "skipped"
        and "Index MAMH absent" in d["message"]
        for d in diagnostics
    )


def test_sirf_records_missing_credentials_without_breaking_pool(tmp_path, monkeypatch):
    from engine.registre_foncier import enrich_pool_with_sirf

    monkeypatch.delenv("SIRF_USERNAME", raising=False)
    monkeypatch.delenv("SIRF_PASSWORD", raising=False)
    pool = [{"no_lot": 1234567, "prix_vente": 0.0, "date_vente": "", "source_type": "role_evaluation_municipale"}]
    diagnostics: list[dict] = []

    result = enrich_pool_with_sirf(
        pool,
        cache_dir=tmp_path,
        supabase_client=None,
        max_sirf_lookups=1,
        diagnostics=diagnostics,
    )

    assert result[0]["prix_vente"] == 0.0
    assert diagnostics[-1]["source"] == "sirf"
    assert diagnostics[-1]["status"] == "failed"
    assert diagnostics[-1]["details"]["error_count"] == 1
