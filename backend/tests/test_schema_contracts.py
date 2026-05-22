"""Formal JSON schema coverage for runtime artifacts and knowledge snapshots."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import api
from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml
from engine.schema_contracts import (
    ARTIFACT_SCHEMA_DIR,
    KNOWLEDGE_SCHEMA_PATH,
    artifact_schema_path,
    validate_artifact_schema,
    validate_json_schema,
    validate_knowledge_schema,
)
from engine.source_diagnostics import attach_source_coverage, append_source_diagnostic, make_source_diagnostic


PIPELINE_PATH = Path(__file__).resolve().parent.parent / "integration" / "PIPELINE-RUNTIME-ASTON-V0.yaml"


def _case() -> dict:
    case = {
        "dossier_id": "D-SCHEMA-001",
        "date_reference": "2026-01-01",
        "surface": {"value": 120, "unit": "m2"},
        "surface_habitable": 120,
        "type_bien": "unifamiliale",
        "zone": "R1",
        "adresse_anonymisee": "123 rue Exemple",
        "confidence": 0.82,
        "comparables": [
            {
                "comparable_id": "C-1",
                "source_id": "SIRF-1",
                "prix_vente": 410000,
                "date_vente": "2025-05-01",
                "surface": {"value": 118, "unit": "m2"},
                "distance_km": 1.2,
                "type_bien": "unifamiliale",
            },
            {
                "comparable_id": "C-2",
                "source_id": "SIRF-2",
                "prix_vente": 425000,
                "date_vente": "2025-07-01",
                "surface": {"value": 124, "unit": "m2"},
                "distance_km": 2.4,
                "type_bien": "unifamiliale",
            },
            {
                "comparable_id": "C-3",
                "source_id": "SIRF-3",
                "prix_vente": 399000,
                "date_vente": "2025-08-15",
                "surface": {"value": 116, "unit": "m2"},
                "distance_km": 3.1,
                "type_bien": "unifamiliale",
            },
        ],
        "ajustements": [{"source_id": "AJ-1", "montant": 12000, "validation_humaine": True}],
        "hypotheses": [{"texte": "Hypothese test", "source_ids": ["HYP-1"]}],
    }
    append_source_diagnostic(
        case,
        make_source_diagnostic("mamh", "skipped", "cache absent", stage="schema-test", severity="warning"),
    )
    attach_source_coverage(case)
    return case


def _payload_for(engine: RuntimeEngine, step_name: str, artifact: str) -> dict:
    payload = engine._artifact_payload(
        step_name,
        artifact,
        _case(),
        "PRET_REVISION_FINALE",
        [],
        [],
        {"approche_comparative": 411000.0},
    )
    payload["source_fixture"] = "schema-test.json"
    return payload


def test_all_pipeline_json_artifacts_have_schema_files():
    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
    json_artifacts = sorted({artifact for step in steps for artifact in step.writes if artifact.endswith(".json")})

    missing = [artifact for artifact in json_artifacts if not artifact_schema_path(artifact).exists()]

    assert missing == []


def test_schema_files_are_valid_json_objects():
    files = [*ARTIFACT_SCHEMA_DIR.glob("*.schema.json"), KNOWLEDGE_SCHEMA_PATH]

    assert files
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), path
        assert payload.get("$schema"), path
        assert payload.get("type") == "object", path


def test_runtime_artifact_payloads_satisfy_formal_schemas():
    engine = RuntimeEngine(steps=load_steps_from_pipeline_yaml(PIPELINE_PATH), strict_mode=False)
    failures: dict[str, list[str]] = {}

    for step in engine.steps:
        for artifact in step.writes:
            if not artifact.endswith(".json"):
                continue
            errors = validate_artifact_schema(artifact, _payload_for(engine, step.name, artifact))
            if errors:
                failures[f"{step.name}/{artifact}"] = errors

    assert failures == {}


def test_artifact_schema_reports_missing_required_field():
    payload = _payload_for(RuntimeEngine(strict_mode=False), "comps-market", "comparables_proposes.json")
    del payload["comparables"]

    errors = validate_artifact_schema("comparables_proposes.json", payload)

    assert any("$.comparables" in error for error in errors)


def test_json_schema_validator_reports_nested_type_errors():
    schema = {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"score": {"type": "number", "minimum": 0, "maximum": 1}},
                },
            }
        },
    }

    errors = validate_json_schema({"items": [{"score": "bad"}]}, schema)

    assert "$.items[0].score" in errors[0]


def test_knowledge_snapshot_satisfies_published_schema(tmp_path):
    session = {
        "session_id": "schema-session",
        "run_id": "run-schema",
        "session_dir": str(tmp_path),
    }
    result = {
        "dossier_id": "D-SCHEMA-001",
        "status": "PRET_REVISION_FINALE",
        "blocking_failures": [],
        "warnings": [],
        "events": [],
        "artifact_dir": str(tmp_path / "artifacts"),
    }
    artifact_index = {"schema_version": "artifact_index_v1", "artifacts_count": 0, "artifacts": []}

    snapshot = api.build_knowledge_snapshot(session, result, artifact_index)

    assert validate_knowledge_schema(snapshot) == []
