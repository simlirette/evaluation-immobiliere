from __future__ import annotations

from engine.claude.yamlish import handoff_string_list, unique


def build_agent_handoff_message(from_agent: str, to_agent: str, result: dict[str, object]) -> dict[str, object]:
    artifact_events = [
        event
        for event in result.get("events", [])
        if isinstance(event, dict) and event.get("event") == "artifact_written" and event.get("artifact")
    ]
    artifacts = [
        {
            "artifact": str(event.get("artifact") or ""),
            "path": str(event.get("path") or ""),
        }
        for event in artifact_events
    ]
    task_state = result.get("task_state", {})
    task_summary = task_state if isinstance(task_state, dict) else {}
    context_state = result.get("context_state", {})
    context_summary = context_state if isinstance(context_state, dict) else {}
    permission_summary = result.get("permission_summary", {})
    return {
        "schema_version": "claude_agent_handoff_v0",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "status": str(result.get("status") or "UNKNOWN"),
        "artifact_dir": str(result.get("artifact_dir") or ""),
        "artifacts_count": len(artifacts),
        "artifacts": artifacts,
        "blocking_failures": handoff_string_list(result.get("blocking_failures")),
        "warnings": handoff_string_list(result.get("warnings")),
        "task_summary": {
            "tasks_count": int(task_summary.get("tasks_count", 0) or 0),
            "completed_count": int(task_summary.get("completed_count", 0) or 0),
            "blocked_count": int(task_summary.get("blocked_count", 0) or 0),
            "ok": bool(task_summary.get("ok")),
        },
        "permission_summary": permission_summary if isinstance(permission_summary, dict) else {},
        "context_summary": {
            "estimated_tokens": int(context_summary.get("estimated_tokens", 0) or 0),
            "needs_compaction": bool(context_summary.get("needs_compaction")),
            "compact_summary_artifact": str(context_summary.get("compact_summary_artifact") or ""),
        },
    }


def summarize_handoffs(handoffs: list[dict[str, object]], *, agent_type: str) -> dict[str, object]:
    valid_handoffs = [handoff for handoff in handoffs if isinstance(handoff, dict)]
    from_agents = unique(
        [str(handoff.get("from_agent") or "") for handoff in valid_handoffs if handoff.get("from_agent")]
    )
    to_agents = unique(
        [str(handoff.get("to_agent") or "") for handoff in valid_handoffs if handoff.get("to_agent")]
    )
    artifacts_count = sum(int(handoff.get("artifacts_count", 0) or 0) for handoff in valid_handoffs)
    blocking_count = sum(len(handoff_string_list(handoff.get("blocking_failures"))) for handoff in valid_handoffs)
    warning_count = sum(len(handoff_string_list(handoff.get("warnings"))) for handoff in valid_handoffs)
    return {
        "schema_version": "claude_handoff_summary_v0",
        "agent_type": agent_type,
        "handoffs_count": len(valid_handoffs),
        "from_agents": from_agents,
        "to_agents": to_agents,
        "artifacts_count": artifacts_count,
        "blocking_count": blocking_count,
        "warning_count": warning_count,
        "ok": blocking_count == 0,
    }
