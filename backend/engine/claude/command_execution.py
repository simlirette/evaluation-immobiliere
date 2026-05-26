from __future__ import annotations

from typing import Callable, Iterable

from engine.claude.commands import find_command
from engine.claude.context import build_context_compact_summary, build_context_state
from engine.claude.envelopes import build_claude_event_envelope, build_claude_message_envelope
from engine.claude.types import CommandSpec


CLAUDE_COMMAND_EXECUTION_SCHEMA_VERSION = "claude_command_execution_v0"
CLAUDE_COMMAND_OUTPUT_BLOCK_TYPE = "local_command_output"

SAFE_LOCAL_COMMANDS = {"compact", "cost", "status", "summary"}
LOCAL_JSX_TEXT_ADAPTERS = {"status"}

CommandHandler = Callable[[CommandSpec, str, dict[str, object]], dict[str, object]]


def execute_slash_command(
    command_name: str,
    commands: Iterable[CommandSpec],
    *,
    args: str = "",
    context: dict[str, object] | None = None,
) -> dict[str, object]:
    runtime_context = context or {}
    command = find_command(command_name, commands)
    if command is None:
        return _execution_result(
            requested_command_name=command_name,
            args=args,
            context=runtime_context,
            ok=False,
            status="unavailable",
            errors=["command_not_available"],
        )

    safety_error = validate_local_command_execution(command)
    if safety_error:
        return _execution_result(
            requested_command_name=command_name,
            command=command,
            args=args,
            context=runtime_context,
            ok=False,
            status="blocked",
            errors=[safety_error],
        )

    handler = COMMAND_HANDLERS.get(command.name)
    if handler is None:
        return _execution_result(
            requested_command_name=command_name,
            command=command,
            args=args,
            context=runtime_context,
            ok=False,
            status="blocked",
            errors=["command_not_implemented"],
        )

    output = handler(command, args, runtime_context)
    return _execution_result(
        requested_command_name=command_name,
        command=command,
        args=args,
        context=runtime_context,
        ok=True,
        status="completed",
        output=output,
    )


def validate_local_command_execution(command: CommandSpec) -> str:
    if command.name not in SAFE_LOCAL_COMMANDS:
        return "command_not_safe"
    if command.type == "prompt":
        return "prompt_command_not_local"
    if command.type == "local-jsx" and command.name not in LOCAL_JSX_TEXT_ADAPTERS:
        return "local_jsx_command_not_executable"
    if command.type == "local" and not (command.supports_non_interactive or command.bridge_safe):
        return "local_command_not_non_interactive"
    return ""


def _handle_status(command: CommandSpec, args: str, context: dict[str, object]) -> dict[str, object]:
    del command, args
    metrics = _dict(context.get("metrics"))
    conversation_state = _dict(context.get("conversation_state"))
    context_state = _dict(context.get("context_state"))
    command_context = _dict(context.get("command_context"))
    settings_context = _dict(context.get("settings_context"))
    skill_context = _dict(context.get("skill_context"))
    tool_registry_summary = _dict(context.get("tool_registry_summary"))
    agent_type = _agent_type(context)
    status = str(context.get("status") or "ready")
    output = {
        "agent_type": agent_type,
        "scope": str(context.get("scope") or agent_type),
        "status": status,
        "model": str(context.get("model") or ""),
        "canonical_model": str(context.get("canonical_model") or ""),
        "permission_mode": str(context.get("permission_mode") or ""),
        "messages_count": int(conversation_state.get("messages_count", _len_list(context.get("messages"))) or 0),
        "tool_use_count": int(metrics.get("tool_use_count", conversation_state.get("tool_use_count", 0)) or 0),
        "estimated_tokens": int(context_state.get("estimated_tokens", metrics.get("total_tokens", 0)) or 0),
        "commands_count": int(command_context.get("commands_count", 0) or 0),
        "settings_filtered_commands_count": int(command_context.get("settings_filtered_commands_count", 0) or 0),
        "skills_count": int(skill_context.get("skills_count", skill_context.get("total_skills_count", 0)) or 0),
        "tools_count": int(tool_registry_summary.get("tools_count", _len_list(context.get("tools_allowed"))) or 0),
        "setting_sources": list(settings_context.get("active_sources", []))
        if isinstance(settings_context.get("active_sources"), list)
        else [],
    }
    output["display_text"] = (
        f"{agent_type}: {status}; model={output['canonical_model'] or output['model']}; "
        f"messages={output['messages_count']}; tools={output['tools_count']}; "
        f"skills={output['skills_count']}; slash_commands={output['commands_count']}"
    )
    return output


def _handle_summary(command: CommandSpec, args: str, context: dict[str, object]) -> dict[str, object]:
    del command
    metrics = _dict(context.get("metrics"))
    task_state = _dict(context.get("task_state"))
    handoff_summary = _dict(context.get("handoff_summary"))
    conversation_state = _dict(context.get("conversation_state"))
    agent_type = _agent_type(context)
    blocking = _list(context.get("blocking_failures"))
    warnings = _list(context.get("warnings"))
    output = {
        "agent_type": agent_type,
        "scope": str(context.get("scope") or agent_type),
        "status": str(context.get("status") or "ready"),
        "instructions": args.strip(),
        "messages_count": int(conversation_state.get("messages_count", _len_list(context.get("messages"))) or 0),
        "tool_use_count": int(metrics.get("tool_use_count", conversation_state.get("tool_use_count", 0)) or 0),
        "tasks_count": int(task_state.get("tasks_count", 0) or 0),
        "completed_tasks_count": int(task_state.get("completed_count", 0) or 0),
        "handoffs_count": int(handoff_summary.get("handoffs_count", 0) or 0),
        "blocking_count": len(blocking),
        "warning_count": len(warnings),
        "blocking_failures": blocking,
        "warnings": warnings,
    }
    output["display_text"] = (
        f"{agent_type} summary: status={output['status']}; "
        f"tasks={output['completed_tasks_count']}/{output['tasks_count']}; "
        f"tool_uses={output['tool_use_count']}; warnings={output['warning_count']}; "
        f"blocking={output['blocking_count']}"
    )
    return output


def _handle_cost(command: CommandSpec, args: str, context: dict[str, object]) -> dict[str, object]:
    del command, args
    usage_accounting = _dict(context.get("usage_accounting"))
    usage = _dict(usage_accounting.get("usage"))
    metrics = _dict(context.get("metrics"))
    total_cost = usage_accounting.get("cost_usd", usage_accounting.get("total_cost_usd", metrics.get("total_cost_usd", 0.0)))
    formatted = usage_accounting.get(
        "formatted_cost",
        usage_accounting.get("formatted_total_cost", metrics.get("formatted_total_cost", f"${float(total_cost or 0.0):.6f}")),
    )
    output = {
        "agent_type": _agent_type(context),
        "scope": str(context.get("scope") or _agent_type(context)),
        "total_cost_usd": float(total_cost or 0.0),
        "formatted_total_cost": str(formatted or "$0.000000"),
        "input_tokens": int(usage.get("input_tokens", usage_accounting.get("input_tokens", metrics.get("input_tokens", 0))) or 0),
        "output_tokens": int(usage.get("output_tokens", usage_accounting.get("output_tokens", metrics.get("output_tokens", 0))) or 0),
        "cache_read_input_tokens": int(
            usage.get(
                "cache_read_input_tokens",
                usage_accounting.get("cache_read_input_tokens", metrics.get("cache_read_input_tokens", 0)),
            )
            or 0
        ),
        "cache_creation_input_tokens": int(
            usage.get(
                "cache_creation_input_tokens",
                usage_accounting.get("cache_creation_input_tokens", metrics.get("cache_creation_input_tokens", 0)),
            )
            or 0
        ),
        "wall_clock_seconds": float(metrics.get("wall_clock_seconds", usage_accounting.get("wall_clock_seconds", 0.0)) or 0.0),
    }
    output["display_text"] = (
        f"Session cost: {output['formatted_total_cost']} "
        f"({output['input_tokens']} input, {output['output_tokens']} output tokens)"
    )
    return output


def _handle_compact(command: CommandSpec, args: str, context: dict[str, object]) -> dict[str, object]:
    del command
    messages = _messages(context)
    context_state = _dict(context.get("context_state"))
    if not context_state:
        context_state = build_context_state(
            messages,
            agent_type=_agent_type(context),
            threshold_tokens=_optional_int(context.get("context_compaction_threshold_tokens")),
            preserve_recent_tool_results=_optional_int(context.get("preserve_recent_tool_results"), default=3) or 3,
        )
    summary = build_context_compact_summary(
        messages,
        context_state,
        agent_type=_agent_type(context),
    )
    if args.strip():
        summary["instructions"] = args.strip()
    output = {
        "agent_type": _agent_type(context),
        "scope": str(context.get("scope") or _agent_type(context)),
        "mutates_messages": False,
        "compaction_result": {
            "type": "compact",
            "summary": summary,
            "messages_before_compaction": len(messages),
            "estimated_tokens": context_state.get("estimated_tokens", 0),
            "preserved_tool_result_ids": context_state.get("preserved_tool_result_ids", []),
            "dropped_tool_result_ids": context_state.get("dropped_tool_result_ids", []),
        },
    }
    output["display_text"] = (
        f"Compact summary prepared: messages={len(messages)}, "
        f"estimated_tokens={context_state.get('estimated_tokens', 0)}"
    )
    return output


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "compact": _handle_compact,
    "cost": _handle_cost,
    "status": _handle_status,
    "summary": _handle_summary,
}


def _execution_result(
    *,
    requested_command_name: str,
    args: str,
    context: dict[str, object],
    ok: bool,
    status: str,
    command: CommandSpec | None = None,
    output: dict[str, object] | None = None,
    errors: list[str] | None = None,
) -> dict[str, object]:
    normalized_name = _normalize_command_name(command.name if command else requested_command_name)
    unique_errors = sorted({str(error) for error in errors or [] if str(error)})
    result: dict[str, object] = {
        "schema_version": CLAUDE_COMMAND_EXECUTION_SCHEMA_VERSION,
        "requested_command_name": requested_command_name,
        "command_name": normalized_name,
        "command_display_name": f"/{normalized_name}" if normalized_name else requested_command_name,
        "command_type": command.type if command else "",
        "source": command.source if command else "",
        "loaded_from": command.loaded_from if command else "",
        "args": args,
        "agent_type": _agent_type(context),
        "status": status,
        "display": "system" if ok else "skip",
        "ok": ok,
        "errors": unique_errors,
        "output": output or {},
    }
    display_text = str((output or {}).get("display_text") or "")
    event_name = "slash_command_executed" if ok else "slash_command_blocked"
    result["event"] = build_claude_event_envelope(
        event_name,
        agent_type=_agent_type(context),
        sequence=_len_list(context.get("events")) + 1,
        payload={
            "event": event_name,
            "agent_type": _agent_type(context),
            "command_name": normalized_name,
            "requested_command_name": requested_command_name,
            "command_type": result["command_type"],
            "status": status,
            "ok": ok,
            "errors": unique_errors,
        },
    )
    if ok and display_text:
        result["message"] = build_claude_message_envelope(
            role="assistant",
            agent_type=_agent_type(context),
            content=[
                {
                    "type": CLAUDE_COMMAND_OUTPUT_BLOCK_TYPE,
                    "command": result["command_display_name"],
                    "text": display_text,
                    "result": output or {},
                }
            ],
            sequence=_len_list(context.get("messages")) + 1,
            metadata={
                "subtype": "local_command",
                "command_name": normalized_name,
                "display": result["display"],
            },
        )
    return result


def _messages(context: dict[str, object]) -> list[dict[str, object]]:
    messages = context.get("messages", [])
    return [message for message in messages if isinstance(message, dict)] if isinstance(messages, list) else []


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _len_list(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _agent_type(context: dict[str, object]) -> str:
    return str(context.get("agent_type") or "claude-runtime")


def _optional_int(value: object, *, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_command_name(value: object) -> str:
    text = str(value or "").strip()
    if text.startswith("/"):
        text = text[1:]
    return text.lower()
