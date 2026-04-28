#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import RuntimeEngine, load_steps_from_pipeline_yaml

FIXTURES_DIR = Path("evaluation-immobiliere/tests/fixtures")
OUT_DIR = Path("evaluation-immobiliere/tests/runtime")
SUMMARY_PATH = OUT_DIR / "runtime_summary.json"
PIPELINE_PATH = Path("evaluation-immobiliere/integration/PIPELINE-RUNTIME-ASTON-V0.yaml")


def main() -> None:
    if OUT_DIR.exists():
        for p in OUT_DIR.iterdir():
            if p.is_file():
                p.unlink()

    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
    engine = RuntimeEngine(steps=steps, strict_mode=True)
    results = []

    print(f"Pipeline chargé: {len(steps)} steps depuis {PIPELINE_PATH}")
    for case_path in sorted(FIXTURES_DIR.glob("case_*.json")):
        result = engine.run_case(case_path, OUT_DIR)
        results.append(result)
        print(f"Simulé: {case_path.name} -> {len(result['events'])} events | status={result['status']}")

    SUMMARY_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résumé runtime: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
