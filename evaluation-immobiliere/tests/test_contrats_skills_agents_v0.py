from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from outils.verifier_contrats_skills_agents_v0 import validate_agent_skill_contracts


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TestContratsSkillsAgentsV0(unittest.TestCase):
    def test_project_agent_skill_contracts_are_ready(self) -> None:
        report = validate_agent_skill_contracts(PROJECT_ROOT)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["agents_checked"], 4)
        self.assertGreaterEqual(report["skills_checked"], 8)
        self.assertGreaterEqual(report["anchors_checked"], 30)

    def test_detects_required_skill_not_allowed_by_agent_config(self) -> None:
        tmp = writable_tmp_dir("agent_contract_config")
        try:
            contract_path = tmp / "contract.json"
            write_json(
                contract_path,
                {
                    "schema_version": "agent_skills_contracts_v0",
                    "agents": [
                        {
                            "agent_type": "data-facts",
                            "agent_config": "AGENTCONFIG-DATA-FACTS-V0.yaml",
                            "required_skills": [
                                {
                                    "name": "analyse-conformite",
                                    "required_anchors": [{"id": "normes", "terms": ["CUSPAP"]}],
                                }
                            ],
                        }
                    ],
                },
            )

            report = validate_agent_skill_contracts(PROJECT_ROOT, contract_path=contract_path)

            self.assertFalse(report["ok"])
            self.assertTrue(any("non autorise" in error for error in report["errors"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_detects_missing_anchor_term(self) -> None:
        tmp = writable_tmp_dir("agent_contract_anchor")
        try:
            contract_path = tmp / "contract.json"
            write_json(
                contract_path,
                {
                    "schema_version": "agent_skills_contracts_v0",
                    "agents": [
                        {
                            "agent_type": "comps-market",
                            "agent_config": "AGENTCONFIG-COMPS-MARKET-V0.yaml",
                            "required_skills": [
                                {
                                    "name": "analyse-selection-comparables",
                                    "required_anchors": [{"id": "missing", "terms": ["terme impossible absent"]}],
                                }
                            ],
                        }
                    ],
                },
            )

            report = validate_agent_skill_contracts(PROJECT_ROOT, contract_path=contract_path)

            self.assertFalse(report["ok"])
            self.assertTrue(any("ancre missing incomplete" in error for error in report["errors"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
