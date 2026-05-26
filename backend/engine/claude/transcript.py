from __future__ import annotations

from pathlib import Path
import json

from engine.claude.envelopes import (
    CLAUDE_MESSAGE_SCHEMA_VERSION,
    normalize_claude_message_envelope,
    validate_claude_message_envelope,
)


def build_claude_transcript_entries(
    messages: list[dict[str, object]],
    *,
    agent_type: str,
    session_id: str = "",
    run_id: str = "",
) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for sequence, message in enumerate(messages, start=1):
        envelope = normalize_claude_message_envelope(message, agent_type=agent_type, sequence=sequence)
        content = envelope.get("content", [])
        block_types = envelope.get("content_block_types", [])
        entries.append(
            {
                "schema_version": "claude_transcript_entry_v0",
                "kind": "message",
                "sequence": sequence,
                "session_id": session_id,
                "run_id": run_id,
                "agent_type": str(envelope.get("agent_type") or agent_type),
                "role": str(envelope.get("role") or "unknown"),
                "message_schema_version": str(envelope.get("schema_version") or ""),
                "message_sequence": int(envelope.get("message_sequence") or sequence),
                "block_types": block_types,
                "content": content,
            }
        )
    return entries


def summarize_claude_transcript_entries(
    entries: list[dict[str, object]],
    *,
    agent_type: str,
    path: str = "",
) -> dict[str, object]:
    valid_entries = [entry for entry in entries if isinstance(entry, dict)]
    roles: dict[str, int] = {}
    agents: list[str] = []
    tool_use_count = 0
    tool_result_count = 0
    handoff_messages_count = 0
    for entry in valid_entries:
        role = str(entry.get("role") or "unknown")
        roles[role] = roles.get(role, 0) + 1
        agent = str(entry.get("agent_type") or "")
        if agent and agent not in agents:
            agents.append(agent)
        block_types = entry.get("block_types", [])
        if isinstance(block_types, list):
            tool_use_count += sum(1 for block_type in block_types if block_type == "tool_use")
            tool_result_count += sum(1 for block_type in block_types if block_type == "tool_result")
            handoff_messages_count += sum(1 for block_type in block_types if block_type == "handoff")
    validation = validate_claude_transcript_entries(valid_entries, agent_type=agent_type)
    return {
        "schema_version": "claude_transcript_summary_v0",
        "agent_type": agent_type,
        "path": path,
        "entries_count": len(valid_entries),
        "messages_count": len(valid_entries),
        "agents": agents,
        "agents_count": len(agents),
        "roles": roles,
        "tool_use_count": tool_use_count,
        "tool_result_count": tool_result_count,
        "handoff_messages_count": handoff_messages_count,
        "validation": validation,
        "ok": bool(valid_entries) and validation["ok"],
    }


def write_claude_transcript(
    path: Path,
    messages: list[dict[str, object]],
    *,
    agent_type: str,
    session_id: str = "",
    run_id: str = "",
) -> dict[str, object]:
    entries = build_claude_transcript_entries(
        messages,
        agent_type=agent_type,
        session_id=session_id,
        run_id=run_id,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries),
        encoding="utf-8",
    )
    return summarize_claude_transcript_entries(entries, agent_type=agent_type, path=path.as_posix())


def validate_claude_transcript_entries(
    entries: list[dict[str, object]],
    *,
    agent_type: str,
    session_id: str = "",
    run_id: str = "",
) -> dict[str, object]:
    errors: list[str] = []
    if not entries:
        errors.append("transcript_empty")

    for expected_sequence, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"entry_invalid:{expected_sequence}")
            continue
        for field_name in ("schema_version", "kind", "sequence", "agent_type", "role", "message_schema_version", "message_sequence"):
            if not entry.get(field_name):
                errors.append(f"missing_{field_name}:{expected_sequence}")
        if entry.get("schema_version") != "claude_transcript_entry_v0":
            errors.append(f"schema_invalid:{expected_sequence}")
        if entry.get("kind") != "message":
            errors.append(f"kind_invalid:{expected_sequence}")
        if entry.get("sequence") != expected_sequence:
            errors.append(f"sequence_invalid:{expected_sequence}")
        if entry.get("message_schema_version") != CLAUDE_MESSAGE_SCHEMA_VERSION:
            errors.append(f"message_schema_invalid:{expected_sequence}")
        if entry.get("message_sequence") != expected_sequence:
            errors.append(f"message_sequence_invalid:{expected_sequence}")
        if agent_type != "claude-pipeline" and entry.get("agent_type") != agent_type:
            errors.append(f"agent_type_mismatch:{expected_sequence}")
        if session_id and entry.get("session_id") != session_id:
            errors.append(f"session_id_mismatch:{expected_sequence}")
        if run_id and entry.get("run_id") != run_id:
            errors.append(f"run_id_mismatch:{expected_sequence}")
        block_types = entry.get("block_types")
        if not isinstance(block_types, list):
            errors.append(f"block_types_invalid:{expected_sequence}")
        message_errors = validate_claude_message_envelope(
            {
                "schema_version": entry.get("message_schema_version"),
                "kind": "message",
                "message_sequence": entry.get("message_sequence"),
                "role": entry.get("role"),
                "agent_type": entry.get("agent_type"),
                "content_block_types": block_types,
                "content": entry.get("content", []),
            },
            expected_sequence=expected_sequence,
        )
        errors.extend(f"{error}:{expected_sequence}" for error in message_errors)

    unique_errors = sorted(set(errors))
    return {
        "schema_version": "claude_transcript_validation_v0",
        "agent_type": agent_type,
        "entries_count": len(entries),
        "errors_count": len(unique_errors),
        "errors": unique_errors,
        "ok": not unique_errors,
    }
