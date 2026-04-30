#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_manifest.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "MANIFEST-RUNTIME-V0.md"
EXCLUDED_NAMES = {
    OUT_JSON_DEFAULT.name,
    OUT_MD_DEFAULT.name,
    "readiness_pre_reponses.json",
    "READINESS-PRE-REPONSES-V0.md",
    "pre_reponses_run.json",
    "knowledge_snapshot.json",
    "KNOWLEDGE-SNAPSHOT-V0.md",
    "runtime_registry.json",
    "RUNTIME-REGISTRY-V0.md",
    "infra_contracts_report.json",
    "RAPPORT-CONTRATS-INFRA-V0.md",
}
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".csv", ".txt", ".yaml", ".yml", ".log"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_manifest_files(runtime_dir: Path) -> list[Path]:
    if not runtime_dir.exists():
        return []
    files: list[Path] = []
    for path in runtime_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def classify_file(path: Path, runtime_dir: Path) -> str:
    relative = path.relative_to(runtime_dir)
    parts = relative.parts
    if parts and parts[0].startswith("case_"):
        return "case_artifact"
    if parts and parts[0] == "ingestion_v0":
        return "ingestion"
    if parts and parts[0] == "source_text":
        return "source_text"
    if path.suffix.lower() == ".json":
        return "runtime_control_json"
    if path.suffix.lower() == ".md":
        return "runtime_control_markdown"
    if path.suffix.lower() == ".csv":
        return "runtime_control_csv"
    return "runtime_control"


def read_json_if_exists(path: Path, default: object) -> object:
    if not path.exists():
        return default
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload


def build_runtime_manifest(runtime_dir: Path) -> dict[str, object]:
    artifacts = []
    total_bytes = 0
    for path in iter_manifest_files(runtime_dir):
        stat = path.stat()
        total_bytes += stat.st_size
        artifacts.append(
            {
                "path": path.relative_to(runtime_dir).as_posix(),
                "category": classify_file(path, runtime_dir),
                "bytes": stat.st_size,
                "sha256": sha256_file(path),
            }
        )

    fingerprint_payload = "\n".join(f"{item['path']} {item['sha256']}" for item in artifacts)
    fingerprint = hashlib.sha256(fingerprint_payload.encode("utf-8")).hexdigest() if artifacts else ""
    summary = read_json_if_exists(runtime_dir / "runtime_summary.json", [])
    quality = read_json_if_exists(runtime_dir / "quality_report.json", {})
    calibration = read_json_if_exists(runtime_dir / "calibration_evaluateurs.json", {})

    return {
        "schema_version": "runtime_manifest_v0",
        "runtime_dir": runtime_dir.as_posix(),
        "fingerprint_sha256": fingerprint,
        "files_count": len(artifacts),
        "total_bytes": total_bytes,
        "runtime_cases": len(summary) if isinstance(summary, list) else 0,
        "quality_status_counts": quality.get("status_counts", {}) if isinstance(quality, dict) else {},
        "calibration_status": calibration.get("status", "") if isinstance(calibration, dict) else "",
        "artifacts": artifacts,
    }


def build_markdown(manifest: dict[str, object]) -> str:
    artifacts = manifest.get("artifacts", [])
    lines = [
        "# Manifest runtime v0",
        "",
        f"- Repertoire: `{manifest.get('runtime_dir', '-')}`",
        f"- Fingerprint SHA-256: `{manifest.get('fingerprint_sha256', '')}`",
        f"- Fichiers: **{manifest.get('files_count', 0)}**",
        f"- Octets: **{manifest.get('total_bytes', 0)}**",
        f"- Dossiers runtime: **{manifest.get('runtime_cases', 0)}**",
        f"- Statut calibration: **{manifest.get('calibration_status') or '-'}**",
        "",
        "## Fichiers",
        "",
        "| Chemin | Categorie | Octets | SHA-256 |",
        "|---|---|---:|---|",
    ]
    if isinstance(artifacts, list):
        for item in artifacts:
            if isinstance(item, dict):
                lines.append(
                    "| {path} | {category} | {bytes} | `{sha}` |".format(
                        path=item.get("path", "-"),
                        category=item.get("category", "-"),
                        bytes=item.get("bytes", 0),
                        sha=item.get("sha256", ""),
                    )
                )
    return "\n".join(lines).rstrip() + "\n"


def write_manifest(manifest: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(manifest), encoding="utf-8")


def generate_manifest(runtime_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    manifest = build_runtime_manifest(runtime_dir)
    write_manifest(manifest, json_out, markdown_out)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere un manifest hashable des sorties runtime.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    manifest = generate_manifest(args.runtime_dir, args.json_out, args.markdown_out)
    print(f"Manifest JSON: {args.json_out}")
    print(f"Manifest Markdown: {args.markdown_out}")
    print(f"Fingerprint: {manifest['fingerprint_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
