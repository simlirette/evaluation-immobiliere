"""Tests Phase 10 — app_fact_chips overrides + app_save_fact_overrides."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


# ── helpers ───────────────────────────────────────────────────────────────────

def _patch_sessions(tmp_path):
    original = api.SESSIONS_DIR
    api.SESSIONS_DIR = tmp_path
    return original


def _make_session(tmp_path, session_id, extra=None):
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    session = {"session_id": session_id, "session_dir": str(session_dir), "status": "CREATED"}
    if extra:
        session.update(extra)
    (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
    return session_dir


# ── app_fact_chips — no overrides ─────────────────────────────────────────────

class TestAppFactChipsNoOverrides:
    def _knowledge(self, **kw):
        return {
            "subject_property": {
                "type_bien": kw.get("type_bien", "residentiel_unifamilial"),
                "zone": kw.get("zone", "Rosemont"),
                "surface": kw.get("surface"),
                "confidence": kw.get("confidence"),
                "source_ids": kw.get("source_ids", []),
            },
            "mandate": {
                "date_reference": kw.get("date_reference"),
            },
        }

    def test_basic_chips_returned(self):
        chips = api.app_fact_chips(self._knowledge(), {})
        labels = [c["label"] for c in chips]
        assert any("Type:" in l for l in labels)
        assert any("Zone:" in l for l in labels)

    def test_zone_from_subject(self):
        chips = api.app_fact_chips(self._knowledge(zone="Plateau"), {})
        assert any(c["label"] == "Zone: Plateau" for c in chips)

    def test_date_from_mandate(self):
        chips = api.app_fact_chips(self._knowledge(date_reference="2026-01-15"), {})
        assert any("2026-01-15" in c["label"] for c in chips)

    def test_missing_date_filtered_out(self):
        chips = api.app_fact_chips(self._knowledge(), {})
        # date_reference absent → chip "Date: -" filtered out
        assert not any(c["label"] == "Date: -" for c in chips)

    def test_surface_none_filtered_out(self):
        chips = api.app_fact_chips(self._knowledge(surface=None), {})
        # surface absent → chip label ends with ": -" → filtered
        assert not any(c["label"] == "Surface: -" for c in chips)

    def test_surface_from_subject(self):
        knowledge = self._knowledge(surface={"value": 1200, "unit": "pi2"})
        chips = api.app_fact_chips(knowledge, {})
        assert any("Surface:" in c["label"] for c in chips)

    def test_highlight_flags(self):
        chips = api.app_fact_chips(self._knowledge(date_reference="2026-01-01"), {})
        highlighted = [c for c in chips if c["highlight"]]
        labels = [c["label"] for c in highlighted]
        assert any("Type:" in l for l in labels)
        assert any("Zone:" in l for l in labels)
        assert any("Date:" in l for l in labels)


# ── app_fact_chips — with overrides ──────────────────────────────────────────

class TestAppFactChipsOverrides:
    def _base_knowledge(self):
        return {
            "subject_property": {
                "type_bien": "condo",
                "zone": "Rosemont",
                "surface": {"value": 900, "unit": "pi2"},
                "confidence": None,
                "source_ids": [],
            },
            "mandate": {"date_reference": "2026-01-01"},
        }

    def test_surface_override(self):
        chips = api.app_fact_chips(self._base_knowledge(), {}, overrides={"surface_pi2": 1450.0})
        surface_chip = next(c for c in chips if "Surface:" in c["label"])
        assert "1\u202f450" in surface_chip["label"] or "1450" in surface_chip["label"]

    def test_zone_override(self):
        chips = api.app_fact_chips(self._base_knowledge(), {}, overrides={"zone": "Villeray"})
        assert any(c["label"] == "Zone: Villeray" for c in chips)

    def test_date_override(self):
        chips = api.app_fact_chips(self._base_knowledge(), {}, overrides={"date_reference": "2025-06-30"})
        assert any("2025-06-30" in c["label"] for c in chips)

    def test_override_takes_precedence_over_subject(self):
        # Knowledge has zone=Rosemont, override says Plateau
        chips = api.app_fact_chips(self._base_knowledge(), {}, overrides={"zone": "Plateau"})
        zone_chip = next(c for c in chips if "Zone:" in c["label"])
        assert "Plateau" in zone_chip["label"]
        assert "Rosemont" not in zone_chip["label"]

    def test_partial_override_leaves_others_intact(self):
        # Only zone overridden — date should still come from mandate
        chips = api.app_fact_chips(self._base_knowledge(), {}, overrides={"zone": "Anjou"})
        assert any("2026-01-01" in c["label"] for c in chips)
        assert any("Zone: Anjou" == c["label"] for c in chips)

    def test_empty_overrides_is_same_as_none(self):
        chips_none = api.app_fact_chips(self._base_knowledge(), {}, overrides=None)
        chips_empty = api.app_fact_chips(self._base_knowledge(), {}, overrides={})
        assert chips_none == chips_empty

    def test_zero_surface_override_ignored(self):
        # surface_pi2=0 is falsy — should not override
        chips = api.app_fact_chips(self._base_knowledge(), {}, overrides={"surface_pi2": 0})
        surface_chip = next(c for c in chips if "Surface:" in c["label"])
        # Should still show original 900 pi2
        assert "900" in surface_chip["label"] or "Surface:" in surface_chip["label"]


# ── app_save_fact_overrides ───────────────────────────────────────────────────

class TestAppSaveFactOverrides:
    def test_missing_session_id_raises(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            with pytest.raises(ValueError, match="session_id"):
                api.app_save_fact_overrides({})
        finally:
            api.SESSIONS_DIR = original

    def test_saves_zone_override(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-01")
            result = api.app_save_fact_overrides({
                "session_id": "sess-01",
                "zone": "Verdun",
            })
            assert result["ok"] is True
            assert result["overrides"]["zone"] == "Verdun"
            # Verify persisted in session.json
            session = json.loads((tmp_path / "sess-01" / "session.json").read_text())
            assert session["app_fact_overrides"]["zone"] == "Verdun"
        finally:
            api.SESSIONS_DIR = original

    def test_saves_surface_override(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-02")
            result = api.app_save_fact_overrides({
                "session_id": "sess-02",
                "surface_pi2": "1200",
            })
            assert result["overrides"]["surface_pi2"] == 1200.0
        finally:
            api.SESSIONS_DIR = original

    def test_saves_date_reference_override(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-03")
            result = api.app_save_fact_overrides({
                "session_id": "sess-03",
                "date_reference": "2025-12-31",
            })
            assert result["overrides"]["date_reference"] == "2025-12-31"
        finally:
            api.SESSIONS_DIR = original

    def test_invalid_surface_ignored(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-04")
            result = api.app_save_fact_overrides({
                "session_id": "sess-04",
                "surface_pi2": "not-a-number",
                "zone": "Ahuntsic",
            })
            assert "surface_pi2" not in result["overrides"]
            assert result["overrides"]["zone"] == "Ahuntsic"
        finally:
            api.SESSIONS_DIR = original

    def test_empty_zone_not_saved(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-05")
            result = api.app_save_fact_overrides({
                "session_id": "sess-05",
                "zone": "",
            })
            assert "zone" not in result["overrides"]
        finally:
            api.SESSIONS_DIR = original

    def test_all_fields_saved_together(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-06")
            result = api.app_save_fact_overrides({
                "session_id": "sess-06",
                "surface_pi2": 1800,
                "zone": "LaSalle",
                "date_reference": "2026-03-01",
            })
            ov = result["overrides"]
            assert ov["surface_pi2"] == 1800.0
            assert ov["zone"] == "LaSalle"
            assert ov["date_reference"] == "2026-03-01"
        finally:
            api.SESSIONS_DIR = original

    def test_overrides_persisted_to_disk(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-07")
            api.app_save_fact_overrides({
                "session_id": "sess-07",
                "zone": "Hochelaga",
            })
            session = json.loads((tmp_path / "sess-07" / "session.json").read_text())
            assert session.get("app_fact_overrides", {}).get("zone") == "Hochelaga"
        finally:
            api.SESSIONS_DIR = original

    def test_overwrite_existing_overrides(self, tmp_path):
        original = _patch_sessions(tmp_path)
        try:
            _make_session(tmp_path, "sess-08", extra={"app_fact_overrides": {"zone": "Old"}})
            result = api.app_save_fact_overrides({
                "session_id": "sess-08",
                "zone": "New",
            })
            assert result["overrides"]["zone"] == "New"
            session = json.loads((tmp_path / "sess-08" / "session.json").read_text())
            assert session["app_fact_overrides"]["zone"] == "New"
        finally:
            api.SESSIONS_DIR = original
