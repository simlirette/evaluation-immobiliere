#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "infra_contracts_report.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "RAPPORT-CONTRATS-INFRA-V0.md"
WAITING_REAL_INPUTS_STATUS = "EN_ATTENTE_ENTREES_TERRAIN_REELLES"
WAITING_ALLOWED_MISSING = {"quality_report.json"}


def load_json(path: Path) -> object:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def has_path(payload: object, dotted_path: str) -> bool:
    current = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True


def validate_file(path: Path, *, required_fields: list[str], expected_schema: str | None = None) -> dict[str, object]:
    failures: list[str] = []
    payload = load_json(path)
    if payload is None:
        return {"path": path.as_posix(), "ok": False, "failures": ["FILE_MISSING"]}
    if not isinstance(payload, dict):
        failures.append("ROOT_NOT_OBJECT")
    else:
        for field in required_fields:
            if not has_path(payload, field):
                failures.append(f"FIELD_MISSING:{field}")
        if expected_schema and payload.get("schema_version") != expected_schema:
            failures.append(f"SCHEMA_VERSION:{payload.get('schema_version')}")
    return {"path": path.as_posix(), "ok": not failures, "failures": failures}


def build_infra_contract_report(runtime_dir: Path) -> dict[str, object]:
    checks = [
        validate_file(
            runtime_dir / "quality_report.json",
            required_fields=["schema_version", "cases_count", "status_counts", "totals", "cases"],
            expected_schema="runtime_quality_report_v0",
        ),
        validate_file(
            runtime_dir / "calibration_evaluateurs.json",
            required_fields=["schema_version", "status", "responses_count", "cases", "backlog"],
            expected_schema="calibration_evaluateurs_v0",
        ),
        validate_file(
            runtime_dir / "runtime_manifest.json",
            required_fields=["schema_version", "fingerprint_sha256", "files_count", "artifacts"],
            expected_schema="runtime_manifest_v0",
        ),
        validate_file(
            runtime_dir / "readiness_pre_reponses.json",
            required_fields=["schema_version", "status", "checks", "risks_to_calibrate"],
            expected_schema="readiness_pre_reponses_v0",
        ),
        validate_file(
            runtime_dir / "knowledge_snapshot.json",
            required_fields=["schema_version", "runtime_fingerprint_sha256", "cases_count", "cases"],
            expected_schema="knowledge_snapshot_v0",
        ),
        validate_file(
            runtime_dir / "runtime_registry.json",
            required_fields=["schema_version", "latest_run_id", "runs_count", "runs"],
            expected_schema="runtime_registry_v0",
        ),
        validate_file(
            runtime_dir / "runtime_delta_report.json",
            required_fields=["schema_version", "status", "current", "previous", "deltas", "regressions"],
            expected_schema="runtime_delta_report_v0",
        ),
        validate_file(
            runtime_dir / "ops_handoff_manifest.json",
            required_fields=["schema_version", "status", "files_count", "required_missing", "files"],
            expected_schema="ops_handoff_manifest_v0",
        ),
    ]
    readiness_status = read_status(runtime_dir / "readiness_pre_reponses.json")
    handoff_status = read_status(runtime_dir / "ops_handoff_manifest.json")
    waiting_mode = readiness_status == WAITING_REAL_INPUTS_STATUS or handoff_status == WAITING_REAL_INPUTS_STATUS
    blocking_failures = [
        {
            "path": check["path"],
            "failure": failure,
        }
        for check in checks
        for failure in check["failures"]
        if is_blocking_failure(str(check["path"]), str(failure), waiting_mode)
    ]
    ok = not blocking_failures
    return {
        "schema_version": "infra_contracts_report_v0",
        "runtime_dir": runtime_dir.as_posix(),
        "status": WAITING_REAL_INPUTS_STATUS if ok and waiting_mode else ("OK" if ok else "A_CORRIGER"),
        "ok": ok,
        "readiness_status": readiness_status,
        "handoff_status": handoff_status,
        "waiting_mode": waiting_mode,
        "files_checked": len(checks),
        "files_invalid": sum(1 for check in checks if not check["ok"]),
        "files_invalid_blocking": len({item["path"] for item in blocking_failures}),
        "blocking_failures": blocking_failures,
        "checks": checks,
    }


def read_status(path: Path) -> str:
    payload = load_json(path)
    return str(payload.get("status", "")) if isinstance(payload, dict) else ""


def is_blocking_failure(path: str, failure: str, waiting_mode: bool) -> bool:
    if waiting_mode and failure == "FILE_MISSING" and Path(path).name in WAITING_ALLOWED_MISSING:
        return False
    return True


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Rapport contrats infra v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Fichiers verifies: **{report.get('files_checked', 0)}**",
        f"- Fichiers invalides: **{report.get('files_invalid', 0)}**",
        f"- Fichiers invalides bloquants: **{report.get('files_invalid_blocking', 0)}**",
        "",
        "| Fichier | Statut | Echecs |",
        "|---|---|---|",
    ]
    for check in report.get("checks", []):
        if isinstance(check, dict):
            lines.append(
                "| {path} | {status} | {failures} |".format(
                    path=check.get("path", "-"),
                    status="OK" if check.get("ok") else "A_CORRIGER",
                    failures=", ".join(check.get("failures", [])) if check.get("failures") else "-",
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def run_validation(runtime_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    report = build_infra_contract_report(runtime_dir)
    write_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide les contrats des rapports infra runtime.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = run_validation(args.runtime_dir, args.json_out, args.markdown_out)
    print(f"Rapport contrats infra JSON: {args.json_out}")
    print(f"Rapport contrats infra Markdown: {args.markdown_out}")
    print(f"OK: {report['ok']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
