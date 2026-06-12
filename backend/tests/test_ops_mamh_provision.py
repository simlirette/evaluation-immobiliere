"""Tests de l'endpoint de provisioning MAMH (/ops/mamh/provision)."""
from __future__ import annotations

import time

import api
import scripts.provision_mamh_cache as prov


def _wait_done(timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = api.ops_mamh_provision_status()
        if state.get("status") not in ("running",):
            return state
        time.sleep(0.05)
    raise AssertionError("provisioning n'a pas terminé dans le délai")


def _reset_state() -> None:
    with api._MAMH_PROVISION_GUARD:
        api._MAMH_PROVISION_STATE.clear()
        api._MAMH_PROVISION_STATE.update({"status": "idle"})


def test_status_initial_idle():
    _reset_state()
    assert api.ops_mamh_provision_status() == {"status": "idle"}


def test_start_runs_worker_and_reports_ok(monkeypatch, tmp_path):
    _reset_state()
    monkeypatch.setenv("DATA_CACHE_DIR", str(tmp_path))

    calls: dict = {}

    def fake_provision(cache_dir, *, include_montreal, xml_cities, force, skip_download=False):
        calls["cache_dir"] = cache_dir
        calls["include_montreal"] = include_montreal
        calls["xml_cities"] = list(xml_cities)
        calls["force"] = force
        return [
            {"source": "mamh-montreal-csv", "city_code": None, "status": "ok",
             "path": str(cache_dir / "role_mtl.csv"), "index_path": None,
             "indexed_count": None, "cache_hit": False, "index_status": None, "error": None},
        ]

    monkeypatch.setattr(prov, "provision_mamh_cache", fake_provision)

    started = api.ops_mamh_provision_start({"force": True})
    assert started["status"] == "running"
    assert started["force"] is True

    final = _wait_done()
    assert final["status"] == "ok"
    assert final["summary"]["ok_count"] == 1
    assert calls["include_montreal"] is True
    assert calls["force"] is True
    assert len(calls["xml_cities"]) >= 1  # toutes les villes XML supportées


def test_start_is_idempotent_while_running(monkeypatch, tmp_path):
    _reset_state()
    monkeypatch.setenv("DATA_CACHE_DIR", str(tmp_path))

    import threading
    release = threading.Event()

    def slow_provision(cache_dir, **kwargs):
        release.wait(timeout=5)
        return []

    monkeypatch.setattr(prov, "provision_mamh_cache", slow_provision)

    first = api.ops_mamh_provision_start({})
    assert first["status"] == "running"
    second = api.ops_mamh_provision_start({"force": True})
    assert second["status"] == "running"
    assert second["started_at"] == first["started_at"]  # pas de relance

    release.set()
    final = _wait_done()
    assert final["status"] == "ok"


def test_worker_failure_is_reported(monkeypatch, tmp_path):
    _reset_state()
    monkeypatch.setenv("DATA_CACHE_DIR", str(tmp_path))

    def boom(cache_dir, **kwargs):
        raise RuntimeError("réseau coupé")

    monkeypatch.setattr(prov, "provision_mamh_cache", boom)

    api.ops_mamh_provision_start({})
    final = _wait_done()
    assert final["status"] == "failed"
    assert "réseau coupé" in final["error"]
