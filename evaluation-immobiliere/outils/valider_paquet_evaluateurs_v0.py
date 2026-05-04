#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
PACKAGE_DIR_DEFAULT = Path("evaluation-immobiliere/paquets_evaluateurs/v0")
ATELIER_DIR_DEFAULT = Path("evaluation-immobiliere/atelier")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "paquet_evaluateurs_gate.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "PAQUET-EVALUATEURS-GATE-V0.md"
PACKAGE_INDEX_NAME = "PAQUET-EVALUATEURS-V0.md"
WAITING_PACKAGE_STATUS = "EN_ATTENTE_DOSSIERS_REELS"
WAITING_REAL_INPUTS_STATUS = "EN_ATTENTE_ENTREES_TERRAIN_REELLES"
REQUIRED_FILES = [
    PACKAGE_INDEX_NAME,
    "CHECKLIST-ENVOI-EVALUATEURS.md",
    "MANIFESTE-CAS-PILOTES.csv",
    "REPONSES-EVALUATEURS-A-REMPLIR.csv",
    "CALIBRATION-EVALUATEURS-A-REMPLIR.csv",
]
EXPECTED_HEADERS = {
    "REPONSES-EVALUATEURS-A-REMPLIR.csv": "REPONSES-EVALUATEURS-TEMPLATE.csv",
    "CALIBRATION-EVALUATEURS-A-REMPLIR.csv": "CALIBRATION-EVALUATEURS-TEMPLATE.csv",
}
SENSITIVE_PATTERNS = {
    "LOCAL_USER_PATH": re.compile(r"C:\\Users\\[^\\\s]+", re.IGNORECASE),
    "EMAIL": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "PHONE": re.compile(r"\b(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b"),
}


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def package_status(index_path: Path) -> str:
    if not index_path.exists():
        return "ABSENT"
    text = index_path.read_text(encoding="utf-8")
    match = re.search(r"Statut:\s+\*\*([^*]+)\*\*", text)
    return match.group(1).strip() if match else "INCONNU"


def scan_sensitive_files(package_dir: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(package_dir.glob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".csv", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8")
        for name, pattern in SENSITIVE_PATTERNS.items():
            matches = sorted({match.group(0) for match in pattern.finditer(text)})
            if matches:
                findings.append({"file": path.name, "pattern": name, "matches_count": len(matches)})
    return findings


def build_file_checks(package_dir: Path) -> list[dict[str, object]]:
    checks = []
    for filename in REQUIRED_FILES:
        path = package_dir / filename
        checks.append({"file": filename, "exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0})
    return checks


def build_header_checks(package_dir: Path, atelier_dir: Path) -> list[dict[str, object]]:
    checks = []
    for package_name, template_name in EXPECTED_HEADERS.items():
        actual = csv_header(package_dir / package_name)
        expected = csv_header(atelier_dir / template_name)
        checks.append(
            {
                "file": package_name,
                "template": template_name,
                "ok": bool(actual) and actual == expected,
                "actual_header": actual,
                "expected_header": expected,
            }
        )
    return checks


def build_case_manifest_check(package_dir: Path, runtime_dir: Path) -> dict[str, object]:
    rows = csv_rows(package_dir / "MANIFESTE-CAS-PILOTES.csv")
    summary = load_json(runtime_dir / "runtime_summary.json", [])
    expected_count = len(summary) if isinstance(summary, list) else 0
    required_columns = ["cas", "dossier_id", "statut_runtime", "blocages", "warnings", "artefacts"]
    header = csv_header(package_dir / "MANIFESTE-CAS-PILOTES.csv")
    return {
        "ok": header == required_columns and len(rows) == expected_count,
        "rows_count": len(rows),
        "expected_rows_count": expected_count,
        "header": header,
        "expected_header": required_columns,
    }


def build_paquet_gate_report(package_dir: Path, runtime_dir: Path, atelier_dir: Path) -> dict[str, object]:
    file_checks = build_file_checks(package_dir)
    header_checks = build_header_checks(package_dir, atelier_dir)
    case_manifest = build_case_manifest_check(package_dir, runtime_dir)
    sensitive_findings = scan_sensitive_files(package_dir) if package_dir.exists() else []
    anonymization = load_json(runtime_dir / "anonymisation_audit.json", {})
    anonymization_status = anonymization.get("status", "ABSENT") if isinstance(anonymization, dict) else "ABSENT"
    index_status = package_status(package_dir / PACKAGE_INDEX_NAME)

    issues: list[dict[str, object]] = []
    for check in file_checks:
        if not check["exists"]:
            issues.append({"severity": "error", "code": "PACKAGE_FILE_MISSING", "target": check["file"]})
    for check in header_checks:
        if not check["ok"]:
            issues.append({"severity": "error", "code": "CSV_HEADER_MISMATCH", "target": check["file"]})
    if not case_manifest["ok"]:
        issues.append({"severity": "error", "code": "CASE_MANIFEST_MISMATCH", "target": "MANIFESTE-CAS-PILOTES.csv"})
    if index_status == WAITING_PACKAGE_STATUS:
        issues.append({"severity": "info", "code": "PACKAGE_WAITING_REAL_INPUTS", "target": index_status})
    elif index_status != "PRET_A_ENVOYER":
        issues.append({"severity": "error", "code": "PACKAGE_STATUS_NOT_READY", "target": index_status})
    if anonymization_status != "OK":
        issues.append({"severity": "error", "code": "ANONYMIZATION_NOT_OK", "target": anonymization_status})
    for finding in sensitive_findings:
        issues.append({"severity": "error", "code": "SENSITIVE_PATTERN", "target": finding["file"], "pattern": finding["pattern"]})

    blocking_issues = [issue for issue in issues if issue.get("severity") == "error"]
    if blocking_issues:
        status = "A_CORRIGER"
    elif index_status == WAITING_PACKAGE_STATUS:
        status = WAITING_REAL_INPUTS_STATUS
    else:
        status = "PRET_A_ENVOYER"

    return {
        "schema_version": "paquet_evaluateurs_gate_v0",
        "status": status,
        "package_dir": package_dir.as_posix(),
        "runtime_dir": runtime_dir.as_posix(),
        "package_status": index_status,
        "anonymization_status": anonymization_status,
        "blocking_issues_count": len(blocking_issues),
        "required_files": file_checks,
        "csv_headers": header_checks,
        "case_manifest": case_manifest,
        "sensitive_findings": sensitive_findings,
        "issues": issues,
    }


def build_markdown(report: dict[str, object]) -> str:
    issues = report.get("issues", []) if isinstance(report.get("issues"), list) else []
    lines = [
        "# Gate paquet evaluateurs v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Statut paquet: **{report.get('package_status', 'UNKNOWN')}**",
        f"- Audit anonymisation: **{report.get('anonymization_status', 'UNKNOWN')}**",
        f"- Issues: **{len(issues)}**",
        f"- Issues bloquantes: **{report.get('blocking_issues_count', 0)}**",
        "",
        "## Fichiers requis",
        "",
        "| Fichier | Present | Octets |",
        "|---|---|---:|",
    ]
    for item in report.get("required_files", []):
        if isinstance(item, dict):
            lines.append(f"| {item.get('file', '-')} | {'oui' if item.get('exists') else 'non'} | {item.get('bytes', 0)} |")
    lines.extend(["", "## Issues", ""])
    if issues:
        for item in issues:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('code', '-')}`: {item.get('target', '-')}")
    else:
        lines.append("- Aucune.")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def run_gate(package_dir: Path, runtime_dir: Path, atelier_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    report = build_paquet_gate_report(package_dir, runtime_dir, atelier_dir)
    write_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Valide le paquet evaluateurs avant envoi.")
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR_DEFAULT)
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--atelier-dir", type=Path, default=ATELIER_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    report = run_gate(args.package_dir, args.runtime_dir, args.atelier_dir, args.json_out, args.markdown_out)
    print(f"Gate paquet JSON: {args.json_out}")
    print(f"Gate paquet Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return 0 if report["status"] in {"PRET_A_ENVOYER", WAITING_REAL_INPUTS_STATUS} else 2


if __name__ == "__main__":
    raise SystemExit(main())
