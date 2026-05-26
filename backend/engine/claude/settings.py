from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Iterable

from engine.claude.constants import PROJECT_ROOT
from engine.claude.permissions import ClaudePermissionPolicy


CLAUDE_SETTINGS_CONTEXT_SCHEMA_VERSION = "claude_settings_context_v0"
CLAUDE_SETTINGS_VALIDATION_SCHEMA_VERSION = "claude_settings_validation_v0"

SETTING_SOURCES = [
    "defaultSettings",
    "userSettings",
    "projectSettings",
    "localSettings",
    "sessionSettings",
    "flagSettings",
    "policySettings",
]

EDITABLE_SETTING_SOURCES = {"userSettings", "projectSettings", "localSettings", "sessionSettings"}

DEFAULT_SETTINGS: dict[str, object] = {
    "runtime": {
        "strict_tool_result_pairing": True,
        "preserve_recent_tool_results": 3,
        "context_compaction_threshold_tokens": None,
    },
    "permissions": {
        "defaultMode": ClaudePermissionPolicy.DEFAULT,
    },
    "commands": {
        "include_builtin": True,
        "disabled": [],
    },
}


def load_claude_settings(
    *,
    project_root: Path | None = None,
    user_settings_path: Path | None = None,
    session_settings: dict[str, object] | None = None,
    flag_settings: dict[str, object] | None = None,
    policy_settings: dict[str, object] | None = None,
    enabled_sources: Iterable[str] | None = None,
) -> dict[str, object]:
    root = project_root or PROJECT_ROOT
    enabled = set(enabled_sources or SETTING_SOURCES)
    merged: dict[str, object] = {}
    sources: list[dict[str, object]] = []
    errors: list[str] = []
    warnings: list[str] = []

    for source in SETTING_SOURCES:
        if source not in enabled:
            continue
        settings, path, exists, source_errors, source_warnings = _settings_for_source(
            source,
            project_root=root,
            user_settings_path=user_settings_path,
            session_settings=session_settings,
            flag_settings=flag_settings,
            policy_settings=policy_settings,
        )
        errors.extend(f"{source}:{error}" for error in source_errors)
        warnings.extend(f"{source}:{warning}" for warning in source_warnings)
        if settings:
            merged = merge_settings(merged, settings)
            sources.append(
                {
                    "source": source,
                    "display_name": setting_source_display_name(source),
                    "path": path.as_posix() if path else "",
                    "exists": exists,
                    "editable": source in EDITABLE_SETTING_SOURCES,
                    "keys": settings_keys(settings),
                    "settings": sanitize_settings(settings),
                }
            )

    runtime_options = runtime_options_from_settings(merged)
    errors.extend(validate_runtime_options(runtime_options))
    validation = {
        "schema_version": CLAUDE_SETTINGS_VALIDATION_SCHEMA_VERSION,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "ok": not errors,
    }
    return {
        "schema_version": CLAUDE_SETTINGS_CONTEXT_SCHEMA_VERSION,
        "source_order": list(SETTING_SOURCES),
        "enabled_sources": [source for source in SETTING_SOURCES if source in enabled],
        "active_sources": [source["source"] for source in sources],
        "sources_count": len(sources),
        "sources": sources,
        "effective": sanitize_settings(merged),
        "effective_keys": settings_keys(merged),
        "runtime_options": runtime_options,
        "validation": validation,
        "ok": validation["ok"],
    }


def runtime_options_from_settings(settings: dict[str, object]) -> dict[str, object]:
    runtime = _as_dict(settings.get("runtime"))
    permissions = _as_dict(settings.get("permissions"))
    commands = _as_dict(settings.get("commands"))
    permission_mode = str(
        runtime.get("permission_mode")
        or runtime.get("permissionMode")
        or permissions.get("defaultMode")
        or ClaudePermissionPolicy.DEFAULT
    )
    preserve_recent = _optional_int(
        runtime.get("preserve_recent_tool_results", runtime.get("preserveRecentToolResults")),
        default=3,
    )
    compaction_threshold = _optional_int(
        runtime.get("context_compaction_threshold_tokens", runtime.get("contextCompactionThresholdTokens")),
        default=None,
    )
    return {
        "schema_version": "claude_runtime_settings_v0",
        "strict_tool_result_pairing": _optional_bool(
            runtime.get("strict_tool_result_pairing", runtime.get("strictToolResultPairing")),
            default=True,
        ),
        "preserve_recent_tool_results": preserve_recent,
        "context_compaction_threshold_tokens": compaction_threshold,
        "permission_mode": permission_mode,
        "include_builtin_commands": _optional_bool(
            commands.get("include_builtin", commands.get("includeBuiltin")),
            default=True,
        ),
        "disabled_commands": _as_list(commands.get("disabled")),
        "enabled_commands": _as_list(commands.get("enabled")),
        "additional_directories": _as_list(
            permissions.get("additionalDirectories", permissions.get("additional_directories"))
        ),
        "env_keys": sorted(str(key) for key in _as_dict(settings.get("env")).keys()),
    }


def merge_settings(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    result = deepcopy(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            result[key] = merge_settings(existing, value)
            continue
        if isinstance(existing, list) and isinstance(value, list):
            result[key] = _unique([*existing, *value])
            continue
        result[key] = deepcopy(value)
    return result


def validate_settings_context(context: dict[str, object]) -> dict[str, object]:
    validation = context.get("validation", {}) if isinstance(context, dict) else {}
    errors = validation.get("errors", []) if isinstance(validation, dict) else ["settings_context_invalid"]
    if not isinstance(errors, list):
        errors = ["settings_context_invalid"]
    if isinstance(context, dict) and context.get("ok") is False:
        errors = [*errors, "settings_context_not_ok"]
    unique_errors = sorted({str(error) for error in errors if str(error)})
    return {
        "schema_version": CLAUDE_SETTINGS_VALIDATION_SCHEMA_VERSION,
        "errors": unique_errors,
        "ok": not unique_errors and bool(context.get("ok", False)) if isinstance(context, dict) else False,
    }


def validate_runtime_options(options: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if options.get("permission_mode") not in ClaudePermissionPolicy.MODES:
        errors.append(f"permission_mode_invalid:{options.get('permission_mode')}")
    preserve_recent = options.get("preserve_recent_tool_results")
    if not isinstance(preserve_recent, int) or preserve_recent < 0:
        errors.append("preserve_recent_tool_results_invalid")
    threshold = options.get("context_compaction_threshold_tokens")
    if threshold is not None and (not isinstance(threshold, int) or threshold < 0):
        errors.append("context_compaction_threshold_tokens_invalid")
    if not isinstance(options.get("strict_tool_result_pairing"), bool):
        errors.append("strict_tool_result_pairing_invalid")
    if not isinstance(options.get("include_builtin_commands"), bool):
        errors.append("include_builtin_commands_invalid")
    return errors


def settings_keys(settings: dict[str, object]) -> list[str]:
    keys: list[str] = []
    for key, value in settings.items():
        if isinstance(value, dict):
            for nested_key in sorted(value):
                keys.append(f"{key}.{nested_key}")
        else:
            keys.append(str(key))
    return sorted(keys)


def sanitize_settings(settings: dict[str, object]) -> dict[str, object]:
    sanitized = deepcopy(settings)
    env = sanitized.get("env")
    if isinstance(env, dict):
        sanitized["env"] = {str(key): "<redacted>" for key in env}
    return sanitized


def setting_source_display_name(source: str) -> str:
    return {
        "defaultSettings": "Defaults",
        "userSettings": "User settings",
        "projectSettings": "Shared project settings",
        "localSettings": "Project local settings",
        "sessionSettings": "Current session",
        "flagSettings": "Command line settings",
        "policySettings": "Managed settings",
    }.get(source, source)


def settings_path_for_source(
    source: str,
    *,
    project_root: Path,
    user_settings_path: Path | None = None,
) -> Path | None:
    if source == "userSettings":
        return user_settings_path
    if source == "projectSettings":
        return project_root / ".claude" / "settings.json"
    if source == "localSettings":
        return project_root / ".claude" / "settings.local.json"
    if source == "flagSettings":
        return project_root / ".claude" / "settings.flag.json"
    if source == "policySettings":
        return project_root / ".claude" / "managed-settings.json"
    return None


def _settings_for_source(
    source: str,
    *,
    project_root: Path,
    user_settings_path: Path | None,
    session_settings: dict[str, object] | None,
    flag_settings: dict[str, object] | None,
    policy_settings: dict[str, object] | None,
) -> tuple[dict[str, object], Path | None, bool, list[str], list[str]]:
    if source == "defaultSettings":
        return deepcopy(DEFAULT_SETTINGS), None, True, [], []
    if source == "sessionSettings":
        settings = session_settings if isinstance(session_settings, dict) else {}
        return dict(settings), None, bool(settings), validate_settings_fragment(settings), _unknown_key_warnings(settings)
    if source == "flagSettings" and flag_settings:
        return dict(flag_settings), None, True, validate_settings_fragment(flag_settings), _unknown_key_warnings(flag_settings)
    if source == "policySettings" and policy_settings:
        return dict(policy_settings), None, True, validate_settings_fragment(policy_settings), _unknown_key_warnings(policy_settings)

    path = settings_path_for_source(source, project_root=project_root, user_settings_path=user_settings_path)
    if not path or not path.exists():
        return {}, path, False, [], []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, path, True, [f"json_invalid:{exc.lineno}:{exc.colno}"], []
    if not isinstance(raw, dict):
        return {}, path, True, ["settings_not_object"], []
    return raw, path, True, validate_settings_fragment(raw), _unknown_key_warnings(raw)


def validate_settings_fragment(settings: object) -> list[str]:
    if not settings:
        return []
    if not isinstance(settings, dict):
        return ["settings_not_object"]
    errors: list[str] = []
    runtime = settings.get("runtime")
    if runtime is not None and not isinstance(runtime, dict):
        errors.append("runtime_not_object")
    if isinstance(runtime, dict):
        options = runtime_options_from_settings({"runtime": runtime, "permissions": settings.get("permissions", {})})
        errors.extend(validate_runtime_options(options))
    permissions = settings.get("permissions")
    if permissions is not None and not isinstance(permissions, dict):
        errors.append("permissions_not_object")
    if isinstance(permissions, dict):
        for key in ("allow", "deny", "ask", "additionalDirectories", "additional_directories"):
            if key in permissions and not isinstance(permissions[key], list):
                errors.append(f"permissions_{key}_not_list")
    commands = settings.get("commands")
    if commands is not None and not isinstance(commands, dict):
        errors.append("commands_not_object")
    if isinstance(commands, dict):
        for key in ("disabled", "enabled"):
            if key in commands and not isinstance(commands[key], list):
                errors.append(f"commands_{key}_not_list")
    env = settings.get("env")
    if env is not None and not isinstance(env, dict):
        errors.append("env_not_object")
    return sorted(set(errors))


def _unknown_key_warnings(settings: object) -> list[str]:
    if not isinstance(settings, dict):
        return []
    known = {"runtime", "permissions", "commands", "env", "hooks", "$schema"}
    return [f"unknown_setting:{key}" for key in sorted(settings) if key not in known]


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def _optional_int(value: object, *, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_bool(value: object, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "on"}:
            return True
        if lowered in {"false", "no", "0", "off"}:
            return False
    return bool(value)


def _unique(values: Iterable[object]) -> list[object]:
    unique: list[object] = []
    seen: set[str] = set()
    for value in values:
        key = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(deepcopy(value))
    return unique
