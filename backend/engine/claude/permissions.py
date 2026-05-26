from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path

from engine.claude.types import ClaudeToolCall, ToolSpec


CLAUDE_PERMISSION_STATE_SCHEMA_VERSION = "claude_permission_state_v0"
CLAUDE_PERMISSION_REPLAY_SCHEMA_VERSION = "claude_permission_replay_v0"
PERMISSION_RULE_SOURCES = {
    "userSettings",
    "projectSettings",
    "localSettings",
    "flagSettings",
    "policySettings",
    "cliArg",
    "command",
    "session",
}
PERMISSION_UPDATE_DESTINATIONS = {
    "userSettings",
    "projectSettings",
    "localSettings",
    "cliArg",
    "session",
}
PERMISSION_BEHAVIORS = {"allow", "deny", "ask"}
RULE_BUCKET_BY_BEHAVIOR = {
    "allow": "alwaysAllowRules",
    "deny": "alwaysDenyRules",
    "ask": "alwaysAskRules",
}


@dataclass(frozen=True)
class ClaudePermissionDecision:
    tool_call_id: str
    tool: str
    agent_type: str
    permission: str
    mode: str
    allowed: bool
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "claude_permission_decision_v0",
            "tool_call_id": self.tool_call_id,
            "tool": self.tool,
            "agent_type": self.agent_type,
            "permission": self.permission,
            "mode": self.mode,
            "allowed": self.allowed,
            "reason": self.reason,
        }


class ClaudePermissionPolicy:
    DEFAULT = "default"
    PLAN = "plan"
    BYPASS = "bypass"
    MODES = {DEFAULT, PLAN, BYPASS}
    PLAN_DENIED_PERMISSIONS = {"runtime_write", "runtime_execute"}

    def __init__(
        self,
        allowed_tools: list[str],
        *,
        mode: str = DEFAULT,
        tool_registry: dict[str, ToolSpec] | None = None,
        permission_state: dict[str, object] | None = None,
    ) -> None:
        if mode not in self.MODES:
            raise ValueError(f"permission_mode invalide: {mode}")
        if tool_registry is None:
            from engine.claude.tools import TOOL_REGISTRY

            tool_registry = TOOL_REGISTRY
        self.allowed_tools = set(allowed_tools)
        self.mode = mode
        self.tool_registry = tool_registry
        self.permission_state = normalize_permission_state(
            permission_state,
            agent_type="",
            mode=mode,
            allowed_tools=allowed_tools,
        ) if permission_state else None

    def decide(self, call: ClaudeToolCall) -> ClaudePermissionDecision:
        spec = self.tool_registry.get(call.name)
        if spec is None:
            return self._decision(call, "unknown", False, "unknown_tool")

        if self.mode == self.BYPASS:
            return self._decision(call, spec.permission, True, "bypass_permissions")

        if call.name not in self.allowed_tools:
            return self._decision(call, spec.permission, False, "tool_not_allowed_for_agent")

        state_behavior = permission_state_behavior_for_call(self.permission_state, call)
        if state_behavior == "deny":
            return self._decision(call, spec.permission, False, "permission_state_deny_rule")
        if state_behavior == "ask":
            return self._decision(call, spec.permission, False, "permission_state_ask_rule")
        if state_behavior == "allow":
            return self._decision(call, spec.permission, True, "permission_state_allow_rule")

        if self.mode == self.PLAN and spec.permission in self.PLAN_DENIED_PERMISSIONS:
            return self._decision(call, spec.permission, False, "plan_mode_requires_approval")

        return self._decision(call, spec.permission, True, "configured_tool_allowed")

    def _decision(
        self,
        call: ClaudeToolCall,
        permission: str,
        allowed: bool,
        reason: str,
    ) -> ClaudePermissionDecision:
        return ClaudePermissionDecision(
            tool_call_id=call.id,
            tool=call.name,
            agent_type=call.agent_type,
            permission=permission,
            mode=self.mode,
            allowed=allowed,
            reason=reason,
        )


def permission_rule_value_to_string(rule: dict[str, object] | str) -> str:
    if isinstance(rule, str):
        return rule.strip()
    tool_name = str(rule.get("toolName") or rule.get("tool") or "").strip()
    rule_content = str(rule.get("ruleContent") or "").strip()
    return f"{tool_name}({rule_content})" if rule_content else tool_name


def permission_rule_value_from_string(value: str) -> dict[str, object]:
    text = value.strip()
    if "(" in text and text.endswith(")"):
        tool_name, rule_content = text[:-1].split("(", 1)
        return {"toolName": tool_name.strip(), "ruleContent": rule_content.strip()}
    return {"toolName": text}


def build_empty_permission_state(
    *,
    agent_type: str,
    mode: str = ClaudePermissionPolicy.DEFAULT,
    allowed_tools: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": CLAUDE_PERMISSION_STATE_SCHEMA_VERSION,
        "agent_type": agent_type,
        "mode": mode,
        "allowed_tools": list(allowed_tools or []),
        "alwaysAllowRules": {"session": []},
        "alwaysDenyRules": {"session": []},
        "alwaysAskRules": {"session": []},
        "additionalWorkingDirectories": [],
        "updates": [],
        "source": "claude_code_permission_context_adapted_v0",
        "ok": True,
    }


def build_permission_state_from_settings_context(
    settings_context: dict[str, object],
    *,
    agent_type: str,
    mode: str = ClaudePermissionPolicy.DEFAULT,
    allowed_tools: list[str] | None = None,
) -> dict[str, object]:
    state = build_empty_permission_state(
        agent_type=agent_type,
        mode=mode,
        allowed_tools=allowed_tools,
    )
    sources = settings_context.get("sources", []) if isinstance(settings_context, dict) else []
    if not isinstance(sources, list):
        sources = []

    for source_record in sources:
        if not isinstance(source_record, dict):
            continue
        source_name = str(source_record.get("source") or "session")
        if source_name not in PERMISSION_RULE_SOURCES:
            source_name = "session"
        settings = source_record.get("settings", {})
        if not isinstance(settings, dict):
            continue
        permissions = settings.get("permissions", {})
        if not isinstance(permissions, dict):
            continue

        for behavior, bucket in RULE_BUCKET_BY_BEHAVIOR.items():
            rules = _permission_setting_rules(permissions.get(behavior))
            if not rules:
                continue
            rules_by_source = _normalize_rules_by_source(state.get(bucket))
            rules_by_source[source_name] = _unique_strings([*rules_by_source.get(source_name, []), *rules])
            state[bucket] = rules_by_source

        directories = _unique_strings(
            permissions.get("additionalDirectories")
            or permissions.get("additional_directories")
            or []
        )
        if directories:
            existing = _normalize_working_directories(state.get("additionalWorkingDirectories"))
            by_path = {str(item["path"]): dict(item) for item in existing}
            for directory in directories:
                by_path[directory] = {"path": directory, "source": source_name}
            state["additionalWorkingDirectories"] = list(by_path.values())

    state["source"] = "claude_code_settings_context_adapted_v0"
    return normalize_permission_state(
        state,
        agent_type=agent_type,
        mode=mode,
        allowed_tools=allowed_tools,
    )


def normalize_permission_state(
    state: dict[str, object] | None,
    *,
    agent_type: str,
    mode: str = ClaudePermissionPolicy.DEFAULT,
    allowed_tools: list[str] | None = None,
) -> dict[str, object]:
    base = build_empty_permission_state(agent_type=agent_type, mode=mode, allowed_tools=allowed_tools)
    if not isinstance(state, dict):
        return base
    normalized = dict(base)
    normalized.update(state)
    normalized["schema_version"] = CLAUDE_PERMISSION_STATE_SCHEMA_VERSION
    normalized["agent_type"] = str(normalized.get("agent_type") or agent_type)
    normalized["mode"] = str(normalized.get("mode") or mode)
    normalized["allowed_tools"] = _unique_strings(normalized.get("allowed_tools") or allowed_tools or [])
    for bucket in RULE_BUCKET_BY_BEHAVIOR.values():
        normalized[bucket] = _normalize_rules_by_source(normalized.get(bucket))
    normalized["additionalWorkingDirectories"] = _normalize_working_directories(
        normalized.get("additionalWorkingDirectories")
    )
    updates = normalized.get("updates", [])
    normalized["updates"] = [update for update in updates if isinstance(update, dict)] if isinstance(updates, list) else []
    normalized["ok"] = not validate_permission_state(normalized)
    return normalized


def validate_permission_state(state: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != CLAUDE_PERMISSION_STATE_SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if str(state.get("mode") or "") not in ClaudePermissionPolicy.MODES:
        errors.append("mode_invalid")
    allowed_tools = state.get("allowed_tools", [])
    if not isinstance(allowed_tools, list) or not all(isinstance(tool, str) for tool in allowed_tools):
        errors.append("allowed_tools_invalid")
    for bucket in RULE_BUCKET_BY_BEHAVIOR.values():
        rules_by_source = state.get(bucket, {})
        if not isinstance(rules_by_source, dict):
            errors.append(f"{bucket}_invalid")
            continue
        for source, rules in rules_by_source.items():
            if source not in PERMISSION_RULE_SOURCES:
                errors.append(f"{bucket}_source_invalid:{source}")
            if not isinstance(rules, list) or not all(isinstance(rule, str) and rule.strip() for rule in rules):
                errors.append(f"{bucket}_rules_invalid:{source}")
    directories = state.get("additionalWorkingDirectories", [])
    if not isinstance(directories, list):
        errors.append("additional_working_directories_invalid")
    else:
        for index, directory in enumerate(directories):
            if not isinstance(directory, dict) or not directory.get("path"):
                errors.append(f"additional_working_directory_invalid:{index}")
    updates = state.get("updates", [])
    if not isinstance(updates, list):
        errors.append("updates_invalid")
    else:
        for index, update in enumerate(updates):
            errors.extend(f"update_{index}:{error}" for error in validate_permission_update(update))
    return errors


def validate_permission_update(update: object) -> list[str]:
    if not isinstance(update, dict):
        return ["update_not_object"]
    update_type = str(update.get("type") or "")
    destination = str(update.get("destination") or "")
    errors: list[str] = []
    if update_type not in {"addRules", "replaceRules", "removeRules", "setMode", "addDirectories", "removeDirectories"}:
        errors.append("type_invalid")
    if destination not in PERMISSION_UPDATE_DESTINATIONS:
        errors.append("destination_invalid")
    if update_type in {"addRules", "replaceRules", "removeRules"}:
        behavior = str(update.get("behavior") or "")
        rules = update.get("rules")
        if behavior not in PERMISSION_BEHAVIORS:
            errors.append("behavior_invalid")
        if not isinstance(rules, list):
            errors.append("rules_invalid")
        else:
            for index, rule in enumerate(rules):
                rule_text = permission_rule_value_to_string(rule)
                if not rule_text:
                    errors.append(f"rule_invalid:{index}")
    if update_type == "setMode" and str(update.get("mode") or "") not in ClaudePermissionPolicy.MODES:
        errors.append("mode_invalid")
    if update_type in {"addDirectories", "removeDirectories"}:
        directories = update.get("directories")
        if not isinstance(directories, list) or not all(isinstance(path, str) and path for path in directories):
            errors.append("directories_invalid")
    return errors


def apply_permission_update(state: dict[str, object], update: dict[str, object]) -> dict[str, object]:
    errors = validate_permission_update(update)
    if errors:
        raise ValueError(f"permission_update invalide: {errors}")

    next_state = normalize_permission_state(
        state,
        agent_type=str(state.get("agent_type") or ""),
        mode=str(state.get("mode") or ClaudePermissionPolicy.DEFAULT),
        allowed_tools=_unique_strings(state.get("allowed_tools", [])),
    )
    update_type = str(update["type"])
    destination = str(update["destination"])

    if update_type == "setMode":
        next_state["mode"] = str(update["mode"])
    elif update_type in {"addRules", "replaceRules", "removeRules"}:
        behavior = str(update["behavior"])
        bucket = RULE_BUCKET_BY_BEHAVIOR[behavior]
        rules_by_source = _normalize_rules_by_source(next_state.get(bucket))
        rule_strings = [permission_rule_value_to_string(rule) for rule in update.get("rules", [])]
        existing = list(rules_by_source.get(destination, []))
        if update_type == "addRules":
            rules_by_source[destination] = _unique_strings([*existing, *rule_strings])
        elif update_type == "replaceRules":
            rules_by_source[destination] = _unique_strings(rule_strings)
        elif update_type == "removeRules":
            remove = set(rule_strings)
            rules_by_source[destination] = [rule for rule in existing if rule not in remove]
        next_state[bucket] = rules_by_source
    elif update_type == "addDirectories":
        directories = _normalize_working_directories(next_state.get("additionalWorkingDirectories"))
        by_path = {str(item["path"]): dict(item) for item in directories}
        for path in update.get("directories", []):
            by_path[str(path)] = {"path": str(path), "source": destination}
        next_state["additionalWorkingDirectories"] = list(by_path.values())
    elif update_type == "removeDirectories":
        remove = {str(path) for path in update.get("directories", [])}
        next_state["additionalWorkingDirectories"] = [
            item
            for item in _normalize_working_directories(next_state.get("additionalWorkingDirectories"))
            if str(item.get("path") or "") not in remove
        ]

    updates = list(next_state.get("updates", [])) if isinstance(next_state.get("updates"), list) else []
    recorded_update = dict(update)
    recorded_update["sequence"] = len(updates) + 1
    updates.append(recorded_update)
    next_state["updates"] = updates
    next_state["ok"] = not validate_permission_state(next_state)
    return next_state


def apply_permission_updates(
    state: dict[str, object],
    updates: list[dict[str, object]],
) -> dict[str, object]:
    next_state = state
    for update in updates:
        next_state = apply_permission_update(next_state, update)
    return next_state


def build_permission_updates_from_decisions(
    decisions: list[dict[str, object]],
    *,
    destination: str = "session",
) -> list[dict[str, object]]:
    rules_by_behavior: dict[str, list[dict[str, object]]] = {"allow": [], "deny": []}
    seen: set[tuple[str, str]] = set()
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        tool_name = str(decision.get("tool") or "").strip()
        if not tool_name:
            continue
        behavior = "allow" if decision.get("allowed") is True else "deny"
        key = (behavior, tool_name)
        if key in seen:
            continue
        seen.add(key)
        rules_by_behavior[behavior].append({"toolName": tool_name})

    updates: list[dict[str, object]] = []
    for behavior in ("allow", "deny"):
        rules = rules_by_behavior[behavior]
        if rules:
            updates.append(
                {
                    "type": "addRules",
                    "destination": destination,
                    "behavior": behavior,
                    "rules": rules,
                }
            )
    return updates


def build_permission_state_from_decisions(
    decisions: list[dict[str, object]],
    *,
    agent_type: str,
    mode: str = ClaudePermissionPolicy.DEFAULT,
    allowed_tools: list[str] | None = None,
    base_state: dict[str, object] | None = None,
) -> dict[str, object]:
    tools = allowed_tools or _unique_strings(decision.get("tool", "") for decision in decisions if isinstance(decision, dict))
    state = normalize_permission_state(
        base_state,
        agent_type=agent_type,
        mode=mode,
        allowed_tools=list(tools),
    )
    state = apply_permission_updates(state, build_permission_updates_from_decisions(decisions))
    state["agent_type"] = agent_type
    state["mode"] = mode
    state["allowed_tools"] = list(tools)
    state["decisions_count"] = len([decision for decision in decisions if isinstance(decision, dict)])
    state["summary"] = summarize_permission_state(state)
    return state


def summarize_permission_state(state: dict[str, object]) -> dict[str, object]:
    normalized = normalize_permission_state(
        state,
        agent_type=str(state.get("agent_type") or ""),
        mode=str(state.get("mode") or ClaudePermissionPolicy.DEFAULT),
        allowed_tools=_unique_strings(state.get("allowed_tools", [])),
    )
    allow_rules = permission_state_rule_strings(normalized, "allow")
    deny_rules = permission_state_rule_strings(normalized, "deny")
    ask_rules = permission_state_rule_strings(normalized, "ask")
    errors = validate_permission_state(normalized)
    return {
        "schema_version": "claude_permission_state_summary_v0",
        "agent_type": normalized.get("agent_type", ""),
        "mode": normalized.get("mode", ""),
        "allowed_tools_count": len(normalized.get("allowed_tools", [])),
        "allow_rules_count": len(allow_rules),
        "deny_rules_count": len(deny_rules),
        "ask_rules_count": len(ask_rules),
        "additional_working_directories_count": len(normalized.get("additionalWorkingDirectories", [])),
        "updates_count": len(normalized.get("updates", [])),
        "errors": errors,
        "ok": not errors,
    }


def permission_state_rule_strings(state: dict[str, object] | None, behavior: str) -> list[str]:
    if not isinstance(state, dict):
        return []
    bucket = RULE_BUCKET_BY_BEHAVIOR.get(behavior)
    if not bucket:
        return []
    rules_by_source = _normalize_rules_by_source(state.get(bucket))
    return [
        rule
        for source in sorted(rules_by_source)
        for rule in rules_by_source[source]
    ]


def permission_state_behavior_for_call(
    state: dict[str, object] | None,
    call: ClaudeToolCall,
) -> str | None:
    if not isinstance(state, dict):
        return None
    for behavior in ("deny", "ask", "allow"):
        for rule in permission_state_rule_strings(state, behavior):
            if permission_rule_matches_tool_call(rule, call):
                return behavior
    return None


def permission_rule_matches_tool_call(rule: str, call: ClaudeToolCall) -> bool:
    parsed = permission_rule_value_from_string(rule)
    tool_name = str(parsed.get("toolName") or "")
    if tool_name != call.name:
        return False
    rule_content = str(parsed.get("ruleContent") or "")
    if not rule_content or rule_content == "*":
        return True
    candidates = [
        str(call.input.get("path") or ""),
        str(call.input.get("command") or ""),
        str(call.input.get("source_id") or ""),
    ]
    return any(candidate and fnmatch.fnmatch(candidate, rule_content) for candidate in candidates)


def replay_permission_decisions(
    permission_state: dict[str, object],
    decisions: list[dict[str, object]],
    *,
    allowed_tools: list[str] | None = None,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> dict[str, object]:
    if tool_registry is None:
        from engine.claude.tools import TOOL_REGISTRY

        tool_registry = TOOL_REGISTRY
    normalized = normalize_permission_state(
        permission_state,
        agent_type=str(permission_state.get("agent_type") or ""),
        mode=str(permission_state.get("mode") or ClaudePermissionPolicy.DEFAULT),
        allowed_tools=allowed_tools or _unique_strings(permission_state.get("allowed_tools", [])),
    )
    policy = ClaudePermissionPolicy(
        allowed_tools or _unique_strings(normalized.get("allowed_tools", [])),
        mode=str(normalized.get("mode") or ClaudePermissionPolicy.DEFAULT),
        tool_registry=tool_registry,
        permission_state=normalized,
    )
    replayed: list[dict[str, object]] = []
    mismatches: list[str] = []
    source_decisions = [decision for decision in decisions if isinstance(decision, dict)]
    for decision in source_decisions:
        call = ClaudeToolCall(
            id=str(decision.get("tool_call_id") or ""),
            name=str(decision.get("tool") or ""),
            input={},
            agent_type=str(decision.get("agent_type") or normalized.get("agent_type") or ""),
        )
        replayed_decision = policy.decide(call).as_dict()
        replayed.append(replayed_decision)
        for field in ("tool", "agent_type", "permission", "allowed"):
            if decision.get(field) != replayed_decision.get(field):
                mismatches.append(f"{call.id}:{field}_mismatch")
    return {
        "schema_version": CLAUDE_PERMISSION_REPLAY_SCHEMA_VERSION,
        "agent_type": normalized.get("agent_type", ""),
        "decisions_count": len(source_decisions),
        "replayed_count": len(replayed),
        "matched_count": len(source_decisions) - len(set(mismatches)),
        "mismatches": sorted(set(mismatches)),
        "ok": not mismatches and len(replayed) == len(source_decisions),
    }


def write_permission_state(path: Path, state: dict[str, object]) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = normalize_permission_state(
        state,
        agent_type=str(state.get("agent_type") or ""),
        mode=str(state.get("mode") or ClaudePermissionPolicy.DEFAULT),
        allowed_tools=_unique_strings(state.get("allowed_tools", [])),
    )
    payload["summary"] = summarize_permission_state(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def load_permission_state(path: Path) -> dict[str, object]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def summarize_permission_decisions(
    decisions: list[dict[str, object]],
    *,
    agent_type: str,
) -> dict[str, object]:
    allowed_count = sum(1 for decision in decisions if decision.get("allowed") is True)
    denied_count = sum(1 for decision in decisions if decision.get("allowed") is False)
    modes = sorted({str(decision.get("mode") or "") for decision in decisions if decision.get("mode")})
    denied_tools = [
        str(decision.get("tool") or "")
        for decision in decisions
        if decision.get("allowed") is False
    ]
    return {
        "schema_version": "claude_permission_summary_v0",
        "agent_type": agent_type,
        "decisions_count": len(decisions),
        "allowed_count": allowed_count,
        "denied_count": denied_count,
        "modes": modes,
        "denied_tools": denied_tools,
        "ok": denied_count == 0,
    }


def _normalize_rules_by_source(value: object) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {"session": []}
    normalized: dict[str, list[str]] = {}
    for source, rules in value.items():
        if not isinstance(source, str):
            continue
        if isinstance(rules, list):
            normalized[source] = _unique_strings(permission_rule_value_to_string(rule) for rule in rules)
        elif isinstance(rules, str):
            normalized[source] = [rules]
    if "session" not in normalized:
        normalized["session"] = []
    return normalized


def _normalize_working_directories(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        if isinstance(item, str):
            path = item
            source = "session"
        elif isinstance(item, dict):
            path = str(item.get("path") or "")
            source = str(item.get("source") or "session")
        else:
            continue
        if not path or path in seen:
            continue
        seen.add(path)
        normalized.append({"path": path, "source": source})
    return normalized


def _permission_setting_rules(value: object) -> list[str]:
    if isinstance(value, list):
        return _unique_strings(permission_rule_value_to_string(rule) for rule in value)
    if isinstance(value, str):
        return _unique_strings([value])
    return []


def _unique_strings(values: object) -> list[str]:
    if isinstance(values, list) or not isinstance(values, (str, bytes)):
        iterable = values if not isinstance(values, (str, bytes)) else [values]
    else:
        iterable = [values]
    seen: set[str] = set()
    result: list[str] = []
    try:
        iterator = iter(iterable)  # type: ignore[arg-type]
    except TypeError:
        iterator = iter([])
    for value in iterator:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
