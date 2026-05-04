from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTILS_DIR = PROJECT_ROOT / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from valider_reponses_evaluateurs import RESPONSE_FIELDS  # noqa: E402
from verifier_campagne_terrain_reelle_v1 import (  # noqa: E402
    NO_GO_STATUS,
    READY_STATUS,
    WAITING_STATUS,
    build_markdown,
    build_phase_h_gate_report,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT.parent / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_empty_responses(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(",".join(RESPONSE_FIELDS) + "\n", encoding="utf-8")


def write_active_response(path: Path) -> None:
    write_empty_responses(path)
    path.write_text(
        ",".join(RESPONSE_FIELDS)
        + "\n"
        + "EV-001,evaluateur,residentiel,intake,reception_mandat,10,1,3,3,3,3,3,oui,non,docs,aucun,rapport,commentaire\n",
        encoding="utf-8",
    )


def valid_case() -> dict[str, object]:
    return {
        "dossier_id": "D-REEL-001",
        "date_reference": "2026-04-28",
        "type_bien": "residentiel",
        "zone": "Secteur anonymise",
        "surface": {"value": 1000, "unit": "pi2"},
        "comparables": [
            {
                "comparable_id": "C-001",
                "prix_vente": 300000,
                "date_vente": "2026-01-15",
                "surface": {"value": 1000, "unit": "pi2"},
                "source_id": "SRC-001",
            }
        ],
        "ajustements": [
            {
                "ajustement_id": "AJ-001",
                "montant": 1000,
                "source_id": "SRC-001",
                "validation_humaine": True,
            }
        ],
        "confidence": 0.78,
    }


def write_ready_runtime(runtime_dir: Path) -> None:
    case_dir = runtime_dir / "case_pilote_reel_001"
    case_dir.mkdir(parents=True)
    for name in [
        "compliance-qa.statut_sortie.json",
        "compliance-qa.rapport_non_conformites.json",
        "compliance-qa.recommandations_corrections.md",
        "redaction.brouillon_rapport.md",
    ]:
        (case_dir / name).write_text("ok", encoding="utf-8")
    write_json(
        runtime_dir / "runtime_summary.json",
        [
            {
                "dossier_id": "D-REEL-001",
                "status": "PRET_REVISION_FINALE",
                "artifact_dir": case_dir.as_posix(),
                "blocking_failures": [],
                "warnings": [],
            }
        ],
    )
    write_json(
        runtime_dir / "ingestion_v0" / "MANIFESTE-INGESTION-PDF-V0.json",
        {
            "schema_version": "ingestion_pdf_v0",
            "normalized_count": 1,
            "errors": [],
            "entries": [{"dossier_id": "D-REEL-001", "status": "NORMALISE"}],
        },
    )
    (runtime_dir / "REVUE-INTERNE-PILOTES-REELS-V0.md").write_text("revue ok", encoding="utf-8")


class TestCampagneTerrainReelleV1(unittest.TestCase):
    def test_waiting_without_real_inputs_is_a_valid_phase_h_gate(self) -> None:
        root = writable_tmp_dir("phase_h_waiting")
        try:
            report = build_phase_h_gate_report(
                fixtures_dir=root / "fixtures_external",
                runtime_dir=root / "runtime",
                package_index=root / "package.md",
                response_input=root / "responses.csv",
            )

            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["decision"], WAITING_STATUS)
            self.assertEqual(report["active_cases_count"], 0)
            self.assertIn("attente de dossiers terrain", build_markdown(report))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_sensitive_active_input_blocks_the_gate_before_runtime(self) -> None:
        root = writable_tmp_dir("phase_h_sensitive")
        try:
            fixtures = root / "fixtures_external"
            fixtures.mkdir()
            case = valid_case()
            case["adresse"] = "123 rue Test"
            write_json(fixtures / "case_pilote_reel_001.json", case)

            report = build_phase_h_gate_report(
                fixtures_dir=fixtures,
                runtime_dir=root / "runtime",
                package_index=root / "package.md",
                response_input=root / "responses.csv",
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], NO_GO_STATUS)
            self.assertIn("audit_anonymisation", [item["name"] for item in report["checks"]])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_ready_active_campaign_requires_full_pre_response_chain(self) -> None:
        root = writable_tmp_dir("phase_h_ready")
        try:
            fixtures = root / "fixtures_external"
            runtime_dir = root / "runtime"
            fixtures.mkdir()
            write_json(fixtures / "case_pilote_reel_001.json", valid_case())
            write_ready_runtime(runtime_dir)
            package_index = root / "package" / "PAQUET-EVALUATEURS-V0.md"
            package_index.parent.mkdir(parents=True)
            package_index.write_text("- Statut: **PRET_A_ENVOYER**\n", encoding="utf-8")
            responses = root / "REPONSES-EVALUATEURS.csv"
            write_empty_responses(responses)

            report = build_phase_h_gate_report(
                fixtures_dir=fixtures,
                runtime_dir=runtime_dir,
                package_index=package_index,
                response_input=responses,
            )

            self.assertTrue(report["ok"], report["errors"])
            self.assertEqual(report["decision"], READY_STATUS)
            statuses = {item["name"]: item["status"] for item in report["checks"]}
            self.assertEqual(statuses["point_arret_avant_reponses"], "PRET_A_RECEVOIR_REPONSES")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_active_evaluator_responses_are_not_allowed_before_the_stop_point(self) -> None:
        root = writable_tmp_dir("phase_h_response")
        try:
            fixtures = root / "fixtures_external"
            runtime_dir = root / "runtime"
            fixtures.mkdir()
            write_json(fixtures / "case_pilote_reel_001.json", valid_case())
            write_ready_runtime(runtime_dir)
            package_index = root / "package" / "PAQUET-EVALUATEURS-V0.md"
            package_index.parent.mkdir(parents=True)
            package_index.write_text("- Statut: **PRET_A_ENVOYER**\n", encoding="utf-8")
            responses = root / "REPONSES-EVALUATEURS.csv"
            write_active_response(responses)

            report = build_phase_h_gate_report(
                fixtures_dir=fixtures,
                runtime_dir=runtime_dir,
                package_index=package_index,
                response_input=responses,
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], NO_GO_STATUS)
            self.assertTrue(any(item["status"] == "REPONSES_DEJA_PRESENTES" for item in report["checks"]))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
