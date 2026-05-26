#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import api

OUT_JSON_DEFAULT = PROJECT_ROOT / "runtime_pilotes_reels" / "beta_ea_readiness_v1.json"
OUT_MD_DEFAULT = PROJECT_ROOT / "runtime_pilotes_reels" / "BETA-EA-READINESS-V1.md"


def build_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Beta E.A. readiness v1",
        "",
        f"- Statut: **{report.get('status', 'UNKNOWN')}**",
        f"- Pret lien externe: **{report.get('ready_for_external_ea_link', False)}**",
        f"- Pret beta locale anonymisee: **{report.get('ready_for_local_anonymized_beta', False)}**",
        f"- Blocages: **{report.get('blocking_count', 0)}**",
        f"- Warnings: **{report.get('warning_count', 0)}**",
        f"- URL beta: `{report.get('hosted_url', '') or 'NON_CONFIGUREE'}`",
        "",
        "## Controles",
        "",
        "| Controle | Statut | Detail | Action |",
        "|---|---:|---|---|",
    ]
    for item in report.get("checks", []):
        if isinstance(item, dict):
            lines.append(
                "| "
                + str(item.get("label", ""))
                + " | "
                + str(item.get("status", ""))
                + " | "
                + str(item.get("detail", "")).replace("|", "\\|")
                + " | "
                + str(item.get("action", "")).replace("|", "\\|")
                + " |"
            )
    evidence = report.get("evidence", {})
    if isinstance(evidence, dict):
        lines.extend(["", "## Evidence", ""])
        for key, value in evidence.items():
            lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie le gate beta E.A. ferme.")
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    parser.add_argument("--strict-link", action="store_true", help="Echoue si le lien externe n'est pas pret.")
    args = parser.parse_args()

    report = api.beta_ea_readiness()
    write_outputs(report, args.json_out, args.markdown_out)
    print(f"Beta E.A. readiness JSON: {args.json_out}")
    print(f"Beta E.A. readiness Markdown: {args.markdown_out}")
    print(f"Statut: {report['status']}")
    if args.strict_link and not report.get("ready_for_external_ea_link"):
        return 1
    return 0 if report.get("ready_for_local_anonymized_beta") else 1


if __name__ == "__main__":
    raise SystemExit(main())
