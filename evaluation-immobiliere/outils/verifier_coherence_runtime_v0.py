#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

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


def parse_pipeline(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    steps: list[dict] = []
    current: dict | None = None
    mode = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if re.match(r"^\s*- step:\s*\d+", line):
            if current:
                steps.append(current)
            current = {"agent_config": None, "reads": [], "writes": []}
            mode = None
            continue

        if current is None:
            continue

        if stripped.startswith("agent_config:"):
            current["agent_config"] = stripped.split(":", 1)[1].strip()
            continue

        if stripped == "reads:":
            mode = "reads"
            continue

        if stripped == "writes:":
            mode = "writes"
            continue

        if stripped.startswith("-") and mode in {"reads", "writes"}:
            current[mode].append(stripped[1:].strip())
            continue

        if stripped and not stripped.startswith("-"):
            mode = None

    if current:
        steps.append(current)

    return steps


def main() -> None:
    steps = parse_pipeline(PIPELINE_PATH)
    available = set(INITIAL_ARTIFACTS)
    errors: list[str] = []

    print(f"Pipeline: {len(steps)} steps")

    for i, step in enumerate(steps, start=1):
        agent_file = step["agent_config"]
        if not agent_file:
            errors.append(f"Step {i}: agent_config manquant")
            continue

        agent_path = INTEGRATION_DIR / agent_file
        if not agent_path.exists():
            errors.append(f"Step {i}: fichier introuvable {agent_file}")
            continue

        cfg = parse_agent_config(agent_path)

        for read in step["reads"]:
            if read not in available:
                errors.append(f"Step {i} ({agent_file}): read introuvable dans handoff '{read}'")

        for write in step["writes"]:
            if write not in cfg["outputs"]:
                errors.append(f"Step {i} ({agent_file}): write '{write}' absent des outputs agent")

        available.update(step["writes"])

    if errors:
        print("\nIncohérences détectées:")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("\nOK: pipeline et AgentConfig cohérents (v0)")


if __name__ == "__main__":
    main()
