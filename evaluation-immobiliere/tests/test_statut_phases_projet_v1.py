from __future__ import annotations

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
from verifier_statut_phases_projet_v1 import build_markdown, build_project_status_report  # noqa: E402


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT.parent / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_response_csv(path: Path, *, active: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ",".join(RESPONSE_FIELDS)
    if not active:
        path.write_text(header + "\n", encoding="utf-8")
        return
    path.write_text(
        header
        + "\n"
        + "EV-001,evaluateur,residentiel,intake,reception_mandat,10,1,3,3,3,3,3,oui,non,docs,aucun,rapport,commentaire\n",
        encoding="utf-8",
    )


class TestStatutPhasesProjetV1(unittest.TestCase):
    def test_project_status_is_ready_for_evaluator_review_but_blocks_prod(self) -> None:
        report = build_project_status_report()
        markdown = build_markdown(report)

        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(report["decision"], "PROJET_PRET_REVUE_EVALUATEUR_AGREE_PROD_BLOQUEE")
        self.assertEqual(report["target"], "V1_PRE_EVALUATEUR")
        self.assertEqual(report["pre_evaluator_decision"], "PRET_REVUE_EVALUATEUR_AGREE")
        self.assertEqual(report["pre_evaluator_package_status"], "PRET_REVUE_EVALUATEUR_AGREE")
        self.assertEqual(report["phase_h_decision"], "EN_ATTENTE_ENTREES_TERRAIN_REELLES")
        self.assertEqual(report["response_active_rows"], 0)
        self.assertIn("DEPLOIEMENT_PROD_BLOQUE", {phase["decision"] for phase in report["phases"]})
        self.assertIn("Aucune reponse evaluateur active", markdown)
        self.assertIn("Paquet V1 pre-evaluateur", markdown)

    def test_active_responses_before_phase_h_real_inputs_block_status(self) -> None:
        root = writable_tmp_dir("statut_phases")
        try:
            responses = root / "responses.csv"
            calibration = root / "calibration.csv"
            write_response_csv(responses, active=True)
            calibration.write_text("respondant_id,role,dossier_id\n", encoding="utf-8")

            report = build_project_status_report(response_input=responses, calibration_input=calibration)

            self.assertFalse(report["ok"])
            self.assertIn("aucune_reponse_inventee", report["errors"])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
