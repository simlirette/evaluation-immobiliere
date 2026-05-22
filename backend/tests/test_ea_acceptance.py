from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from engine.acceptance import validate_anonymized_case
from scripts import run_ea_acceptance


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "acceptance" / "ea_acceptance_anonymized_residential.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_acceptance_fixture_is_anonymized_and_complete():
    result = validate_anonymized_case(_load_fixture())

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["pii_hits"] == []


def test_acceptance_anonymization_rejects_direct_identifiers():
    case = _load_fixture()
    case["commanditaire"]["nom"] = "Jean Tremblay"
    case["commanditaire"]["courriel"] = "jean.tremblay@example.test"

    result = validate_anonymized_case(case)

    assert result["ok"] is False
    assert "pii_detected" in result["errors"]
    assert {hit["type"] for hit in result["pii_hits"]} >= {"email", "direct_identifier_field"}


def test_ea_acceptance_script_runs_pipeline_review_and_package(tmp_path, monkeypatch):
    from engine import data_enrichment, report_export

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("RUNTIME_DETERMINISTIC", "1")
    monkeypatch.setattr(data_enrichment, "enrich_case", lambda *args, **kwargs: None)
    monkeypatch.setattr(report_export, "_generate_pdf", lambda md_text, dossier_id: b"%PDF-acceptance")

    report_path = tmp_path / "acceptance_report.json"
    original_sessions = api.SESSIONS_DIR
    try:
        args = run_ea_acceptance._parse_args([
            str(FIXTURE),
            "--sessions-dir",
            str(tmp_path / "sessions"),
            "--evaluator-id",
            "ea-test-user",
            "--reviewer",
            "EA Acceptance Test",
            "--output",
            str(report_path),
        ])
        report = run_ea_acceptance.run_acceptance(args)
    finally:
        api.SESSIONS_DIR = original_sessions

    persisted = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert persisted["schema_version"] == "ea_acceptance_report_v1"
    assert persisted["human_signoff_required"] is True
    assert persisted["certification_automatic"] is False
    assert persisted["reviewer_evidence"]["confirmed_by"] == "ea-test-user"
    assert persisted["package"]["status"] == "PRET_REVUE_EVALUATEUR_AGREE"
    assert Path(persisted["package"]["manifest_path"]).exists()
    assert all(check["ok"] for check in persisted["checks"])


def test_ea_acceptance_script_stops_before_runtime_when_anonymization_fails(tmp_path):
    bad_case = _load_fixture()
    bad_case["commanditaire"]["email"] = "client@example.test"
    bad_case_path = tmp_path / "bad_case.json"
    bad_case_path.write_text(json.dumps(bad_case), encoding="utf-8")

    with patch("api.start_runtime") as start_runtime:
        args = run_ea_acceptance._parse_args([
            str(bad_case_path),
            "--sessions-dir",
            str(tmp_path / "sessions"),
            "--output",
            str(tmp_path / "blocked_report.json"),
        ])
        report = run_ea_acceptance.run_acceptance(args)

    assert report["status"] == "BLOCKED"
    assert "anonymization" in report["blocking_checks"]
    start_runtime.assert_not_called()
