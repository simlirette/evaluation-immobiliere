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

from generer_livrables_preprod_v0 import (
    build_preprod_context,
    build_preprod_gaps,
    generate_phase_j_deliverables,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class TestPreprodPhaseJV0(unittest.TestCase):
    def test_context_blocks_prod_when_phase_h_is_waiting(self) -> None:
        context = build_preprod_context(
            {"status": "OK", "summary": {"review_queue_items": 16}},
            {"status": "PRET_A_TRANSMETTRE", "required_present": 19, "required_count": 19},
            {"status": "PRET_A_RECEVOIR_REPONSES", "risks_to_calibrate": {"contract_errors": 1}},
            "Statut courant: **EN_ATTENTE_REPONSES_TERRAIN**.",
            "| latence_p95_dossier | n/d | <= 900 sec | INSTRUMENTATION_REQUISE |",
            "La production reste bloquee",
            "# RUNBOOK ROLLBACK V1",
        )
        gaps = build_preprod_gaps(context)

        self.assertEqual(context["decision"], "NO_GO_PROD_PREPARATION")
        self.assertTrue(any(gap["id"] == "PREPROD-J-001" for gap in gaps))
        self.assertTrue(any(gap["id"] == "PREPROD-J-002" for gap in gaps))

    def test_generate_phase_j_deliverables_writes_three_documents(self) -> None:
        root = writable_tmp_dir("phase_j")
        try:
            ops = root / "ops.json"
            handoff = root / "handoff.json"
            readiness = root / "readiness.json"
            slo = root / "slo.md"
            acceptance = root / "acceptance.md"
            cd = root / "cd.md"
            rollback = root / "rollback.md"
            dress = root / "dress.md"
            pv = root / "pv.md"
            register = root / "register.md"

            write_json(ops, {"status": "OK", "summary": {"review_queue_items": 2}})
            write_json(handoff, {"status": "PRET_A_TRANSMETTRE", "required_present": 2, "required_count": 2})
            write_json(readiness, {"status": "PRET_A_RECEVOIR_REPONSES", "risks_to_calibrate": {}})
            slo.write_text("INSTRUMENTATION_REQUISE\n", encoding="utf-8")
            acceptance.write_text("EN_ATTENTE_REPONSES_TERRAIN\n", encoding="utf-8")
            cd.write_text("production reste bloquee\n", encoding="utf-8")
            rollback.write_text("# RUNBOOK ROLLBACK V1\n", encoding="utf-8")

            outputs = generate_phase_j_deliverables(
                ops_doctor_path=ops,
                handoff_path=handoff,
                readiness_path=readiness,
                slo_path=slo,
                acceptance_path=acceptance,
                cd_path=cd,
                rollback_path=rollback,
                dress_out=dress,
                pv_out=pv,
                register_out=register,
            )

            self.assertEqual(outputs["decision"], "NO_GO_PROD_PREPARATION")
            self.assertTrue(dress.exists())
            self.assertTrue(pv.exists())
            self.assertTrue(register.exists())
            self.assertIn("RAPPORT DRESS REHEARSAL V1", dress.read_text(encoding="utf-8"))
            self.assertIn("Go production: **NON**", pv.read_text(encoding="utf-8"))
            self.assertIn("PREPROD-J-001", register.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
