from __future__ import annotations

from math import ceil
from pathlib import Path
from typing import Iterable

from engine.claude.constants import PROJECT_ROOT
from engine.claude.types import SkillSpec
from engine.claude.yamlish import as_list
from engine.skills import load_skill_registry, parse_frontmatter


CLAUDE_SKILL_CONTEXT_SCHEMA_VERSION = "claude_skill_context_v0"
CLAUDE_SKILL_PIPELINE_CONTEXT_SCHEMA_VERSION = "claude_skill_pipeline_context_v0"
CLAUDE_SKILL_VALIDATION_SCHEMA_VERSION = "claude_skill_context_validation_v0"

SUPPORTED_SKILL_LOADED_FROM = {
    "skills",
    "plugin",
    "managed",
    "bundled",
    "mcp",
    "commands_DEPRECATED",
}


def estimate_skill_frontmatter_tokens(
    name: str,
    description: str = "",
    when_to_use: str = "",
) -> int:
    text = "\n".join(part for part in (name, description, when_to_use) if part)
    return max(1, int(ceil(len(text) / 4))) if text else 0


def load_claude_skill_specs(
    skill_names: Iterable[str],
    *,
    project_root: Path | None = None,
    registry: dict | None = None,
) -> list[SkillSpec]:
    root = project_root or PROJECT_ROOT
    skill_registry = registry or load_skill_registry(root / "skills" / "SKILLS-REGISTRY.json")
    by_name = {
        str(skill.get("name")): skill
        for skill in skill_registry.get("skills", [])
        if isinstance(skill, dict) and skill.get("name")
    }
    return [
        _build_skill_spec(skill_name, by_name.get(skill_name, {}), project_root=root)
        for skill_name in skill_names
    ]


def summarize_skill_context(
    skills: Iterable[SkillSpec],
    *,
    agent_type: str = "",
) -> dict[str, object]:
    items = list(skills)
    validation_errors = validate_skill_specs(items)
    errors = sorted({error for skill in items for error in skill.errors} | set(validation_errors))
    plugins = sorted({skill.plugin for skill in items if skill.plugin})
    loaded_from = sorted({skill.loaded_from for skill in items if skill.loaded_from})
    sources = sorted({skill.source for skill in items if skill.source})
    allowed_tools = sorted(
        {
            tool
            for skill in items
            for tool in skill.allowed_tools
            if tool
        }
    )
    agents = sorted(
        {
            agent
            for skill in items
            for agent in skill.agents
            if agent
        }
    )
    return {
        "schema_version": CLAUDE_SKILL_CONTEXT_SCHEMA_VERSION,
        "agent_type": agent_type,
        "skills_count": len(items),
        "skill_names": [skill.name for skill in items],
        "loaded_from": loaded_from,
        "loaded_from_counts": _count_by(items, "loaded_from"),
        "sources": sources,
        "source_counts": _count_by(items, "source"),
        "plugins": plugins,
        "plugins_count": len(plugins),
        "agents": agents,
        "allowed_tools": allowed_tools,
        "total_frontmatter_tokens": sum(skill.frontmatter_tokens for skill in items),
        "total_content_length": sum(skill.content_length for skill in items),
        "user_invocable_count": sum(1 for skill in items if skill.user_invocable),
        "disable_model_invocation_count": sum(1 for skill in items if skill.disable_model_invocation),
        "path_scoped_count": sum(1 for skill in items if skill.paths),
        "analysis_backed_count": sum(1 for skill in items if skill.has_analysis),
        "validation": {
            "schema_version": CLAUDE_SKILL_VALIDATION_SCHEMA_VERSION,
            "errors": errors,
            "ok": not errors,
        },
        "ok": not errors,
        "skills": [skill.as_dict() for skill in items],
    }


def summarize_pipeline_skill_context(
    contexts_by_agent: dict[str, dict[str, object]],
) -> dict[str, object]:
    contexts = {
        str(agent): context
        for agent, context in contexts_by_agent.items()
        if isinstance(context, dict)
    }
    all_skill_names: list[str] = []
    all_loaded_from: set[str] = set()
    all_sources: set[str] = set()
    all_plugins: set[str] = set()
    errors: set[str] = set()
    total_frontmatter_tokens = 0
    total_content_length = 0
    skills_count = 0
    user_invocable_count = 0
    path_scoped_count = 0
    analysis_backed_count = 0

    for agent, context in contexts.items():
        skill_names = context.get("skill_names", [])
        if isinstance(skill_names, list):
            all_skill_names.extend(str(name) for name in skill_names if str(name))
        loaded_from = context.get("loaded_from", [])
        if isinstance(loaded_from, list):
            all_loaded_from.update(str(item) for item in loaded_from if str(item))
        sources = context.get("sources", [])
        if isinstance(sources, list):
            all_sources.update(str(item) for item in sources if str(item))
        plugins = context.get("plugins", [])
        if isinstance(plugins, list):
            all_plugins.update(str(item) for item in plugins if str(item))
        validation = context.get("validation", {})
        validation_errors = validation.get("errors", []) if isinstance(validation, dict) else []
        if isinstance(validation_errors, list):
            errors.update(f"{agent}:{error}" for error in validation_errors if str(error))
        if context.get("ok") is False:
            errors.add(f"{agent}:skill_context_not_ok")
        skills_count += int(context.get("skills_count", 0) or 0)
        total_frontmatter_tokens += int(context.get("total_frontmatter_tokens", 0) or 0)
        total_content_length += int(context.get("total_content_length", 0) or 0)
        user_invocable_count += int(context.get("user_invocable_count", 0) or 0)
        path_scoped_count += int(context.get("path_scoped_count", 0) or 0)
        analysis_backed_count += int(context.get("analysis_backed_count", 0) or 0)

    return {
        "schema_version": CLAUDE_SKILL_PIPELINE_CONTEXT_SCHEMA_VERSION,
        "agent_type": "claude-pipeline",
        "agents": list(contexts),
        "agents_count": len(contexts),
        "skills_count": skills_count,
        "unique_skills_count": len(set(all_skill_names)),
        "skill_names": sorted(set(all_skill_names)),
        "loaded_from": sorted(all_loaded_from),
        "sources": sorted(all_sources),
        "plugins": sorted(all_plugins),
        "plugins_count": len(all_plugins),
        "total_frontmatter_tokens": total_frontmatter_tokens,
        "total_content_length": total_content_length,
        "user_invocable_count": user_invocable_count,
        "path_scoped_count": path_scoped_count,
        "analysis_backed_count": analysis_backed_count,
        "contexts_by_agent": contexts,
        "validation": {
            "schema_version": CLAUDE_SKILL_VALIDATION_SCHEMA_VERSION,
            "errors": sorted(errors),
            "ok": not errors,
        },
        "ok": not errors,
    }


def validate_skill_specs(skills: Iterable[SkillSpec]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        if not skill.name:
            errors.append("skill_missing_name")
        if skill.name in seen:
            errors.append(f"skill_duplicate:{skill.name}")
        seen.add(skill.name)
        if not skill.path:
            errors.append(f"{skill.name}:skill_missing_path")
        if skill.loaded_from not in SUPPORTED_SKILL_LOADED_FROM:
            errors.append(f"{skill.name}:unsupported_loaded_from:{skill.loaded_from}")
        if skill.content_length <= 0:
            errors.append(f"{skill.name}:skill_content_empty")
        errors.extend(f"{skill.name}:{error}" for error in skill.errors)
    return sorted(set(errors))


def validate_skill_context(context: dict[str, object]) -> dict[str, object]:
    validation = context.get("validation", {}) if isinstance(context, dict) else {}
    errors = validation.get("errors", []) if isinstance(validation, dict) else ["skill_context_invalid"]
    if not isinstance(errors, list):
        errors = ["skill_context_invalid"]
    if isinstance(context, dict) and context.get("ok") is False:
        errors = [*errors, "skill_context_not_ok"]
    return {
        "schema_version": CLAUDE_SKILL_VALIDATION_SCHEMA_VERSION,
        "errors": sorted({str(error) for error in errors if str(error)}),
        "ok": not errors and bool(context.get("ok", False)) if isinstance(context, dict) else False,
    }


def _build_skill_spec(skill_name: str, raw: dict, *, project_root: Path) -> SkillSpec:
    raw_path = str(raw.get("path") or f"skills/{skill_name}/SKILL.md")
    skill_path = _resolve_project_path(raw_path, project_root)
    errors: list[str] = []
    meta: dict[str, object] = {}
    content = ""
    if skill_path.exists() and skill_path.is_file():
        content = skill_path.read_text(encoding="utf-8")
        meta = parse_frontmatter(skill_path)
    else:
        errors.append("skill_file_missing")

    name = str(meta.get("name") or raw.get("name") or skill_name)
    description = str(meta.get("description") or raw.get("description") or "")
    when_to_use = str(meta.get("when_to_use") or meta.get("when-to-use") or raw.get("when_to_use") or description)
    loaded_from = str(raw.get("loaded_from") or raw.get("loadedFrom") or meta.get("loaded_from") or "skills")
    source = str(raw.get("source") or meta.get("source") or "projectSettings")
    relative_path = _relative_project_path(skill_path, project_root)
    skill_root = _relative_project_path(skill_path.parent, project_root)
    allowed_tools = _as_listish(meta.get("allowed-tools") or meta.get("allowed_tools") or raw.get("allowed_tools"))
    paths = _as_listish(meta.get("paths") or raw.get("paths"))
    agents = _unique(
        [
            *as_list(raw.get("agents")),
            *as_list(meta.get("agents")),
            *as_list(meta.get("agent")),
        ]
    )
    plugin = str(raw.get("plugin") or meta.get("plugin") or "")
    if loaded_from == "plugin" and not plugin:
        plugin = str(source)
    has_analysis = bool(raw.get("has_analysis")) or (skill_path.parent / "analysis.md").exists()

    return SkillSpec(
        name=name,
        path=relative_path,
        description=description,
        type=str(meta.get("type") or raw.get("type") or ""),
        sources=_unique([*as_list(raw.get("sources")), *as_list(meta.get("sources"))]),
        agents=agents,
        loaded_from=loaded_from,
        source=source,
        skill_root=skill_root,
        plugin=plugin,
        display_name=str(meta.get("displayName") or meta.get("display_name") or meta.get("name") or name),
        when_to_use=when_to_use,
        version=str(meta.get("version") or raw.get("version") or ""),
        model=str(meta.get("model") or raw.get("model") or ""),
        argument_hint=str(meta.get("argument-hint") or meta.get("argument_hint") or raw.get("argument_hint") or ""),
        arguments=_as_listish(meta.get("arguments") or raw.get("arguments")),
        allowed_tools=allowed_tools,
        paths=paths,
        hooks=_as_listish(meta.get("hooks") or raw.get("hooks")),
        context=_as_listish(meta.get("context") or raw.get("context")),
        effort=str(meta.get("effort") or raw.get("effort") or ""),
        shell=str(meta.get("shell") or raw.get("shell") or ""),
        content_length=len(content),
        frontmatter_tokens=estimate_skill_frontmatter_tokens(name, description, when_to_use),
        has_analysis=has_analysis,
        user_invocable=_as_bool(_first_present(meta.get("user-invocable"), meta.get("user_invocable")), default=True),
        disable_model_invocation=_as_bool(
            _first_present(meta.get("disable-model-invocation"), meta.get("disable_model_invocation")),
            default=False,
        ),
        ok=not errors,
        errors=errors,
    )


def _resolve_project_path(path_value: str, project_root: Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = project_root / path
    return path


def _relative_project_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _as_listish(value: object) -> list[str]:
    if isinstance(value, list):
        return _unique(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, str) and value.strip():
        if "," in value:
            return _unique(part.strip() for part in value.split(",") if part.strip())
        return [value.strip()]
    return []


def _as_bool(value: object, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "on"}:
            return True
        if normalized in {"false", "no", "0", "off"}:
            return False
    return bool(value)


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _count_by(skills: Iterable[SkillSpec], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for skill in skills:
        value = str(getattr(skill, field_name) or "")
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
