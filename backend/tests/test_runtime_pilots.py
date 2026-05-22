"""T01-T05 runtime pilot tests from TEST-PLAN-V0."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml


BACKEND_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_TESTS = BACKEND_ROOT / "tests" / "runtime"
TEST_PLAN = RUNTIME_TESTS / "TEST-PLAN-V0.md"
PIPELINE = BACKEND_ROOT / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"
PILOT_FIXTURES = sorted(RUNTIME_TESTS.glob("T*.yaml"))


def _load_fixture(path: Path) -> dict:
    # The fixtures are JSON-compatible YAML by design; no PyYAML dependency.
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _run_pilot(path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    fixture = _load_fixture(path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("RUNTIME_DETERMINISTIC", "1")
    engine = RuntimeEngine(steps=load_steps_from_pipeline_yaml(PIPELINE), strict_mode=False)
    return engine.run_case_data(
        fixture["case"],
        tmp_path / fixture["id"],
        source_fixture=path.name,
        case_stem=fixture["id"],
        case_subdir=True,
    )


def test_test_plan_exists_and_mentions_all_pilot_ids():
    assert TEST_PLAN.exists()
    text = TEST_PLAN.read_text(encoding="utf-8")
    for case_id in ("T01", "T02", "T03", "T04", "T05"):
        assert case_id in text


def test_exactly_five_pilot_fixtures_exist():
    assert [path.name[:3] for path in PILOT_FIXTURES] == ["T01", "T02", "T03", "T04", "T05"]


@pytest.mark.parametrize("path", PILOT_FIXTURES, ids=lambda p: p.name[:3])
def test_pilot_fixture_has_required_sections(path):
    fixture = _load_fixture(path)

    assert fixture["id"] == path.name[:3]
    assert fixture.get("description")
    assert isinstance(fixture.get("case"), dict)
    assert isinstance(fixture.get("expected"), dict)
    assert fixture["case"].get("dossier_id", "").startswith("D-RUNTIME-")
    assert fixture["expected"].get("status") in {"PRET_REVISION_FINALE", "A_REVOIR"}
    assert isinstance(fixture["expected"].get("required_artifacts"), list)


@pytest.mark.parametrize("path", PILOT_FIXTURES, ids=lambda p: p.name[:3])
def test_pilot_runtime_case_matches_expected_status(path, tmp_path, monkeypatch):
    fixture = _load_fixture(path)

    result = _run_pilot(path, tmp_path, monkeypatch)

    assert result["status"] == fixture["expected"]["status"]
    for prefix in fixture["expected"].get("blocking_prefixes", []):
        assert any(str(item).startswith(prefix) for item in result["blocking_failures"]), (
            path.name,
            result["blocking_failures"],
        )


@pytest.mark.parametrize("path", PILOT_FIXTURES, ids=lambda p: p.name[:3])
def test_pilot_runtime_case_writes_required_artifacts(path, tmp_path, monkeypatch):
    fixture = _load_fixture(path)

    result = _run_pilot(path, tmp_path, monkeypatch)

    artifact_dir = Path(result["artifact_dir"])
    for relative_name in fixture["expected"]["required_artifacts"]:
        assert (artifact_dir / relative_name).exists(), f"{path.name}: {relative_name} missing"


def test_t01_reaches_redaction_and_has_positive_comparative_value(tmp_path, monkeypatch):
    result = _run_pilot(RUNTIME_TESTS / "T01_nominal_unifamiliale.yaml", tmp_path, monkeypatch)
    artifact_dir = Path(result["artifact_dir"])

    comparative = json.loads(
        (artifact_dir / "valuation-draft.calculs_approche_comparative.json").read_text(encoding="utf-8")
    )

    assert result["blocking_failures"] == []
    assert comparative["value"] > 0
    assert comparative["input_count"] >= 3
    assert (artifact_dir / "redaction.brouillon_rapport.md").read_text(encoding="utf-8").strip()


def test_blocking_pilots_stop_before_redaction(tmp_path, monkeypatch):
    for path in PILOT_FIXTURES:
        if path.name.startswith("T01"):
            continue
        result = _run_pilot(path, tmp_path, monkeypatch)
        artifact_dir = Path(result["artifact_dir"])
        assert result["status"] == "A_REVOIR"
        assert not (artifact_dir / "redaction.brouillon_rapport.md").exists()
