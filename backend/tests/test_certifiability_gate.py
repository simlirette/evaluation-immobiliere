"""Regression tests for report/export/package certifiability gates."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_gate_session(
    tmp_path: Path,
    session_id: str = "gate-session",
    *,
    review: bool = False,
    compliance_blocking: list[str] | None = None,
    runtime_blocking: list[str] | None = None,
    report: bool = True,
    comparative_input_count: int = 3,
    comparative_value: float | None = 400000.0,
) -> dict:
    dossier_id = "D-GATE-0001"
    run_id = f"run-{session_id}"
    session_dir = tmp_path / session_id
    session_dir.mkdir(parents=True)
    artifacts_dir = session_dir / "artifacts" / dossier_id
    artifacts_dir.mkdir(parents=True)

    artifacts: list[tuple[str, str, str, Path]] = []
    if report:
        rapport_path = artifacts_dir / "redaction.brouillon_rapport.md"
        rapport_path.write_text("## Rapport\n\nContenu pret.", encoding="utf-8")
        artifacts.append(("evt_report", "redaction", "brouillon_rapport.md", rapport_path))

    compliance_path = artifacts_dir / "compliance-qa.statut_sortie.json"
    blocking = compliance_blocking or []
    _write_json(
        compliance_path,
        {
            "status": "A_REVOIR" if blocking else "PRET_REVISION_FINALE",
            "blocking_failures": blocking,
            "warnings": [],
        },
    )
    artifacts.append(("evt_compliance", "compliance-qa", "statut_sortie.json", compliance_path))

    comparative_path = artifacts_dir / "valuation-draft.calculs_approche_comparative.json"
    _write_json(
        comparative_path,
        {
            "value": comparative_value,
            "input_count": comparative_input_count,
            "calculation_status": "OK" if comparative_input_count >= 3 else "INSUFFICIENT_COMPARABLES",
        },
    )
    artifacts.append(("evt_comparative", "valuation-draft", "calculs_approche_comparative.json", comparative_path))

    result_path = session_dir / "result.json"
    _write_json(
        result_path,
        {
            "dossier_id": dossier_id,
            "status": "PRET_REVISION_FINALE",
            "blocking_failures": runtime_blocking or [],
            "warnings": [],
            "artifact_dir": str(artifacts_dir),
        },
    )

    review_path = session_dir / "review.json"
    if review:
        _write_json(review_path, {"decision": "VALIDE", "reviewer": "EA test", "notes": "ok"})

    events_path = session_dir / "events.jsonl"
    events_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "event_id": event_id,
                    "session_id": session_id,
                    "run_id": run_id,
                    "sequence": index,
                    "event": "artifact_written",
                    "step": step,
                    "artifact": artifact,
                    "path": str(path),
                    "artifact_path": str(path),
                }
            )
            for index, (event_id, step, artifact, path) in enumerate(artifacts, start=1)
        )
        + "\n",
        encoding="utf-8",
    )

    artifact_index_path = session_dir / "artifact_index.json"
    _write_json(
        artifact_index_path,
        {
            "schema_version": "artifact_index_v1",
            "artifacts_count": len(artifacts),
            "artifacts": [
                {
                    "event_id": event_id,
                    "step": step,
                    "artifact": artifact,
                    "path": str(path),
                    "exists": True,
                }
                for event_id, step, artifact, path in artifacts
            ],
        },
    )

    session = {
        "session_id": session_id,
        "run_id": run_id,
        "session_dir": str(session_dir),
        "dossier_id": dossier_id,
        "result_path": str(result_path),
        "events_path": str(events_path),
        "artifact_index_path": str(artifact_index_path),
    }
    if review:
        session["review_path"] = str(review_path)
    _write_json(session_dir / "session.json", session)
    return session


def test_gate_reads_compliance_artifact_blockers(tmp_path):
    original = api.SESSIONS_DIR
    api.SESSIONS_DIR = tmp_path
    try:
        session = _make_gate_session(tmp_path, compliance_blocking=["B008: moins de 3 ventes"])
        gate = api.certifiability_gate(session, require_review=False)
    finally:
        api.SESSIONS_DIR = original

    assert gate["ok"] is False
    assert "compliance_blocking_failures_present" in gate["blocking_errors"]
    assert any("Regles B" in message for message in gate["blocking_messages"])


def test_internal_review_rejects_compliance_blockers_not_only_runtime_result(tmp_path):
    original = api.SESSIONS_DIR
    api.SESSIONS_DIR = tmp_path
    try:
        _make_gate_session(tmp_path, compliance_blocking=["B008: moins de 3 ventes"])
        with pytest.raises(ValueError, match="Revue bloquee"):
            api.app_validate_review({"session_id": "gate-session", "reviewer": "EA test"})
    finally:
        api.SESSIONS_DIR = original


def test_report_export_requires_valid_internal_review(tmp_path):
    original = api.SESSIONS_DIR
    api.SESSIONS_DIR = tmp_path
    try:
        _make_gate_session(tmp_path, review=False)
        with pytest.raises(ValueError, match="export rapport refuse"):
            api.app_export_rapport({"session_id": "gate-session", "format": "html"})
    finally:
        api.SESSIONS_DIR = original


def test_package_generation_embeds_gate_and_requires_report_pdf(tmp_path):
    original = api.SESSIONS_DIR
    api.SESSIONS_DIR = tmp_path
    try:
        _make_gate_session(tmp_path, review=True)
        with patch("engine.report_export._generate_pdf", return_value=b"%PDF-gate"):
            package = api.generate_v1_package_for_session("gate-session")
    finally:
        api.SESSIONS_DIR = original

    assert package["status"] == "PRET_REVUE_EVALUATEUR_AGREE"
    assert package["gate"]["ok"] is True
    assert package["manifest"]["certifiability_gate"]["ok"] is True
    assert any(item["name"] == "rapport.pdf" for item in package["files"])

