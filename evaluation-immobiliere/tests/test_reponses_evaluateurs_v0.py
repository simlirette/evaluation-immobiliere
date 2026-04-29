from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from valider_reponses_evaluateurs import RESPONSE_FIELDS, validate_headers, validate_rows


def response_row(**overrides: str) -> dict[str, str]:
    row = {field: "" for field in RESPONSE_FIELDS}
    row.update(
        {
            "respondant_id": "EVAL-001",
            "role": "senior",
            "segment": "residentiel",
            "phase": "comps_market",
            "tache": "selection_comparables",
            "temps_moyen_min": "30",
            "frequence_par_mois": "12",
            "douleur_1_5": "4",
            "risque_conformite_1_5": "4",
            "automatisation_potentielle_1_5": "5",
            "complexite_technique_1_5": "3",
            "disponibilite_donnees_1_5": "4",
            "validation_humaine_obligatoire": "oui",
            "decision_non_delegable": "oui",
        }
    )
    row.update(overrides)
    return row


class TestReponsesEvaluateursV0(unittest.TestCase):
    def test_empty_file_is_ready_to_receive_responses(self) -> None:
        result = validate_rows(Path("responses.csv"), [])
        self.assertTrue(result.ok)
        self.assertEqual(result.active_rows, 0)
        self.assertEqual(len(result.warnings), 1)

    def test_valid_response_row_passes(self) -> None:
        result = validate_rows(Path("responses.csv"), [response_row()])
        self.assertTrue(result.ok)
        self.assertEqual(result.active_rows, 1)
        self.assertEqual(result.respondent_count, 1)

    def test_invalid_rating_boolean_phase_and_duplicate_fail(self) -> None:
        rows = [
            response_row(douleur_1_5="6", validation_humaine_obligatoire="peut-etre"),
            response_row(phase="intake"),
        ]
        result = validate_rows(Path("responses.csv"), rows)
        messages = " ".join(issue.message for issue in result.errors)
        self.assertFalse(result.ok)
        self.assertIn("entre 1 et 5", messages)
        self.assertIn("oui/non", messages)
        self.assertIn("Phase incoherente", messages)
        self.assertIn("Doublon", messages)

    def test_template_placeholder_rows_are_not_active(self) -> None:
        result = validate_rows(
            Path("template.csv"),
            [
                response_row(
                    respondant_id="",
                    phase="intake",
                    tache="reception_mandat",
                    temps_moyen_min="",
                    frequence_par_mois="",
                    douleur_1_5="",
                    risque_conformite_1_5="",
                    automatisation_potentielle_1_5="",
                    complexite_technique_1_5="",
                    disponibilite_donnees_1_5="",
                    validation_humaine_obligatoire="",
                    decision_non_delegable="",
                )
            ],
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.active_rows, 0)

    def test_missing_header_is_error_and_extra_header_is_warning(self) -> None:
        errors, warnings = validate_headers(["respondant_id", "tache", "extra"])
        self.assertGreater(len(errors), 0)
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
