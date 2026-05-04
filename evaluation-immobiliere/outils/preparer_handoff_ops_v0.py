#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "ops_handoff_manifest.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "OPS-HANDOFF-MANIFEST-V0.md"
WAITING_REAL_INPUTS_STATUS = "EN_ATTENTE_ENTREES_TERRAIN_REELLES"
WAITING_ALLOWED_MISSING = {"quality_report.json", "RAPPORT-QUALITE-RUNTIME-V0.md"}


@dataclass(frozen=True)
class HandoffFile:
    key: str
    path: str
    category: str
    required: bool = True


HANDOFF_FILES = [
    HandoffFile("quality_json", "quality_report.json", "quality"),
    HandoffFile("quality_markdown", "RAPPORT-QUALITE-RUNTIME-V0.md", "quality"),
    HandoffFile("readiness_json", "readiness_pre_reponses.json", "readiness"),
    HandoffFile("readiness_markdown", "READINESS-PRE-REPONSES-V0.md", "readiness"),
    HandoffFile("review_queue_csv", "FILE-REVUE-HUMAINE-V0.csv", "human_review"),
    HandoffFile("review_queue_markdown", "FILE-REVUE-HUMAINE-V0.md", "human_review"),
    HandoffFile("knowledge_json", "knowledge_snapshot.json", "knowledge"),
    HandoffFile("knowledge_markdown", "KNOWLEDGE-SNAPSHOT-V0.md", "knowledge"),
    HandoffFile("manifest_json", "runtime_manifest.json", "traceability"),
    HandoffFile("manifest_markdown", "MANIFEST-RUNTIME-V0.md", "traceability"),
    HandoffFile("registry_json", "runtime_registry.json", "traceability"),
    HandoffFile("registry_markdown", "RUNTIME-REGISTRY-V0.md", "traceability"),
    HandoffFile("delta_json", "runtime_delta_report.json", "observability"),
    HandoffFile("delta_markdown", "RAPPORT-DELTA-RUNTIME-V0.md", "observability"),
    HandoffFile("anonymization_json", "anonymisation_audit.json", "security"),
    HandoffFile("anonymization_markdown", "RAPPORT-ANONYMISATION-V0.md", "security"),
    HandoffFile("calibration_json", "calibration_evaluateurs.json", "calibration"),
    HandoffFile("calibration_markdown", "RAPPORT-CALIBRATION-EVALUATEURS-V0.md", "calibration"),
    HandoffFile("backlog_markdown", "BACKLOG-V1.md", "calibration"),
    HandoffFile("infra_contracts_json", "infra_contracts_report.json", "contracts", required=False),
    HandoffFile("infra_contracts_markdown", "RAPPORT-CONTRATS-INFRA-V0.md", "contracts", required=False),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(runtime_dir: Path, item: HandoffFile) -> dict[str, object]:
    path = runtime_dir / item.path
    if not path.exists():
        return {
            "key": item.key,
            "path": item.path,
            "category": item.category,
            "required": item.required,
            "exists": False,
            "bytes": 0,
            "sha256": "",
        }
    stat = path.stat()
    return {
        "key": item.key,
        "path": item.path,
        "category": item.category,
        "required": item.required,
        "exists": True,
        "bytes": stat.st_size,
        "sha256": sha256_file(path),
    }


def build_handoff_manifest(runtime_dir: Path, files: list[HandoffFile] | None = None) -> dict[str, object]:
    entries = [inspect_file(runtime_dir, item) for item in (files or HANDOFF_FILES)]
    required_missing = [str(item["path"]) for item in entries if item["required"] and not item["exists"]]
    readiness_status = load_readiness_status(runtime_dir)
    required_missing_blocking = blocking_missing(required_missing, readiness_status)
    present_required = sum(1 for item in entries if item["required"] and item["exists"])
    required_count = sum(1 for item in entries if item["required"])
    return {
        "schema_version": "ops_handoff_manifest_v0",
        "status": handoff_status(required_missing, required_missing_blocking, readiness_status),
        "readiness_status": readiness_status,
        "runtime_dir": runtime_dir.as_posix(),
        "files_count": len(entries),
        "required_count": required_count,
        "required_present": present_required,
        "required_missing": required_missing,
        "required_missing_blocking": required_missing_blocking,
        "total_bytes": sum(int(item["bytes"]) for item in entries),
        "files": entries,
    }


def load_readiness_status(runtime_dir: Path) -> str:
    path = runtime_dir / "readiness_pre_reponses.json"
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(payload.get("status", "")) if isinstance(payload, dict) else ""


def blocking_missing(required_missing: list[str], readiness_status: str) -> list[str]:
    if readiness_status != WAITING_REAL_INPUTS_STATUS:
        return required_missing
    return [path for path in required_missing if path not in WAITING_ALLOWED_MISSING]


def handoff_status(required_missing: list[str], required_missing_blocking: list[str], readiness_status: str) -> str:
    if not required_missing:
        return "PRET_A_TRANSMETTRE"
    if readiness_status == WAITING_REAL_INPUTS_STATUS and not required_missing_blocking:
        return WAITING_REAL_INPUTS_STATUS
    return "A_COMPLETER"


def build_markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# Manifest handoff ops v0",
        "",
        f"- Statut: **{manifest.get('status', 'UNKNOWN')}**",
        f"- Readiness: **{manifest.get('readiness_status', '-')}**",
        f"- Repertoire runtime: `{manifest.get('runtime_dir', '-')}`",
        f"- Fichiers requis presents: **{manifest.get('required_present', 0)}/{manifest.get('required_count', 0)}**",
        f"- Octets inventories: **{manifest.get('total_bytes', 0)}**",
        "",
        "## Fichiers",
        "",
        "| Cle | Categorie | Requis | Present | Octets | SHA-256 |",
        "|---|---|---|---|---:|---|",
    ]
    for item in manifest.get("files", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            "| {key} | {category} | {required} | {exists} | {bytes} | `{sha}` |".format(
                key=item.get("key", "-"),
                category=item.get("category", "-"),
                required="oui" if item.get("required") else "non",
                exists="oui" if item.get("exists") else "non",
                bytes=item.get("bytes", 0),
                sha=item.get("sha256", ""),
            )
        )
    missing = manifest.get("required_missing", []) if isinstance(manifest.get("required_missing"), list) else []
    lines.extend(["", "## Manquants requis", ""])
    if missing:
        for path in missing:
            lines.append(f"- `{path}`")
    else:
        lines.append("- Aucun.")
    blocking = manifest.get("required_missing_blocking", []) if isinstance(manifest.get("required_missing_blocking"), list) else []
    lines.extend(["", "## Manquants bloquants", ""])
    if blocking:
        for path in blocking:
            lines.append(f"- `{path}`")
    else:
        lines.append("- Aucun.")
    return "\n".join(lines).rstrip() + "\n"


def write_manifest(manifest: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(manifest), encoding="utf-8")


def generate_handoff_manifest(runtime_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    manifest = build_handoff_manifest(runtime_dir)
    write_manifest(manifest, json_out, markdown_out)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare le manifeste de handoff operationnel pre-reponses.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    manifest = generate_handoff_manifest(args.runtime_dir, args.json_out, args.markdown_out)
    print(f"Handoff ops JSON: {args.json_out}")
    print(f"Handoff ops Markdown: {args.markdown_out}")
    print(f"Statut: {manifest['status']}")
    return 0 if manifest["status"] in {"PRET_A_TRANSMETTRE", WAITING_REAL_INPUTS_STATUS} else 1


if __name__ == "__main__":
    raise SystemExit(main())
