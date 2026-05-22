"""S3 tests — Pipeline stoppable par checkpoint + log horodaté.

Couvre :
- engine/checkpoints.py : is_checkpoint_confirmed, confirm_checkpoint,
                          assert_checkpoint_confirmed, read_checkpoint_log
- engine/runtime.py     : steps_filter filtre correctement les steps
- api.py                : app_confirm_checkpoint, app_resume_checkpoint (gate 409),
                          _normalize_session_id
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from engine.checkpoints import (
    CHECKPOINT_LABELS,
    CHECKPOINT_STEPS,
    CheckpointRequiredError,
    assert_checkpoint_confirmed,
    confirm_checkpoint,
    is_checkpoint_confirmed,
    read_checkpoint_log,
    checkpoint_log_path,
)
from api import app_confirm_checkpoint, app_resume_checkpoint, _normalize_session_id


# ── Helpers ──────────────────────────────────────────────────────────────────

def _session_dir(tmp_path: Path, session_id: str) -> Path:
    sd = tmp_path / session_id
    sd.mkdir(parents=True)
    return sd


def _make_session(tmp_path: Path, session_id: str, dossier_id: str = "D-USR-TEST001") -> dict:
    sd = _session_dir(tmp_path, session_id)
    session = {
        "session_id": session_id,
        "run_id": f"run_{session_id}",
        "dossier_id": dossier_id,
        "status": "CREATED",
        "created_at_utc": "2026-05-20T10:00:00+00:00",
        "updated_at_utc": "2026-05-20T10:00:00+00:00",
        "session_dir": str(sd),
        "strict_mode": False,
    }
    (sd / "session.json").write_text(json.dumps(session), encoding="utf-8")
    return session


# ── checkpoint_log : lecture / écriture ──────────────────────────────────────

class TestCheckpointLog:
    def test_empty_log_returns_empty_list(self, tmp_path):
        sd = _session_dir(tmp_path, "sess01")
        assert read_checkpoint_log(sd) == []

    def test_confirm_writes_entry(self, tmp_path):
        sd = _session_dir(tmp_path, "sess02")
        entry = confirm_checkpoint(sd, 1, "uid-abc")
        assert entry["checkpoint"] == 1
        assert entry["label"] == "faits_bien_sujet"
        assert entry["confirmed_by"] == "uid-abc"
        assert "confirmed_at" in entry
        assert entry["snapshot_hash"].startswith("sha256:")

    def test_confirm_appends_to_jsonl(self, tmp_path):
        sd = _session_dir(tmp_path, "sess03")
        confirm_checkpoint(sd, 1, "uid-1")
        confirm_checkpoint(sd, 2, "uid-2")
        entries = read_checkpoint_log(sd)
        assert len(entries) == 2
        assert entries[0]["checkpoint"] == 1
        assert entries[1]["checkpoint"] == 2

    def test_invalid_checkpoint_raises(self, tmp_path):
        sd = _session_dir(tmp_path, "sess04")
        with pytest.raises(ValueError, match="checkpoint invalide"):
            confirm_checkpoint(sd, 99, "uid")

    def test_jsonl_format_valid(self, tmp_path):
        sd = _session_dir(tmp_path, "sess05")
        confirm_checkpoint(sd, 1, "uid-x")
        raw = checkpoint_log_path(sd).read_text(encoding="utf-8").strip()
        parsed = json.loads(raw)  # must be valid JSON
        assert parsed["checkpoint"] == 1


# ── is_checkpoint_confirmed ───────────────────────────────────────────────────

class TestIsCheckpointConfirmed:
    def test_false_when_no_log(self, tmp_path):
        sd = _session_dir(tmp_path, "ck01")
        assert not is_checkpoint_confirmed(sd, 1)

    def test_true_after_confirm(self, tmp_path):
        sd = _session_dir(tmp_path, "ck02")
        confirm_checkpoint(sd, 1, "uid")
        assert is_checkpoint_confirmed(sd, 1)

    def test_false_for_wrong_checkpoint(self, tmp_path):
        sd = _session_dir(tmp_path, "ck03")
        confirm_checkpoint(sd, 1, "uid")
        assert not is_checkpoint_confirmed(sd, 2)

    def test_true_for_each_confirmed_checkpoint(self, tmp_path):
        sd = _session_dir(tmp_path, "ck04")
        for cp in (1, 2, 3):
            confirm_checkpoint(sd, cp, "uid")
        for cp in (1, 2, 3):
            assert is_checkpoint_confirmed(sd, cp)
        assert not is_checkpoint_confirmed(sd, 4)


# ── assert_checkpoint_confirmed ──────────────────────────────────────────────

class TestAssertCheckpointConfirmed:
    def test_raises_when_not_confirmed(self, tmp_path):
        sd = _session_dir(tmp_path, "ac01")
        with pytest.raises(CheckpointRequiredError) as exc_info:
            assert_checkpoint_confirmed(sd, 1)
        assert exc_info.value.required_checkpoint == 1

    def test_no_raise_when_confirmed(self, tmp_path):
        sd = _session_dir(tmp_path, "ac02")
        confirm_checkpoint(sd, 1, "uid")
        assert_checkpoint_confirmed(sd, 1)  # should not raise

    def test_error_message_includes_checkpoint_label(self, tmp_path):
        sd = _session_dir(tmp_path, "ac03")
        with pytest.raises(CheckpointRequiredError) as exc_info:
            assert_checkpoint_confirmed(sd, 2)
        assert "comparables" in str(exc_info.value)
        assert "2" in str(exc_info.value)


# ── CheckpointRequiredError ───────────────────────────────────────────────────

class TestCheckpointRequiredError:
    def test_has_required_checkpoint_attr(self):
        err = CheckpointRequiredError(2)
        assert err.required_checkpoint == 2

    def test_is_value_error_subclass(self):
        assert issubclass(CheckpointRequiredError, ValueError)

    def test_all_checkpoint_labels_covered(self):
        for cp in (1, 2, 3, 4):
            err = CheckpointRequiredError(cp)
            assert CHECKPOINT_LABELS[cp] in str(err)


# ── RuntimeEngine steps_filter ────────────────────────────────────────────────

class TestRuntimeEngineStepsFilter:
    def _make_steps(self, names: list[str]):
        from engine.runtime import RuntimeStep
        # Non-empty reads/writes so validate_pipeline_steps passes and artifact loop runs.
        return [
            RuntimeStep(name=n, agent_config=None, reads=["input.json"], writes=["output.json"], skills=[])
            for n in names
        ]

    def _run_with_tracking(self, engine, out_dir, steps_filter):
        """Run engine.run_case_data with all heavy calls mocked; return list of executed step names."""
        executed: list[str] = []

        def fake_payload(step_name, artifact, *a, **kw):
            executed.append(step_name)
            return {"source_fixture": "test", "status": "OK"}

        with patch.object(engine, "_artifact_payload", side_effect=fake_payload), \
             patch.object(engine, "_enrich_artifact_llm", side_effect=lambda s, a, p, c: p), \
             patch("engine.runtime.validate_schema", return_value=(True, [])), \
             patch("engine.runtime.validate_contract_rules", return_value=[]), \
             patch("engine.runtime.write_artifact_payload"):
            engine.run_case_data(
                {"dossier_id": "D-TEST"},
                out_dir,
                steps_filter=steps_filter,
            )
        return executed

    def test_filter_limits_executed_steps(self, tmp_path):
        from engine.runtime import RuntimeEngine
        steps = self._make_steps(["step-a", "step-b", "step-c"])
        with patch("engine.runtime.validate_pipeline_steps"):
            engine = RuntimeEngine(steps=steps, strict_mode=False)
        executed = self._run_with_tracking(engine, tmp_path / "all", steps_filter=None)
        assert set(executed) == {"step-a", "step-b", "step-c"}

    def test_filter_runs_only_specified_steps(self, tmp_path):
        from engine.runtime import RuntimeEngine
        steps = self._make_steps(["step-a", "step-b", "step-c"])
        with patch("engine.runtime.validate_pipeline_steps"):
            engine = RuntimeEngine(steps=steps, strict_mode=False)
        executed = self._run_with_tracking(engine, tmp_path / "filtered", steps_filter=["step-a", "step-c"])
        assert "step-b" not in executed
        assert "step-a" in executed or "step-c" in executed

    def test_empty_filter_runs_no_steps(self, tmp_path):
        from engine.runtime import RuntimeEngine
        steps = self._make_steps(["step-a", "step-b"])
        with patch("engine.runtime.validate_pipeline_steps"):
            engine = RuntimeEngine(steps=steps, strict_mode=False)
        executed = self._run_with_tracking(engine, tmp_path / "empty", steps_filter=[])
        assert executed == []


# ── app_confirm_checkpoint ────────────────────────────────────────────────────

class TestAppConfirmCheckpoint:
    def test_confirm_checkpoint_1(self, tmp_path):
        session_id = "conftest01"
        _make_session(tmp_path, session_id)

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with patch("api.app_state", return_value={}):
                result = app_confirm_checkpoint({
                    "session_id": session_id,
                    "checkpoint": 1,
                    "_evaluator_id": "uid-evaluateur",
                })

        assert result["checkpoint"] == 1
        assert result["label"] == "faits_bien_sujet"
        assert result["entry"]["confirmed_by"] == "uid-evaluateur"

        # Verify file was written
        sd = tmp_path / session_id
        assert is_checkpoint_confirmed(sd, 1)

    def test_invalid_checkpoint_returns_error(self, tmp_path):
        session_id = "conftest02"
        _make_session(tmp_path, session_id)

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with pytest.raises(ValueError, match="checkpoint invalide"):
                app_confirm_checkpoint({
                    "session_id": session_id,
                    "checkpoint": 99,
                })


# ── app_resume_checkpoint — gate 409 ─────────────────────────────────────────

class TestAppResumeCheckpointGate:
    def test_gate_blocks_when_previous_not_confirmed(self, tmp_path):
        """resume(checkpoint=2) doit échouer si CP1 n'est pas confirmé."""
        session_id = "gate01"
        _make_session(tmp_path, session_id)
        # CP1 NOT confirmed — gate must block

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with pytest.raises(CheckpointRequiredError) as exc_info:
                app_resume_checkpoint({
                    "session_id": session_id,
                    "checkpoint": 2,
                })
        assert exc_info.value.required_checkpoint == 1

    def test_gate_passes_when_previous_confirmed(self, tmp_path):
        """resume(checkpoint=2) doit passer si CP1 est confirmé."""
        session_id = "gate02"
        _make_session(tmp_path, session_id)
        sd = tmp_path / session_id
        confirm_checkpoint(sd, 1, "uid-ok")  # CP1 confirmed

        # Create required input file (named after dossier_id, as api.py uses safe_path_id(dossier_id))
        (sd / "D-USR-TEST001.input.json").write_text(
            json.dumps({"dossier_id": "D-USR-TEST001"}), encoding="utf-8"
        )

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with patch("api._run_pipeline_segment"):  # don't actually run pipeline
                with patch("api.app_state", return_value={}):
                    result = app_resume_checkpoint({
                        "session_id": session_id,
                        "checkpoint": 2,
                    })

        assert result["checkpoint"] == 2
        assert result["status"] == "running"

    def test_gate_blocks_cp3_when_cp2_missing(self, tmp_path):
        """resume(checkpoint=3) bloqué si CP2 absent même si CP1 ok."""
        session_id = "gate03"
        _make_session(tmp_path, session_id)
        sd = tmp_path / session_id
        confirm_checkpoint(sd, 1, "uid")
        # CP2 not confirmed

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with pytest.raises(CheckpointRequiredError) as exc_info:
                app_resume_checkpoint({
                    "session_id": session_id,
                    "checkpoint": 3,
                })
        assert exc_info.value.required_checkpoint == 2

    def test_invalid_checkpoint_value_rejected(self, tmp_path):
        session_id = "gate04"
        _make_session(tmp_path, session_id)

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            with pytest.raises(ValueError):
                app_resume_checkpoint({
                    "session_id": session_id,
                    "checkpoint": 1,  # 1 is invalid for resume (must be 2-4)
                })


# ── _normalize_session_id ─────────────────────────────────────────────────────

class TestNormalizeSessionId:
    def test_hex_id_returned_unchanged(self, tmp_path):
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = _normalize_session_id("abcdef123456")
        assert result == "abcdef123456"

    def test_dossier_id_resolved(self, tmp_path):
        session_id = "hexsession0ab"
        _make_session(tmp_path, session_id, dossier_id="D-USR-NORM0001")

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = _normalize_session_id("D-USR-NORM0001")
        assert result == session_id

    def test_unknown_dossier_id_returned_as_is(self, tmp_path):
        with patch.object(api, "SESSIONS_DIR", tmp_path):
            result = _normalize_session_id("D-USR-UNKNOWN1")
        assert result == "D-USR-UNKNOWN1"
