from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from executer_dossiers_pilotes_reels_v0 import build_waiting_report, discover_real_pilot_cases


class TestExecuterPilotesReelsV0(unittest.TestCase):
    def test_discover_real_pilot_cases_ignores_drafts_and_synthetic_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixtures_dir = Path(tmp)
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


if __name__ == "__main__":
    unittest.main()
