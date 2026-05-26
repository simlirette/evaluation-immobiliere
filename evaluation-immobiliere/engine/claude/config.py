from __future__ import annotations

from pathlib import Path

from engine.claude.commands import build_agent_command_specs, summarize_command_context
from engine.claude.constants import PROJECT_ROOT
from engine.claude.exceptions import AgentConfigError
from engine.claude.models import resolve_model_profile
from engine.claude.skills import load_claude_skill_specs, summarize_skill_context
from engine.claude.tools import TOOL_REGISTRY, summarize_tool_registry, validate_tool_registry
from engine.claude.types import (
    ClaudeAgentBudget,
    ClaudeAgentFlags,
    ClaudeStyleAgentDefinition,
    SkillSpec,
    ToolSpec,
)
from engine.claude.yamlish import as_dict, as_list, as_optional_int, parse_yaml_subset
from engine.skills import load_skill_registry


def load_claude_agent_definition(
    config_path: Path,
    *,
    project_root: Path | None = None,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> ClaudeStyleAgentDefinition:
    root = project_root or PROJECT_ROOT
    config = parse_yaml_subset(config_path)
    registry = tool_registry or TOOL_REGISTRY
    registry_errors = validate_tool_registry(registry)
    if registry_errors:
        raise AgentConfigError(f"{config_path}: registre outils invalide: {registry_errors}")

    agent_type = str(config.get("agent_type") or "").strip()
    if not agent_type:
        raise AgentConfigError(f"{config_path}: agent_type manquant")

    tools = as_list(config.get("tools_allowed"))
    unknown_tools = [name for name in tools if name not in registry]
    if unknown_tools:
        raise AgentConfigError(f"{config_path}: tools inconnus: {unknown_tools}")
    tool_registry_summary = summarize_tool_registry(tools, registry)
    if not tool_registry_summary["ok"]:
        raise AgentConfigError(f"{config_path}: tools invalides: {tool_registry_summary['validation_errors']}")

    skills = as_list(config.get("skills_allowed"))
    skill_registry = load_skill_registry(root / "skills" / "SKILLS-REGISTRY.json")
    known_skills = {str(skill.get("name")) for skill in skill_registry.get("skills", []) if isinstance(skill, dict)}
    unknown_skills = [name for name in skills if name not in known_skills]
    if unknown_skills:
        raise AgentConfigError(f"{config_path}: skills inconnus: {unknown_skills}")
    skill_specs = load_claude_skill_specs(skills, project_root=root, registry=skill_registry)
    skill_context = summarize_skill_context(skill_specs, agent_type=agent_type)
    if not skill_context["ok"]:
        raise AgentConfigError(f"{config_path}: skills invalides: {skill_context['validation']['errors']}")
    command_context = summarize_command_context(
        build_agent_command_specs(skill_specs),
        agent_type=agent_type,
    )
    if not command_context["ok"]:
        raise AgentConfigError(f"{config_path}: commandes invalides: {command_context['validation']['errors']}")

    prompts = as_dict(config.get("prompts"))
    budgets = as_dict(config.get("budgets"))
    flags = as_dict(config.get("flags"))
    quality_gates = as_dict(config.get("quality_gates"))
    human_validation = as_dict(config.get("human_validation"))
    budget = ClaudeAgentBudget(
        max_iterations=int(budgets.get("max_iterations") or 12),
        max_tokens=int(budgets.get("max_tokens") or 8192),
        max_total_tokens=int(budgets.get("max_total_tokens") or 25000),
        window_size=int(budgets.get("window_size") or 8),
        max_wall_clock_seconds=as_optional_int(budgets.get("max_wall_clock_seconds")),
    )
    model = str(config.get("model") or "claude-sonnet-4-6")

    return ClaudeStyleAgentDefinition(
        agent_type=agent_type,
        model=model,
        model_profile=resolve_model_profile(model),
        system_prompt_static=str(prompts.get("system_prompt_static") or ""),
        system_prompt_dynamic_template=str(prompts.get("system_prompt_dynamic_template") or ""),
        inputs=as_list(config.get("inputs")),
        outputs=as_list(config.get("outputs")),
        tools=tools,
        tool_registry_summary=tool_registry_summary,
        skills=skills,
        skill_context=skill_context,
        command_context=command_context,
        budgets=budget,
        flags=ClaudeAgentFlags(
            thinking_enabled=bool(flags.get("thinking_enabled", False)),
            long_cache=bool(flags.get("long_cache", False)),
            verification_checklist=str(flags.get("verification_checklist") or "") or None,
        ),
        quality_gates={
            "blocking": as_list(quality_gates.get("blocking")),
            "warnings": as_list(quality_gates.get("warnings")),
        },
        human_validation=human_validation,
        config_path=config_path.relative_to(root).as_posix() if config_path.is_relative_to(root) else config_path.as_posix(),
    )


def resolve_tool_specs(
    definition: ClaudeStyleAgentDefinition,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> list[ToolSpec]:
    registry = tool_registry or TOOL_REGISTRY
    return [registry[name] for name in definition.tools]


def resolve_skill_specs(
    definition: ClaudeStyleAgentDefinition,
    *,
    project_root: Path | None = None,
) -> list[SkillSpec]:
    root = project_root or PROJECT_ROOT
    registry = load_skill_registry(root / "skills" / "SKILLS-REGISTRY.json")
    return load_claude_skill_specs(definition.skills, project_root=root, registry=registry)
