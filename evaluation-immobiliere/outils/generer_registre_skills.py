from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.skills import build_skill_registry


def main() -> int:
    registry = build_skill_registry(PROJECT_ROOT / "skills")
    registry_path = PROJECT_ROOT / "skills" / "SKILLS-REGISTRY.json"
    matrix_path = PROJECT_ROOT / "integration" / "AGENT-SKILLS-MATRIX.md"

    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    matrix_path.write_text(render_matrix(registry), encoding="utf-8")

    print(f"skills={len(registry['skills'])}")
    print(f"registry={registry_path}")
    print(f"matrix={matrix_path}")
    return 0


def render_matrix(registry: dict) -> str:
    lines = [
        "# Agent skills matrix",
        "",
        "Registre des skills projet utilises par les agents du runtime Aston-like.",
        "",
        "## Agents",
        "",
    ]
    for agent, skills in sorted(registry["skills_by_agent"].items()):
        lines.append(f"### {agent}")
        lines.append("")
        for skill in skills:
            lines.append(f"- `{skill}`")
        lines.append("")

    lines.extend(["## Skills", ""])
    for skill in registry["skills"]:
        agents = ", ".join(f"`{agent}`" for agent in skill["agents"]) or "`non-declare`"
        sources = ", ".join(f"`{source}`" for source in skill["sources"]) or "`non-declare`"
        analysis = "oui" if skill["has_analysis"] else "non"
        lines.append(f"### {skill['name']}")
        lines.append("")
        lines.append(f"- Type: `{skill['type']}`")
        lines.append(f"- Agents: {agents}")
        lines.append(f"- Sources: {sources}")
        lines.append(f"- Analysis encodee: {analysis}")
        lines.append(f"- Fichier: `{skill['path']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
