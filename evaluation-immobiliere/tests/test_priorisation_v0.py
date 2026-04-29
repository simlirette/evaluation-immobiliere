from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from compiler_reponses_evaluateurs import compile_matrix
from prioriser_mvp import compute_score


class TestPriorisationV0(unittest.TestCase):
    def test_compute_score_uses_readiness_fields(self) -> None:
        score = compute_score(
            {
                "tache": "selection_comparables",
                "temps_moyen_min": "45",
                "frequence_par_mois": "20",
                "douleur_1_5": "5",
                "risque_conformite_1_5": "4",
                "automatisation_potentielle_1_5": "4",
                "complexite_technique_1_5": "2",
                "disponibilite_donnees_1_5": "4",
            }
        )
        self.assertGreater(score.score, 0)
        self.assertGreater(float(score.details["readiness_score"]), 0)

    def test_compile_matrix_aggregates_multiple_evaluators(self) -> None:
        rows = [
            {
                "respondant_id": "E1",
                "phase": "comps_market",
                "tache": "selection_comparables",
                "temps_moyen_min": "40",
                "frequence_par_mois": "12",
                "douleur_1_5": "5",
                "risque_conformite_1_5": "4",
                "automatisation_potentielle_1_5": "4",
                "complexite_technique_1_5": "3",
                "disponibilite_donnees_1_5": "4",
                "validation_humaine_obligatoire": "oui",
                "decision_non_delegable": "oui",
                "source_donnees_requise": "ventes comparables",
                "irritant_principal": "recherche longue",
                "commentaires": "prioritaire",
            },
            {
                "respondant_id": "E2",
                "phase": "comps_market",
                "tache": "selection_comparables",
                "temps_moyen_min": "20",
                "frequence_par_mois": "18",
                "douleur_1_5": "3",
                "risque_conformite_1_5": "4",
                "automatisation_potentielle_1_5": "5",
                "complexite_technique_1_5": "3",
                "disponibilite_donnees_1_5": "3",
                "validation_humaine_obligatoire": "oui",
                "decision_non_delegable": "oui",
                "source_donnees_requise": "MLS anonymise",
                "irritant_principal": "comparaison manuelle",
                "commentaires": "gros gain potentiel",
            },
        ]
        matrix = compile_matrix(rows)
        selection = next(row for row in matrix if row["tache"] == "selection_comparables")
        self.assertEqual(selection["temps_moyen_min"], "30")
        self.assertEqual(selection["repondants"], "2")
        self.assertEqual(selection["validation_humaine_obligatoire"], "oui")
        self.assertIn("MLS anonymise", selection["source_donnees_requise"])


if __name__ == "__main__":
    unittest.main()
