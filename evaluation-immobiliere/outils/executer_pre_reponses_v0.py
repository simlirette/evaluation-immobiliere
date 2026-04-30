#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
REPORT_DEFAULT = OUT_DIR_DEFAULT / "pre_reponses_run.json"


@dataclass(frozen=True)
class PreResponseStep:
    name: str
    script: Path


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
        PreResponseStep("generer_registry_runtime", outils / "generer_registry_runtime_v0.py"),
        PreResponseStep("valider_rapports_infra", outils / "valider_rapports_infra_v0.py"),
    ]


def run_steps(steps: list[PreResponseStep], *, cwd: Path, dry_run: bool = False) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for step in steps:
        command = [sys.executable, str(step.script)]
        if dry_run:
            results.append({"name": step.name, "command": command, "returncode": None, "status": "DRY_RUN"})
            continue
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        results.append(
            {
                "name": step.name,
                "command": command,
                "returncode": completed.returncode,
                "status": "OK" if completed.returncode == 0 else "FAILED",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        if completed.returncode != 0:
            break
    return {
        "schema_version": "pre_reponses_run_v0",
        "ok": all(item["status"] in {"OK", "DRY_RUN"} for item in results),
        "steps": results,
    }


def write_run_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute toute la chaine operationnelle pre-reponses.")
    parser.add_argument("--report-out", type=Path, default=REPORT_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = run_steps(build_pre_response_steps(), cwd=PROJECT_ROOT.parent, dry_run=args.dry_run)
    write_run_report(args.report_out, report)
    print(f"Rapport execution pre-reponses: {args.report_out}")
    print(f"OK: {report['ok']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
