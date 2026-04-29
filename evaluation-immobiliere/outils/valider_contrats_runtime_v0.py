from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import validate_contract_rules


ARTIFACTS_TO_CHECK = {
    "fiche_bien.json",
    "comparables_proposes.json",
    "statut_sortie.json",
}


def iter_artifacts(runtime_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in runtime_dir.rglob("*.json"):
        name = path.name
        if "." in name:
            artifact = name.split(".", 1)[1]
        else:
            artifact = name
        if artifact in ARTIFACTS_TO_CHECK:
            files.append(path)
    return sorted(files)


def validate_runtime_contracts(runtime_dir: Path) -> dict:
    report = {
        "runtime_dir": runtime_dir.as_posix(),
        "files_checked": 0,
        "files_invalid": 0,
        "failures": [],
    }

    for path in iter_artifacts(runtime_dir):
        payload = json.loads(path.read_text(encoding="utf-8"))
        artifact = path.name.split(".", 1)[1] if "." in path.name else path.name
        failures = validate_contract_rules(artifact, payload)
        report["files_checked"] += 1
        if failures:
            report["files_invalid"] += 1
            report["failures"].append(
                {
                    "path": path.as_posix(),
                    "artifact": artifact,
                    "failures": failures,
                }
            )

    report["ok"] = report["files_invalid"] == 0
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Valider les contrats runtime sur les artefacts JSON generes")
    parser.add_argument("--runtime-dir", default="evaluation-immobiliere/tests/runtime", help="Repertoire runtime a analyser")
    parser.add_argument("--report-out", default="", help="Chemin optionnel du rapport JSON")
    args = parser.parse_args()

    runtime_dir = Path(args.runtime_dir)
    report = validate_runtime_contracts(runtime_dir)

    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
