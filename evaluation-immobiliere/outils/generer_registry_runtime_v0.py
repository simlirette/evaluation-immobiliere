#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OUT_JSON_DEFAULT = RUNTIME_DIR_DEFAULT / "runtime_registry.json"
OUT_MD_DEFAULT = RUNTIME_DIR_DEFAULT / "RUNTIME-REGISTRY-V0.md"


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    fixed = os.environ.get("RUNTIME_FIXED_TIMESTAMP_UTC")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def current_commit_sha(cwd: Path = PROJECT_ROOT.parent) -> str:
    if os.environ.get("GITHUB_SHA"):
        return str(os.environ["GITHUB_SHA"])
    try:
        completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, text=True, capture_output=True, check=True)
    except Exception:
        return ""
    return completed.stdout.strip()


def report_paths(runtime_dir: Path) -> dict[str, str]:
    names = {
        "quality": "quality_report.json",
        "calibration": "calibration_evaluateurs.json",
        "manifest": "runtime_manifest.json",
        "readiness": "readiness_pre_reponses.json",
        "knowledge": "knowledge_snapshot.json",
        "human_review_queue": "FILE-REVUE-HUMAINE-V0.csv",
        "anonymization": "anonymisation_audit.json",
    }
    return {key: (runtime_dir / name).as_posix() for key, name in names.items() if (runtime_dir / name).exists()}


def build_registry_entry(runtime_dir: Path, *, timestamp_utc: str | None = None, commit_sha: str | None = None) -> dict[str, object]:
    timestamp = timestamp_utc or utc_now_iso()
    commit = commit_sha if commit_sha is not None else current_commit_sha()
    manifest = load_json(runtime_dir / "runtime_manifest.json", {})
    quality = load_json(runtime_dir / "quality_report.json", {})
    calibration = load_json(runtime_dir / "calibration_evaluateurs.json", {})
    readiness = load_json(runtime_dir / "readiness_pre_reponses.json", {})
    pre_run = load_json(runtime_dir / "pre_reponses_run.json", {})
    pre_response_chain_ok = (
        bool(pre_run.get("ok"))
        if isinstance(pre_run, dict) and "ok" in pre_run
        else os.environ.get("PRE_RESPONSE_CHAIN_ACTIVE") == "1"
    )

    fingerprint = manifest.get("fingerprint_sha256", "") if isinstance(manifest, dict) else ""
    run_seed = f"{commit}:{fingerprint}:{timestamp}"
    run_id = hashlib.sha256(run_seed.encode("utf-8")).hexdigest()[:16]
    totals = quality.get("totals", {}) if isinstance(quality, dict) and isinstance(quality.get("totals"), dict) else {}

    return {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "commit_sha": commit,
        "runtime_fingerprint_sha256": fingerprint,
        "pre_response_chain_ok": pre_response_chain_ok,
        "readiness_status": readiness.get("status", "") if isinstance(readiness, dict) else "",
        "calibration_status": calibration.get("status", "") if isinstance(calibration, dict) else "",
        "cases_count": quality.get("cases_count", 0) if isinstance(quality, dict) else 0,
        "status_counts": quality.get("status_counts", {}) if isinstance(quality, dict) else {},
        "totals": {
            "blocking_failures": totals.get("blocking_failures", 0),
            "warnings": totals.get("warnings", 0),
            "contract_errors": totals.get("contract_errors", 0),
            "missing_artifacts": totals.get("missing_artifacts", 0),
        },
        "reports": report_paths(runtime_dir),
    }


def load_registry(path: Path) -> dict[str, object]:
    payload = load_json(path, {})
    if isinstance(payload, dict) and isinstance(payload.get("runs"), list):
        return payload
    return {"schema_version": "runtime_registry_v0", "runs": []}


def append_registry_entry(registry_path: Path, entry: dict[str, object]) -> dict[str, object]:
    registry = load_registry(registry_path)
    registry["runs"].append(entry)
    registry["latest_run_id"] = entry["run_id"]
    registry["runs_count"] = len(registry["runs"])
    return registry


def build_markdown(registry: dict[str, object]) -> str:
    runs = registry.get("runs", [])
    lines = [
        "# Runtime registry v0",
        "",
        f"- Runs: **{len(runs) if isinstance(runs, list) else 0}**",
        f"- Dernier run: `{registry.get('latest_run_id', '-')}`",
        "",
        "| Run | Commit | Fingerprint | Readiness | Calibration | Cases | Blocages | Warnings |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    if isinstance(runs, list):
        for item in runs:
            if not isinstance(item, dict):
                continue
            totals = item.get("totals", {}) if isinstance(item.get("totals"), dict) else {}
            lines.append(
                "| {run} | {commit} | {fingerprint} | {readiness} | {calibration} | {cases} | {blocking} | {warnings} |".format(
                    run=item.get("run_id", "-"),
                    commit=str(item.get("commit_sha", ""))[:12],
                    fingerprint=str(item.get("runtime_fingerprint_sha256", ""))[:12],
                    readiness=item.get("readiness_status", "-"),
                    calibration=item.get("calibration_status", "-"),
                    cases=item.get("cases_count", 0),
                    blocking=totals.get("blocking_failures", 0),
                    warnings=totals.get("warnings", 0),
                )
            )
    return "\n".join(lines).rstrip() + "\n"


def write_registry(registry: dict[str, object], json_out: Path, markdown_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_out.write_text(build_markdown(registry), encoding="utf-8")


def generate_registry(runtime_dir: Path, json_out: Path, markdown_out: Path) -> dict[str, object]:
    entry = build_registry_entry(runtime_dir)
    registry = append_registry_entry(json_out, entry)
    write_registry(registry, json_out, markdown_out)
    return registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Ajoute un run au registre runtime.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    parser.add_argument("--markdown-out", type=Path, default=OUT_MD_DEFAULT)
    args = parser.parse_args()

    registry = generate_registry(args.runtime_dir, args.json_out, args.markdown_out)
    print(f"Registry JSON: {args.json_out}")
    print(f"Registry Markdown: {args.markdown_out}")
    print(f"Runs: {registry['runs_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
