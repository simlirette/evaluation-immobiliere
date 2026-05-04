from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.runtime import PipelineValidationError, load_steps_from_pipeline_yaml
from engine.skills import build_skill_registry, load_agent_config_skills
from outils.generer_registre_skills import render_matrix


def parse_agent_type(config_path: Path) -> str:
    for raw in config_path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.startswith("agent_type:"):
            return stripped.split(":", 1)[1].strip()
    return ""


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_skill_readiness(
    project_root: Path = PROJECT_ROOT,
    *,
    registry_path: Path | None = None,
    matrix_path: Path | None = None,
    integration_dir: Path | None = None,
    pipeline_path: Path | None = None,
) -> dict:
    registry_path = registry_path or project_root / "skills" / "SKILLS-REGISTRY.json"
    matrix_path = matrix_path or project_root / "integration" / "AGENT-SKILLS-MATRIX.md"
    integration_dir = integration_dir or project_root / "integration"
    pipeline_path = pipeline_path or integration_dir / "PIPELINE-RUNTIME-ASTON-V0.yaml"

    errors: list[str] = []
    warnings: list[str] = []
    expected_registry = build_skill_registry(project_root / "skills")
    actual_registry = load_registry(registry_path)
    skill_names = {skill["name"] for skill in expected_registry["skills"]}

    if actual_registry != expected_registry:
        errors.append(f"{registry_path.as_posix()}: registre non synchronise avec skills/*/SKILL.md")

    expected_matrix = render_matrix(expected_registry)
    if not matrix_path.exists():
        errors.append(f"{matrix_path.as_posix()}: matrice introuvable")
    elif matrix_path.read_text(encoding="utf-8") != expected_matrix:
        errors.append(f"{matrix_path.as_posix()}: matrice non synchronisee avec le registre genere")

    for skill in expected_registry["skills"]:
        skill_path = project_root / skill["path"]
        if not skill_path.exists():
            errors.append(f"{skill['name']}: fichier skill introuvable {skill['path']}")
        if not skill["description"]:
            errors.append(f"{skill['name']}: description frontmatter manquante")
        if not skill["agents"]:
            errors.append(f"{skill['name']}: aucun agent declare")
        if not skill["sources"]:
            warnings.append(f"{skill['name']}: aucune source declaree")
        if not skill["has_analysis"]:
            errors.append(f"{skill['name']}: analysis.md manquant")

    agent_configs = {}
    for config_path in sorted(integration_dir.glob("AGENTCONFIG-*-V0.yaml")):
        agent_type = parse_agent_type(config_path)
        if not agent_type:
            errors.append(f"{config_path.as_posix()}: agent_type manquant")
            continue
        agent_configs[agent_type] = config_path

    for agent, registry_skills in sorted(expected_registry["skills_by_agent"].items()):
        config_path = agent_configs.get(agent)
        if config_path is None:
            errors.append(f"{agent}: AgentConfig introuvable")
            continue
        config_skills = load_agent_config_skills(config_path)
        if not config_skills:
            errors.append(f"{config_path.as_posix()}: skills_allowed vide ou manquant")
        unknown = sorted(set(config_skills) - skill_names)
        if unknown:
            errors.append(f"{config_path.as_posix()}: skills_allowed inconnus {unknown}")
        if config_skills != registry_skills:
            errors.append(
                f"{config_path.as_posix()}: skills_allowed divergent du registre "
                f"(config={config_skills}, registry={registry_skills})"
            )

    try:
        steps = load_steps_from_pipeline_yaml(pipeline_path)
    except PipelineValidationError as exc:
        errors.append(str(exc))
        steps = []

    for step in steps:
        config_path = integration_dir / str(step.agent_config or "")
        if not step.agent_config or not config_path.exists():
            errors.append(f"{step.name}: agent_config pipeline introuvable {step.agent_config}")
            continue
        config_skills = load_agent_config_skills(config_path)
        if step.skills != config_skills:
            errors.append(f"{step.name}: skills pipeline divergents de {config_path.name}")

    return {
        "schema_version": "skills_readiness_v0",
        "ok": not errors,
        "skills_count": len(expected_registry["skills"]),
        "agents_count": len(expected_registry["skills_by_agent"]),
        "agent_configs_count": len(agent_configs),
        "pipeline_steps_count": len(steps),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifier la coherence skills/AgentConfig/runtime Aston-like")
    parser.add_argument("--report-out", default="", help="Chemin optionnel du rapport JSON")
    args = parser.parse_args()

    report = validate_skill_readiness(PROJECT_ROOT)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)

    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
