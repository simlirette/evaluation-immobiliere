from __future__ import annotations

import sys
import shutil
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from executer_dossiers_pilotes_reels_v0 import FIXTURES_DIR, build_waiting_report, discover_real_pilot_cases, reset_output_dir

TEST_TMP_ROOT = Path(__file__).resolve().parents[2] / ".test-tmp" / "test_executer_pilotes_reels_v0"


class TestExecuterPilotesReelsV0(unittest.TestCase):
    def make_tmp(self, name: str) -> Path:
        path = TEST_TMP_ROOT / name
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_default_fixture_dir_is_external_to_repo_baseline(self) -> None:
        self.assertIn("fixtures_external", FIXTURES_DIR.as_posix())

    def test_discover_real_pilot_cases_ignores_drafts_and_synthetic_cases(self) -> None:
        fixtures_dir = self.make_tmp("fixtures")
        (fixtures_dir / "case_pilote_reel_002.json").write_text("{}", encoding="utf-8")
        (fixtures_dir / "case_pilote_reel_001.json").write_text("{}", encoding="utf-8")
        (fixtures_dir / "case_nominal.json").write_text("{}", encoding="utf-8")
        (fixtures_dir / "draft_dossier_reel_001.json").write_text("{}", encoding="utf-8")

        names = [path.name for path in discover_real_pilot_cases(fixtures_dir)]

        self.assertEqual(names, ["case_pilote_reel_001.json", "case_pilote_reel_002.json"])

    def test_build_waiting_report_explains_missing_real_cases(self) -> None:
        report = build_waiting_report(Path("fixtures-test"))

        self.assertIn("EN_ATTENTE_DOSSIERS", report)
        self.assertIn("case_pilote_reel_*.json", report)
        self.assertIn("fixtures-test", report)
        self.assertIn("hors repo", report)

    def test_reset_output_dir_preserves_ingestion_context(self) -> None:
        out_dir = self.make_tmp("runtime")
        (out_dir / "case_old").mkdir(parents=True)
        (out_dir / "case_old" / "artifact.json").write_text("{}", encoding="utf-8")
        (out_dir / "ingestion_v0").mkdir()
        (out_dir / "ingestion_v0" / "trace.json").write_text("[]", encoding="utf-8")
        (out_dir / "source_text").mkdir()
        (out_dir / "source_text" / "D-001.txt").write_text("texte", encoding="utf-8")
        (out_dir / "REVUE-INTERNE-PILOTES-REELS-V0.md").write_text("revue", encoding="utf-8")
        (out_dir / "runtime_registry.json").write_text('{"runs": []}', encoding="utf-8")

        reset_output_dir(out_dir)

        self.assertFalse((out_dir / "case_old").exists())
        self.assertTrue((out_dir / "ingestion_v0" / "trace.json").exists())
        self.assertTrue((out_dir / "source_text" / "D-001.txt").exists())
        self.assertTrue((out_dir / "REVUE-INTERNE-PILOTES-REELS-V0.md").exists())
        self.assertTrue((out_dir / "runtime_registry.json").exists())


if __name__ == "__main__":
    unittest.main()
