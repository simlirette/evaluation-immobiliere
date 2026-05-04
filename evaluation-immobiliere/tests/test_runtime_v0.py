from __future__ import annotations

import sys
import shutil
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeEngine, RuntimeStep, PipelineValidationError, validate_contract_rules, validate_pipeline_steps
import engine.runtime as runtime_module
from engine.skills import build_skill_registry


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestRuntimeV0(unittest.TestCase):
    def test_pipeline_validation_rejects_empty_writes(self) -> None:
        with self.assertRaises(PipelineValidationError):
            validate_pipeline_steps([RuntimeStep("agent", ["input"], [])])

    def test_run_case_data_persists_case_directory_and_metrics(self) -> None:
        case = {
            "dossier_id": "D-TEST",
            "date_reference": "2026-04-28",
            "comparables": [{"comparable_id": "C1", "prix_vente": 500000, "source_id": "SRC-1", "date_vente": "2026-02-01"}],
            "ajustements": [{"ajustement_id": "A1", "montant": 10000, "source_id": "SRC-1", "validation_humaine": True}],
            "confidence": 0.85,
        }
        root = writable_tmp_dir("runtime_case")
        try:
            result = RuntimeEngine().run_case_data(case, root, case_subdir=True)
            self.assertEqual(result["status"], "PRET_REVISION_FINALE")
            self.assertTrue(Path(result["artifact_dir"]).exists())
            self.assertGreaterEqual(result["metrics"]["wall_clock_seconds"], 0)
            self.assertIn("artifact_written", {event["event"] for event in result["events"]})
            self.assertIn("analyse-extraction-faits", result["skills_by_agent"]["data-facts"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_skill_registry_maps_project_skills_to_agents(self) -> None:
        registry = build_skill_registry(PROJECT_ROOT / "skills")
        self.assertEqual(len(registry["skills"]), 20)
        self.assertIn("analyse-conformite", registry["skills_by_agent"]["compliance-qa"])
        self.assertIn("redaction-rapport-evaluation", registry["skills_by_agent"]["redaction"])

    def test_run_case_data_blocks_on_contract_failure(self) -> None:
        case = {
            "dossier_id": "D-CONTRACT",
            "date_reference": "2026-04-28",
            "comparables": [],
            "ajustements": [],
            "confidence": 0.9,
        }
        root = writable_tmp_dir("runtime_contract")
        try:
            result = RuntimeEngine().run_case_data(case, root, case_subdir=True)
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertTrue(any("CONF002" in failure for failure in result["blocking_failures"]))
            events = [event["event"] for event in result["events"]]
            self.assertIn("contract_invalid", events)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_validate_contract_rules_detects_temporal_window_violation(self) -> None:
        payload = {
            "date_reference": "2026-04-28",
            "comparables": [
                {
                    "comparable_id": "C-OLD",
                    "source_id": "SRC-OLD",
                    "score": 0.5,
                    "date_vente": "2020-01-01",
                }
            ],
        }
        failures = validate_contract_rules("comparables_proposes.json", payload)
        self.assertTrue(any("CONF005" in failure for failure in failures))

    def test_validate_contract_rules_detects_inter_approach_incoherence(self) -> None:
        payload = {
            "status": "PRET_REVISION_FINALE",
            "blocking_failures": [],
            "warnings": [],
            "valuation_values": {
                "approche_comparative": 100000,
                "approche_cout": 180000,
                "approche_revenu": 140000,
            },
        }
        failures = validate_contract_rules("statut_sortie.json", payload)
        self.assertTrue(any("CONF007" in failure for failure in failures))

    def test_validate_contract_rules_rejects_status_outside_contract(self) -> None:
        payload = {
            "status": "INCONNU",
            "blocking_failures": [],
            "warnings": [],
            "valuation_values": {},
        }
        failures = validate_contract_rules("statut_sortie.json", payload)
        self.assertTrue(any("CONF004" in failure for failure in failures))

    def test_validate_contract_rules_rejects_score_outside_contract_range(self) -> None:
        payload = {
            "date_reference": "2026-04-28",
            "comparables": [
                {"comparable_id": "C-HIGH", "source_id": "SRC-1", "score": 1.25, "date_vente": "2026-01-01"},
            ],
        }
        failures = validate_contract_rules("comparables_proposes.json", payload)
        self.assertTrue(any("CONF006" in failure for failure in failures))

    def test_run_case_data_collects_valuation_values_from_valuation_artifacts(self) -> None:
        case = {
            "dossier_id": "D-VAL",
            "date_reference": "2026-04-28",
            "comparables": [
                {"comparable_id": "C1", "prix_vente": 100000, "source_id": "SRC-1", "date_vente": "2025-12-01"},
                {"comparable_id": "C2", "prix_vente": 200000, "source_id": "SRC-2", "date_vente": "2026-01-01"},
                {"comparable_id": "C3", "prix_vente": 1000000, "source_id": "SRC-3", "date_vente": "2026-02-01"},
            ],
            "ajustements": [],
            "confidence": 0.9,
        }
        root = writable_tmp_dir("runtime_valuation")
        try:
            result = RuntimeEngine().run_case_data(case, root, case_subdir=True)
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertTrue(any("CONF007" in failure for failure in result["blocking_failures"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_compute_qa_uses_contract_thresholds_for_distance_and_confidence(self) -> None:
        original = runtime_module._CONTRACT_TREE_CACHE
        runtime_module._CONTRACT_TREE_CACHE = {
            "contracts": {
                "rapport_conformite": {
                    "constraints": {
                        "max_comparable_distance_km_warning": 5,
                        "confidence_min_warning": 0.95,
                    }
                }
            }
        }
        try:
            case = {
                "dossier_id": "D-T",
                "date_reference": "2026-04-28",
                "comparables": [{"comparable_id": "C1", "distance_km": 6, "source_id": "SRC-1", "date_vente": "2026-01-01"}],
                "ajustements": [],
                "confidence": 0.90,
            }
            _, _, warnings = RuntimeEngine()._compute_qa(case)
            self.assertIn("W002: comparable eloigne", warnings)
            self.assertIn("W001: confiance faible", warnings)
        finally:
            runtime_module._CONTRACT_TREE_CACHE = original


if __name__ == "__main__":
    unittest.main()
