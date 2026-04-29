from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api import UI_PATH, list_fixtures


class TestApiV0(unittest.TestCase):
    def test_list_fixtures_excludes_templates(self) -> None:
        fixtures = list_fixtures()
        names = {fixture["name"] for fixture in fixtures}
        self.assertIn("case_nominal.json", names)
        self.assertNotIn("template_dossier_anonymise.json", names)

    def test_ui_file_exists(self) -> None:
        self.assertTrue(UI_PATH.exists())


if __name__ == "__main__":
    unittest.main()
