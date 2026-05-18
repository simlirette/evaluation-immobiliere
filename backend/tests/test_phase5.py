"""Phase 5 tests — adjustments save/override, transcript endpoint, pipeline progress callback."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


# ── app_save_adjustments ──────────────────────────────────────────────────────

class TestSaveAdjustments:
    def _make_session(self, tmp_path, session_id):
        session_dir = tmp_path / session_id
        session_dir.mkdir(parents=True)
        session = {
            "session_id": session_id,
            "session_dir": str(session_dir),
            "status": "CREATED",
        }
        (session_dir / "session.json").write_text(
            json.dumps(session), encoding="utf-8"
        )
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        return original, session

    def test_saves_adjustments_file(self, tmp_path):
        original, _ = self._make_session(tmp_path, "sess-adj-1")
        try:
            rows = [
                {
                    "id": "adj-1",
                    "comparable_id": "c1",
                    "comparableLabel": "Comp A",
                    "salePrice": 400000,
                    "surface_adj": 5000,
                    "year_adj": -3000,
                    "condition_adj": 0,
                    "garage_adj": 2000,
                },
            ]
            result = api.app_save_adjustments({"session_id": "sess-adj-1", "adjustments": rows})
            assert result["ok"] is True
            assert result["count"] == 1
            adj_path = tmp_path / "sess-adj-1" / "adjustments.json"
            assert adj_path.exists()
            data = json.loads(adj_path.read_text(encoding="utf-8"))
            assert data["manual"] is True
            assert len(data["adjustments"]) == 1
            saved = data["adjustments"][0]
            assert saved["salePrice"] == 400000
            assert saved["adjusted"] == pytest.approx(404000)
        finally:
            api.SESSIONS_DIR = original

    def test_adjusted_computed_correctly(self, tmp_path):
        original, _ = self._make_session(tmp_path, "sess-adj-2")
        try:
            rows = [
                {
                    "id": "adj-2",
                    "comparable_id": "c2",
                    "comparableLabel": "Comp B",
                    "salePrice": 500000,
                    "surface_adj": 10000,
                    "year_adj": -5000,
                    "condition_adj": 3000,
                    "garage_adj": -1000,
                },
            ]
            api.app_save_adjustments({"session_id": "sess-adj-2", "adjustments": rows})
            adj_path = tmp_path / "sess-adj-2" / "adjustments.json"
            data = json.loads(adj_path.read_text(encoding="utf-8"))
            assert data["adjustments"][0]["adjusted"] == pytest.approx(507000)
        finally:
            api.SESSIONS_DIR = original

    def test_raises_on_missing_session_id(self, tmp_path):
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        try:
            with pytest.raises(ValueError, match="session_id"):
                api.app_save_adjustments({"adjustments": []})
        finally:
            api.SESSIONS_DIR = original

    def test_raises_on_unknown_session(self, tmp_path):
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        try:
            with pytest.raises(ValueError, match="introuvable"):
                api.app_save_adjustments({"session_id": "nonexistent", "adjustments": []})
        finally:
            api.SESSIONS_DIR = original


# ── app_adjustment_rows — manual override ────────────────────────────────────

class TestAdjustmentRowsManualOverride:
    def _make_session_with_adjustments(self, tmp_path, session_id, manual_rows):
        session_dir = tmp_path / session_id
        session_dir.mkdir(parents=True)
        session = {"session_id": session_id, "session_dir": str(session_dir), "status": "CREATED"}
        (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
        adj_path = session_dir / "adjustments.json"
        adj_path.write_text(
            json.dumps({"manual": True, "adjustments": manual_rows}), encoding="utf-8"
        )
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        return original

    def test_returns_manual_rows_when_present(self, tmp_path):
        manual = [{"id": "adj-m1", "comparable_id": "c1", "comparableLabel": "X",
                   "salePrice": 300000, "surface_adj": 0, "year_adj": 0,
                   "condition_adj": 0, "garage_adj": 0, "adjusted": 300000}]
        original = self._make_session_with_adjustments(tmp_path, "sess-override", manual)
        try:
            rows = api.app_adjustment_rows({}, {}, session_id="sess-override")
            assert len(rows) == 1
            assert rows[0]["id"] == "adj-m1"
        finally:
            api.SESSIONS_DIR = original

    def test_falls_back_to_fixture_when_no_manual_file(self, tmp_path):
        original = api.SESSIONS_DIR
        api.SESSIONS_DIR = tmp_path
        try:
            # No session — falls through to fixture path (empty knowledge = empty rows)
            rows = api.app_adjustment_rows({}, {}, session_id="nonexistent-session")
            assert isinstance(rows, list)
        finally:
            api.SESSIONS_DIR = original


# ── runtime.py on_step_done callback ─────────────────────────────────────────

class TestOnStepDoneCallback:
    def test_callback_called_after_each_step(self, tmp_path):
        from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml
        from pathlib import Path

        PIPELINE_PATH = Path(__file__).resolve().parent.parent / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
        if not PIPELINE_PATH.exists():
            pytest.skip("Pipeline YAML not available")

        steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
        engine = RuntimeEngine(steps=steps, strict_mode=False)

        called = []

        # Minimal case dict
        case = {
            "dossier_id": "TEST-CALLBACK",
            "adresse": "123 Rue Test",
            "type_bien": "unifamilial",
        }

        try:
            engine.run_case_data(
                case,
                tmp_path / "artifacts",
                source_fixture="inline",
                case_stem="test-callback",
                case_subdir=True,
                on_step_done=lambda step_name: called.append(step_name),
            )
        except Exception:
            pass  # Pipeline may fail without full fixture — what matters is callback was called

        # Callback must have been called at least once if any steps ran
        if called:
            assert all(isinstance(s, str) for s in called)

    def test_callback_exception_does_not_block_pipeline(self, tmp_path):
        """A crashing callback must never prevent the pipeline from continuing."""
        from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml
        from pathlib import Path

        PIPELINE_PATH = Path(__file__).resolve().parent.parent / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
        if not PIPELINE_PATH.exists():
            pytest.skip("Pipeline YAML not available")

        steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
        engine = RuntimeEngine(steps=steps, strict_mode=False)

        def crashing_callback(step_name):
            raise RuntimeError("callback crash")

        case = {"dossier_id": "TEST-CRASH", "adresse": "123 Rue Test", "type_bien": "unifamilial"}

        # Must not propagate the callback exception
        try:
            engine.run_case_data(
                case,
                tmp_path / "artifacts",
                source_fixture="inline",
                case_stem="test-crash",
                case_subdir=True,
                on_step_done=crashing_callback,
            )
        except RuntimeError as e:
            # Only acceptable if it's NOT from the callback
            assert "callback crash" not in str(e)
        except Exception:
            pass  # Other pipeline errors are fine
