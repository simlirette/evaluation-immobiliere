from __future__ import annotations

import json


def build_context_state(
    messages: list[dict[str, object]],
    *,
    agent_type: str,
    threshold_tokens: int | None,
    preserve_recent_tool_results: int = 3,
) -> dict[str, object]:
    tool_result_ids = _tool_result_ids(messages)
    preserved_count = max(0, preserve_recent_tool_results)
    preserved_ids = tool_result_ids[-preserved_count:] if preserved_count else []
    estimated_tokens = estimate_message_tokens(messages)
    needs_compaction = threshold_tokens is not None and threshold_tokens > 0 and estimated_tokens > threshold_tokens
    return {
        "schema_version": "claude_context_state_v0",
        "agent_type": agent_type,
        "messages_count": len(messages),
        "estimated_tokens": estimated_tokens,
        "threshold_tokens": threshold_tokens,
        "needs_compaction": needs_compaction,
        "tool_results_count": len(tool_result_ids),
        "preserve_recent_tool_results": preserved_count,
        "preserved_tool_result_ids": preserved_ids if needs_compaction else tool_result_ids,
        "dropped_tool_result_ids": tool_result_ids[:-preserved_count] if needs_compaction and preserved_count else ([] if not needs_compaction else tool_result_ids),
        "compact_summary_artifact": "",
    }


def build_context_compact_summary(
    messages: list[dict[str, object]],
    context_state: dict[str, object],
    *,
    agent_type: str,
) -> dict[str, object]:
    role_counts: dict[str, int] = {}
    for message in messages:
        role = str(message.get("role") or "unknown")
        role_counts[role] = role_counts.get(role, 0) + 1
    return {
        "schema_version": "claude_context_compact_summary_v0",
        "agent_type": agent_type,
        "reason": "estimated_context_tokens_exceeded",
        "estimated_tokens": context_state["estimated_tokens"],
        "threshold_tokens": context_state["threshold_tokens"],
        "messages_before_compaction": len(messages),
        "role_counts": role_counts,
        "preserved_tool_result_ids": context_state["preserved_tool_result_ids"],
        "dropped_tool_result_ids": context_state["dropped_tool_result_ids"],
        "continuation_context": [
            "Conserver les messages systeme et le contrat runtime agent.",
            "Conserver les resultats d'outils recents listes dans preserved_tool_result_ids.",
            "Remplacer les resultats d'outils plus anciens par ce resume structure.",
        ],
    }


def estimate_message_tokens(messages: list[dict[str, object]]) -> int:
    encoded = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    return max(1, (len(encoded) + 3) // 4)


def _tool_result_ids(messages: list[dict[str, object]]) -> list[str]:
    ids: list[str] = []
    for message in messages:
        content = message.get("content", [])
        blocks = [content] if isinstance(content, dict) else content if isinstance(content, list) else []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                ids.append(str(block.get("tool_use_id") or ""))
    return ids
