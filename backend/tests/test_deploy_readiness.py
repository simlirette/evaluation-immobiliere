from __future__ import annotations

import json
import sys
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from scripts import check_deploy_readiness


def _prod_env(sessions_dir: Path, data_cache_dir: Path) -> dict[str, str]:
    return {
        "APP_ENV": "production",
        "EVAL_RUNTIME_API_TOKEN": "runtime-token",
        "EVAL_RUNTIME_ALLOWED_ORIGIN": "https://app.example.test",
        "OPENAI_API_KEY": "sk-test",
        "SESSIONS_DIR": str(sessions_dir),
        "DATA_CACHE_DIR": str(data_cache_dir),
    }


def _checks_by_name(status: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(check["name"]): check for check in status["checks"]}  # type: ignore[index]


def _handler(path: str) -> api.RuntimeApiHandler:
    handler = api.RuntimeApiHandler.__new__(api.RuntimeApiHandler)
    handler.path = path
    handler.headers = Message()
    handler._send_json = MagicMock()
    return handler


def test_deploy_readiness_blocks_incomplete_production_config(tmp_path):
    with patch.dict("os.environ", {"APP_ENV": "production"}, clear=True), patch.object(
        api, "SESSIONS_DIR", tmp_path / "sessions"
    ):
        status = api.deploy_readiness_status()

    checks = _checks_by_name(status)
    assert status["ok"] is False
    assert checks["EVAL_RUNTIME_API_TOKEN"]["status"] == "critical"
    assert checks["EVAL_RUNTIME_ALLOWED_ORIGIN"]["status"] == "critical"
    assert checks["SESSIONS_DIR"]["status"] == "critical"
    assert checks["DATA_CACHE_DIR"]["status"] == "critical"
    assert checks["OPENAI_API_KEY"]["status"] == "critical"


def test_deploy_readiness_accepts_production_config_with_writable_volumes(tmp_path):
    sessions_dir = tmp_path / "sessions"
    data_cache_dir = tmp_path / "data_cache"
    data_cache_dir.mkdir()
    (data_cache_dir / "role_mtl.csv").write_text("matricule,adresse\n", encoding="utf-8")

    with patch.dict("os.environ", _prod_env(sessions_dir, data_cache_dir), clear=True), patch.object(
        api, "SESSIONS_DIR", sessions_dir
    ):
        status = api.deploy_readiness_status()

    checks = _checks_by_name(status)
    assert status["ok"] is True
    assert status["summary"]["critical"] == 0  # type: ignore[index]
    assert checks["SESSIONS_DIR"]["status"] == "ok"
    assert checks["DATA_CACHE_DIR"]["status"] == "ok"
    assert checks["MAMH_CACHE"]["status"] == "ok"
    assert checks["SIRF_CREDENTIALS"]["status"] == "warning"


def test_readiness_endpoint_returns_503_when_production_is_blocked(tmp_path):
    handler = _handler("/readiness")
    with patch.dict("os.environ", {"APP_ENV": "production"}, clear=True), patch.object(
        api, "SESSIONS_DIR", tmp_path / "sessions"
    ):
        handler._handle_get()

    handler._send_json.assert_called_once()
    status, payload = handler._send_json.call_args.args
    assert status == 503
    assert payload["status"] == "blocked"
    assert payload["ok"] is False


def test_deploy_readiness_script_returns_json_and_exit_code(capsys, tmp_path):
    sessions_dir = tmp_path / "sessions"
    data_cache_dir = tmp_path / "data_cache"
    data_cache_dir.mkdir()
    (data_cache_dir / "role_mtl.csv").write_text("matricule,adresse\n", encoding="utf-8")

    with patch.dict("os.environ", _prod_env(sessions_dir, data_cache_dir), clear=True), patch.object(
        api, "SESSIONS_DIR", sessions_dir
    ):
        code = check_deploy_readiness.main(["--json"])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert payload["schema_version"] == "runtime_deploy_readiness_v1"
