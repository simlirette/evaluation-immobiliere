"""Phase 5 T5.1–T5.4 — Multi-bureau : RLS tenant, dashboard directeur, metering.

DoD T5.2 : session_access_allowed bureau-aware (bureau_admin accède sessions bureau).
DoD T5.3 : bureau_dashboard_summary retourne stats par évaluateur.
DoD T5.4 : track_llm_usage incrémente compteur session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── T5.1+T5.2 : migrations (contenu SQL) ─────────────────────────────────────

def test_migration_007_bureaux_exists():
    migration = Path(__file__).resolve().parent.parent.parent / \
        "supabase" / "migrations" / "007_bureaux_tenant.sql"
    assert migration.exists()
    content = migration.read_text(encoding="utf-8")
    assert "create table" in content.lower() and "bureaux" in content
    assert "bureau_membres" in content
    assert "bureau_role" in content
    assert "my_bureau_id" in content
    assert "is_bureau_admin" in content


def test_migration_008_rls_tenant_exists():
    migration = Path(__file__).resolve().parent.parent.parent / \
        "supabase" / "migrations" / "008_rls_tenant.sql"
    assert migration.exists()
    content = migration.read_text(encoding="utf-8")
    assert "bureau_id" in content
    assert "dossiers_read_bureau" in content
    assert "sessions_read_bureau" in content


# ── T5.2 : session_access_allowed bureau-aware ────────────────────────────────

def test_session_access_owner():
    import api  # type: ignore
    session = {"owner_evaluator_id": "ea-001"}
    assert api.session_access_allowed(session, "ea-001") is True


def test_session_access_wrong_owner():
    import api  # type: ignore
    session = {"owner_evaluator_id": "ea-001"}
    assert api.session_access_allowed(session, "ea-002") is False


def test_session_access_bureau_admin():
    """Bureau admin accède aux sessions du même bureau."""
    import api  # type: ignore
    session = {"owner_evaluator_id": "ea-001", "bureau_id": "bureau-A"}
    # Un autre évaluateur du même bureau peut accéder si bureau_id match
    assert api.session_access_allowed(session, "ea-002", bureau_id="bureau-A") is True


def test_session_access_wrong_bureau():
    import api  # type: ignore
    session = {"owner_evaluator_id": "ea-001", "bureau_id": "bureau-A"}
    assert api.session_access_allowed(session, "ea-002", bureau_id="bureau-B") is False


def test_session_access_no_evaluator_id():
    import api  # type: ignore
    session = {"owner_evaluator_id": "ea-001"}
    assert api.session_access_allowed(session, "") is False


# ── T5.3 : bureau_dashboard_summary ──────────────────────────────────────────

def test_bureau_dashboard_no_bureau_id(tmp_path, monkeypatch):
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)
    result = api.bureau_dashboard_summary("")
    assert "error" in result


def test_bureau_dashboard_empty_bureau(tmp_path, monkeypatch):
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)
    result = api.bureau_dashboard_summary("bureau-X")
    assert result["bureau_id"] == "bureau-X"
    assert result["sessions"] == []
    assert result["stats"]["total"] == 0


def test_bureau_dashboard_with_sessions(tmp_path, monkeypatch):
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)

    # Créer 2 sessions du bureau A et 1 du bureau B
    for i, bureau in [("s001", "bureau-A"), ("s002", "bureau-A"), ("s003", "bureau-B")]:
        d = tmp_path / i
        d.mkdir()
        session = {
            "schema_version": "runtime_session_v1",
            "session_id": i,
            "bureau_id": bureau,
            "owner_evaluator_id": f"ea-{i}",
            "status": "COMPLETED" if i != "s003" else "RUNNING",
            "created_at_utc": "2026-01-01T00:00:00Z",
            "updated_at_utc": "2026-01-01T00:00:00Z",
            "session_dir": str(d),
        }
        (d / "session.json").write_text(json.dumps(session), encoding="utf-8")

    result = api.bureau_dashboard_summary("bureau-A")
    assert result["stats"]["total"] == 2
    assert result["stats"]["by_status"].get("COMPLETED", 0) == 2
    assert len(result["stats"]["by_evaluateur"]) == 2


# ── T5.4 : track_llm_usage ───────────────────────────────────────────────────

def test_track_llm_usage_no_session():
    """track_llm_usage est silencieux si session introuvable."""
    import api  # type: ignore
    api.track_llm_usage("session-inexistante", 100, 50, 0.001)  # no exception


def test_track_llm_usage_increments(tmp_path, monkeypatch):
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)

    session_id = "meter-test"
    d = tmp_path / session_id
    d.mkdir()
    session = {
        "schema_version": "runtime_session_v1",
        "session_id": session_id,
        "status": "RUNNING",
        "session_dir": str(d),
        "usage": {"llm_calls": 0, "llm_tokens_in": 0, "llm_tokens_out": 0, "llm_cost_usd": 0.0},
    }
    (d / "session.json").write_text(json.dumps(session), encoding="utf-8")

    api.track_llm_usage(session_id, 1000, 500, 0.005)
    api.track_llm_usage(session_id, 800, 400, 0.004)

    loaded = json.loads((d / "session.json").read_text(encoding="utf-8"))
    usage = loaded["usage"]
    assert usage["llm_calls"] == 2
    assert usage["llm_tokens_in"] == 1800
    assert usage["llm_tokens_out"] == 900
    assert abs(usage["llm_cost_usd"] - 0.009) < 0.001


def test_create_session_has_usage(tmp_path, monkeypatch):
    """create_session initialise le compteur usage."""
    import api  # type: ignore
    monkeypatch.setattr(api, "SESSIONS_DIR", tmp_path)
    session = api.create_session(owner_evaluator_id="ea-001")
    assert "usage" in session
    assert session["usage"]["llm_calls"] == 0
    assert session["usage"]["llm_cost_usd"] == 0.0
