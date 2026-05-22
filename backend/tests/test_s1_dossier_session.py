"""S1 tests — Séparation Dossier / Session.

Couvre :
- _find_session_for_dossier()
- load_session() fallback dossier_id
- _archive_stale_sessions()
- app_dossier_card_from_record() — slug/id = dossier_id
- app_state() — déduplication par dossier_id, slug ≠ session_id
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from api import (
    _find_session_for_dossier,
    _archive_stale_sessions,
    app_dossier_card_from_record,
    app_state,
    load_session,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_session(
    tmp_path: Path,
    session_id: str,
    dossier_id: str,
    display_name: str = "123 rue Test",
    archived: bool = False,
    review_decision: str = "A_SAISIR",
    created_at: str | None = None,
) -> Path:
    """Write a minimal session.json into tmp_path/{session_id}/."""
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    now = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    data = {
        "schema_version": "runtime_session_v1",
        "session_id": session_id,
        "dossier_id": dossier_id,
        "app_display_name": display_name,
        "app_property_type": "residentiel_unifamilial",
        "app_neighborhood": "Plateau",
        "status": "PRET_REVISION_FINALE",
        "created_at_utc": now,
        "updated_at_utc": now,
        "session_dir": str(session_dir),
        "review_decision": review_decision,
    }
    if archived:
        data["app_archived"] = True
    (session_dir / "session.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
    return session_dir


# ── _find_session_for_dossier ────────────────────────────────────────────────

class TestFindSessionForDossier:
    def test_returns_none_for_empty_dir(self, tmp_path):
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _find_session_for_dossier("D-USR-ABCD1234") is None

    def test_returns_none_for_unknown_dossier(self, tmp_path):
        _make_session(tmp_path, "aaa111bbb222", "D-USR-KNOWN0001")
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _find_session_for_dossier("D-USR-UNKNOWN") is None

    def test_finds_matching_session(self, tmp_path):
        _make_session(tmp_path, "abc123def456", "D-USR-TARGET01")
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = _find_session_for_dossier("D-USR-TARGET01")
        assert result == "abc123def456"

    def test_returns_most_recent_session(self, tmp_path):
        older = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        newer = datetime.now(timezone.utc).isoformat()
        _make_session(tmp_path, "oldsession0aa", "D-USR-MULTI001", created_at=older)
        _make_session(tmp_path, "newsession0bb", "D-USR-MULTI001", created_at=newer)
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = _find_session_for_dossier("D-USR-MULTI001")
        assert result == "newsession0bb"

    def test_skips_archived_sessions(self, tmp_path):
        _make_session(tmp_path, "archived000aa", "D-USR-ARCH0001", archived=True)
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _find_session_for_dossier("D-USR-ARCH0001") is None

    def test_returns_active_when_archived_and_active_exist(self, tmp_path):
        older = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        _make_session(tmp_path, "archivedold0a", "D-USR-MIX00001", archived=True, created_at=older)
        _make_session(tmp_path, "activenew00bb", "D-USR-MIX00001", archived=False)
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = _find_session_for_dossier("D-USR-MIX00001")
        assert result == "activenew00bb"


# ── load_session fallback ────────────────────────────────────────────────────

class TestLoadSessionDossierFallback:
    def test_returns_none_for_unknown_dossier_id(self, tmp_path):
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert load_session("D-USR-NOTFOUND") is None

    def test_resolves_dossier_id_to_session(self, tmp_path):
        _make_session(tmp_path, "res123abc456", "D-USR-RESOLVE1")
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            session = load_session("D-USR-RESOLVE1")
        assert session is not None
        assert session["session_id"] == "res123abc456"
        assert session["dossier_id"] == "D-USR-RESOLVE1"

    def test_direct_session_id_still_works(self, tmp_path):
        _make_session(tmp_path, "directhex012", "D-USR-DIRECT01")
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            session = load_session("directhex012")
        assert session is not None
        assert session["session_id"] == "directhex012"

    def test_no_dash_id_does_not_trigger_fallback(self, tmp_path):
        # ID without dash → no fallback scan, returns None quickly
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert load_session("nonexisthex0") is None


# ── app_dossier_card_from_record ─────────────────────────────────────────────

class TestAppDossierCardFromRecord:
    def _record(self, session_id: str, dossier_id: str, name: str = "1 rue Example") -> dict:
        return {
            "session_id": session_id,
            "dossier_id": dossier_id,
            "app_display_name": name,
            "app_property_type": "residentiel_unifamilial",
            "app_neighborhood": "Rosemont",
            "status": "PRET_REVISION_FINALE",
            "updated_at_utc": "2026-05-20T10:00:00+00:00",
            "pinned": False,
        }

    def test_slug_is_dossier_id(self):
        card = app_dossier_card_from_record(
            self._record("hexsession0ab", "D-USR-SLUG0001")
        )
        assert card["slug"] == "D-USR-SLUG0001"

    def test_id_is_dossier_id(self):
        card = app_dossier_card_from_record(
            self._record("hexsession0ab", "D-USR-ID000001")
        )
        assert card["id"] == "D-USR-ID000001"

    def test_session_id_preserved_internally(self):
        card = app_dossier_card_from_record(
            self._record("hexsession0ab", "D-USR-KEEP0001")
        )
        assert card["session_id"] == "hexsession0ab"

    def test_slug_differs_from_session_id(self):
        card = app_dossier_card_from_record(
            self._record("hexsession0ab", "D-USR-DIFF0001")
        )
        assert card["slug"] != card["session_id"]

    def test_fallback_when_no_dossier_id(self):
        # Old sessions without dossier_id: slug falls back to session_id
        record = {
            "session_id": "oldhexses0000",
            "app_display_name": "Vieux dossier",
            "status": "CREATED",
            "updated_at_utc": "",
        }
        card = app_dossier_card_from_record(record)
        assert card["slug"] == "oldhexses0000"
        assert card["id"] == "oldhexses0000"


# ── _archive_stale_sessions ──────────────────────────────────────────────────

class TestArchiveStaleSessions:
    def test_no_sessions_returns_zero(self, tmp_path):
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _archive_stale_sessions() == 0

    def test_fresh_sessions_not_archived(self, tmp_path):
        _make_session(tmp_path, "freshsess00aa", "D-USR-FRESH001")
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _archive_stale_sessions() == 0

    def test_stale_session_gets_archived(self, tmp_path):
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        _make_session(tmp_path, "stalesess00aa", "D-USR-STALE001", created_at=old_date)
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            count = _archive_stale_sessions()
        assert count == 1
        session_data = json.loads((tmp_path / "stalesess00aa" / "session.json").read_text())
        assert session_data.get("app_archived") is True

    def test_validated_session_not_archived(self, tmp_path):
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        _make_session(
            tmp_path, "validsess00aa", "D-USR-VALID001",
            review_decision="VALIDE", created_at=old_date,
        )
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _archive_stale_sessions() == 0

    def test_already_archived_not_counted(self, tmp_path):
        old_date = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        _make_session(
            tmp_path, "alreadyarch0aa", "D-USR-ARCH0002",
            archived=True, created_at=old_date,
        )
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert _archive_stale_sessions() == 0

    def test_archives_only_stale_leaves_fresh(self, tmp_path):
        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        _make_session(tmp_path, "stalesess00bb", "D-USR-STALE002", created_at=old_date)
        _make_session(tmp_path, "freshsess00bb", "D-USR-FRESH002")
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            count = _archive_stale_sessions()
        assert count == 1
        fresh_data = json.loads((tmp_path / "freshsess00bb" / "session.json").read_text())
        assert not fresh_data.get("app_archived")


# ── app_state deduplication ──────────────────────────────────────────────────

class TestAppStateDedup:
    def _fake_session_records(self, sessions: list[dict]) -> list[dict]:
        """Build session_workbench_record-like dicts from minimal data."""
        records = []
        for s in sessions:
            records.append({
                "session_id": s["session_id"],
                "dossier_id": s["dossier_id"],
                "app_display_name": s.get("name", "Test"),
                "app_property_type": "residentiel_unifamilial",
                "app_neighborhood": "Zone",
                "status": "CREATED",
                "updated_at_utc": s.get("updated_at", "2026-05-20T10:00:00+00:00"),
                "pinned": False,
                "review_decision": "A_SAISIR",
                "package_status": "ABSENT",
                "next_action": "",
            })
        return records

    def test_no_duplicates_when_one_session_per_dossier(self, tmp_path):
        records = self._fake_session_records([
            {"session_id": "hex111aaa000", "dossier_id": "D-USR-A00001"},
            {"session_id": "hex222bbb000", "dossier_id": "D-USR-B00002"},
        ])
        with (
            patch.object(api, "SESSIONS_DIR", tmp_path),
            patch("api.list_session_records", return_value=records),
            patch("api.app_session_view", return_value=None),
            patch("api.product_summary", return_value={}),
        ):
            state = app_state()
        slugs = [d["slug"] for d in state["dossiers"]]
        assert slugs == ["D-USR-A00001", "D-USR-B00002"]
        assert len(slugs) == len(set(slugs))

    def test_deduplicates_multiple_sessions_same_dossier(self, tmp_path):
        records = self._fake_session_records([
            {"session_id": "hex111aaa001", "dossier_id": "D-USR-SAME01",
             "updated_at": "2026-05-20T12:00:00+00:00"},
            {"session_id": "hex222bbb001", "dossier_id": "D-USR-SAME01",
             "updated_at": "2026-05-20T10:00:00+00:00"},
        ])
        with (
            patch.object(api, "SESSIONS_DIR", tmp_path),
            patch("api.list_session_records", return_value=records),
            patch("api.app_session_view", return_value=None),
            patch("api.product_summary", return_value={}),
        ):
            state = app_state()
        dossiers = state["dossiers"]
        assert len(dossiers) == 1
        assert dossiers[0]["slug"] == "D-USR-SAME01"
        # Most recent session wins
        assert dossiers[0]["session_id"] == "hex111aaa001"

    def test_slug_never_equals_session_id_for_dossier_records(self, tmp_path):
        records = self._fake_session_records([
            {"session_id": "abcdef123456", "dossier_id": "D-USR-SLUG001"},
        ])
        with (
            patch.object(api, "SESSIONS_DIR", tmp_path),
            patch("api.list_session_records", return_value=records),
            patch("api.app_session_view", return_value=None),
            patch("api.product_summary", return_value={}),
        ):
            state = app_state()
        for d in state["dossiers"]:
            if d.get("dossier_id"):
                assert d["slug"] != d["session_id"], (
                    f"slug equals session_id for dossier {d['dossier_id']}"
                )
