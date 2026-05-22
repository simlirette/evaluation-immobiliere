"""Filesystem state hardening tests: atomic writes, corrupt reads, locks."""
from __future__ import annotations

import json
import sys
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from engine.checkpoints import confirm_checkpoint, read_checkpoint_log


def _session_payload(tmp_path: Path, session_id: str, dossier_id: str, **extra) -> dict:
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    now = extra.pop("created_at_utc", datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    payload = {
        "schema_version": "runtime_session_v1",
        "session_id": session_id,
        "dossier_id": dossier_id,
        "status": "READY",
        "created_at_utc": now,
        "updated_at_utc": now,
        "session_dir": str(session_dir),
        **extra,
    }
    (session_dir / "session.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


class TestAtomicJsonState:
    def test_write_json_uses_complete_replace_without_temp_leftovers(self, tmp_path):
        path = tmp_path / "sess01" / "session.json"
        api.write_json(path, {"session_id": "sess01", "value": "ok"})

        assert json.loads(path.read_text(encoding="utf-8"))["value"] == "ok"
        assert list(path.parent.glob("*.tmp")) == []

    def test_concurrent_write_json_leaves_valid_json(self, tmp_path):
        path = tmp_path / "sess02" / "pipeline_progress.json"

        def worker(i: int) -> None:
            api.write_json(path, {"writer": i, "items": list(range(i % 7))})

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(40)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload["writer"], int)
        assert isinstance(payload["items"], list)
        assert list(path.parent.glob("*.tmp")) == []


class TestCorruptJsonRecovery:
    def test_read_json_dict_returns_empty_for_corrupt_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text('{"broken": ', encoding="utf-8")

        assert api.read_json_dict(path) == {}

    def test_load_session_returns_none_for_corrupt_session_file(self, tmp_path):
        session_dir = tmp_path / "badsession01"
        session_dir.mkdir()
        (session_dir / "session.json").write_text('{"session_id": ', encoding="utf-8")

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert api.load_session("badsession01") is None

    def test_app_state_skips_corrupt_session_without_crashing(self, tmp_path):
        _session_payload(tmp_path, "goodsession1", "D-USR-GOOD0001")
        bad_dir = tmp_path / "badsession02"
        bad_dir.mkdir()
        (bad_dir / "session.json").write_text('{"session_id": ', encoding="utf-8")

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            state = api.app_state()

        assert state["dossiers_count"] == 1
        assert state["dossiers"][0]["id"] == "D-USR-GOOD0001"


class TestSessionResolutionAndArchival:
    def test_find_session_skips_path_mismatch_collision(self, tmp_path):
        payload = _session_payload(tmp_path, "realpath01", "D-USR-COLLIDE1")
        payload["session_id"] = "otherpath02"
        (tmp_path / "realpath01" / "session.json").write_text(json.dumps(payload), encoding="utf-8")

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert api._find_session_for_dossier("D-USR-COLLIDE1") is None

    def test_archive_stale_sessions_skips_active_pipeline_progress(self, tmp_path):
        old = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        _session_payload(tmp_path, "activeold01", "D-USR-ACTIVE01", created_at_utc=old)
        api.write_json(tmp_path / "activeold01" / "pipeline_progress.json", {
            "steps": ["data-facts"],
            "completed": [],
            "running": "data-facts",
        })

        with patch.object(api, "SESSIONS_DIR", tmp_path):
            assert api._archive_stale_sessions() == 0

        saved = json.loads((tmp_path / "activeold01" / "session.json").read_text(encoding="utf-8"))
        assert saved.get("app_archived") is not True


class TestCheckpointLogLocking:
    def test_concurrent_checkpoint_confirms_leave_valid_jsonl(self, tmp_path):
        session_dir = tmp_path / "checkpoints"
        session_dir.mkdir()

        def worker(i: int) -> None:
            checkpoint = (i % 4) + 1
            confirm_checkpoint(session_dir, checkpoint, f"uid-{i}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(24)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        entries = read_checkpoint_log(session_dir)
        assert len(entries) == 24
        assert {entry["checkpoint"] for entry in entries} == {1, 2, 3, 4}
