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

from outils.verifier_contrat_redaction_skills_v0 import validate_redaction_skill_contract


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_skill(path: Path, *, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "name: redaction-test",
                "description: Skill de test",
                "type: redaction",
                "agents:",
                "  - redaction",
                "sources:",
                "  - source-test",
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )


class TestContratRedactionSkillsV0(unittest.TestCase):
    def test_project_redaction_skills_contract_is_ready(self) -> None:
        report = validate_redaction_skill_contract(PROJECT_ROOT)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["skills_checked"], 4)
        self.assertGreaterEqual(report["anchors_checked"], 20)

    def test_detects_missing_required_anchor_term(self) -> None:
        tmp = writable_tmp_dir("redaction_contract_missing")
        try:
            skills_dir = tmp / "skills"
            write_skill(skills_dir / "redaction-test" / "SKILL.md", body="Ce skill couvre une ancre presente.")
            contract_path = tmp / "contract.json"
            write_json(
                contract_path,
                {
                    "schema_version": "redaction_skills_contract_v0",
                    "required_skills": [
                        {
                            "name": "redaction-test",
                            "required_anchors": [{"id": "test", "terms": ["ancre presente", "ancre absente"]}],
                        }
                    ],
                },
            )

            report = validate_redaction_skill_contract(tmp, contract_path=contract_path, skills_dir=skills_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("ancre test incomplete" in error for error in report["errors"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_detects_forbidden_d_reel_reference_in_active_skill(self) -> None:
        tmp = writable_tmp_dir("redaction_contract_dreel")
        try:
            skills_dir = tmp / "skills"
            write_skill(skills_dir / "redaction-test" / "SKILL.md", body="Ce skill ne doit pas charger D-REEL comme source active.")
            contract_path = tmp / "contract.json"
            write_json(
                contract_path,
                {
                    "schema_version": "redaction_skills_contract_v0",
                    "policy": {"forbidden_in_skill_md": ["D-REEL"]},
                    "required_skills": [
                        {
                            "name": "redaction-test",
                            "required_anchors": [{"id": "test", "terms": ["source active"]}],
                        }
                    ],
                },
            )

            report = validate_redaction_skill_contract(tmp, contract_path=contract_path, skills_dir=skills_dir)

            self.assertFalse(report["ok"])
            self.assertTrue(any("terme interdit" in error for error in report["errors"]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
