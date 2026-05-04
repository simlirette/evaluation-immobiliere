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

from generer_paquet_v1_pre_evaluateur import (  # noqa: E402
    PACKAGE_FILES,
    PACKAGE_STATUS,
    SUMMARY_DEFAULT,
    generate_package,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT.parent / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


class TestPaquetV1PreEvaluateur(unittest.TestCase):
    def test_generate_package_from_nominal_runtime_case(self) -> None:
        root = writable_tmp_dir("paquet_v1_pre_evaluateur")
        try:
            result = generate_package(summary_path=SUMMARY_DEFAULT, out_dir=root, dossier_id="D-001")
            manifest = load_json(root / PACKAGE_FILES["manifest"])
            grid = (root / PACKAGE_FILES["grille"]).read_text(encoding="utf-8")
            limits = (root / PACKAGE_FILES["limites"]).read_text(encoding="utf-8")

            self.assertEqual(result["status"], PACKAGE_STATUS)
            self.assertEqual(result["dossier_id"], "D-001")
            self.assertEqual(manifest["status"], PACKAGE_STATUS)
            self.assertEqual(manifest["target"], "V1_PRE_EVALUATEUR")
            self.assertEqual(manifest["field_validation"], "NON_REVENDIQUEE")
            self.assertEqual(manifest["runtime_status"], "PRET_REVISION_FINALE")
            self.assertGreaterEqual(manifest["comparables_count"], 1)
            self.assertIn("approche_comparative", manifest["valuation_values"])
            self.assertIn("A REMPLIR PAR L'EVALUATEUR", grid)
            self.assertIn("Aucune validation terrain reelle", limits)
            for filename in PACKAGE_FILES.values():
                self.assertTrue((root / filename).exists(), filename)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
