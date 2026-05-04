from __future__ import annotations

import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from outils.verifier_readiness_skills_v0 import validate_skill_readiness


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestReadinessSkillsV0(unittest.TestCase):
    def test_project_skills_registry_matrix_and_agent_configs_are_ready(self) -> None:
        report = validate_skill_readiness(PROJECT_ROOT)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["skills_count"], 20)
        self.assertEqual(report["pipeline_steps_count"], 5)

    def test_detects_matrix_drift(self) -> None:
        tmp = writable_tmp_dir("skills_matrix")
        try:
            matrix_path = tmp / "AGENT-SKILLS-MATRIX.md"
            matrix_path.write_text("# stale\n", encoding="utf-8")

            report = validate_skill_readiness(PROJECT_ROOT, matrix_path=matrix_path)

            self.assertFalse(report["ok"])
            self.assertTrue(any("matrice non synchronisee" in error for error in report["errors"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_detects_unknown_skill_in_agent_config(self) -> None:
        tmp = writable_tmp_dir("skills_config")
        try:
            integration_dir = tmp / "integration"
            shutil.copytree(PROJECT_ROOT / "integration", integration_dir)
            config_path = integration_dir / "AGENTCONFIG-DATA-FACTS-V0.yaml"
            config_text = config_path.read_text(encoding="utf-8")
            config_path.write_text(config_text.replace("\nquality_gates:", "\n  - skill-inexistant\n\nquality_gates:"), encoding="utf-8")

            report = validate_skill_readiness(PROJECT_ROOT, integration_dir=integration_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("skills_allowed inconnus" in error for error in report["errors"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
