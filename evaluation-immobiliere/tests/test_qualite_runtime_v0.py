from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from outils.analyser_qualite_runtime_v0 import build_markdown, build_quality_report, write_quality_report


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class TestQualiteRuntimeV0(unittest.TestCase):
    def test_build_quality_report_collects_case_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "runtime"
            case_dir = runtime_dir / "case_001"
            ingestion_dir = runtime_dir / "ingestion_v0"
            summary_path = runtime_dir / "runtime_summary.json"

            write_json(
                summary_path,
                [
                    {
                        "dossier_id": "D-001",
                        "status": "BROUILLON",
                        "blocking_failures": [],
                        "warnings": ["W001: confiance faible"],
                        "artifact_dir": case_dir.as_posix(),
                    }
                ],
            )
            write_json(
                case_dir / "data-facts.fiche_bien.json",
                {
                    "dossier_id": "D-001",
                    "step": "data-facts",
                    "artifact": "fiche_bien.json",
                    "source_fixture": "case.json",
                    "date_reference": "2026-04-28",
                    "surface": {"value": 1000, "unit": "pi2"},
                    "confidence": 0.7,
                    "source_ids": ["SRC-1"],
                },
            )
            write_json(
                case_dir / "comps-market.comparables_proposes.json",
                {
                    "dossier_id": "D-001",
                    "step": "comps-market",
                    "artifact": "comparables_proposes.json",
                    "source_fixture": "case.json",
                    "date_reference": "2026-04-28",
                    "comparables": [
                        {"comparable_id": "C1", "source_id": "SRC-1", "score": 0.8, "date_vente": "2026-01-01"},
                        {"comparable_id": "C2", "source_id": "SRC-2", "score": 0.6, "date_vente": "2025-12-01"},
                    ],
                },
            )
            write_json(
                case_dir / "valuation-draft.calculs_approche_comparative.json",
                {"trace": {"base_value": 1}},
            )
            write_json(case_dir / "valuation-draft.calculs_approche_cout.json", {"trace": {"base_value": 1}})
            write_json(case_dir / "valuation-draft.calculs_approche_revenu.json", {"trace": {"base_value": 1}})
            write_json(
                ingestion_dir / "D-001" / "dossier_normalise.json",
                {
                    "dossier_id": "D-001",
                    "quality": {
                        "review_flags": ["SOURCE_TEXT_CONTAINS_MASKED_VALUES"],
                        "missing_fields": ["type_bien"],
                    },
                    "source_documents": [{"text_stats": {"masked_token_count": 2}}],
                },
            )
            write_json(
                ingestion_dir / "D-001" / "trace_champs.json",
                [
                    {"field_path": "dossier_id", "source_ids": ["SRC-1"], "review_status": "MACHINE_READY", "value_status": "PRESENT"},
                    {"field_path": "zone", "source_ids": [], "review_status": "NEEDS_HUMAN_REVIEW", "value_status": "ABSENT"},
                ],
            )

            report = build_quality_report(
                runtime_dir=runtime_dir,
                summary_path=summary_path,
                ingestion_dir=ingestion_dir,
                expected_artifacts=[
                    "data-facts.fiche_bien.json",
                    "comps-market.comparables_proposes.json",
                    "valuation-draft.calculs_approche_comparative.json",
                    "valuation-draft.calculs_approche_cout.json",
                    "valuation-draft.calculs_approche_revenu.json",
                    "redaction.brouillon_rapport.md",
                ],
            )

        case = report["cases"][0]
        self.assertEqual(report["cases_count"], 1)
        self.assertEqual(report["status_counts"], {"BROUILLON": 1})
        self.assertEqual(case["artifacts"]["missing"], ["redaction.brouillon_rapport.md"])
        self.assertEqual(case["comparables"]["average_score"], 0.7)
        self.assertTrue(case["calculation_traces"]["present"])
        self.assertEqual(case["sourcing"]["sourced_field_rate"], 0.5)
        self.assertEqual(case["ingestion_pdf"]["review_flags"], ["SOURCE_TEXT_CONTAINS_MASKED_VALUES"])
        self.assertEqual(report["totals"]["warnings"], 1)

    def test_quality_report_surfaces_contract_errors_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime_dir = root / "runtime"
            case_dir = runtime_dir / "case_bad"
            summary_path = runtime_dir / "runtime_summary.json"
            json_out = root / "quality.json"
            md_out = root / "quality.md"

            write_json(
                summary_path,
                [
                    {
                        "dossier_id": "D-BAD",
                        "status": "A_REVOIR",
                        "blocking_failures": ["CONF003: comparable[0] sans source_id"],
                        "warnings": [],
                        "artifact_dir": case_dir.as_posix(),
                    }
                ],
            )
            write_json(
                case_dir / "comps-market.comparables_proposes.json",
                {
                    "dossier_id": "D-BAD",
                    "step": "comps-market",
                    "artifact": "comparables_proposes.json",
                    "source_fixture": "case.json",
                    "date_reference": "2026-04-28",
                    "comparables": [{"comparable_id": "C1", "score": 0.8, "date_vente": "2026-01-01"}],
                },
            )

            report = build_quality_report(
                runtime_dir=runtime_dir,
                summary_path=summary_path,
                ingestion_dir=None,
                expected_artifacts=["comps-market.comparables_proposes.json"],
            )
            markdown = build_markdown(report)
            write_quality_report(report, json_out, md_out)

            self.assertTrue(json_out.exists())
            self.assertTrue(md_out.exists())
            written_report = json.loads(json_out.read_text(encoding="utf-8"))

        self.assertEqual(report["totals"]["contract_errors"], 1)
        self.assertIn("CONF003", markdown)
        self.assertEqual(written_report["cases"][0]["dossier_id"], "D-BAD")


if __name__ == "__main__":
    unittest.main()
