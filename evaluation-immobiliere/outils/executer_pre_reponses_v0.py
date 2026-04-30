#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
REPORT_DEFAULT = OUT_DIR_DEFAULT / "pre_reponses_run.json"
LOCK_DEFAULT = OUT_DIR_DEFAULT / "pre_reponses.lock"
LOCK_TTL_SECONDS_DEFAULT = 60 * 60


@dataclass(frozen=True)
class PreResponseStep:
    name: str
    script: Path


class PreResponseLockError(RuntimeError):
    pass


def build_pre_response_steps(project_root: Path = PROJECT_ROOT) -> list[PreResponseStep]:
    outils = project_root / "outils"
    return [
        PreResponseStep("executer_dossiers_reels", outils / "executer_dossiers_pilotes_reels_v0.py"),
        PreResponseStep("preparer_revue_interne", outils / "preparer_revue_interne_pilotes_v0.py"),
        PreResponseStep("preparer_durcissement_contrats", outils / "preparer_durcissement_contrats_v0.py"),
        PreResponseStep("preparer_paquet_evaluateurs", outils / "preparer_paquet_evaluateurs_v0.py"),
        PreResponseStep("calibrer_reponses_evaluateurs", outils / "calibrer_reponses_evaluateurs_v0.py"),
        PreResponseStep("generer_file_revue_humaine", outils / "generer_file_revue_humaine_v0.py"),
        PreResponseStep("auditer_anonymisation", outils / "auditer_anonymisation_v0.py"),
        PreResponseStep("generer_manifest_runtime_initial", outils / "generer_manifest_runtime_v0.py"),
        PreResponseStep("generer_knowledge_snapshot", outils / "generer_knowledge_snapshot_v0.py"),
        PreResponseStep("generer_manifest_runtime_final", outils / "generer_manifest_runtime_v0.py"),
        PreResponseStep("verifier_readiness_pre_reponses", outils / "verifier_readiness_pre_reponses_v0.py"),
        PreResponseStep("analyser_delta_runtime", outils / "analyser_delta_runtime_v0.py"),
        PreResponseStep("generer_registry_runtime", outils / "generer_registry_runtime_v0.py"),
        PreResponseStep("preparer_handoff_ops", outils / "preparer_handoff_ops_v0.py"),
        PreResponseStep("valider_rapports_infra", outils / "valider_rapports_infra_v0.py"),
        PreResponseStep("valider_schemas_ops", outils / "valider_schemas_ops_v0.py"),
        PreResponseStep("valider_paquet_evaluateurs", outils / "valider_paquet_evaluateurs_v0.py"),
        PreResponseStep("ops_doctor", outils / "ops_doctor_v0.py"),
    ]


def run_steps(steps: list[PreResponseStep], *, cwd: Path, dry_run: bool = False) -> dict[str, object]:
    results: list[dict[str, object]] = []
    started_at = utc_now_iso()
    monotonic_start = time.perf_counter()
    for step in steps:
        command = [sys.executable, str(step.script)]
        step_started_at = utc_now_iso()
        step_monotonic_start = time.perf_counter()
        if dry_run:
            results.append(
                {
                    "name": step.name,
                    "command": command,
                    "returncode": None,
                    "status": "DRY_RUN",
                    "started_at_utc": step_started_at,
                    "ended_at_utc": utc_now_iso(),
                    "duration_seconds": round(time.perf_counter() - step_monotonic_start, 4),
                }
            )
            continue
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        results.append(
            {
                "name": step.name,
                "command": command,
                "returncode": completed.returncode,
                "status": "OK" if completed.returncode == 0 else "FAILED",
                "started_at_utc": step_started_at,
                "ended_at_utc": utc_now_iso(),
                "duration_seconds": round(time.perf_counter() - step_monotonic_start, 4),
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            break
    ok = all(item["status"] in {"OK", "DRY_RUN"} for item in results)
    failed = next((item for item in results if item.get("status") == "FAILED"), None)
    return {
        "schema_version": "pre_reponses_run_v0",
        "ok": ok,
        "started_at_utc": started_at,
        "ended_at_utc": utc_now_iso(),
        "duration_seconds": round(time.perf_counter() - monotonic_start, 4),
        "steps_count": len(results),
        "failed_step": failed.get("name") if isinstance(failed, dict) else "",
        "steps": results,
    }


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def read_lock(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"invalid": True}
    return payload if isinstance(payload, dict) else {"invalid": True}


def lock_is_stale(payload: dict[str, object], ttl_seconds: int, *, now: datetime | None = None) -> bool:
    if payload.get("invalid"):
        return True
    acquired = parse_iso_datetime(payload.get("acquired_at_utc"))
    if acquired is None:
        return True
    active_now = now or utc_now()
    return (active_now - acquired).total_seconds() > ttl_seconds


def acquire_lock(path: Path, *, ttl_seconds: int = LOCK_TTL_SECONDS_DEFAULT, force: bool = False) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        payload = read_lock(path)
        if not force and not lock_is_stale(payload, ttl_seconds):
            raise PreResponseLockError(f"Execution pre-reponses deja en cours: {path}")
        path.unlink()

    payload = {
        "schema_version": "pre_reponses_lock_v0",
        "status": "RUNNING",
        "pid": os.getpid(),
        "acquired_at_utc": utc_now_iso(),
        "ttl_seconds": ttl_seconds,
    }
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(path), flags)
    except FileExistsError as exc:
        raise PreResponseLockError(f"Execution pre-reponses deja en cours: {path}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return payload


def release_lock(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def execute_pre_response_chain(
    *,
    report_out: Path = REPORT_DEFAULT,
    dry_run: bool = False,
    lock_file: Path = LOCK_DEFAULT,
    lock_ttl_seconds: int = LOCK_TTL_SECONDS_DEFAULT,
    force_lock: bool = False,
) -> dict[str, object]:
    locked = False
    previous_chain_active = os.environ.get("PRE_RESPONSE_CHAIN_ACTIVE")
    if not dry_run:
        acquire_lock(lock_file, ttl_seconds=lock_ttl_seconds, force=force_lock)
        locked = True
    try:
        os.environ["PRE_RESPONSE_CHAIN_ACTIVE"] = "1"
        report = run_steps(build_pre_response_steps(), cwd=PROJECT_ROOT.parent, dry_run=dry_run)
        write_run_report(report_out, report)
        return report
    finally:
        if previous_chain_active is None:
            os.environ.pop("PRE_RESPONSE_CHAIN_ACTIVE", None)
        else:
            os.environ["PRE_RESPONSE_CHAIN_ACTIVE"] = previous_chain_active
        if locked:
            release_lock(lock_file)


def write_run_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute toute la chaine operationnelle pre-reponses.")
    parser.add_argument("--report-out", type=Path, default=REPORT_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--lock-file", type=Path, default=LOCK_DEFAULT)
    parser.add_argument("--lock-ttl-seconds", type=int, default=LOCK_TTL_SECONDS_DEFAULT)
    parser.add_argument("--force-lock", action="store_true")
    args = parser.parse_args()

    report = execute_pre_response_chain(
        report_out=args.report_out,
        dry_run=args.dry_run,
        lock_file=args.lock_file,
        lock_ttl_seconds=args.lock_ttl_seconds,
        force_lock=args.force_lock,
    )
    print(f"Rapport execution pre-reponses: {args.report_out}")
    print(f"OK: {report['ok']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
