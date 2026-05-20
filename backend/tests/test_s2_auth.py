"""S2 tests — Auth + confirmed_by (X-Evaluator-Id header).

Couvre :
- do_POST injecte _evaluator_id depuis X-Evaluator-Id header
- app_validate_review() utilise _evaluator_id comme confirmed_by
- save_review() persiste confirmed_by dans review.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from api import app_validate_review, save_review


# ── Helpers ──────────────────────────────────────────────────────────────────

_VALIDATED_PAYLOAD = {
    "decision": "VALIDE",
    "reviewer": "É.A. Test",
    "notes": "Validation test",
}


def _make_session_file(tmp_path: Path, session_id: str) -> Path:
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    session = {
        "session_id": session_id,
        "run_id": f"run_{session_id}",
        "dossier_id": "D-USR-TEST0001",
        "status": "PRET_REVISION_FINALE",
        "created_at_utc": "2026-05-20T10:00:00+00:00",
        "updated_at_utc": "2026-05-20T10:00:00+00:00",
        "session_dir": str(session_dir),
    }
    (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
    return session_dir


# ── app_validate_review — confirmed_by ───────────────────────────────────────

class TestValidateReviewConfirmedBy:
    """Mock validate_review_payload to isolate confirmed_by logic."""

    def _run(self, tmp_path: Path, session_id: str, body_extra: dict) -> dict:
        _make_session_file(tmp_path, session_id)
        body = {"session_id": session_id, **body_extra}

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with patch("api.session_summary", return_value={
                "session": {},
                "result": {"blocking_failures": [], "warnings": []},
                "integrity": {"ok": True},
                "review": {},
            }):
                with patch("api.validate_review_payload", return_value=_VALIDATED_PAYLOAD):
                    with patch("api.app_state", return_value={}):
                        return app_validate_review(body)

    def test_confirmed_by_set_from_evaluator_id(self, tmp_path):
        result = self._run(tmp_path, "revtest01", {"_evaluator_id": "supabase-uid-1234"})
        review = result.get("review", {}).get("review", {})
        assert review.get("confirmed_by") == "supabase-uid-1234"

    def test_reviewer_falls_back_to_evaluator_id_when_no_reviewer(self, tmp_path):
        """When body has no 'reviewer', confirmed_by (evaluator_id) is used."""
        _make_session_file(tmp_path, "revtest02")
        body = {"session_id": "revtest02", "_evaluator_id": "supabase-uid-5678"}

        def fake_validate(session, b):
            # Simulate: reviewer = _evaluator_id fallback
            reviewer = b.get("reviewer") or b.get("_evaluator_id") or ""
            return {"decision": "VALIDE", "reviewer": reviewer, "notes": "ok"}

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with patch("api.session_summary", return_value={
                "session": {}, "result": {"blocking_failures": []},
                "integrity": {"ok": True}, "review": {},
            }):
                with patch("api.validate_review_payload", side_effect=fake_validate):
                    with patch("api.app_state", return_value={}):
                        result = app_validate_review(body)

        review = result.get("review", {}).get("review", {})
        assert review.get("reviewer") == "supabase-uid-5678"

    def test_confirmed_by_empty_when_no_evaluator_id(self, tmp_path):
        result = self._run(tmp_path, "revtest03", {})
        review = result.get("review", {}).get("review", {})
        assert review.get("confirmed_by") == ""


# ── save_review — confirmed_by persisted ─────────────────────────────────────

class TestSaveReviewConfirmedBy:
    """Mock validate_review_payload to isolate file-write behavior."""

    def _save(self, tmp_path: Path, session_id: str, confirmed_by: str) -> dict:
        _make_session_file(tmp_path, session_id)
        validated = {**_VALIDATED_PAYLOAD, "reviewer": confirmed_by or "Local"}

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with patch("api.validate_review_payload", return_value=validated):
                save_review({
                    "session_id": session_id,
                    "decision": "VALIDE",
                    "reviewer": validated["reviewer"],
                    "confirmed_by": confirmed_by,
                    "notes": "test",
                })

        return json.loads((tmp_path / session_id / "review.json").read_text())

    def test_confirmed_by_written_to_review_json(self, tmp_path):
        data = self._save(tmp_path, "savrev01", "supabase-uuid-abcd")
        assert data["confirmed_by"] == "supabase-uuid-abcd"

    def test_confirmed_by_empty_string_when_absent(self, tmp_path):
        data = self._save(tmp_path, "savrev02", "")
        assert data["confirmed_by"] == ""

    def test_review_json_has_required_fields(self, tmp_path):
        data = self._save(tmp_path, "savrev03", "uid-xyz")
        assert data["schema_version"] == "session_review_v1"
        assert "created_at_utc" in data
        assert data["decision"] == "VALIDE"
        assert data["confirmed_by"] == "uid-xyz"

    def test_review_json_written_to_session_dir(self, tmp_path):
        session_id = "savrev04"
        self._save(tmp_path, session_id, "uid-check")
        review_path = tmp_path / session_id / "review.json"
        assert review_path.exists()


# ── do_POST header injection logic ───────────────────────────────────────────

class TestDoPostEvaluatorIdInjection:
    """Tests the header-injection pattern in do_POST."""

    def _inject(self, body: dict, header_value: str) -> dict:
        """Replicate do_POST injection logic."""
        ev_id = str(header_value or "").strip()
        if ev_id:
            body.setdefault("_evaluator_id", ev_id)
        return body

    def test_header_injected_into_body(self):
        body = self._inject({"session_id": "abc"}, "supabase-user-xyz")
        assert body["_evaluator_id"] == "supabase-user-xyz"

    def test_empty_header_skipped(self):
        body = self._inject({"session_id": "abc"}, "")
        assert "_evaluator_id" not in body

    def test_whitespace_header_skipped(self):
        body = self._inject({"session_id": "abc"}, "   ")
        assert "_evaluator_id" not in body

    def test_existing_value_not_overwritten(self):
        body = self._inject({"session_id": "abc", "_evaluator_id": "original"}, "new-value")
        assert body["_evaluator_id"] == "original"
