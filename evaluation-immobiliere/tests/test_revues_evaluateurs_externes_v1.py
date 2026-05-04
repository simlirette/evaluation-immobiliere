from __future__ import annotations

import csv
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

from verifier_revues_evaluateurs_externes_v1 import (  # noqa: E402
    EXTERNAL_REVIEWS_DEFAULT,
    RUNTIME_DIR_DEFAULT,
    validate_external_evaluator_reviews,
    write_outputs,
)


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


class TestRevuesEvaluateursExternesV1(unittest.TestCase):
    def test_project_fixture_passes_strict_gate_with_conditionnal_gaps(self) -> None:
        report = validate_external_evaluator_reviews(EXTERNAL_REVIEWS_DEFAULT, strict=True)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["decision"], "GO_CONDITIONNEL_ECARTS_EVALUATEURS")
        self.assertEqual(report["reviewers_count"], 2)
        self.assertEqual(report["reviewed_pilot_cases"], 3)
        self.assertEqual(report["status_disagreements"], 0)
        self.assertEqual(report["gap_counts_by_priority"]["P1"], 1)
        self.assertEqual(report["gap_counts_by_priority"]["P2"], 2)

    def test_strict_gate_fails_when_fixture_is_missing(self) -> None:
        root = writable_tmp_dir("revues_missing")
        try:
            report = validate_external_evaluator_reviews(root / "missing.json", strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("absente" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_p0_gap_blocks_external_review_gate(self) -> None:
        root = writable_tmp_dir("revues_p0")
        try:
            payload = load_json(EXTERNAL_REVIEWS_DEFAULT)
            payload["reviews"][1]["gaps"][0]["priority"] = "P0"
            path = root / "reviews.json"
            write_json(path, payload)

            report = validate_external_evaluator_reviews(path, strict=True)

            self.assertFalse(report["ok"])
            self.assertTrue(any("ecart bloquant P0" in error for error in report["errors"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_write_outputs_writes_markdown_and_gap_matrix(self) -> None:
        root = writable_tmp_dir("revues_outputs")
        try:
            report = validate_external_evaluator_reviews(EXTERNAL_REVIEWS_DEFAULT, runtime_dir=RUNTIME_DIR_DEFAULT, strict=True)
            json_out = root / "report.json"
            markdown_out = root / "report.md"
            gap_report_out = root / "gap_report.md"
            gap_matrix_out = root / "gaps.csv"

            write_outputs(report, json_out, markdown_out, gap_report_out, gap_matrix_out)

            self.assertTrue(json_out.exists())
            self.assertIn("Revues evaluateurs externes Evidence V1", markdown_out.read_text(encoding="utf-8"))
            self.assertIn("Rapport ecarts evaluateurs externes V1", gap_report_out.read_text(encoding="utf-8"))
            with gap_matrix_out.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
