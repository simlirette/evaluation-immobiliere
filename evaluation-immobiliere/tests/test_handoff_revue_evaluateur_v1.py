from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from generer_handoff_revue_evaluateur_v1 import (  # noqa: E402
    HANDOFF_FILES,
    HANDOFF_STATUS,
    STOP_POINT,
    generate_handoff,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT.parent / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TestHandoffRevueEvaluateurV1(unittest.TestCase):
    def test_generate_handoff_from_committed_v1_package(self) -> None:
        root = writable_tmp_dir("handoff_revue")
        try:
            result = generate_handoff(out_dir=root)
            manifest = load_json(root / HANDOFF_FILES["manifest"])
            brief = (root / HANDOFF_FILES["brief"]).read_text(encoding="utf-8")
            agenda = (root / HANDOFF_FILES["agenda"]).read_text(encoding="utf-8")
            checklist = (root / HANDOFF_FILES["checklist"]).read_text(encoding="utf-8")

            self.assertEqual(result["status"], HANDOFF_STATUS)
            self.assertEqual(manifest["status"], HANDOFF_STATUS)
            self.assertEqual(manifest["target"], "V1_PRE_EVALUATEUR")
            self.assertEqual(manifest["package_status"], "PRET_REVUE_EVALUATEUR_AGREE")
            self.assertEqual(manifest["field_validation"], "NON_REVENDIQUEE")
            self.assertTrue(manifest["no_evaluator_responses_invented"])
            self.assertFalse(manifest["real_field_validation_claimed"])
            self.assertEqual(manifest["stop_point"], STOP_POINT)
            self.assertGreaterEqual(manifest["questions_count"], 1)
            self.assertIn("Ne pas pre-remplir de reponse", brief)
            self.assertIn(STOP_POINT, agenda)
            self.assertIn("grille est vide", checklist)
            for filename in HANDOFF_FILES.values():
                self.assertTrue((root / filename).exists(), filename)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_claiming_real_field_validation_blocks_handoff(self) -> None:
        root = writable_tmp_dir("handoff_invalid")
        try:
            package_dir = root / "package"
            shutil.copytree(PROJECT_ROOT / "atelier" / "PAQUET-V1-PRE-EVALUATEUR", package_dir)
            manifest_path = package_dir / "DEMO-MANIFEST-V1.json"
            manifest = load_json(manifest_path)
            manifest["field_validation"] = "REVENDIQUEE"
            write_json(manifest_path, manifest)

            with self.assertRaises(ValueError):
                generate_handoff(package_dir=package_dir, out_dir=root / "out")
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
