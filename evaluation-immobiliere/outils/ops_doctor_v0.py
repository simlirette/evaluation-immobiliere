#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "ops_doctor_report.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "OPS-DOCTOR-V0.md"
WAITING_REAL_INPUTS_STATUS = "EN_ATTENTE_ENTREES_TERRAIN_REELLES"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"status": "ABSENT", "path": path.as_posix()}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"status": "INVALID_ROOT", "path": path.as_posix()}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def correction_issue(code: str, target: str, detail: object = "") -> dict[str, object]:
    return {"severity": "A_CORRIGER", "code": code, "target": target, "detail": detail}


def control_issue(code: str, target: str, detail: object = "") -> dict[str, object]:
    return {"severity": "A_CONTROLER", "code": code, "target": target, "detail": detail}


def build_ops_doctor_report(runtime_dir: Path) -> dict[str, object]:
    readiness = load_json(runtime_dir / "readiness_pre_reponses.json")
    delta = load_json(runtime_dir / "runtime_delta_report.json")
    handoff = load_json(runtime_dir / "ops_handoff_manifest.json")
    infra = load_json(runtime_dir / "infra_contracts_report.json")
    schemas = load_json(runtime_dir / "schema_validation_report.json")
    package_gate = load_json(runtime_dir / "paquet_evaluateurs_gate.json")
    anonymization = load_json(runtime_dir / "anonymisation_audit.json")
    review_queue = load_csv_rows(runtime_dir / "FILE-REVUE-HUMAINE-V0.csv")

    issues: list[dict[str, object]] = []
    waiting_mode = any(
        item.get("status") == WAITING_REAL_INPUTS_STATUS
        for item in (readiness, handoff, schemas, package_gate)
    )
    if readiness.get("status") not in {"PRET_A_RECEVOIR_REPONSES", WAITING_REAL_INPUTS_STATUS}:
        issues.append(control_issue("READINESS_NOT_READY", "readiness", readiness.get("status")))
    if delta.get("status") == "A_CONTROLER":
        issues.append(control_issue("RUNTIME_DELTA_TO_REVIEW", "delta", delta.get("regressions", [])))
    if delta.get("status") in {"ABSENT", "INVALID_ROOT"}:
        issues.append(correction_issue("RUNTIME_DELTA_ABSENT", "delta", delta.get("path", "")))
    if handoff.get("status") not in {"PRET_A_TRANSMETTRE", WAITING_REAL_INPUTS_STATUS}:
        issues.append(correction_issue("HANDOFF_NOT_READY", "handoff", handoff.get("status")))
    if infra.get("ok") is not True:
        issues.append(correction_issue("INFRA_CONTRACTS_NOT_OK", "infra_contracts", infra.get("files_invalid", "")))
    if schemas.get("status") not in {"OK", WAITING_REAL_INPUTS_STATUS}:
        issues.append(correction_issue("SCHEMAS_NOT_OK", "schema_validation", schemas.get("files_invalid", "")))
    if package_gate.get("status") not in {"PRET_A_ENVOYER", WAITING_REAL_INPUTS_STATUS}:
        issues.append(correction_issue("PACKAGE_GATE_NOT_READY", "package_gate", package_gate.get("status")))
    if anonymization.get("status") != "OK":
        issues.append(correction_issue("ANONYMIZATION_NOT_OK", "anonymization", anonymization.get("status")))

    if any(item["severity"] == "A_CORRIGER" for item in issues):
        status = "A_CORRIGER"
    elif issues:
        status = "A_CONTROLER"
    elif waiting_mode:
        status = WAITING_REAL_INPUTS_STATUS
    else:
        status = "OK"

    return {
        "schema_version": "ops_doctor_report_v0",
        "status": status,
        "runtime_dir": runtime_dir.as_posix(),
        "summary": {
            "readiness_status": readiness.get("status", "UNKNOWN"),
            "delta_status": delta.get("status", "UNKNOWN"),
            "handoff_status": handoff.get("status", "UNKNOWN"),
            "infra_contracts_ok": infra.get("ok") is True,
            "schema_validation_status": schemas.get("status", "UNKNOWN"),
            "package_gate_status": package_gate.get("status", "UNKNOWN"),
            "anonymization_status": anonymization.get("status", "UNKNOWN"),
            "review_queue_items": len(review_queue),
        },
        "issues": issues,
    }


def build_markdown(report: dict[str, object]) -> str:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    issues = report.get("issues", []) if isinstance(report.get("issues"), list) else []
    lines = [
        "# Ops doctor v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Readiness: **{summary.get('readiness_status', 'UNKNOWN')}**",
        f"- Delta: **{summary.get('delta_status', 'UNKNOWN')}**",
        f"- Handoff: **{summary.get('handoff_status', 'UNKNOWN')}**",
        f"- Schemas: **{summary.get('schema_validation_status', 'UNKNOWN')}**",
        f"- Gate paquet: **{summary.get('package_gate_status', 'UNKNOWN')}**",
        f"- File humaine: **{summary.get('review_queue_items', 0)}**",
        "",
        "## Issues",
        "",
    ]
    if issues:
        for item in issues:
            if isinstance(item, dict):
                lines.append(f"- **{item.get('severity', '-')}** `{item.get('code', '-')}` sur `{item.get('target', '-')}`: {item.get('detail', '-')}")
    else:
        lines.append("- Aucune.")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def run_doctor(runtime_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    report = build_ops_doctor_report(runtime_dir)
    write_report(report, json_out, markdown_out)
    return report


def exit_code(status: str) -> int:
    return {"OK": 0, WAITING_REAL_INPUTS_STATUS: 0, "A_CONTROLER": 1, "A_CORRIGER": 2}.get(status, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostique l'etat operationnel pre-reponses.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = run_doctor(args.runtime_dir, args.json_out, args.markdown_out)
    print(f"Ops doctor JSON: {args.json_out}")
    print(f"Ops doctor Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return exit_code(str(report["status"]))


if __name__ == "__main__":
    raise SystemExit(main())
