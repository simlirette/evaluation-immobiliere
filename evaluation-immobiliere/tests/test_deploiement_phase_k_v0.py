from __future__ import annotations

import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

OUTILS_DIR = Path(__file__).resolve().parents[1] / "outils"
if str(OUTILS_DIR) not in sys.path:
    sys.path.insert(0, str(OUTILS_DIR))

from generer_livrables_deploiement_v0 import (
    build_deployment_context,
    count_open_preprod_gaps,
    generate_phase_k_deliverables,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class TestDeploiementPhaseKV0(unittest.TestCase):
    def test_count_open_preprod_gaps_by_severity(self) -> None:
        total, p0, p1 = count_open_preprod_gaps(
            "\n".join(
                [
                    "| PREPROD-J-001 | P0 | metier | ouvert | oui | Owner | gap | mitigation |",
                    "| PREPROD-J-002 | P1 | perf | ouvert | oui | Owner | gap | mitigation |",
                    "| PREPROD-J-003 | P2 | ops | ferme | non | Owner | gap | mitigation |",
                ]
            )
        )

        self.assertEqual((total, p0, p1), (2, 1, 1))

    def test_context_blocks_prod_when_pv_is_no_go(self) -> None:
        context = build_deployment_context(
            {"status": "OK", "summary": {"delta_status": "STABLE", "review_queue_items": 3}},
            "Go production: **NON**",
            "| PREPROD-J-001 | P0 | metier | ouvert | oui | Owner | gap | mitigation |",
            "# RUNBOOK ROLLBACK V1",
            "OPS-DOCTOR-V0",
        )

        self.assertEqual(context["decision"], "DEPLOIEMENT_PROD_BLOQUE")
        self.assertTrue(context["prod_no_go"])
        self.assertEqual(context["p0_open"], 1)

    def test_generate_phase_k_deliverables_writes_three_documents(self) -> None:
        root = writable_tmp_dir("phase_k")
        try:
            ops = root / "ops.json"
            pv = root / "pv.md"
            register = root / "register.md"
            rollback = root / "rollback.md"
            ops_runbook = root / "ops_runbook.md"
            canary = root / "canary.md"
            dashboard = root / "dashboard.md"
            stabilization = root / "j7.md"

            write_json(
                ops,
                {
                    "status": "OK",
                    "summary": {
                        "delta_status": "STABLE",
                        "handoff_status": "PRET_A_TRANSMETTRE",
                        "schema_validation_status": "OK",
                        "package_gate_status": "PRET_A_ENVOYER",
                        "review_queue_items": 16,
                    },
                },
            )
            pv.write_text("Go production: **NON**\n", encoding="utf-8")
            register.write_text("| PREPROD-J-001 | P0 | metier | ouvert | oui | Owner | gap | mitigation |\n", encoding="utf-8")
            rollback.write_text("# RUNBOOK ROLLBACK V1\n", encoding="utf-8")
            ops_runbook.write_text("OPS-DOCTOR-V0\n", encoding="utf-8")

            outputs = generate_phase_k_deliverables(
                ops_doctor_path=ops,
                pv_path=pv,
                register_path=register,
                rollback_path=rollback,
                ops_runbook_path=ops_runbook,
                canary_out=canary,
                dashboard_out=dashboard,
                stabilization_out=stabilization,
            )

            self.assertEqual(outputs["decision"], "DEPLOIEMENT_PROD_BLOQUE")
            self.assertIn("PLAN DEPLOIEMENT CANARY V1", canary.read_text(encoding="utf-8"))
            self.assertIn("TABLEAU BORD PROD V1", dashboard.read_text(encoding="utf-8"))
            self.assertIn("RAPPORT STABILISATION J7", stabilization.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
