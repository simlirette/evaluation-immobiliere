from __future__ import annotations


CLAUDE_MESSAGE_SCHEMA_VERSION = "claude_message_envelope_v0"
CLAUDE_EVENT_SCHEMA_VERSION = "claude_runtime_event_v0"
CLAUDE_ALLOWED_MESSAGE_ROLES = {"system", "assistant", "user"}


def build_claude_message_envelope(
    *,
    role: str,
    agent_type: str,
    content: object,
    sequence: int,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    if role not in CLAUDE_ALLOWED_MESSAGE_ROLES:
        raise ValueError(f"role Claude invalide: {role}")
    if sequence < 1:
        raise ValueError("message sequence doit etre >= 1")
    return {
        "schema_version": CLAUDE_MESSAGE_SCHEMA_VERSION,
        "kind": "message",
        "message_sequence": sequence,
        "role": role,
        "agent_type": agent_type,
        "content_block_types": _content_block_types(content),
        "content": content,
        "metadata": metadata or {},
    }


def normalize_claude_message_envelope(
    message: dict[str, object],
    *,
    agent_type: str,
    sequence: int,
) -> dict[str, object]:
    if message.get("schema_version") == CLAUDE_MESSAGE_SCHEMA_VERSION:
        envelope = dict(message)
        envelope["message_sequence"] = int(envelope.get("message_sequence") or sequence)
        envelope["content_block_types"] = _content_block_types(envelope.get("content", []))
        envelope.setdefault("kind", "message")
        envelope.setdefault("agent_type", agent_type)
        envelope.setdefault("metadata", {})
        return envelope
    return build_claude_message_envelope(
        role=str(message.get("role") or "unknown"),
        agent_type=str(message.get("agent_type") or agent_type),
        content=message.get("content", []),
        sequence=sequence,
    )


def validate_claude_message_envelope(message: dict[str, object], *, expected_sequence: int | None = None) -> list[str]:
    errors: list[str] = []
    if message.get("schema_version") != CLAUDE_MESSAGE_SCHEMA_VERSION:
        errors.append("message_schema_invalid")
    if message.get("kind") != "message":
        errors.append("message_kind_invalid")
    if message.get("role") not in CLAUDE_ALLOWED_MESSAGE_ROLES:
        errors.append("message_role_invalid")
    if not message.get("agent_type"):
        errors.append("message_agent_type_missing")
    if "content" not in message:
        errors.append("message_content_missing")
    content_block_types = message.get("content_block_types")
    if not isinstance(content_block_types, list):
        errors.append("message_content_block_types_invalid")
    if expected_sequence is not None and message.get("message_sequence") != expected_sequence:
        errors.append("message_sequence_invalid")
    return errors


def build_claude_event_envelope(
    event: str,
    *,
    agent_type: str,
    sequence: int,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    if not event:
        raise ValueError("event requis")
    if sequence < 1:
        raise ValueError("event sequence doit etre >= 1")
    envelope = dict(payload or {})
    envelope["schema_version"] = CLAUDE_EVENT_SCHEMA_VERSION
    envelope["kind"] = "runtime_event"
    envelope["event_sequence"] = sequence
    envelope["event"] = event
    envelope["agent_type"] = str(envelope.get("agent_type") or agent_type)
    envelope.setdefault("metadata", {})
    return envelope


def validate_claude_event_envelope(event: dict[str, object], *, expected_sequence: int | None = None) -> list[str]:
    errors: list[str] = []
    if event.get("schema_version") != CLAUDE_EVENT_SCHEMA_VERSION:
        errors.append("event_schema_invalid")
    if event.get("kind") != "runtime_event":
        errors.append("event_kind_invalid")
    if not event.get("event"):
        errors.append("event_name_missing")
    if not event.get("agent_type"):
        errors.append("event_agent_type_missing")
    if expected_sequence is not None and event.get("event_sequence") != expected_sequence:
        errors.append("event_sequence_invalid")
    return errors


def summarize_envelope_validation(items: list[dict[str, object]], *, kind: str) -> dict[str, object]:
    errors: list[str] = []
    for expected_sequence, item in enumerate(items, start=1):
        if kind == "message":
            item_errors = validate_claude_message_envelope(item, expected_sequence=expected_sequence)
        elif kind == "runtime_event":
            item_errors = validate_claude_event_envelope(item, expected_sequence=expected_sequence)
        else:
            item_errors = [f"unsupported_kind:{kind}"]
        errors.extend(f"{error}:{expected_sequence}" for error in item_errors)
    return {
        "schema_version": "claude_envelope_validation_v0",
        "kind": kind,
        "items_count": len(items),
        "errors": sorted(set(errors)),
        "errors_count": len(set(errors)),
        "ok": not errors,
    }


def _content_block_types(content: object) -> list[str]:
    blocks = [content] if isinstance(content, dict) else content if isinstance(content, list) else []
    block_types: list[str] = []
    for block in blocks:
        if isinstance(block, dict) and block.get("type"):
            block_types.append(str(block.get("type")))
        elif isinstance(block, str):
            block_types.append("text")
    return block_types
