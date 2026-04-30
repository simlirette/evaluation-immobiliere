from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from preparer_durcissement_contrats_v0 import (
    build_contract_decisions,
    build_hardening_markdown,
    build_waiting_report,
    infer_contract_area,
    parse_contract_constraints,
)


class TestDurcissementContratsV0(unittest.TestCase):
    def test_parse_contract_constraints_extracts_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contracts.yaml"
            path.write_text(
                "\n".join(
                    [
                        "constraints:",
                        "  max_comparable_distance_km_warning: 30",
                        "  ajustement_sensible_montant_min: 25000",
                        "  confidence_min_warning: 0.60",
                    ]
                ),
                encoding="utf-8",
            )

            constraints = parse_contract_constraints(path)

        self.assertEqual(constraints["max_comparable_distance_km_warning"], "30")
        self.assertEqual(constraints["confidence_min_warning"], "0.60")

    def test_waiting_report_keeps_current_thresholds_visible(self) -> None:
        report = build_waiting_report(
            Path("runtime-test"),
            Path("contracts.yaml"),
            {"confidence_min_warning": "0.60"},
        )

        self.assertIn("EN_ATTENTE_SORTIES_PHASE_3", report)
        self.assertIn("confidence_min_warning", report)

    def test_infer_contract_area_maps_known_issue_types(self) -> None:
        self.assertEqual(infer_contract_area("W001: confiance faible"), "confidence_min_warning")
        self.assertEqual(infer_contract_area("B005: ajustement sensible sans validation"), "ajustement_sensible_montant_min")
        self.assertEqual(infer_contract_area("W002: comparable eloigne"), "max_comparable_distance_km_warning")

    def test_build_contract_decisions_prioritizes_contract_failures_and_warnings(self) -> None:
        summary = [
            {
                "status": "BROUILLON",
                "blocking_failures": [],
                "warnings": ["W001: confiance faible"],
            }
        ]
        contracts_report = {"files_checked": 3, "files_invalid": 1, "failures": []}

        decisions = build_contract_decisions(summary, contracts_report)

        self.assertEqual(decisions[0]["priority"], "P0")
        self.assertTrue(any(item["area"] == "confidence_min_warning" for item in decisions))

    def test_build_hardening_markdown_includes_decision_table(self) -> None:
        markdown = build_hardening_markdown(
            [{"status": "PRET_REVISION_FINALE", "blocking_failures": [], "warnings": []}],
            {"files_checked": 1, "files_invalid": 0, "failures": []},
            {"confidence_min_warning": "0.60"},
        )

        self.assertIn("Decisions a prendre", markdown)
        self.assertIn("Conserver les seuils actuels", markdown)


if __name__ == "__main__":
    unittest.main()
