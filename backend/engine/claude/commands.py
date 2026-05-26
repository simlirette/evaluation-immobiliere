from __future__ import annotations

from collections import Counter
from typing import Iterable

from engine.claude.types import CommandSpec, SkillSpec


CLAUDE_COMMAND_CONTEXT_SCHEMA_VERSION = "claude_command_context_v0"
CLAUDE_COMMAND_PIPELINE_CONTEXT_SCHEMA_VERSION = "claude_command_pipeline_context_v0"
CLAUDE_COMMAND_VALIDATION_SCHEMA_VERSION = "claude_command_context_validation_v0"

SUPPORTED_COMMAND_TYPES = {"prompt", "local", "local-jsx"}
SUPPORTED_COMMAND_SOURCES = {"builtin", "projectSettings", "plugin", "managed", "bundled", "mcp"}
SUPPORTED_COMMAND_LOADED_FROM = {
    "builtin",
    "commands_DEPRECATED",
    "skills",
    "plugin",
    "managed",
    "bundled",
    "mcp",
}


BUILTIN_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec(
        name="agents",
        type="local-jsx",
        description="Manage agent configurations",
        source="builtin",
        immediate=True,
    ),
    CommandSpec(
        name="compact",
        type="local",
        description="Clear conversation history but keep a summary in context",
        source="builtin",
        argument_hint="<optional custom summarization instructions>",
        supports_non_interactive=True,
        bridge_safe=True,
    ),
    CommandSpec(
        name="cost",
        type="local",
        description="Show session usage and estimated cost",
        source="builtin",
        supports_non_interactive=True,
        bridge_safe=True,
        remote_safe=True,
    ),
    CommandSpec(
        name="help",
        type="local-jsx",
        description="Show available commands and runtime help",
        source="builtin",
        immediate=True,
        remote_safe=True,
    ),
    CommandSpec(
        name="hooks",
        type="local-jsx",
        description="Inspect and manage hook configuration",
        source="builtin",
    ),
    CommandSpec(
        name="permissions",
        type="local-jsx",
        description="Inspect and manage tool permission rules",
        source="builtin",
    ),
    CommandSpec(
        name="resume",
        type="local-jsx",
        description="Resume a previous runtime session",
        source="builtin",
        argument_hint="<session id>",
    ),
    CommandSpec(
        name="skills",
        type="local-jsx",
        description="List project skills available to the agent",
        source="builtin",
    ),
    CommandSpec(
        name="status",
        type="local-jsx",
        description="Show runtime status, model, account, and tool state",
        source="builtin",
        immediate=True,
    ),
    CommandSpec(
        name="summary",
        type="local",
        description="Summarize the current runtime session",
        source="builtin",
        supports_non_interactive=True,
        bridge_safe=True,
    ),
)


def build_agent_command_specs(
    skills: Iterable[SkillSpec],
    *,
    include_builtin: bool = True,
    disabled_commands: Iterable[str] | None = None,
    enabled_commands: Iterable[str] | None = None,
) -> list[CommandSpec]:
    commands = list(BUILTIN_COMMANDS) if include_builtin else []
    commands.extend(skill_as_prompt_command(skill) for skill in skills)
    return filter_enabled_commands(
        commands,
        disabled_commands=disabled_commands,
        enabled_commands=enabled_commands,
    )


def filter_enabled_commands(
    commands: Iterable[CommandSpec],
    *,
    disabled_commands: Iterable[str] | None = None,
    enabled_commands: Iterable[str] | None = None,
) -> list[CommandSpec]:
    disabled = _normalize_command_names(disabled_commands)
    enabled = _normalize_command_names(enabled_commands)
    filtered: list[CommandSpec] = []
    for command in commands:
        if _command_matches(command, disabled):
            continue
        if enabled and not _command_matches(command, enabled):
            continue
        filtered.append(command)
    return filtered


def skill_as_prompt_command(skill: SkillSpec) -> CommandSpec:
    return CommandSpec(
        name=skill.name,
        type="prompt",
        description=skill.description,
        source=skill.source,
        loaded_from=skill.loaded_from,
        argument_hint=skill.argument_hint,
        progress_message=f"loading {skill.name}",
        content_length=skill.content_length,
        has_user_specified_description=bool(skill.description),
        allowed_tools=list(skill.allowed_tools),
        model=skill.model,
        when_to_use=skill.when_to_use,
        version=skill.version,
        disable_model_invocation=skill.disable_model_invocation,
        user_invocable=skill.user_invocable,
        plugin=skill.plugin,
        skill_root=skill.skill_root,
        context=skill.context[0] if skill.context else "inline",
        effort=skill.effort,
        paths=list(skill.paths),
        hooks=list(skill.hooks),
        ok=skill.ok,
        errors=list(skill.errors),
    )


def summarize_command_context(
    commands: Iterable[CommandSpec],
    *,
    agent_type: str = "",
    all_commands: Iterable[CommandSpec] | None = None,
    include_builtin_commands: bool = True,
    disabled_commands: Iterable[str] | None = None,
    enabled_commands: Iterable[str] | None = None,
) -> dict[str, object]:
    items = list(commands)
    all_items = list(all_commands) if all_commands is not None else list(items)
    requested_disabled = _normalize_command_names(disabled_commands)
    requested_enabled = _normalize_command_names(enabled_commands)
    filtered_names = {command.name for command in all_items} - {command.name for command in items}
    disabled_filtered = [
        command.name for command in all_items
        if command.name in filtered_names and _command_matches(command, requested_disabled)
    ]
    not_enabled_filtered = [
        command.name for command in all_items
        if command.name in filtered_names
        and requested_enabled
        and not _command_matches(command, requested_enabled)
        and command.name not in disabled_filtered
    ]
    validation_errors = validate_command_specs(items)
    errors = sorted({error for command in items for error in command.errors} | set(validation_errors))
    model_invocable = filter_model_invocable_commands(items)
    slash_skill_commands = filter_slash_command_tool_skills(items)
    return {
        "schema_version": CLAUDE_COMMAND_CONTEXT_SCHEMA_VERSION,
        "agent_type": agent_type,
        "commands_count": len(items),
        "unfiltered_commands_count": len(all_items),
        "command_names": [command.name for command in items],
        "include_builtin_commands": include_builtin_commands,
        "requested_disabled_command_names": sorted(requested_disabled),
        "requested_enabled_command_names": sorted(requested_enabled),
        "disabled_command_names": disabled_filtered,
        "not_enabled_command_names": not_enabled_filtered,
        "settings_filtered_command_names": sorted(filtered_names),
        "settings_filtered_commands_count": len(filtered_names),
        "commands_by_type": _count_by(items, "type"),
        "sources": sorted({command.source for command in items if command.source}),
        "source_counts": _count_by(items, "source"),
        "loaded_from": sorted({command.loaded_from for command in items if command.loaded_from}),
        "loaded_from_counts": _count_by(items, "loaded_from"),
        "builtin_commands_count": sum(1 for command in items if command.source == "builtin"),
        "prompt_commands_count": sum(1 for command in items if command.type == "prompt"),
        "local_commands_count": sum(1 for command in items if command.type == "local"),
        "local_jsx_commands_count": sum(1 for command in items if command.type == "local-jsx"),
        "model_invocable_command_names": [command.name for command in model_invocable],
        "model_invocable_commands_count": len(model_invocable),
        "slash_skill_command_names": [command.name for command in slash_skill_commands],
        "slash_skill_commands_count": len(slash_skill_commands),
        "user_invocable_count": sum(1 for command in items if command.user_invocable),
        "bridge_safe_command_names": [command.name for command in items if command.bridge_safe],
        "bridge_safe_count": sum(1 for command in items if command.bridge_safe),
        "remote_safe_command_names": [command.name for command in items if command.remote_safe],
        "remote_safe_count": sum(1 for command in items if command.remote_safe),
        "hidden_count": sum(1 for command in items if command.is_hidden),
        "sensitive_count": sum(1 for command in items if command.is_sensitive),
        "commands": [command.as_dict() for command in items],
        "validation": {
            "schema_version": CLAUDE_COMMAND_VALIDATION_SCHEMA_VERSION,
            "errors": errors,
            "ok": not errors,
        },
        "ok": not errors,
    }


def summarize_pipeline_command_context(
    contexts_by_agent: dict[str, dict[str, object]],
) -> dict[str, object]:
    contexts = {
        str(agent): context
        for agent, context in contexts_by_agent.items()
        if isinstance(context, dict)
    }
    all_names: list[str] = []
    all_model_invocable: list[str] = []
    all_slash_skills: list[str] = []
    sources: set[str] = set()
    loaded_from: set[str] = set()
    by_type: Counter[str] = Counter()
    errors: set[str] = set()
    commands_count = 0
    unfiltered_commands_count = 0
    settings_filtered_commands_count = 0
    builtin_commands_count = 0
    bridge_safe_count = 0
    remote_safe_count = 0
    disabled_command_names: set[str] = set()
    not_enabled_command_names: set[str] = set()
    settings_filtered_command_names: set[str] = set()

    for agent, context in contexts.items():
        command_names = context.get("command_names", [])
        if isinstance(command_names, list):
            all_names.extend(str(name) for name in command_names if str(name))
        disabled_names = context.get("disabled_command_names", [])
        if isinstance(disabled_names, list):
            disabled_command_names.update(str(name) for name in disabled_names if str(name))
        not_enabled_names = context.get("not_enabled_command_names", [])
        if isinstance(not_enabled_names, list):
            not_enabled_command_names.update(str(name) for name in not_enabled_names if str(name))
        filtered_names = context.get("settings_filtered_command_names", [])
        if isinstance(filtered_names, list):
            settings_filtered_command_names.update(str(name) for name in filtered_names if str(name))
        model_invocable = context.get("model_invocable_command_names", [])
        if isinstance(model_invocable, list):
            all_model_invocable.extend(str(name) for name in model_invocable if str(name))
        slash_skills = context.get("slash_skill_command_names", [])
        if isinstance(slash_skills, list):
            all_slash_skills.extend(str(name) for name in slash_skills if str(name))
        for source in context.get("sources", []) if isinstance(context.get("sources"), list) else []:
            if str(source):
                sources.add(str(source))
        for item in context.get("loaded_from", []) if isinstance(context.get("loaded_from"), list) else []:
            if str(item):
                loaded_from.add(str(item))
        type_counts = context.get("commands_by_type", {})
        if isinstance(type_counts, dict):
            by_type.update({str(key): int(value or 0) for key, value in type_counts.items()})
        validation = context.get("validation", {})
        validation_errors = validation.get("errors", []) if isinstance(validation, dict) else []
        if isinstance(validation_errors, list):
            errors.update(f"{agent}:{error}" for error in validation_errors if str(error))
        if context.get("ok") is False:
            errors.add(f"{agent}:command_context_not_ok")
        commands_count += int(context.get("commands_count", 0) or 0)
        unfiltered_commands_count += int(context.get("unfiltered_commands_count", 0) or 0)
        settings_filtered_commands_count += int(context.get("settings_filtered_commands_count", 0) or 0)
        builtin_commands_count += int(context.get("builtin_commands_count", 0) or 0)
        bridge_safe_count += int(context.get("bridge_safe_count", 0) or 0)
        remote_safe_count += int(context.get("remote_safe_count", 0) or 0)

    return {
        "schema_version": CLAUDE_COMMAND_PIPELINE_CONTEXT_SCHEMA_VERSION,
        "agent_type": "claude-pipeline",
        "agents": list(contexts),
        "agents_count": len(contexts),
        "commands_count": commands_count,
        "unfiltered_commands_count": unfiltered_commands_count,
        "unique_commands_count": len(set(all_names)),
        "command_names": sorted(set(all_names)),
        "disabled_command_names": sorted(disabled_command_names),
        "not_enabled_command_names": sorted(not_enabled_command_names),
        "settings_filtered_command_names": sorted(settings_filtered_command_names),
        "settings_filtered_commands_count": settings_filtered_commands_count,
        "commands_by_type": dict(sorted(by_type.items())),
        "sources": sorted(sources),
        "loaded_from": sorted(loaded_from),
        "builtin_commands_count": builtin_commands_count,
        "model_invocable_command_names": sorted(set(all_model_invocable)),
        "model_invocable_commands_count": len(set(all_model_invocable)),
        "slash_skill_command_names": sorted(set(all_slash_skills)),
        "slash_skill_commands_count": len(set(all_slash_skills)),
        "bridge_safe_count": bridge_safe_count,
        "remote_safe_count": remote_safe_count,
        "contexts_by_agent": contexts,
        "validation": {
            "schema_version": CLAUDE_COMMAND_VALIDATION_SCHEMA_VERSION,
            "errors": sorted(errors),
            "ok": not errors,
        },
        "ok": not errors,
    }


def filter_model_invocable_commands(commands: Iterable[CommandSpec]) -> list[CommandSpec]:
    return [
        command
        for command in commands
        if command.type == "prompt"
        and not command.disable_model_invocation
        and command.source != "builtin"
        and (
            command.loaded_from in {"bundled", "skills", "commands_DEPRECATED"}
            or command.has_user_specified_description
            or bool(command.when_to_use)
        )
    ]


def filter_slash_command_tool_skills(commands: Iterable[CommandSpec]) -> list[CommandSpec]:
    return [
        command
        for command in commands
        if command.type == "prompt"
        and command.source != "builtin"
        and (command.has_user_specified_description or bool(command.when_to_use))
        and (
            command.loaded_from in {"skills", "plugin", "bundled"}
            or command.disable_model_invocation
        )
    ]


def find_command(command_name: str, commands: Iterable[CommandSpec]) -> CommandSpec | None:
    normalized = _normalize_command_name(command_name)
    for command in commands:
        names = [command.name, *command.aliases]
        if normalized in {_normalize_command_name(name) for name in names}:
            return command
    return None


def validate_command_specs(commands: Iterable[CommandSpec]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for command in commands:
        if not command.name:
            errors.append("command_missing_name")
        if command.name in seen:
            errors.append(f"command_duplicate:{command.name}")
        seen.add(command.name)
        if command.type not in SUPPORTED_COMMAND_TYPES:
            errors.append(f"{command.name}:unsupported_type:{command.type}")
        if command.source not in SUPPORTED_COMMAND_SOURCES:
            errors.append(f"{command.name}:unsupported_source:{command.source}")
        if command.loaded_from not in SUPPORTED_COMMAND_LOADED_FROM:
            errors.append(f"{command.name}:unsupported_loaded_from:{command.loaded_from}")
        if command.type == "prompt" and command.content_length <= 0:
            errors.append(f"{command.name}:prompt_content_empty")
        errors.extend(f"{command.name}:{error}" for error in command.errors)
    return sorted(set(errors))


def validate_command_context(context: dict[str, object]) -> dict[str, object]:
    validation = context.get("validation", {}) if isinstance(context, dict) else {}
    errors = validation.get("errors", []) if isinstance(validation, dict) else ["command_context_invalid"]
    if not isinstance(errors, list):
        errors = ["command_context_invalid"]
    if isinstance(context, dict) and context.get("ok") is False:
        errors = [*errors, "command_context_not_ok"]
    unique_errors = sorted({str(error) for error in errors if str(error)})
    return {
        "schema_version": CLAUDE_COMMAND_VALIDATION_SCHEMA_VERSION,
        "errors": unique_errors,
        "ok": not unique_errors and bool(context.get("ok", False)) if isinstance(context, dict) else False,
    }


def _count_by(commands: Iterable[CommandSpec], field_name: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for command in commands:
        value = str(getattr(command, field_name) or "")
        if value:
            counts[value] += 1
    return dict(sorted(counts.items()))


def _command_matches(command: CommandSpec, names: set[str]) -> bool:
    if not names:
        return False
    command_names = {_normalize_command_name(command.name)}
    command_names.update(_normalize_command_name(alias) for alias in command.aliases)
    return bool(command_names & names)


def _normalize_command_names(values: Iterable[str] | None) -> set[str]:
    return {
        normalized
        for normalized in (_normalize_command_name(value) for value in values or [])
        if normalized
    }


def _normalize_command_name(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("/"):
        text = text[1:]
    return text.lower()
