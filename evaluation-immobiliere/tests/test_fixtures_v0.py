from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from valider_fixtures_v0 import validate_fixture


def fixture_payload(**overrides: object) -> dict:
    payload: dict[str, object] = {
        "dossier_id": "D-PILOTE-TEST",
        "date_reference": "2026-04-28",
        "zone": "SECTEUR-ANONYMISE",
        "surface": {"value": 1200, "unit": "pi2"},
        "comparables": [
            {
                "comparable_id": "C1",
                "prix_vente": 500000,
                "source_id": "SRC-1",
                "surface": {"value": 1180, "unit": "pi2"},
            }
        ],
        "ajustements": [
            {
                "ajustement_id": "A1",
                "montant": 10000,
                "source_id": "SRC-1",
                "validation_humaine": True,
            }
        ],
        "confidence": 0.85,
    }
    payload.update(overrides)
    return payload


def validate_payload(payload: dict, *, strict: bool = True):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "case.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return validate_fixture(path, strict=strict)


class TestFixturesV0(unittest.TestCase):
    def test_strict_valid_fixture_passes(self) -> None:
        result = validate_payload(fixture_payload())
        self.assertTrue(result.ok)

    def test_missing_required_strict_field_fails(self) -> None:
        payload = fixture_payload()
        payload.pop("surface")
        result = validate_payload(payload)
        self.assertFalse(result.ok)
        self.assertIn("surface", " ".join(issue.location for issue in result.errors))

    def test_sensitive_adjustment_without_human_validation_fails(self) -> None:
        result = validate_payload(
            fixture_payload(
                ajustements=[
                    {
                        "ajustement_id": "A1",
                        "montant": 30000,
                        "source_id": "SRC-1",
                        "validation_humaine": False,
                    }
                ]
            )
        )
        self.assertFalse(result.ok)
        self.assertIn("Ajustement sensible", " ".join(issue.message for issue in result.errors))

    def test_low_confidence_is_warning_not_error(self) -> None:
        result = validate_payload(fixture_payload(confidence=0.45))
        self.assertTrue(result.ok)
        self.assertEqual(len(result.warnings), 1)

    def test_possible_precise_address_fails_anonymization(self) -> None:
        result = validate_payload(fixture_payload(zone="123 rue Principale"))
        self.assertFalse(result.ok)
        self.assertIn("Possible information", " ".join(issue.message for issue in result.errors))


if __name__ == "__main__":
    unittest.main()
