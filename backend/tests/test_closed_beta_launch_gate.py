from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import check_closed_beta_launch


def _ready_evidence() -> dict[str, object]:
    return {
        "schema_version": "closed_beta_launch_evidence_v1",
        "production": {
            "frontend_url": "https://eval-immo.example.test",
            "backend_url": "https://eval-immo-runtime.example.test",
            "railway_readiness_ok": True,
            "vercel_bff_smoke_ok": True,
            "runtime_token_set": True,
            "cors_strict": True,
            "persistent_sessions": True,
            "persistent_data_cache": True,
            "mamh_cache_provisioned": True,
            "openai_configured": True,
        },
        "privacy": {
            "data_inventory_approved": True,
            "retention_days": 14,
            "deletion_workflow_approved": True,
            "access_logging_reviewable": True,
            "backup_restore_defined": True,
            "incident_response_defined": True,
            "professional_disclaimer_approved": True,
            "raw_client_files_allowed": False,
        },
        "pilot_ea": {
            "pilot_ea_id": "ea-pilot-001",
            "terms_accepted": True,
            "workflow_signoff": True,
        },
        "real_dossiers": [
            {
                "id": "D-BETA-001",
                "type": "standard_residential",
                "anonymized": True,
                "acceptance_status": "PASS",
                "package_or_block_evidence": "runtime_sessions/D-BETA-001/package_v1/manifest_v1.json",
                "p0_open_count": 0,
            },
            {
                "id": "D-BETA-002",
                "type": "edge_or_low_confidence",
                "anonymized": True,
                "acceptance_status": "JUSTIFIED_BLOCKED",
                "package_or_block_evidence": "runtime_sessions/D-BETA-002/acceptance_ea_report.json",
                "p0_open_count": 0,
            },
            {
                "id": "D-BETA-003",
                "type": "correction_or_blocked",
                "anonymized": True,
                "acceptance_status": "PASS",
                "package_or_block_evidence": "runtime_sessions/D-BETA-003/package_v1/manifest_v1.json",
                "p0_open_count": 0,
            },
        ],
        "data_sources": {
            "mamh_validated": True,
            "infolot_validated": True,
            "sirf_status": "explicitly_disabled_for_beta",
            "jlr_policy": "manual_export",
            "cost_approach_status": "explicitly_marked_incomplete",
            "insufficient_data_blocking_policy": True,
        },
        "launch": {
            "named_users_only": True,
            "max_named_users": 1,
            "support_owner": "ops-owner",
            "daily_review_owner": "ops-owner",
            "week1_review_schedule": True,
            "rollback_plan": True,
            "p0_open_count": 0,
        },
    }


def test_closed_beta_launch_gate_accepts_complete_evidence():
    report = check_closed_beta_launch.validate_evidence(_ready_evidence())

    assert report["ok"] is True
    assert report["status"] == "READY_FOR_CLOSED_BETA"
    assert report["blocking_checks"] == []


def test_closed_beta_launch_gate_blocks_missing_external_evidence():
    evidence = _ready_evidence()
    evidence["production"]["frontend_url"] = "http://localhost:3000"  # type: ignore[index]
    evidence["privacy"]["retention_days"] = 0  # type: ignore[index]
    evidence["real_dossiers"] = []  # type: ignore[assignment]

    report = check_closed_beta_launch.validate_evidence(evidence)

    assert report["ok"] is False
    assert report["status"] == "BLOCKED"
    assert "production.frontend_url" in report["blocking_checks"]
    assert "privacy.retention_days" in report["blocking_checks"]
    assert "real_dossiers.count" in report["blocking_checks"]


def test_closed_beta_launch_gate_script_returns_nonzero_for_blocked_evidence(tmp_path, capsys):
    path = tmp_path / "evidence.json"
    evidence = _ready_evidence()
    evidence["launch"]["p0_open_count"] = 1  # type: ignore[index]
    path.write_text(json.dumps(evidence), encoding="utf-8")

    code = check_closed_beta_launch.main([str(path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert code == 1
    assert output["ok"] is False
    assert "launch.p0_open_count" in output["blocking_checks"]
