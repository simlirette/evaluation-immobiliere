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

from preparer_ingestion_pdf_v0 import SourceInput, build_text_stats, run_ingestion


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def fixture_payload() -> dict:
    return {
        "dossier_id": "D-REEL-001",
        "source_pdf": "D-REEL-001.pdf",
        "extraction_notes": ["Prix comparable approxime depuis le rapport anonymise."],
        "date_reference": "2024-04-29",
        "type_bien": "terrain_vacant",
        "zone": "ZONE-ANONYMISEE",
        "surface": {"value": 1000, "unit": "pi2"},
        "comparables": [
            {
                "comparable_id": "C1",
                "prix_vente": 100000,
                "date_vente": "2024-01-01",
                "distance_km": 2.5,
                "surface": {"value": 950, "unit": "pi2"},
                "source_id": "SRC-1",
                "confidence": 0.7,
            }
        ],
        "ajustements": [
            {
                "ajustement_id": "A1",
                "montant": 10000,
                "source_id": "SRC-2",
                "validation_humaine": True,
            }
        ],
        "hypotheses": [{"hypothese_id": "H1", "description": "Hypothese", "source_ids": ["SRC-1", "SRC-2"]}],
        "confidence": 0.72,
    }


class TestIngestionPdfV0(unittest.TestCase):
    def test_build_text_stats_counts_masks_and_pages(self) -> None:
        stats = build_text_stats("Page 1 [DATE]\fPage 2 [MONTANT]\n")
        self.assertEqual(stats["pages_estimate"], 2)
        self.assertEqual(stats["masked_token_count"], 2)
        self.assertEqual(stats["masked_token_types"], ["DATE", "MONTANT"])

    def test_run_ingestion_writes_normalized_dossier_and_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures_dir = root / "fixtures"
            text_dir = root / "text"
            out_dir = root / "out"
            pdf_path = root / "pdfs" / "D-REEL-001.pdf"
            pdf_path.parent.mkdir(parents=True)
            pdf_path.write_bytes(b"%PDF-FAKE")
            (text_dir / "D-REEL-001.txt").parent.mkdir(parents=True)
            (text_dir / "D-REEL-001.txt").write_text("Rapport anonymise [DATE]", encoding="utf-8")
            write_json(fixtures_dir / "case_pilote_reel_001.json", fixture_payload())

            manifest = run_ingestion(
                [SourceInput("D-REEL-001", pdf_path, text_dir / "D-REEL-001.txt")],
                fixtures_dir=fixtures_dir,
                out_dir=out_dir,
            )

            self.assertEqual(manifest["normalized_count"], 1)
            dossier_path = out_dir / "D-REEL-001" / "dossier_normalise.json"
            trace_path = out_dir / "D-REEL-001" / "trace_champs.json"
            self.assertTrue(dossier_path.exists())
            self.assertTrue(trace_path.exists())

            dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            self.assertEqual(dossier["schema_version"], "dossier_normalise_v0")
            self.assertIn("SOURCE_TEXT_CONTAINS_MASKED_VALUES", dossier["quality"]["review_flags"])
            self.assertIn("TRACE_CONTAINS_INFERRED_OR_APPROXIMATED_VALUES", dossier["quality"]["review_flags"])
            self.assertTrue(any(item["field_path"] == "comparables[1].prix_vente" for item in trace))

    def test_missing_text_raises_and_writes_manifest_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures_dir = root / "fixtures"
            out_dir = root / "out"
            pdf_path = root / "D-REEL-001.pdf"
            pdf_path.write_bytes(b"%PDF-FAKE")
            write_json(fixtures_dir / "case_pilote_reel_001.json", fixture_payload())

            with self.assertRaises(Exception):
                run_ingestion(
                    [SourceInput("D-REEL-001", pdf_path, root / "missing.txt")],
                    fixtures_dir=fixtures_dir,
                    out_dir=out_dir,
                )

            manifest = json.loads((out_dir / "MANIFESTE-INGESTION-PDF-V0.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["normalized_count"], 0)
            self.assertTrue(manifest["errors"])


if __name__ == "__main__":
    unittest.main()
