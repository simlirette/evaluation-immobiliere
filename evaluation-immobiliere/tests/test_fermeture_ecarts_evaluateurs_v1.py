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

from verifier_fermeture_ecarts_evaluateurs_v1 import (  # noqa: E402
    REGISTER_DEFAULT,
    build_pv_signature_markdown,
    validate_gap_closure_register,
    write_outputs,
)
from verifier_revues_evaluateurs_externes_v1 import EXTERNAL_REVIEWS_DEFAULT  # noqa: E402


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TestFermetureEcartsEvaluateursV1(unittest.TestCase):
    def test_project_register_closes_external_gaps_and_signatures(self) -> None:
        report = validate_gap_closure_register(REGISTER_DEFAULT, strict=True)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["decision"], "GO_PROD_PREPARATION")
        self.assertEqual(report["external_gaps_to_close"], 3)
        self.assertIn("Lead Metier", report["signed_roles"])
        self.assertIn("Product", report["signed_roles"])
        self.assertIn("GO_PROD_PREPARATION", build_pv_signature_markdown(report))

    def test_strict_gate_fails_when_register_is_missing(self) -> None:
        root = writable_tmp_dir("closure_missing")
        try:
            report = validate_gap_closure_register(root / "missing.json", strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("registre fermeture ecarts absent" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_missing_signature_blocks_strict_gate(self) -> None:
        root = writable_tmp_dir("closure_signature")
        try:
            payload = load_json(REGISTER_DEFAULT)
            payload["signatures"] = [item for item in payload["signatures"] if item["role"] != "Product"]
            path = root / "register.json"
            write_json(path, payload)

            report = validate_gap_closure_register(path, strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("signature requise manquante: Product" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_open_p1_or_p2_gap_blocks_strict_gate(self) -> None:
        root = writable_tmp_dir("closure_open")
        try:
            payload = load_json(REGISTER_DEFAULT)
            payload["closures"][0]["closure_status"] = "OUVERT"
            path = root / "register.json"
            write_json(path, payload)

            report = validate_gap_closure_register(path, strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("statut fermeture invalide" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_register_tied_to_other_fixture_is_rejected_in_strict_mode(self) -> None:
        root = writable_tmp_dir("closure_source")
        try:
            payload = load_json(REGISTER_DEFAULT)
            payload["source_external_reviews_fixture"] = "evaluation-immobiliere/tests/fixtures_external/other.json"
            path = root / "register.json"
            write_json(path, payload)

            report = validate_gap_closure_register(path, external_reviews_path=EXTERNAL_REVIEWS_DEFAULT, strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("autre fixture" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_write_outputs_writes_evidence_and_signature_pv(self) -> None:
        root = writable_tmp_dir("closure_outputs")
        try:
            report = validate_gap_closure_register(REGISTER_DEFAULT, strict=True)
            json_out = root / "report.json"
            markdown_out = root / "report.md"
            pv_out = root / "pv.md"

            write_outputs(report, json_out, markdown_out, pv_out)

            self.assertTrue(json_out.exists())
            self.assertIn("Fermeture ecarts evaluateurs Evidence V1", markdown_out.read_text(encoding="utf-8"))
            self.assertIn("PV SIGNATURE METIER V1", pv_out.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
