from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "acceptance" / "ea_acceptance_anonymized_residential.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _ready_env(sessions_dir: Path, data_cache_dir: Path) -> dict[str, str]:
    return {
        "APP_ENV": "production",
        "EVAL_RUNTIME_API_TOKEN": "runtime-token",
        "EVAL_RUNTIME_ALLOWED_ORIGIN": "https://app.example.test",
        "EVAL_IMMO_BETA_HOSTED_URL": "https://beta.example.test",
        "OPENAI_API_KEY": "sk-test",
        "SESSIONS_DIR": str(sessions_dir),
        "DATA_CACHE_DIR": str(data_cache_dir),
        "EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME": "false",
        "EVAL_IMMO_RUN_LIVE_SMOKE": "false",
    }


def _ok_pymupdf(production: bool) -> dict[str, object]:
    return {"name": "pymupdf", "status": "ok", "message": "PyMuPDF disponible"}


def test_beta_readiness_blocks_missing_external_link_config(tmp_path):
    with patch.dict(os.environ, {}, clear=True), patch.object(api, "SESSIONS_DIR", tmp_path / "sessions"):
        report = api.beta_ea_readiness()

    assert report["status"] == "BETA_LIEN_BLOQUE"
    assert report["ready_for_external_ea_link"] is False
    assert report["ready_for_local_anonymized_beta"] is True
    assert {"hosted_url_configured", "token_auth_enabled", "allowed_origin_configured", "openai_configured"}.issubset(
        set(report["blocking_checks"])
    )


def test_beta_readiness_accepts_hardened_production_config(tmp_path):
    sessions_dir = tmp_path / "sessions"
    data_cache_dir = tmp_path / "data_cache"
    sessions_dir.mkdir()
    data_cache_dir.mkdir()
    (data_cache_dir / "role_mtl.csv").write_text("matricule,adresse\n", encoding="utf-8")

    with patch.dict(os.environ, _ready_env(sessions_dir, data_cache_dir), clear=True), patch.object(
        api, "SESSIONS_DIR", sessions_dir
    ), patch.object(api, "_deploy_status_for_pymupdf", side_effect=_ok_pymupdf):
        report = api.beta_ea_readiness()

    assert report["status"] == "PRET_LIEN_EA"
    assert report["ready_for_external_ea_link"] is True
    assert report["blocking_checks"] == []
    assert report["routes"]["intake"] == "/beta/intake"


def test_beta_readiness_blocks_live_provider_operator_mode(tmp_path):
    sessions_dir = tmp_path / "sessions"
    data_cache_dir = tmp_path / "data_cache"
    sessions_dir.mkdir()
    data_cache_dir.mkdir()
    (data_cache_dir / "role_mtl.csv").write_text("matricule,adresse\n", encoding="utf-8")
    env = {**_ready_env(sessions_dir, data_cache_dir), "EVAL_IMMO_RUN_LIVE_SMOKE": "true"}

    with patch.dict(os.environ, env, clear=True), patch.object(api, "SESSIONS_DIR", sessions_dir), patch.object(
        api, "_deploy_status_for_pymupdf", side_effect=_ok_pymupdf
    ):
        report = api.beta_ea_readiness()

    assert report["status"] == "BETA_LIEN_BLOQUE"
    assert "live_ai_provider_policy" in report["blocking_checks"]


def test_beta_intake_accepts_anonymized_case_and_persists_session_summary(tmp_path):
    sessions_dir = tmp_path / "sessions"
    captured: dict[str, object] = {}

    def fake_start_runtime(payload: dict) -> dict:
        captured["payload"] = payload
        session = api.create_session(
            strict_mode=bool(payload.get("strict_mode", True)),
            owner_evaluator_id=str(payload.get("_evaluator_id") or ""),
        )
        session["dossier_id"] = payload["case"]["dossier_id"]
        session["status"] = "PRET_REVISION_FINALE"
        api.save_session(session)
        return {
            "session": session,
            "result": {
                "dossier_id": session["dossier_id"],
                "status": "PRET_REVISION_FINALE",
                "events": [],
                "artifact_dir": str(Path(session["session_dir"]) / "artifacts"),
            },
        }

    with patch.object(api, "SESSIONS_DIR", sessions_dir), patch("api.start_runtime", side_effect=fake_start_runtime), patch(
        "api.app_state", return_value={"schema_version": "test_state"}
    ):
        result = api.beta_start_dossier(
            {
                "case": _load_fixture(),
                "source_fixture": "acceptance/ea_acceptance_anonymized_residential.json",
                "accepted_beta_terms": True,
                "anonymization_attestation": True,
                "_evaluator_id": "ea-beta-user",
                "documents": [{"document_id": "DOC-1", "type": "fixture", "anonymized": True}],
            }
        )

    assert result["accepted"] is True
    assert result["status"] == "ACCEPTE"
    assert captured["payload"]["source_fixture"].startswith("beta:")
    session = result["session"]
    assert session["owner_evaluator_id"] == "ea-beta-user"
    assert session["beta_intake_summary"]["status"] == "ACCEPTE"
    assert Path(session["beta_intake_path"]).exists()


def test_beta_intake_refuses_identifying_case_before_runtime(tmp_path):
    bad_case = _load_fixture()
    bad_case["commanditaire"]["courriel"] = "client@example.test"
    bad_case["adresse"] = "123 rue Principale"

    with patch.object(api, "SESSIONS_DIR", tmp_path / "sessions"), patch("api.start_runtime") as start_runtime:
        result = api.beta_start_dossier(
            {
                "case": bad_case,
                "accepted_beta_terms": True,
                "anonymization_attestation": True,
                "_evaluator_id": "ea-beta-user",
            }
        )

    assert result["accepted"] is False
    assert result["status"] == "REFUSE"
    assert "anonymized_case_validation_failed" in result["errors"]
    assert "anonymization_blocking_findings" in result["errors"]
    start_runtime.assert_not_called()
