#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
PACKAGE_INDEX_DEFAULT = Path("evaluation-immobiliere/paquets_evaluateurs/v0/PAQUET-EVALUATEURS-V0.md")
QUALITY_DEFAULT = RUNTIME_DIR_DEFAULT / "quality_report.json"
CALIBRATION_DEFAULT = RUNTIME_DIR_DEFAULT / "calibration_evaluateurs.json"
MANIFEST_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_manifest.json"
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "readiness_pre_reponses.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "READINESS-PRE-REPONSES-V0.md"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def package_status(path: Path) -> str:
    if not path.exists():
        return "PAQUET_ABSENT"
    text = path.read_text(encoding="utf-8")
    match = re.search(r"- Statut: \*\*(.+?)\*\*", text)
    return match.group(1).strip() if match else "STATUT_PAQUET_INCONNU"


def build_readiness_report(quality: dict, calibration: dict, manifest: dict, package_state: str) -> dict[str, object]:
    checks = {
        "quality_report_present": bool(quality),
        "runtime_cases_present": int(quality.get("cases_count", 0) or 0) > 0,
        "package_ready": package_state == "PRET_A_ENVOYER",
        "manifest_present": bool(manifest.get("fingerprint_sha256")),
        "calibration_ready_or_waiting": calibration.get("status") in {"PRET_A_RECEVOIR_REPONSES", "CALIBRATION_COMPILEE"},
        "calibration_has_no_errors": calibration.get("status") != "A_CORRIGER",
    }
    risks = {
        "runtime_blocking_failures": int(nested(quality, "totals", "blocking_failures") or 0),
        "runtime_warnings": int(nested(quality, "totals", "warnings") or 0),
        "contract_errors": int(nested(quality, "totals", "contract_errors") or 0),
        "missing_artifacts": int(nested(quality, "totals", "missing_artifacts") or 0),
        "open_runtime_questions": len(calibration.get("runtime_questions", [])) if isinstance(calibration.get("runtime_questions"), list) else 0,
    }
    status = readiness_status(checks, calibration.get("status", ""))
    return {
        "schema_version": "readiness_pre_reponses_v0",
        "status": status,
        "package_status": package_state,
        "calibration_status": calibration.get("status", ""),
        "runtime_fingerprint_sha256": manifest.get("fingerprint_sha256", ""),
        "checks": checks,
        "risks_to_calibrate": risks,
        "decision": decision_text(status, risks),
    }


def nested(data: dict, *keys: str) -> object:
    current: object = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def readiness_status(checks: dict[str, bool], calibration_status: str) -> str:
    if not checks.get("calibration_has_no_errors"):
        return "A_CORRIGER"
    required = [
        "quality_report_present",
        "runtime_cases_present",
        "package_ready",
        "manifest_present",
        "calibration_ready_or_waiting",
    ]
    if not all(checks.get(key) for key in required):
        return "A_COMPLETER_AVANT_ENVOI"
    if calibration_status == "CALIBRATION_COMPILEE":
        return "REPONSES_A_INTEGRER"
    if calibration_status == "PRET_A_RECEVOIR_REPONSES":
        return "PRET_A_RECEVOIR_REPONSES"
    return "A_CONTROLER"


def decision_text(status: str, risks: dict[str, int]) -> str:
    if status == "PRET_A_RECEVOIR_REPONSES":
        return "Infrastructure prete; attendre les reponses evaluateurs sans modifier les contrats metier."
    if status == "REPONSES_A_INTEGRER":
        return "Des reponses sont compilees; traiter le backlog v1 avant de changer les contrats."
    if status == "A_COMPLETER_AVANT_ENVOI":
        return "Completer les artefacts de controle avant envoi ou attente officielle."
    if status == "A_CORRIGER":
        return "Corriger les erreurs de saisie ou de structure avant de poursuivre."
    return f"Controle manuel requis; risques ouverts: {risks}."


def build_markdown(report: dict[str, object]) -> str:
    checks = report.get("checks", {}) if isinstance(report.get("checks"), dict) else {}
    risks = report.get("risks_to_calibrate", {}) if isinstance(report.get("risks_to_calibrate"), dict) else {}
    lines = [
        "# Readiness pre-reponses v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Statut paquet: **{report.get('package_status', '-')}**",
        f"- Statut calibration: **{report.get('calibration_status', '-')}**",
        f"- Fingerprint runtime: `{report.get('runtime_fingerprint_sha256', '')}`",
        f"- Decision: {report.get('decision', '-')}",
        "",
        "## Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- `{key}`: {'OK' if value else 'NON'}")
    lines.extend(["", "## Risques a calibrer", ""])
    for key, value in risks.items():
        lines.append(f"- `{key}`: **{value}**")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def run_readiness(
    quality_path: Path,
    calibration_path: Path,
    manifest_path: Path,
    package_index: Path,
    json_out: Path,
    markdown_out: Path,
) -> dict[str, object]:
    report = build_readiness_report(
        load_json(quality_path),
        load_json(calibration_path),
        load_json(manifest_path),
        package_status(package_index),
    )
    write_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie le readiness gate avant reponses evaluateurs.")
    parser.add_argument("--quality-report", type=Path, default=QUALITY_DEFAULT)
    parser.add_argument("--calibration", type=Path, default=CALIBRATION_DEFAULT)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--package-index", type=Path, default=PACKAGE_INDEX_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = run_readiness(args.quality_report, args.calibration, args.manifest, args.package_index, args.json_out, args.markdown_out)
    print(f"Readiness JSON: {args.json_out}")
    print(f"Readiness Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return 0 if report["status"] in {"PRET_A_RECEVOIR_REPONSES", "REPONSES_A_INTEGRER"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
