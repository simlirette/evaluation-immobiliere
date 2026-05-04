#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOTS_DEFAULT = [
    Path("evaluation-immobiliere/tests/fixtures"),
    Path("evaluation-immobiliere/tests/fixtures_external"),
    Path("evaluation-immobiliere/runtime_pilotes_reels"),
]
OUT_JSON_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/anonymisation_audit.json")
OUT_MD_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels/RAPPORT-ANONYMISATION-V0.md")
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".csv", ".txt", ".yaml", ".yml", ".log"}
PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "postal_code": re.compile(r"\b[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d\b", re.IGNORECASE),
    "precise_address": re.compile(r"\b\d{1,6}\s+(rue|avenue|av\.|boulevard|boul\.|chemin|ch\.|route|rang)\b", re.IGNORECASE),
    "local_user_path": re.compile(r"C:\\Users\\[^\\\s]+", re.IGNORECASE),
}


def iter_text_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def scan_file(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[dict[str, object]] = []
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(
                {
                    "path": path.as_posix(),
                    "type": name,
                    "line": 1 + text.count("\n", 0, match.start()),
                    "excerpt": redact(match.group(0)),
                }
            )
    return findings


def redact(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "***" + value[-2:]


def build_anonymization_audit(roots: list[Path]) -> dict[str, object]:
    files = iter_text_files(roots)
    findings: list[dict[str, object]] = []
    for path in files:
        findings.extend(scan_file(path))
    return {
        "schema_version": "anonymisation_audit_v0",
        "status": "A_REVOIR_ANONYMISATION" if findings else "OK",
        "roots": [root.as_posix() for root in roots],
        "files_scanned": len(files),
        "findings_count": len(findings),
        "findings": findings,
    }


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Rapport anonymisation v0",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Fichiers analyses: **{report.get('files_scanned', 0)}**",
        f"- Findings: **{report.get('findings_count', 0)}**",
        "",
        "## Findings",
        "",
    ]
    findings = report.get("findings", [])
    if not findings:
        lines.append("- Aucun motif sensible evident detecte.")
    elif isinstance(findings, list):
        for item in findings:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('path')}` ligne {item.get('line')}: {item.get('type')} `{item.get('excerpt')}`")
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def run_audit(roots: list[Path], json_out: Path, markdown_out: Path) -> dict[str, object]:
    report = build_anonymization_audit(roots)
    write_report(report, json_out, markdown_out)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audite les fichiers texte pour motifs de donnees sensibles evidents.")
    parser.add_argument("--root", type=Path, action="append", default=[], help="Racine a scanner. Repetable.")
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    roots = args.root or ROOTS_DEFAULT
    report = run_audit(roots, args.json_out, args.markdown_out)
    print(f"Audit anonymisation JSON: {args.json_out}")
    print(f"Audit anonymisation Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    return 0 if report["status"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
