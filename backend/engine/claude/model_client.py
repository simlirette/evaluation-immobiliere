from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import importlib
import importlib.util
import os
from typing import Callable, Protocol


CLAUDE_MODEL_REQUEST_SCHEMA_VERSION = "claude_model_request_v0"
CLAUDE_MODEL_RESPONSE_SCHEMA_VERSION = "claude_model_response_v0"
CLAUDE_MODEL_CLIENT_SUMMARY_SCHEMA_VERSION = "claude_model_client_summary_v0"
CLAUDE_MODEL_PROVIDER_CONFIG_SCHEMA_VERSION = "claude_model_provider_config_v0"
CLAUDE_MODEL_PROVIDER_DIAGNOSTICS_SCHEMA_VERSION = "claude_model_provider_diagnostics_v0"
ANTHROPIC_MESSAGES_REQUEST_SCHEMA_VERSION = "anthropic_messages_request_v0"
ANTHROPIC_SDK_TRANSPORT_SCHEMA_VERSION = "anthropic_sdk_transport_v0"
ANTHROPIC_SDK_MODULE_NAME = "anthropic"
ANTHROPIC_SDK_RUNTIME_ENV_FLAG = "EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME"
SUPPORTED_MODEL_PROVIDERS = {"fake", "anthropic"}
EXECUTABLE_MODEL_PROVIDERS = {"fake"}
SDK_ADAPTER_MODEL_PROVIDERS = {"anthropic"}
MODEL_PROVIDER_ADAPTERS = {
    "fake": "fake_local_v0",
    "anthropic": "anthropic_messages_v0",
}
SECRET_OPTION_TOKENS = ("api_key", "apikey", "token", "secret", "authorization", "password")
NON_SECRET_OPTION_KEYS = {
    "max_tokens",
    "input_tokens",
    "output_tokens",
    "total_tokens",
}


class ModelProviderConfigurationError(ValueError):
    pass


class ModelProviderTransportError(RuntimeError):
    def __init__(
        self,
        code: str,
        *,
        provider: str = "",
        retryable: bool = False,
        attempts: int = 1,
        details: str = "",
    ) -> None:
        super().__init__(code)
        self.code = code
        self.provider = provider
        self.retryable = retryable
        self.attempts = attempts
        self.details = details

    def as_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "code": self.code,
            "retryable": self.retryable,
            "attempts": self.attempts,
            "details": self.details,
        }


def _bounded_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, minimum), maximum)


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "oui", "on"}


def _safe_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def redact_model_provider_options(options: Mapping[str, object] | None) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in dict(options or {}).items():
        normalized_key = str(key).lower().replace("-", "_")
        if normalized_key not in NON_SECRET_OPTION_KEYS and any(
            token in normalized_key for token in SECRET_OPTION_TOKENS
        ):
            redacted[str(key)] = "[REDACTED]" if value else ""
        else:
            redacted[str(key)] = value
    return redacted


def detect_anthropic_sdk_available() -> bool:
    return importlib.util.find_spec(ANTHROPIC_SDK_MODULE_NAME) is not None


def load_anthropic_sdk_client_class() -> object:
    if not detect_anthropic_sdk_available():
        raise ModelProviderConfigurationError("anthropic_sdk_missing")
    module = importlib.import_module(ANTHROPIC_SDK_MODULE_NAME)
    client_class = getattr(module, "Anthropic", None)
    if client_class is None:
        raise ModelProviderConfigurationError("anthropic_sdk_client_missing")
    return client_class


@dataclass(frozen=True)
class ClaudeModelProviderConfig:
    provider: str = "fake"
    model: str = ""
    api_key_env: str = ""
    api_key_present: bool = False
    endpoint: str = ""
    timeout_seconds: int = 60
    max_retries: int = 2
    allow_network: bool = False
    sdk_execution_enabled: bool = False
    sdk_available: bool = False
    options: dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        network_execution_enabled = (
            self.provider == "anthropic"
            and self.allow_network
            and self.sdk_execution_enabled
            and self.api_key_present
            and self.sdk_available
        )
        return {
            "schema_version": CLAUDE_MODEL_PROVIDER_CONFIG_SCHEMA_VERSION,
            "provider": self.provider,
            "model": self.model,
            "api_key_env": self.api_key_env,
            "api_key_present": self.api_key_present,
            "endpoint_configured": bool(self.endpoint),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "allow_network": self.allow_network,
            "executable": self.provider in EXECUTABLE_MODEL_PROVIDERS,
            "adapter": MODEL_PROVIDER_ADAPTERS.get(self.provider, ""),
            "adapter_available": self.provider in EXECUTABLE_MODEL_PROVIDERS
            or self.provider in SDK_ADAPTER_MODEL_PROVIDERS,
            "sdk": {
                "module": ANTHROPIC_SDK_MODULE_NAME if self.provider == "anthropic" else "",
                "available": self.sdk_available if self.provider == "anthropic" else False,
                "transport": ANTHROPIC_SDK_TRANSPORT_SCHEMA_VERSION
                if self.provider == "anthropic"
                else "",
                "execution_enabled": self.sdk_execution_enabled,
            },
            "sdk_execution_enabled": self.sdk_execution_enabled,
            "network_execution_enabled": network_execution_enabled,
            "options": redact_model_provider_options(self.options),
            "redacted": True,
        }


def build_model_provider_config(
    options: Mapping[str, object] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    sdk_available: bool | None = None,
) -> ClaudeModelProviderConfig:
    raw_options = dict(options or {})
    provider = str(raw_options.get("provider") or "fake").strip().lower().replace("_", "-")
    api_key_env = str(raw_options.get("api_key_env") or ("ANTHROPIC_API_KEY" if provider == "anthropic" else ""))
    env_values = env or {}
    api_key_present = bool(raw_options.get("api_key")) or bool(api_key_env and env_values.get(api_key_env))
    sdk_enabled = _truthy(raw_options.get("enable_sdk_execution")) or _truthy(
        env_values.get("EVAL_IMMO_ENABLE_ANTHROPIC_SDK")
    )
    return ClaudeModelProviderConfig(
        provider=provider,
        model=str(raw_options.get("model") or ""),
        api_key_env=api_key_env,
        api_key_present=api_key_present,
        endpoint=str(raw_options.get("endpoint") or ""),
        timeout_seconds=_bounded_int(
            raw_options.get("timeout_seconds"),
            default=60,
            minimum=1,
            maximum=300,
        ),
        max_retries=_bounded_int(raw_options.get("max_retries"), default=2, minimum=0, maximum=8),
        allow_network=_truthy(raw_options.get("allow_network")),
        sdk_execution_enabled=sdk_enabled,
        sdk_available=detect_anthropic_sdk_available() if sdk_available is None else bool(sdk_available),
        options=redact_model_provider_options(raw_options),
    )


class ClaudeProviderTransport(Protocol):
    network_enabled: bool

    def complete(
        self,
        payload: Mapping[str, object],
        config: ClaudeModelProviderConfig,
    ) -> Mapping[str, object]:
        ...


def validate_model_provider_config(
    config: ClaudeModelProviderConfig,
    *,
    require_executable: bool = True,
    require_network_for_non_fake: bool = True,
    require_sdk_for_network: bool = False,
) -> list[str]:
    errors: list[str] = []
    if config.provider not in SUPPORTED_MODEL_PROVIDERS:
        errors.append(f"provider_unsupported:{config.provider}")
    if require_executable and config.provider not in EXECUTABLE_MODEL_PROVIDERS:
        errors.append(f"provider_not_executable:{config.provider}")
    if config.provider != "fake":
        if require_network_for_non_fake and not config.allow_network:
            errors.append("network_not_enabled")
        if not config.api_key_present:
            errors.append(f"api_key_missing:{config.api_key_env or 'api_key_env_missing'}")
        if require_sdk_for_network:
            if not config.sdk_execution_enabled:
                errors.append("sdk_execution_not_enabled")
            if not config.sdk_available:
                errors.append("anthropic_sdk_missing")
    if config.provider == "fake" and config.allow_network:
        errors.append("fake_provider_network_not_allowed")
    if config.provider == "fake" and config.sdk_execution_enabled:
        errors.append("fake_provider_sdk_not_allowed")
    return errors


def summarize_model_provider_config(
    config: ClaudeModelProviderConfig,
    *,
    require_executable: bool = True,
    require_network_for_non_fake: bool = True,
    require_sdk_for_network: bool = False,
) -> dict[str, object]:
    errors = validate_model_provider_config(
        config,
        require_executable=require_executable,
        require_network_for_non_fake=require_network_for_non_fake,
        require_sdk_for_network=require_sdk_for_network,
    )
    return {
        **config.as_dict(),
        "errors": errors,
        "ok": not errors,
    }


def build_model_provider_diagnostics(
    options: Mapping[str, object] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    sdk_available: bool | None = None,
) -> dict[str, object]:
    env_values = env or {}
    config = build_model_provider_config(
        options,
        env=env_values,
        sdk_available=sdk_available,
    )
    default_errors = validate_model_provider_config(config)
    sdk_transport_errors = validate_model_provider_config(
        config,
        require_executable=False,
        require_network_for_non_fake=True,
        require_sdk_for_network=True,
    )
    operator_runtime_enabled = _truthy(env_values.get(ANTHROPIC_SDK_RUNTIME_ENV_FLAG))
    sdk_transport_ready = not sdk_transport_errors
    api_runtime_ready = (
        config.provider == "fake"
        or (
            config.provider == "anthropic"
            and sdk_transport_ready
            and operator_runtime_enabled
        )
    )
    guardrails = [
        {
            "id": "provider_supported",
            "ok": config.provider in SUPPORTED_MODEL_PROVIDERS,
            "required_for": ["default", "sdk_transport", "api_runtime"],
        },
        {
            "id": "default_runtime_fake_only",
            "ok": config.provider in EXECUTABLE_MODEL_PROVIDERS,
            "required_for": ["default"],
        },
        {
            "id": "network_allowed",
            "ok": config.provider == "fake" or config.allow_network,
            "required_for": ["sdk_transport", "api_runtime"],
        },
        {
            "id": "sdk_execution_enabled",
            "ok": config.provider == "fake" or config.sdk_execution_enabled,
            "required_for": ["sdk_transport", "api_runtime"],
        },
        {
            "id": "anthropic_sdk_available",
            "ok": config.provider == "fake" or config.sdk_available,
            "required_for": ["sdk_transport", "api_runtime"],
        },
        {
            "id": "api_key_present",
            "ok": config.provider == "fake" or config.api_key_present,
            "required_for": ["sdk_transport", "api_runtime"],
        },
        {
            "id": "operator_runtime_enabled",
            "ok": config.provider == "fake" or operator_runtime_enabled,
            "required_for": ["api_runtime"],
            "env_flag": ANTHROPIC_SDK_RUNTIME_ENV_FLAG if config.provider == "anthropic" else "",
        },
        {
            "id": "fake_provider_has_no_network",
            "ok": config.provider != "fake" or not config.allow_network,
            "required_for": ["default", "sdk_transport", "api_runtime"],
        },
    ]
    default_runtime_missing_guardrails = [
        str(item["id"])
        for item in guardrails
        if not bool(item.get("ok")) and "default" in item.get("required_for", [])
    ]
    sdk_transport_missing_guardrails = [
        str(item["id"])
        for item in guardrails
        if not bool(item.get("ok")) and "sdk_transport" in item.get("required_for", [])
    ]
    api_runtime_missing_guardrails = [
        str(item["id"])
        for item in guardrails
        if not bool(item.get("ok")) and "api_runtime" in item.get("required_for", [])
    ]
    return {
        "schema_version": CLAUDE_MODEL_PROVIDER_DIAGNOSTICS_SCHEMA_VERSION,
        "provider": config.provider,
        "adapter": MODEL_PROVIDER_ADAPTERS.get(config.provider, ""),
        "config": config.as_dict(),
        "default_runtime": {
            "ready": not default_errors,
            "errors": default_errors,
            "executable_providers": sorted(EXECUTABLE_MODEL_PROVIDERS),
        },
        "sdk_transport": {
            "ready": sdk_transport_ready,
            "errors": sdk_transport_errors,
            "missing_guardrails": sdk_transport_missing_guardrails,
            "schema_version": ANTHROPIC_SDK_TRANSPORT_SCHEMA_VERSION
            if config.provider == "anthropic"
            else "",
            "client_constructed": False,
        },
        "api_runtime": {
            "ready": api_runtime_ready,
            "operator_runtime_enabled": operator_runtime_enabled,
            "operator_env_flag": ANTHROPIC_SDK_RUNTIME_ENV_FLAG,
            "missing_guardrails": api_runtime_missing_guardrails,
            "client_constructed": False,
        },
        "guardrails": guardrails,
        "missing_guardrails": api_runtime_missing_guardrails,
        "default_runtime_missing_guardrails": default_runtime_missing_guardrails,
        "sdk_transport_missing_guardrails": sdk_transport_missing_guardrails,
        "redacted": True,
        "ok": config.provider == "fake" or sdk_transport_ready,
    }


def build_model_client(
    config: ClaudeModelProviderConfig | None = None,
    *,
    transports: Mapping[str, ClaudeProviderTransport] | None = None,
    enable_experimental_adapters: bool = False,
    enable_sdk_execution: bool = False,
    sdk_factory: Callable[..., object] | None = None,
    env: Mapping[str, str] | None = None,
) -> "ClaudeModelClient":
    provider_config = config or build_model_provider_config()
    errors = validate_model_provider_config(
        provider_config,
        require_executable=not enable_experimental_adapters,
        require_network_for_non_fake=not enable_experimental_adapters,
        require_sdk_for_network=enable_sdk_execution,
    )
    if errors:
        raise ModelProviderConfigurationError(";".join(errors))
    if provider_config.provider == "fake":
        return FakeClaudeModelClient()
    if enable_experimental_adapters and provider_config.provider == "anthropic":
        transport = (transports or {}).get("anthropic")
        if transport is None and enable_sdk_execution:
            transport = AnthropicSDKTransport(
                provider_config,
                sdk_factory=sdk_factory,
                env=env,
            )
        return AnthropicClaudeModelClient(
            provider_config,
            transport=transport,
        )
    raise ModelProviderConfigurationError(f"provider_not_implemented:{provider_config.provider}")


@dataclass(frozen=True)
class ClaudeModelRequest:
    agent_type: str
    model: str
    system_prompt: list[str]
    messages: list[dict[str, object]]
    context: dict[str, object]
    tools: list[str]
    skills: list[str]
    expected_outputs: list[str]
    runtime_mode: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": CLAUDE_MODEL_REQUEST_SCHEMA_VERSION,
            "agent_type": self.agent_type,
            "model": self.model,
            "system_prompt_sections_count": len(self.system_prompt),
            "messages_count": len(self.messages),
            "context": dict(self.context),
            "tools": list(self.tools),
            "skills": list(self.skills),
            "expected_outputs": list(self.expected_outputs),
            "runtime_mode": self.runtime_mode,
        }


@dataclass(frozen=True)
class ClaudeModelResponse:
    agent_type: str
    model: str
    provider: str
    content: list[dict[str, object]]
    stop_reason: str = "end_turn"
    tool_calls: list[dict[str, object]] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=dict)
    raw_response_id: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": CLAUDE_MODEL_RESPONSE_SCHEMA_VERSION,
            "agent_type": self.agent_type,
            "model": self.model,
            "provider": self.provider,
            "content": list(self.content),
            "content_block_types": [
                str(block.get("type"))
                for block in self.content
                if isinstance(block, dict) and block.get("type")
            ],
            "stop_reason": self.stop_reason,
            "tool_calls": list(self.tool_calls),
            "tool_calls_count": len(self.tool_calls),
            "usage": dict(self.usage),
            "raw_response_id": self.raw_response_id,
        }


class ClaudeModelClient(Protocol):
    provider: str

    def complete(self, request: ClaudeModelRequest) -> ClaudeModelResponse:
        ...


class FakeClaudeModelClient:
    provider = "fake"

    def complete(self, request: ClaudeModelRequest) -> ClaudeModelResponse:
        output_text = (
            f"Plan d'execution {request.agent_type}: produire "
            f"{', '.join(request.expected_outputs)} avec les outils autorises."
        )
        estimated_input_tokens = max(
            1,
            int(
                sum(len(section) for section in request.system_prompt)
                + sum(len(str(message.get("content", ""))) for message in request.messages)
            )
            // 4,
        )
        estimated_output_tokens = max(1, len(output_text) // 4)
        return ClaudeModelResponse(
            agent_type=request.agent_type,
            model=request.model,
            provider=self.provider,
            content=[{"type": "text", "text": output_text}],
            stop_reason="end_turn",
            usage={
                "input_tokens": estimated_input_tokens,
                "output_tokens": estimated_output_tokens,
            },
            raw_response_id=f"fake-{request.agent_type}-001",
        )


def build_anthropic_request_payload(request: ClaudeModelRequest) -> dict[str, object]:
    return {
        "schema_version": ANTHROPIC_MESSAGES_REQUEST_SCHEMA_VERSION,
        "model": request.model,
        "system": [
            {"type": "text", "text": section}
            for section in request.system_prompt
            if str(section).strip()
        ],
        "messages": [dict(message) for message in request.messages],
        "tools": [{"name": tool} for tool in request.tools],
        "metadata": {
            "agent_type": request.agent_type,
            "runtime_mode": request.runtime_mode,
            "skills": list(request.skills),
            "expected_outputs": list(request.expected_outputs),
        },
    }


def build_anthropic_sdk_messages_params(
    payload: Mapping[str, object],
    config: ClaudeModelProviderConfig,
) -> dict[str, object]:
    params: dict[str, object] = {
        "model": str(payload.get("model") or config.model),
        "max_tokens": _bounded_int(
            config.options.get("max_tokens"),
            default=4096,
            minimum=1,
            maximum=64000,
        ),
        "messages": [
            dict(message)
            for message in payload.get("messages", [])
            if isinstance(message, Mapping)
        ],
    }
    system = payload.get("system")
    if isinstance(system, list) and system:
        params["system"] = [
            dict(block)
            for block in system
            if isinstance(block, Mapping)
        ]
    tools = payload.get("tools")
    if isinstance(tools, list) and tools:
        params["tools"] = [
            dict(tool)
            for tool in tools
            if isinstance(tool, Mapping)
        ]
    return params


def _coerce_content_blocks(content: object) -> list[dict[str, object]]:
    if isinstance(content, list):
        blocks: list[dict[str, object]] = []
        for block in content:
            if isinstance(block, Mapping):
                blocks.append(dict(block))
            elif str(block):
                blocks.append({"type": "text", "text": str(block)})
        return blocks
    if content:
        return [{"type": "text", "text": str(content)}]
    return []


def _coerce_anthropic_usage(usage: object) -> dict[str, int]:
    if not isinstance(usage, Mapping):
        return {"input_tokens": 0, "output_tokens": 0}
    return {
        "input_tokens": _safe_int(usage.get("input_tokens", usage.get("inputTokens", 0))),
        "output_tokens": _safe_int(usage.get("output_tokens", usage.get("outputTokens", 0))),
    }


def parse_anthropic_response_payload(
    request: ClaudeModelRequest,
    payload: Mapping[str, object],
) -> ClaudeModelResponse:
    content = _coerce_content_blocks(payload.get("content"))
    return ClaudeModelResponse(
        agent_type=request.agent_type,
        model=str(payload.get("model") or request.model),
        provider="anthropic",
        content=content,
        stop_reason=str(payload.get("stop_reason") or "end_turn"),
        tool_calls=[
            dict(block)
            for block in content
            if isinstance(block, Mapping) and block.get("type") == "tool_use"
        ],
        usage=_coerce_anthropic_usage(payload.get("usage")),
        raw_response_id=str(payload.get("id") or payload.get("response_id") or ""),
    )


def _object_to_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        dumped = to_dict()
        if isinstance(dumped, Mapping):
            return dumped
    fields = ("id", "model", "stop_reason", "content", "usage")
    mapped = {
        field: getattr(value, field)
        for field in fields
        if hasattr(value, field)
    }
    return mapped


def classify_anthropic_sdk_error(
    error: BaseException,
    *,
    provider: str = "anthropic",
    attempts: int = 1,
) -> ModelProviderTransportError:
    class_name = error.__class__.__name__.lower()
    message = str(error).lower()
    status_code = getattr(error, "status_code", None)
    retry_after = getattr(error, "retry_after", None)
    if status_code is None:
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)
    details_parts: list[str] = []
    if status_code is not None:
        details_parts.append(f"status={status_code}")
    if retry_after is not None:
        details_parts.append(f"retry_after={retry_after}")
    if "timeout" in class_name or "timeout" in message or "timed out" in message:
        return ModelProviderTransportError(
            "anthropic_sdk_timeout",
            provider=provider,
            retryable=True,
            attempts=attempts,
            details=";".join(details_parts),
        )
    if status_code in {408, 409, 425, 429} or "ratelimit" in class_name or "rate_limit" in class_name:
        return ModelProviderTransportError(
            "anthropic_sdk_retryable",
            provider=provider,
            retryable=True,
            attempts=attempts,
            details=";".join(details_parts),
        )
    if status_code is not None and int(status_code) >= 500:
        return ModelProviderTransportError(
            "anthropic_sdk_server_error",
            provider=provider,
            retryable=True,
            attempts=attempts,
            details=";".join(details_parts),
        )
    if status_code in {400, 422} or "badrequest" in class_name:
        return ModelProviderTransportError(
            "anthropic_sdk_bad_request",
            provider=provider,
            retryable=False,
            attempts=attempts,
            details=";".join(details_parts),
        )
    if status_code in {401, 403} or "auth" in class_name or "permission" in class_name:
        return ModelProviderTransportError(
            "anthropic_sdk_auth_error",
            provider=provider,
            retryable=False,
            attempts=attempts,
            details=";".join(details_parts),
        )
    if "connection" in class_name or "network" in class_name:
        return ModelProviderTransportError(
            "anthropic_sdk_connection_error",
            provider=provider,
            retryable=True,
            attempts=attempts,
            details=";".join(details_parts),
        )
    return ModelProviderTransportError(
        "anthropic_sdk_error",
        provider=provider,
        retryable=False,
        attempts=attempts,
        details=";".join(details_parts),
    )


class AnthropicSDKTransport:
    schema_version = ANTHROPIC_SDK_TRANSPORT_SCHEMA_VERSION
    network_enabled = True

    def __init__(
        self,
        config: ClaudeModelProviderConfig,
        *,
        sdk_factory: Callable[..., object] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        if config.provider != "anthropic":
            raise ModelProviderConfigurationError(f"provider_mismatch:{config.provider}:anthropic")
        if not config.allow_network:
            raise ModelProviderConfigurationError("network_not_enabled")
        if not config.sdk_execution_enabled:
            raise ModelProviderConfigurationError("sdk_execution_not_enabled")
        env_values = env if env is not None else os.environ
        api_key = env_values.get(config.api_key_env or "ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ModelProviderConfigurationError(f"api_key_missing:{config.api_key_env or 'ANTHROPIC_API_KEY'}")
        factory = sdk_factory
        if factory is None:
            factory = load_anthropic_sdk_client_class()  # type: ignore[assignment]
        client_kwargs: dict[str, object] = {
            "api_key": api_key,
            "timeout": config.timeout_seconds,
            "max_retries": config.max_retries,
        }
        if config.endpoint:
            client_kwargs["base_url"] = config.endpoint
        self.config = config
        self.client = factory(**client_kwargs)

    def complete(
        self,
        payload: Mapping[str, object],
        config: ClaudeModelProviderConfig,
    ) -> Mapping[str, object]:
        params = build_anthropic_sdk_messages_params(payload, config)
        messages = getattr(self.client, "messages", None)
        create = getattr(messages, "create", None)
        if not callable(create):
            raise ModelProviderConfigurationError("anthropic_sdk_messages_create_missing")
        try:
            return _object_to_mapping(create(**params))
        except Exception as exc:
            raise classify_anthropic_sdk_error(
                exc,
                attempts=config.max_retries + 1,
            ) from exc


class AnthropicClaudeModelClient:
    provider = "anthropic"
    adapter = "anthropic_messages_v0"

    def __init__(
        self,
        config: ClaudeModelProviderConfig,
        *,
        transport: ClaudeProviderTransport | None = None,
    ) -> None:
        if config.provider != "anthropic":
            raise ModelProviderConfigurationError(f"provider_mismatch:{config.provider}:anthropic")
        if not config.api_key_present:
            raise ModelProviderConfigurationError(f"api_key_missing:{config.api_key_env or 'api_key_env_missing'}")
        if transport is None:
            raise ModelProviderConfigurationError("anthropic_transport_missing")
        if bool(getattr(transport, "network_enabled", False)) and not (
            config.allow_network and config.sdk_execution_enabled
        ):
            raise ModelProviderConfigurationError("anthropic_network_transport_blocked")
        self.config = config
        self.transport = transport

    def complete(self, request: ClaudeModelRequest) -> ClaudeModelResponse:
        payload = build_anthropic_request_payload(request)
        raw_response = self.transport.complete(payload, self.config)
        if not isinstance(raw_response, Mapping):
            raise ModelProviderConfigurationError("anthropic_transport_response_invalid")
        return parse_anthropic_response_payload(request, raw_response)


def summarize_model_client_interaction(
    *,
    request: ClaudeModelRequest | None,
    response: ClaudeModelResponse | None,
    enabled: bool,
    provider: str = "",
) -> dict[str, object]:
    if not enabled:
        return {
            "schema_version": CLAUDE_MODEL_CLIENT_SUMMARY_SCHEMA_VERSION,
            "enabled": False,
            "provider": provider,
            "requests_count": 0,
            "responses_count": 0,
            "tool_calls_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "ok": True,
        }
    errors = validate_model_response(response)
    usage = response.usage if response is not None else {}
    return {
        "schema_version": CLAUDE_MODEL_CLIENT_SUMMARY_SCHEMA_VERSION,
        "enabled": True,
        "provider": response.provider if response else provider,
        "agent_type": response.agent_type if response else (request.agent_type if request else ""),
        "model": response.model if response else (request.model if request else ""),
        "requests_count": 1 if request is not None else 0,
        "responses_count": 1 if response is not None else 0,
        "request_schema_version": CLAUDE_MODEL_REQUEST_SCHEMA_VERSION if request is not None else "",
        "response_schema_version": CLAUDE_MODEL_RESPONSE_SCHEMA_VERSION if response is not None else "",
        "stop_reason": response.stop_reason if response else "",
        "content_blocks_count": len(response.content) if response else 0,
        "tool_calls_count": len(response.tool_calls) if response else 0,
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "errors": errors,
        "ok": not errors,
    }


def validate_model_response(response: ClaudeModelResponse | None) -> list[str]:
    if response is None:
        return ["model_response_missing"]
    errors: list[str] = []
    if not response.agent_type:
        errors.append("agent_type_missing")
    if not response.model:
        errors.append("model_missing")
    if not response.provider:
        errors.append("provider_missing")
    if not response.content:
        errors.append("content_empty")
    if response.stop_reason not in {"end_turn", "tool_use", "max_tokens", "stop_sequence"}:
        errors.append(f"stop_reason_invalid:{response.stop_reason}")
    return errors
