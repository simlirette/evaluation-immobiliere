from __future__ import annotations

import shutil
import sys
import unittest
import uuid
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from generer_livrables_cicd_v0 import (
    build_cd_markdown,
    build_ci_markdown,
    build_rollback_markdown,
    generate_phase_i_deliverables,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestCicdPhaseIV0(unittest.TestCase):
    def test_ci_markdown_reflects_existing_validation_workflow(self) -> None:
        workflow_text = "\n".join(
            [
                "python -m py_compile",
                "python evaluation-immobiliere/outils/valider_reponses_evaluateurs.py",
                "python evaluation-immobiliere/outils/valider_fixtures_v0.py",
                "python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py",
                "python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py",
                "python evaluation-immobiliere/outils/executer_pre_reponses_v0.py",
                "python evaluation-immobiliere/outils/valider_rapports_infra_v0.py",
                "python evaluation-immobiliere/outils/verifier_campagne_terrain_reelle_v1.py",
                "python evaluation-immobiliere/outils/verifier_statut_phases_projet_v1.py",
                "python evaluation-immobiliere/outils/verifier_revues_evaluateurs_externes_v1.py --strict",
                "python evaluation-immobiliere/outils/verifier_fermeture_ecarts_evaluateurs_v1.py --strict",
                "python evaluation-immobiliere/outils/verifier_release_candidate_v1.py --strict",
                "python -m unittest discover",
            ]
        )

        markdown = build_ci_markdown(Path(".github/workflows/validation.yml"), workflow_text)

        self.assertIn("PIPELINE CI V1", markdown)
        self.assertIn("GO_PREPARATION_STAGING", markdown)
        self.assertIn("Gate campagne terrain reelle", markdown)
        self.assertIn("Statut phases projet", markdown)
        self.assertIn("Fermeture ecarts evaluateurs stricte", markdown)
        self.assertIn("Release candidate strict", markdown)
        self.assertIn("| Tests unitaires | `python -m unittest discover` | present | oui |", markdown)

    def test_cd_and_rollback_block_prod_while_phase_h_is_waiting(self) -> None:
        cd = build_cd_markdown("EN_ATTENTE_REPONSES_TERRAIN")
        rollback = build_rollback_markdown("EN_ATTENTE_REPONSES_TERRAIN")

        self.assertIn("production reste bloquee", cd)
        self.assertIn("| prod |", cd)
        self.assertIn("RUNBOOK ROLLBACK V1", rollback)
        self.assertIn("Aucun rollback prod reel", rollback)

    def test_generate_phase_i_deliverables_writes_three_documents(self) -> None:
        root = writable_tmp_dir("phase_i")
        try:
            workflow = root / "validation.yml"
            workflow.write_text("python -m py_compile\npython -m unittest discover\n", encoding="utf-8")
            ci_out = root / "PIPELINE-CI-V1.md"
            cd_out = root / "PIPELINE-CD-V1.md"
            rollback_out = root / "RUNBOOK-ROLLBACK-V1.md"

            outputs = generate_phase_i_deliverables(
                workflow_path=workflow,
                ci_out=ci_out,
                cd_out=cd_out,
                rollback_out=rollback_out,
            )

            self.assertTrue(ci_out.exists())
            self.assertTrue(cd_out.exists())
            self.assertTrue(rollback_out.exists())
            self.assertEqual(outputs["phase_h_status"], "EN_ATTENTE_ENTREES_TERRAIN_REELLES")
            self.assertIn("PIPELINE CI V1", ci_out.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
