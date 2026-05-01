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

from generer_bench_perf_cout_v0 import build_phase_g_report, write_phase_g_deliverables


def writable_tmp_dir() -> Path:
    root = Path.cwd() / ".test-tmp" / f"evaluation_immobiliere_phase_g_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class TestPerfCoutPhaseGV0(unittest.TestCase):
    def test_build_phase_g_report_computes_perf_cost_and_slo_statuses(self) -> None:
        summary = [
            {
                "dossier_id": "D-001",
                "status": "PRET_REVISION_FINALE",
                "blocking_failures": [],
                "warnings": [],
                "events": [
                    {"event": "step_start", "step": "data-facts"},
                    {"event": "artifact_written", "step": "data-facts", "artifact": "fiche_bien.json"},
                    {"event": "step_done", "step": "data-facts"},
                ],
                "metrics": {"wall_clock_seconds": 2.0},
            },
            {
                "dossier_id": "D-002",
                "status": "BROUILLON",
                "blocking_failures": [],
                "warnings": ["W001"],
                "events": [
                    {"event": "warning_detected"},
                    {"event": "step_start", "step": "data-facts"},
                    {"event": "artifact_written", "step": "data-facts", "artifact": "fiche_bien.json"},
                    {"event": "step_done", "step": "data-facts"},
                ],
                "metrics": {"wall_clock_seconds": 5.0},
            },
        ]
        quality = {
            "status_counts": {"PRET_REVISION_FINALE": 1, "BROUILLON": 1},
            "totals": {
                "blocking_failures": 0,
                "warnings": 1,
                "contract_errors": 0,
                "expected_artifacts": 4,
                "produced_artifacts": 3,
                "missing_artifacts": 1,
            },
            "averages": {"sourced_field_rate": 1.0},
            "cases": [
                {
                    "dossier_id": "D-001",
                    "artifacts": {"expected_count": 2, "produced_count": 2, "missing_count": 0},
                    "sourcing": {"sourced_field_rate": 1.0},
                    "ingestion_pdf": {"text_stats": {"chars": 1000, "pages_estimate": 5}},
                    "contract_errors": [],
                },
                {
                    "dossier_id": "D-002",
                    "artifacts": {"expected_count": 2, "produced_count": 1, "missing_count": 1},
                    "sourcing": {"sourced_field_rate": 1.0},
                    "ingestion_pdf": {"text_stats": {"chars": 2000, "pages_estimate": 10}},
                    "contract_errors": [],
                },
            ],
        }
        manifest = {
            "artifacts": [
                {"category": "case_artifact", "bytes": 2048},
                {"category": "runtime_control_json", "bytes": 1024},
            ]
        }
        delta = {"status": "STABLE", "regressions": []}

        report = build_phase_g_report(summary, quality, manifest, delta)
        slo_statuses = {item["metric"]: item["status"] for item in report["slo_candidates"]}

        self.assertEqual(report["cases_count"], 2)
        self.assertEqual(report["latency"]["events_total"], 7)
        self.assertEqual(report["latency"]["p95_wall_clock_seconds"], 4.85)
        self.assertEqual(report["cost_proxy"]["source_chars"], 3000)
        self.assertEqual(report["cost_proxy"]["proxy_units_per_case"], 6.0)
        self.assertEqual(report["reliability"]["artifact_completion_rate"], 0.75)
        self.assertEqual(slo_statuses["latence_p95_dossier"], "OK")
        self.assertEqual(slo_statuses["completion_artefacts"], "A_TRAITER")
        self.assertEqual(slo_statuses["regressions_delta_runtime"], "OK")
        self.assertEqual(report["decision"]["status"], "GO_CONDITIONNEL")

    def test_missing_wall_clock_requires_instrumentation_and_writes_deliverables(self) -> None:
        report = build_phase_g_report(
            [
                {
                    "dossier_id": "D-001",
                    "status": "PRET_REVISION_FINALE",
                    "blocking_failures": [],
                    "warnings": [],
                    "events": [{"event": "step_start", "step": "data-facts"}],
                    "metrics": {"wall_clock_seconds": 0.0},
                }
            ],
            {
                "status_counts": {"PRET_REVISION_FINALE": 1},
                "totals": {
                    "blocking_failures": 0,
                    "warnings": 0,
                    "contract_errors": 0,
                    "expected_artifacts": 1,
                    "produced_artifacts": 1,
                    "missing_artifacts": 0,
                },
                "averages": {"sourced_field_rate": 1.0},
                "cases": [
                    {
                        "dossier_id": "D-001",
                        "artifacts": {"expected_count": 1, "produced_count": 1, "missing_count": 0},
                        "sourcing": {"sourced_field_rate": 1.0},
                        "ingestion_pdf": {"text_stats": {"chars": 500, "pages_estimate": 2}},
                        "contract_errors": [],
                    }
                ],
            },
            {"artifacts": [{"category": "case_artifact", "bytes": 512}]},
            {"status": "STABLE", "regressions": []},
        )

        slo_statuses = {item["metric"]: item["status"] for item in report["slo_candidates"]}
        self.assertEqual(slo_statuses["latence_p95_dossier"], "INSTRUMENTATION_REQUISE")

        root = writable_tmp_dir()
        try:
            json_out = root / "phase_g.json"
            bench_out = root / "BENCH-PERF-COUT-V1.md"
            slo_out = root / "SLO-SLA-V1.md"
            plan_out = root / "PLAN-OPTIMISATION-V1.md"

            write_phase_g_deliverables(report, json_out=json_out, bench_out=bench_out, slo_out=slo_out, plan_out=plan_out)

            self.assertTrue(json_out.exists())
            self.assertIn("BENCH PERF COUT V1", bench_out.read_text(encoding="utf-8"))
            self.assertIn("SLO SLA V1", slo_out.read_text(encoding="utf-8"))
            self.assertIn("PLAN OPTIMISATION V1", plan_out.read_text(encoding="utf-8"))
            written = json.loads(json_out.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(root, ignore_errors=True)

        self.assertEqual(written["schema_version"], "phase_g_perf_cost_report_v0")


if __name__ == "__main__":
    unittest.main()
