from __future__ import annotations

from engine.claude.exceptions import ToolResultPairingError


def summarize_claude_messages(
    messages: list[dict[str, object]],
    *,
    agent_type: str,
    strict_tool_result_pairing: bool = True,
) -> dict[str, object]:
    pending_tool_uses: list[str] = []
    orphan_tool_results: list[str] = []
    duplicate_tool_uses: list[str] = []
    seen_tool_uses: set[str] = set()
    tool_use_count = 0
    tool_result_count = 0
    system_messages_count = 0

    for message in messages:
        if message.get("role") == "system":
            system_messages_count += 1
        content = message.get("content", [])
        if isinstance(content, dict):
            blocks = [content]
        elif isinstance(content, list):
            blocks = content
        else:
            blocks = []

        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "tool_use":
                tool_use_id = str(block.get("id") or "")
                tool_use_count += 1
                if tool_use_id in seen_tool_uses:
                    duplicate_tool_uses.append(tool_use_id)
                else:
                    seen_tool_uses.add(tool_use_id)
                    pending_tool_uses.append(tool_use_id)
            if block_type == "tool_result":
                tool_result_id = str(block.get("tool_use_id") or "")
                tool_result_count += 1
                if tool_result_id in pending_tool_uses:
                    pending_tool_uses.remove(tool_result_id)
                else:
                    orphan_tool_results.append(tool_result_id)

    ok = not pending_tool_uses and not orphan_tool_results and not duplicate_tool_uses
    state = {
        "schema_version": "claude_conversation_state_v0",
        "agent_type": agent_type,
        "messages_count": len(messages),
        "system_messages_count": system_messages_count,
        "tool_use_count": tool_use_count,
        "tool_result_count": tool_result_count,
        "pending_tool_use_ids": pending_tool_uses,
        "orphan_tool_result_ids": orphan_tool_results,
        "duplicate_tool_use_ids": duplicate_tool_uses,
        "strict_tool_result_pairing": strict_tool_result_pairing,
        "ok": ok,
    }
    if strict_tool_result_pairing and not ok:
        raise ToolResultPairingError(
            f"tool_use/tool_result pairing invalide pour {agent_type}: "
            f"pending={pending_tool_uses}, orphan={orphan_tool_results}, duplicate={duplicate_tool_uses}"
        )
    return state
