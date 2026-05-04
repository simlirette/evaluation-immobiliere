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

from generer_livrables_hypercare_v0 import (
    build_hypercare_context,
    build_improvement_items,
    generate_phase_l_deliverables,
    parse_preprod_open_counts,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = Path.cwd() / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class TestHypercarePhaseLV0(unittest.TestCase):
    def test_context_prepares_hypercare_when_prod_is_blocked(self) -> None:
        context = build_hypercare_context(
            "Lignes actives: **0**",
            {"total_cases": 5, "status_counts": {"PRET_REVISION_FINALE": 1}, "conformite_globale_pct": 20.0},
            "DEPLOIEMENT_PROD_BLOQUE",
            "Canary ouvert | non",
            "| PREPROD-J-001 | P0 | metier | ouvert | oui | Owner | gap | mitigation |",
        )
        items = build_improvement_items(context)

        self.assertEqual(context["decision"], "HYPERCARE_PREPARE_PROD_BLOQUEE")
        self.assertEqual(context["p0_open"], 1)
        self.assertEqual(context["dry_run_ready_rate"], 0.2)
        self.assertTrue(any(item["id"] == "V2-001" for item in items))

    def test_parse_preprod_open_counts(self) -> None:
        self.assertEqual(
            parse_preprod_open_counts(
                "\n".join(
                    [
                        "| PREPROD-J-001 | P0 | metier | ouvert | oui | Owner | gap | mitigation |",
                        "| PREPROD-J-002 | P1 | perf | ouvert | oui | Owner | gap | mitigation |",
                        "| PREPROD-J-003 | P2 | ops | ferme | non | Owner | gap | mitigation |",
                    ]
                )
            ),
            (2, 1, 1),
        )

    def test_generate_phase_l_deliverables_writes_three_documents(self) -> None:
        root = writable_tmp_dir("phase_l")
        try:
            validation = root / "responses.md"
            summary = root / "summary.json"
            canary = root / "canary.md"
            stabilization = root / "j7.md"
            register = root / "register.md"
            hypercare = root / "hypercare.md"
            backlog = root / "backlog.md"
            adoption = root / "adoption.md"

            validation.write_text("Lignes actives: **0**\n", encoding="utf-8")
            write_json(summary, {"total_cases": 5, "status_counts": {"PRET_REVISION_FINALE": 1}, "conformite_globale_pct": 20.0})
            canary.write_text("DEPLOIEMENT_PROD_BLOQUE\n", encoding="utf-8")
            stabilization.write_text("Canary ouvert | non\n", encoding="utf-8")
            register.write_text("| PREPROD-J-001 | P0 | metier | ouvert | oui | Owner | gap | mitigation |\n", encoding="utf-8")

            outputs = generate_phase_l_deliverables(
                validation_responses_path=validation,
                summary_json_path=summary,
                canary_plan_path=canary,
                stabilization_path=stabilization,
                preprod_register_path=register,
                hypercare_out=hypercare,
                backlog_out=backlog,
                adoption_out=adoption,
            )

            self.assertEqual(outputs["decision"], "HYPERCARE_PREPARE_PROD_BLOQUEE")
            self.assertIn("PLAN HYPERCARE V1", hypercare.read_text(encoding="utf-8"))
            self.assertIn("BACKLOG AMELIORATION V2", backlog.read_text(encoding="utf-8"))
            self.assertIn("RAPPORT ADOPTION V1", adoption.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
