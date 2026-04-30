from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from preparer_paquet_evaluateurs_v0 import (
    build_case_rows,
    build_package_index,
    build_waiting_index,
    missing_required_artifacts,
    package_status,
    write_package,
)


class TestPaquetEvaluateursV0(unittest.TestCase):
    def test_waiting_index_marks_missing_real_runtime(self) -> None:
        index = build_waiting_index(Path("runtime-test"), "EN_ATTENTE_DOSSIERS_REELS")

        self.assertIn("EN_ATTENTE_DOSSIERS_REELS", index)
        self.assertIn("QUESTIONNAIRE-EVALUATEURS.md", index)

    def test_package_status_waits_without_summary(self) -> None:
        self.assertEqual(package_status(None, Path("runtime-test")), "EN_ATTENTE_DOSSIERS_REELS")

    def test_missing_required_artifacts_detects_absent_files(self) -> None:
        case = {"artifact_dir": "missing-dir"}

        missing = missing_required_artifacts(case)

        self.assertIn("compliance-qa.statut_sortie.json", missing)

    def test_case_rows_summarize_runtime_cases(self) -> None:
        rows = build_case_rows(
            [
                {
                    "artifact_dir": "runtime/case_1",
                    "dossier_id": "D-1",
                    "status": "BROUILLON",
                    "blocking_failures": ["B001"],
                    "warnings": ["W001", "W002"],
                }
            ]
        )

        self.assertEqual(rows[0]["cas"], "case_1")
        self.assertEqual(rows[0]["blocages"], "1")
        self.assertEqual(rows[0]["warnings"], "2")

    def test_build_package_index_lists_cases_and_questions(self) -> None:
        index = build_package_index(
            [
                {
                    "artifact_dir": "runtime/case_1",
                    "dossier_id": "D-1",
                    "status": "PRET_REVISION_FINALE",
                    "blocking_failures": [],
                    "warnings": [],
                }
            ],
            Path("runtime"),
            "PRET_A_ENVOYER",
        )

        self.assertIn("Questions ciblees", index)
        self.assertIn("D-1", index)

    def test_write_package_creates_waiting_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "runtime"
            out_dir = root / "package"
            runtime_dir.mkdir()

            status = write_package(runtime_dir, out_dir)

            self.assertEqual(status, "EN_ATTENTE_DOSSIERS_REELS")
            self.assertTrue((out_dir / "PAQUET-EVALUATEURS-V0.md").exists())
            self.assertTrue((out_dir / "REPONSES-EVALUATEURS-A-REMPLIR.csv").exists())
            self.assertTrue((out_dir / "MANIFESTE-CAS-PILOTES.csv").exists())

    def test_package_status_ready_when_artifacts_and_review_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runtime_dir = Path(tmp) / "runtime"
            case_dir = runtime_dir / "case"
            case_dir.mkdir(parents=True)
            for name in [
                "compliance-qa.statut_sortie.json",
                "compliance-qa.rapport_non_conformites.json",
                "compliance-qa.recommandations_corrections.md",
            ]:
                (case_dir / name).write_text("ok", encoding="utf-8")
            (runtime_dir / "REVUE-INTERNE-PILOTES-REELS-V0.md").write_text("ok", encoding="utf-8")
            summary = [{"artifact_dir": str(case_dir), "status": "A_REVOIR"}]
            (runtime_dir / "runtime_summary.json").write_text(json.dumps(summary), encoding="utf-8")

            self.assertEqual(package_status(summary, runtime_dir), "PRET_A_ENVOYER")


if __name__ == "__main__":
    unittest.main()
