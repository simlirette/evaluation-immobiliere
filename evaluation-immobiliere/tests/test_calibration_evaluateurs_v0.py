from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from calibrer_reponses_evaluateurs_v0 import (
    CALIBRATION_FIELDS,
    build_backlog_markdown,
    build_calibration_report,
    build_markdown_report,
    read_csv_rows,
    run_calibration,
    write_csv_template,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def quality_report() -> dict:
    return {
        "status_counts": {"BROUILLON": 1, "A_REVOIR": 1},
        "cases": [
            {
                "dossier_id": "D-001",
                "status": "BROUILLON",
                "blocking_failures": [],
                "warnings": ["W001: confiance faible"],
                "artifacts": {"missing": []},
            },
            {
                "dossier_id": "D-002",
                "status": "A_REVOIR",
                "blocking_failures": ["CONF005: comparable[2] hors fenetre temporelle"],
                "warnings": ["W002: comparable eloigne"],
                "artifacts": {"missing": ["redaction.brouillon_rapport.md"]},
            },
        ],
    }


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALIBRATION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class TestCalibrationEvaluateursV0(unittest.TestCase):
    def test_empty_responses_keep_waiting_status_and_runtime_questions(self) -> None:
        report = build_calibration_report([], quality_report(), Path("calibration.csv"))
        markdown = build_markdown_report(report)
        backlog = build_backlog_markdown(report)

        self.assertEqual(report["status"], "PRET_A_RECEVOIR_REPONSES")
        self.assertEqual(report["responses_count"], 0)
        self.assertEqual(report["summary"]["backlog_items"], 0)
        self.assertGreaterEqual(len(report["runtime_questions"]), 3)
        self.assertIn("Ne pas inventer", markdown)
        self.assertIn("Aucun item confirme", backlog)

    def test_active_responses_create_status_and_scoring_backlog(self) -> None:
        rows = [
            {
                "respondant_id": "EV-1",
                "role": "evaluateur",
                "dossier_id": "D-001",
                "cible_type": "statut",
                "cible_id": "statut_sortie",
                "artefact": "compliance-qa.statut_sortie.json",
                "statut_attendu": "PRET_REVISION_FINALE",
                "decision": "ajuster",
                "impact_1_5": "4",
                "effort_1_5": "2",
                "priorite": "",
                "commentaire": "Le dossier est revisable malgre la confiance faible.",
            },
            {
                "respondant_id": "EV-1",
                "role": "evaluateur",
                "dossier_id": "D-002",
                "cible_type": "comparable",
                "cible_id": "C-OLD",
                "artefact": "comps-market.comparables_proposes.json",
                "statut_attendu": "",
                "decision": "refuser",
                "impact_1_5": "5",
                "effort_1_5": "3",
                "priorite": "",
                "commentaire": "Comparable trop ancien pour ce secteur.",
            },
        ]

        report = build_calibration_report(rows, quality_report(), Path("calibration.csv"))

        self.assertEqual(report["status"], "CALIBRATION_COMPILEE")
        self.assertEqual(report["respondent_count"], 1)
        self.assertEqual(report["summary"]["status_disagreements"], 1)
        self.assertEqual(report["summary"]["backlog_items"], 2)
        self.assertEqual(report["backlog"][0]["priority"], "P0")
        self.assertEqual(report["backlog"][1]["area"], "scoring_comparables")

    def test_simulated_evaluator_fixture_compiles_status_blocking_and_scoring_backlog(self) -> None:
        fixture_path = FIXTURES_DIR / "calibration_evaluateurs_simulee.csv"
        report = build_calibration_report(
            read_csv_rows(fixture_path),
            {
                "status_counts": {"BROUILLON": 1, "A_REVOIR": 1},
                "cases": [
                    {
                        "dossier_id": "D-REEL-002",
                        "status": "BROUILLON",
                        "blocking_failures": [],
                        "warnings": ["W001: confiance faible"],
                        "artifacts": {"missing": []},
                    },
                    {
                        "dossier_id": "D-REEL-003",
                        "status": "A_REVOIR",
                        "blocking_failures": ["CONF005: comparable hors fenetre temporelle"],
                        "warnings": [],
                        "artifacts": {"missing": []},
                    },
                ],
            },
            fixture_path,
        )

        self.assertEqual(report["status"], "CALIBRATION_COMPILEE")
        self.assertEqual(report["responses_count"], 3)
        self.assertEqual(report["summary"]["status_disagreements"], 1)
        self.assertEqual(report["summary"]["backlog_items"], 2)
        self.assertIn("P0", {item["priority"] for item in report["backlog"]})
        self.assertIn("P2", {item["priority"] for item in report["backlog"]})
        self.assertIn("scoring_comparables", {item["area"] for item in report["backlog"]})

    def test_invalid_response_is_marked_a_corriger(self) -> None:
        rows = [
            {
                "respondant_id": "EV-1",
                "dossier_id": "D-001",
                "cible_type": "inconnu",
                "decision": "mystere",
                "impact_1_5": "invalide",
            }
        ]

        report = build_calibration_report(rows, quality_report(), Path("calibration.csv"))

        self.assertEqual(report["status"], "A_CORRIGER")
        self.assertTrue(any(issue["severity"] == "error" for issue in report["issues"]))

    def test_run_calibration_writes_json_markdown_and_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "calibration.csv"
            quality_path = root / "quality.json"
            json_out = root / "calibration.json"
            report_out = root / "report.md"
            backlog_out = root / "backlog.md"
            write_rows(
                input_path,
                [
                    {
                        "respondant_id": "EV-1",
                        "role": "evaluateur",
                        "dossier_id": "D-002",
                        "cible_type": "blocage",
                        "cible_id": "CONF005",
                        "artefact": "comps-market.comparables_proposes.json",
                        "statut_attendu": "",
                        "decision": "confirmer",
                        "impact_1_5": "4",
                        "effort_1_5": "1",
                        "priorite": "",
                        "commentaire": "Blocage valide.",
                    }
                ],
            )
            quality_path.write_text(json.dumps(quality_report()), encoding="utf-8")

            report = run_calibration(input_path, quality_path, json_out, report_out, backlog_out)

            self.assertTrue(json_out.exists())
            self.assertTrue(report_out.exists())
            self.assertTrue(backlog_out.exists())
            self.assertEqual(report["status"], "CALIBRATION_COMPILEE")

    def test_write_csv_template_writes_header_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "template.csv"
            write_csv_template(path)

            self.assertEqual(path.read_text(encoding="utf-8").strip(), ",".join(CALIBRATION_FIELDS))


if __name__ == "__main__":
    unittest.main()
