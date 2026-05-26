from __future__ import annotations

from pathlib import Path

from engine.audit import append_audit_log
from engine.claude.exceptions import ToolPermissionError
from engine.claude.permissions import ClaudePermissionDecision, ClaudePermissionPolicy
from engine.claude.types import ClaudeToolCall, ClaudeToolResult, ToolSpec
from engine.runtime import write_artifact_payload
from engine.tools import run_calculation, search_comparables, validate_schema


VALID_TOOL_PERMISSIONS = {"runtime_read", "runtime_write", "runtime_execute"}
VALID_SCHEMA_TYPES = {"object", "string", "array", "integer", "number", "boolean"}
TOOL_REGISTRY_SUMMARY_SCHEMA_VERSION = "claude_tool_registry_summary_v0"
TOOL_INPUT_VALIDATION_SCHEMA_VERSION = "claude_tool_input_validation_v0"


def _object_schema(
    properties: dict[str, dict[str, object]] | None = None,
    *,
    required: list[str] | None = None,
    additional_properties: bool = False,
) -> dict[str, object]:
    return {
        "type": "object",
        "properties": properties or {},
        "required": required or [],
        "additionalProperties": additional_properties,
    }


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "append_audit_log": ToolSpec(
        name="append_audit_log",
        description="Append an immutable runtime audit event.",
        permission="runtime_write",
        input_schema=_object_schema({"event": {"type": "object"}}, required=["event"]),
        search_hint="runtime audit trail",
    ),
    "extract_text": ToolSpec(
        name="extract_text",
        description="Extract text from provided source documents.",
        permission="runtime_read",
        input_schema=_object_schema(
            {
                "source_id": {"type": "string"},
                "path": {"type": "string"},
            },
            required=["source_id"],
        ),
        read_only=True,
        search_hint="source text extraction",
    ),
    "format_document": ToolSpec(
        name="format_document",
        description="Format a report artifact without adding new facts.",
        permission="runtime_write",
        input_schema=_object_schema(
            {
                "path": {"type": "string"},
                "artifact": {"type": "string"},
            },
            required=["path"],
        ),
        search_hint="report formatting",
    ),
    "list_files": ToolSpec(
        name="list_files",
        description="List files available in the case directory.",
        permission="runtime_read",
        input_schema=_object_schema(),
        read_only=True,
        search_hint="case file listing",
    ),
    "read_file": ToolSpec(
        name="read_file",
        description="Read an artifact or source document from the case directory.",
        permission="runtime_read",
        input_schema=_object_schema({"path": {"type": "string"}}, required=["path"]),
        read_only=True,
        search_hint="case file read",
    ),
    "run_calculation": ToolSpec(
        name="run_calculation",
        description="Run deterministic valuation calculations.",
        permission="runtime_execute",
        input_schema=_object_schema(
            {
                "method": {"type": "string"},
                "values": {"type": "array", "items": {"type": "number"}},
                "weights": {"type": "array", "items": {"type": "number"}},
            },
            required=["method", "values"],
        ),
        search_hint="valuation math",
    ),
    "search_comparables": ToolSpec(
        name="search_comparables",
        description="Search and score market comparables.",
        permission="runtime_read",
        input_schema=_object_schema(
            {
                "pool": {"type": "array", "items": {"type": "object"}},
                "subject": {"type": "object"},
                "date_reference": {"type": "string"},
                "max_items": {"type": "integer"},
            },
            required=["subject"],
        ),
        read_only=True,
        search_hint="market comparable search",
    ),
    "validate_schema": ToolSpec(
        name="validate_schema",
        description="Validate an artifact against required fields.",
        permission="runtime_execute",
        input_schema=_object_schema(
            {
                "payload": {"type": "object"},
                "required_fields": {"type": "array", "items": {"type": "string"}},
            },
            required=["payload", "required_fields"],
        ),
        read_only=True,
        search_hint="artifact schema validation",
    ),
    "write_file": ToolSpec(
        name="write_file",
        description="Write a runtime artifact in the case directory.",
        permission="runtime_write",
        input_schema=_object_schema(
            {
                "path": {"type": "string"},
                "content": {"type": "object"},
            },
            required=["path", "content"],
        ),
        destructive=True,
        search_hint="case artifact write",
    ),
}


def validate_tool_registry(tool_registry: dict[str, ToolSpec] | None = None) -> list[str]:
    registry = tool_registry or TOOL_REGISTRY
    errors: list[str] = []
    for registry_name, spec in registry.items():
        if registry_name != spec.name:
            errors.append(f"{registry_name}:name_mismatch:{spec.name}")
        if not spec.name:
            errors.append(f"{registry_name}:missing_name")
        if not spec.description:
            errors.append(f"{registry_name}:missing_description")
        if spec.permission not in VALID_TOOL_PERMISSIONS:
            errors.append(f"{registry_name}:invalid_permission:{spec.permission}")
        if spec.max_result_size_chars <= 0:
            errors.append(f"{registry_name}:invalid_max_result_size_chars")
        errors.extend(f"{registry_name}:{error}" for error in _validate_input_schema_shape(spec.input_schema))
    return errors


def summarize_tool_registry(
    tool_names: list[str] | None = None,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> dict[str, object]:
    registry = tool_registry or TOOL_REGISTRY
    selected_names = list(tool_names) if tool_names is not None else sorted(registry)
    specs = [registry[name] for name in selected_names if name in registry]
    missing = [name for name in selected_names if name not in registry]
    validation_errors = validate_tool_registry({spec.name: spec for spec in specs})
    validation_errors.extend(f"{name}:missing_from_registry" for name in missing)
    return {
        "schema_version": TOOL_REGISTRY_SUMMARY_SCHEMA_VERSION,
        "tools_count": len(specs),
        "tool_names": [spec.name for spec in specs],
        "permissions": sorted({spec.permission for spec in specs}),
        "read_only_tools": [spec.name for spec in specs if spec.read_only],
        "write_tools": [spec.name for spec in specs if spec.permission == "runtime_write"],
        "execute_tools": [spec.name for spec in specs if spec.permission == "runtime_execute"],
        "destructive_tools": [spec.name for spec in specs if spec.destructive],
        "strict_tools_count": sum(1 for spec in specs if spec.strict),
        "model_facing_tools": [spec.model_facing_schema() for spec in specs],
        "validation_errors": validation_errors,
        "ok": not validation_errors,
    }


def validate_tool_call_input(
    call: ClaudeToolCall,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> list[str]:
    registry = tool_registry or TOOL_REGISTRY
    spec = registry.get(call.name)
    if spec is None:
        return ["unknown_tool"]
    return validate_tool_input(call.name, call.input, tool_registry=registry)


def validate_tool_input(
    tool_name: str,
    value: object,
    *,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> list[str]:
    registry = tool_registry or TOOL_REGISTRY
    spec = registry.get(tool_name)
    if spec is None:
        return ["unknown_tool"]
    if not isinstance(value, dict):
        return ["input_not_object"]

    schema = spec.input_schema
    errors = _validate_input_schema_shape(schema)
    if errors:
        return [f"schema:{error}" for error in errors]

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list):
        required = []
    for field in required:
        if isinstance(field, str) and field not in value:
            errors.append(f"missing_required:{field}")
    for key, item in value.items():
        property_schema = properties.get(key)
        if property_schema is None:
            if schema.get("additionalProperties") is False:
                errors.append(f"unexpected_property:{key}")
            continue
        if not isinstance(property_schema, dict):
            errors.append(f"invalid_property_schema:{key}")
            continue
        errors.extend(_validate_value_against_schema(key, item, property_schema))
    return errors


def build_tool_input_validation(
    call: ClaudeToolCall,
    tool_registry: dict[str, ToolSpec] | None = None,
) -> dict[str, object]:
    errors = validate_tool_call_input(call, tool_registry)
    return {
        "schema_version": TOOL_INPUT_VALIDATION_SCHEMA_VERSION,
        "tool_call_id": call.id,
        "tool": call.name,
        "agent_type": call.agent_type,
        "errors": errors,
        "errors_count": len(errors),
        "ok": not errors,
    }


def _validate_input_schema_shape(schema: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if schema.get("type") != "object":
        errors.append("schema_type_must_be_object")
    properties = schema.get("properties", {})
    if properties is not None and not isinstance(properties, dict):
        errors.append("schema_properties_must_be_object")
        properties = {}
    required = schema.get("required", [])
    if required is not None and not isinstance(required, list):
        errors.append("schema_required_must_be_list")
        required = []
    for field in required:
        if not isinstance(field, str):
            errors.append("schema_required_field_must_be_string")
        elif isinstance(properties, dict) and field not in properties:
            errors.append(f"schema_required_property_missing:{field}")
    if isinstance(properties, dict):
        for field, property_schema in properties.items():
            if not isinstance(field, str):
                errors.append("schema_property_name_must_be_string")
                continue
            if not isinstance(property_schema, dict):
                errors.append(f"schema_property_must_be_object:{field}")
                continue
            property_type = property_schema.get("type")
            if property_type not in VALID_SCHEMA_TYPES:
                errors.append(f"schema_property_type_invalid:{field}")
    return errors


def _validate_value_against_schema(field: str, value: object, schema: dict[str, object]) -> list[str]:
    expected_type = str(schema.get("type") or "")
    if not _matches_schema_type(value, expected_type):
        return [f"type_mismatch:{field}:expected_{expected_type}"]
    if expected_type == "array" and isinstance(value, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict) and item_schema.get("type") in VALID_SCHEMA_TYPES:
            errors: list[str] = []
            item_type = str(item_schema["type"])
            for index, item in enumerate(value):
                if not _matches_schema_type(item, item_type):
                    errors.append(f"type_mismatch:{field}[{index}]:expected_{item_type}")
            return errors
    return []


def _matches_schema_type(value: object, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    return False


class ClaudeToolExecutor:
    def __init__(
        self,
        allowed_tools: list[str],
        case_dir: Path,
        *,
        audit_log_path: Path | None = None,
        tool_registry: dict[str, ToolSpec] | None = None,
        permission_mode: str = ClaudePermissionPolicy.DEFAULT,
        permission_policy: ClaudePermissionPolicy | None = None,
        permission_state: dict[str, object] | None = None,
    ) -> None:
        self.allowed_tools = set(allowed_tools)
        self.case_dir = case_dir
        self.audit_log_path = audit_log_path
        self.tool_registry = tool_registry or TOOL_REGISTRY
        registry_errors = validate_tool_registry(self.tool_registry)
        if registry_errors:
            raise ValueError(f"tool_registry invalide: {registry_errors}")
        unknown_allowed_tools = sorted(self.allowed_tools - set(self.tool_registry))
        if unknown_allowed_tools:
            raise ValueError(f"allowed_tools inconnus: {unknown_allowed_tools}")
        self.permission_policy = permission_policy or ClaudePermissionPolicy(
            allowed_tools,
            mode=permission_mode,
            tool_registry=self.tool_registry,
            permission_state=permission_state,
        )
        self.permission_decisions: list[dict[str, object]] = []

    def decide(self, call: ClaudeToolCall) -> ClaudePermissionDecision:
        decision = self.permission_policy.decide(call)
        self.permission_decisions.append(decision.as_dict())
        return decision

    def execute(
        self,
        call: ClaudeToolCall,
        *,
        decision: ClaudePermissionDecision | None = None,
    ) -> ClaudeToolResult:
        decision = decision or self.decide(call)
        if not decision.allowed:
            raise ToolPermissionError(f"outil refuse pour {call.agent_type}: {call.name} ({decision.reason})")

        input_validation = build_tool_input_validation(call, self.tool_registry)
        if not input_validation["ok"]:
            return ClaudeToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=input_validation,
                error=f"ToolInputValidationError: {input_validation['errors']}",
                permission=decision.permission,
            )

        try:
            output = self._execute_allowed(call)
            return ClaudeToolResult(
                call_id=call.id,
                name=call.name,
                ok=True,
                output=output,
                permission=decision.permission,
            )
        except Exception as exc:
            return ClaudeToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                permission=decision.permission,
            )

    def _execute_allowed(self, call: ClaudeToolCall) -> object:
        if call.name == "append_audit_log":
            if self.audit_log_path is None:
                raise ValueError("audit_log_path requis")
            event = call.input.get("event")
            if not isinstance(event, dict):
                raise ValueError("event doit etre un objet")
            append_audit_log(self.audit_log_path, event)
            return {"audit_log": self.audit_log_path.as_posix()}

        if call.name == "extract_text":
            source_id = str(call.input.get("source_id") or "")
            path_value = call.input.get("path") or source_id
            path = self._resolve_case_path(str(path_value))
            if path.exists() and path.is_file():
                return {"source_id": source_id, "text": path.read_text(encoding="utf-8")}
            return {"source_id": source_id, "text": "", "missing": True}

        if call.name == "format_document":
            path = self._resolve_case_path(str(call.input.get("path") or ""))
            return {"path": path.as_posix(), "status": "noop"}

        if call.name == "list_files":
            files = [
                path.relative_to(self.case_dir).as_posix()
                for path in sorted(self.case_dir.rglob("*"))
                if path.is_file()
            ]
            return {"files": files}

        if call.name == "read_file":
            path = self._resolve_case_path(str(call.input.get("path") or ""))
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(path.as_posix())
            return {"path": path.as_posix(), "content": path.read_text(encoding="utf-8")}

        if call.name == "run_calculation":
            values = call.input.get("values")
            if not isinstance(values, list):
                raise ValueError("values doit etre une liste")
            weights = call.input.get("weights")
            if weights is not None and not isinstance(weights, list):
                raise ValueError("weights doit etre une liste")
            return {
                "value": run_calculation(
                    values,
                    str(call.input.get("method") or "mean"),
                    weights=weights,
                )
            }

        if call.name == "search_comparables":
            pool = call.input.get("pool")
            if not isinstance(pool, list):
                raise ValueError("pool doit etre une liste")
            subject = call.input.get("subject")
            if subject is not None and not isinstance(subject, dict):
                raise ValueError("subject doit etre un objet")
            comparables = search_comparables(
                pool,
                max_items=int(call.input.get("max_items") or 5),
                subject=subject,
                date_reference=str(call.input.get("date_reference") or ""),
            )
            return {"comparables": [comparable.__dict__ for comparable in comparables]}

        if call.name == "validate_schema":
            payload = call.input.get("payload")
            required_fields = call.input.get("required_fields")
            if not isinstance(payload, dict):
                raise ValueError("payload doit etre un objet")
            if not isinstance(required_fields, list):
                raise ValueError("required_fields doit etre une liste")
            ok, missing = validate_schema(payload, [str(field) for field in required_fields])
            return {"ok": ok, "missing": missing}

        if call.name == "write_file":
            path = self._resolve_case_path(str(call.input.get("path") or ""))
            content = call.input.get("content")
            if not isinstance(content, dict):
                raise ValueError("content doit etre un objet")
            write_artifact_payload(path, content)
            return {"path": path.as_posix()}

        raise NotImplementedError(call.name)

    def _resolve_case_path(self, value: str) -> Path:
        if not value:
            raise ValueError("path requis")
        path = Path(value)
        candidate = path if path.is_absolute() else self.case_dir / path
        resolved = candidate.resolve()
        base = self.case_dir.resolve()
        if resolved != base and base not in resolved.parents:
            raise PermissionError(f"path hors case_dir: {value}")
        return resolved
