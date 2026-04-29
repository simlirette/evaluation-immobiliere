#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import load_steps_from_pipeline_yaml

ROOT = Path("evaluation-immobiliere")
PIPELINE_PATH = ROOT / "integration/PIPELINE-RUNTIME-ASTON-V0.yaml"
INTEGRATION_DIR = ROOT / "integration"

INITIAL_ARTIFACTS = {
    "dossier_input",
    "documents_sources",
    "market_data_sources",
    "couts_reference",
    "revenus_depenses",
    "ruleset",
    "traceability_log",
}

REQUIRED_EVENTS = {
    "step_start",
    "step_done",
    "blocking_detected",
    "warning_detected",
    "artifact_written",
}

REQUIRED_METRICS = {
    "wall_clock_seconds",
    "total_tokens",
    "blocking_count",
    "warning_count",
}


def parse_agent_config(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    data = {"inputs": [], "outputs": [], "tools_allowed": []}
    mode = None
    for raw in lines:
        s = raw.strip()
        if s == "inputs:":
            mode = "inputs"
            continue
        if s == "outputs:":
            mode = "outputs"
            continue
        if s == "tools_allowed:":
            mode = "tools_allowed"
            continue
        if s.startswith("-") and mode:
            data[mode].append(s[1:].strip())
            continue
        if s and not s.startswith("-"):
            mode = None
    return data


def parse_list_block(path: Path, block_name: str) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    items: list[str] = []
    mode = None
    for raw in lines:
        stripped = raw.strip()
        if stripped == f"{block_name}:":
            mode = block_name
            continue
        if stripped.startswith("-") and mode == block_name:
            items.append(stripped[1:].strip())
            continue
        if stripped and not stripped.startswith("-"):
            mode = None
    return items


def main() -> None:
    steps = load_steps_from_pipeline_yaml(PIPELINE_PATH)
    available = set(INITIAL_ARTIFACTS)
    errors: list[str] = []

    print(f"Pipeline: {len(steps)} steps")

    for i, step in enumerate(steps, start=1):
        agent_file = f"AGENTCONFIG-{step.name.upper()}-V0.yaml"
        agent_path = INTEGRATION_DIR / agent_file
        if not agent_path.exists():
            errors.append(f"Step {i}: fichier introuvable {agent_file}")
            continue

        cfg = parse_agent_config(agent_path)

        for read in step.reads:
            if read not in available:
                errors.append(f"Step {i} ({agent_file}): read introuvable dans handoff '{read}'")

        for write in step.writes:
            if write not in cfg["outputs"]:
                errors.append(f"Step {i} ({agent_file}): write '{write}' absent des outputs agent")
            if re.search(r"\.(json|md)\.(json|md)$", write):
                errors.append(f"Step {i} ({agent_file}): extension double suspecte '{write}'")

        available.update(step.writes)

    emitted_events = set(parse_list_block(PIPELINE_PATH, "emit_events"))
    missing_events = REQUIRED_EVENTS - emitted_events
    if missing_events:
        errors.append(f"Observability: events manquants {sorted(missing_events)}")

    metrics = set(parse_list_block(PIPELINE_PATH, "required_metrics"))
    missing_metrics = REQUIRED_METRICS - metrics
    if missing_metrics:
        errors.append(f"Observability: metrics manquantes {sorted(missing_metrics)}")

    if errors:
        print("\nIncoherences detectees:")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("\nOK: pipeline, AgentConfig, observability et conventions runtime coherents (v0)")


if __name__ == "__main__":
    main()
