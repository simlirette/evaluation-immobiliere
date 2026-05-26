from __future__ import annotations


CLAUDE_HOOK_EVENTS = {
    "SessionStart",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PermissionDenied",
    "PreCompact",
    "PostCompact",
    "SessionEnd",
}


def build_claude_hook_invocation(
    hook_event: str,
    *,
    agent_type: str,
    payload: dict[str, object] | None = None,
    sequence: int = 1,
) -> dict[str, object]:
    if hook_event not in CLAUDE_HOOK_EVENTS:
        raise ValueError(f"hook_event inconnu: {hook_event}")
    return {
        "schema_version": "claude_hook_invocation_v0",
        "hook_event": hook_event,
        "sequence": sequence,
        "agent_type": agent_type,
        "payload": payload or {},
        "status": "ok",
        "blocking": False,
    }


def summarize_hook_invocations(
    invocations: list[dict[str, object]],
    *,
    agent_type: str,
) -> dict[str, object]:
    valid_invocations = [invocation for invocation in invocations if isinstance(invocation, dict)]
    hook_events: dict[str, int] = {}
    agents: list[str] = []
    blocking_count = 0
    for invocation in valid_invocations:
        hook_event = str(invocation.get("hook_event") or "unknown")
        hook_events[hook_event] = hook_events.get(hook_event, 0) + 1
        invocation_agent = str(invocation.get("agent_type") or "")
        if invocation_agent and invocation_agent not in agents:
            agents.append(invocation_agent)
        if invocation.get("blocking") is True:
            blocking_count += 1
    return {
        "schema_version": "claude_hook_summary_v0",
        "agent_type": agent_type,
        "invocations_count": len(valid_invocations),
        "hook_events": hook_events,
        "agents": agents,
        "agents_count": len(agents),
        "blocking_count": blocking_count,
        "ok": blocking_count == 0,
    }
