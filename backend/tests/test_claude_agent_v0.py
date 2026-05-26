from __future__ import annotations

from dataclasses import replace
import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import engine.claude_agent as claude_agent
from engine.claude.command_execution import execute_slash_command as modular_execute_slash_command
from engine.claude.commands import summarize_command_context as modular_summarize_command_context
from engine.claude.config import load_claude_agent_definition as modular_load_claude_agent_definition
from engine.claude.envelopes import build_claude_message_envelope as modular_build_claude_message_envelope
from engine.claude.hooks import build_claude_hook_invocation as modular_build_claude_hook_invocation
from engine.claude.model_client import AnthropicClaudeModelClient as ModularAnthropicClaudeModelClient
from engine.claude.model_client import AnthropicSDKTransport as ModularAnthropicSDKTransport
from engine.claude.model_client import FakeClaudeModelClient as ModularFakeClaudeModelClient
from engine.claude.model_client import build_anthropic_request_payload as modular_build_anthropic_request_payload
from engine.claude.model_client import build_anthropic_sdk_messages_params as modular_build_anthropic_sdk_messages_params
from engine.claude.model_client import build_model_client as modular_build_model_client
from engine.claude.model_client import build_model_provider_diagnostics as modular_build_model_provider_diagnostics
from engine.claude.model_client import build_model_provider_config as modular_build_model_provider_config
from engine.claude.model_client import classify_anthropic_sdk_error as modular_classify_anthropic_sdk_error
from engine.claude.model_client import detect_anthropic_sdk_available as modular_detect_anthropic_sdk_available
from engine.claude.model_client import parse_anthropic_response_payload as modular_parse_anthropic_response_payload
from engine.claude.model_client import redact_model_provider_options as modular_redact_model_provider_options
from engine.claude.model_client import summarize_model_client_interaction as modular_summarize_model_client_interaction
from engine.claude.model_client import summarize_model_provider_config as modular_summarize_model_provider_config
from engine.claude.model_client import validate_model_provider_config as modular_validate_model_provider_config
from engine.claude.models import resolve_model_profile as modular_resolve_model_profile
from engine.claude.permissions import build_empty_permission_state as modular_build_empty_permission_state
from engine.claude.permissions import (
    build_permission_state_from_settings_context as modular_build_permission_state_from_settings_context,
)
from engine.claude.settings import (
    load_claude_settings,
    merge_settings,
    runtime_options_from_settings,
    validate_settings_context,
)
from engine.claude.skills import summarize_skill_context as modular_summarize_skill_context
from engine.claude.tools import (
    ClaudeToolExecutor as ModularClaudeToolExecutor,
    summarize_tool_registry as modular_summarize_tool_registry,
)
from engine.claude.types import ClaudeToolCall as ModularClaudeToolCall
from engine.claude.usage import build_usage_accounting as modular_build_usage_accounting
from engine.claude_agent import (
    AgentConfigError,
    AnthropicClaudeModelClient,
    AnthropicSDKTransport,
    ClaudeModelProviderConfig,
    ClaudeModelRequest,
    ClaudeModelResponse,
    ClaudePermissionPolicy,
    CommandSpec,
    ClaudeToolCall,
    ClaudeToolExecutor,
    ClaudeStyleAgentRunner,
    FakeClaudeModelClient,
    ModelProviderConfigurationError,
    ModelProviderTransportError,
    TOOL_REGISTRY,
    ToolSpec,
    ToolPermissionError,
    ToolResultPairingError,
    build_agent_handoff_message,
    build_agent_task_state,
    build_agent_command_specs,
    build_claude_event_envelope,
    build_claude_message_envelope,
    build_claude_transcript_entries,
    build_claude_hook_invocation,
    build_token_budget_state,
    build_empty_permission_state,
    build_permission_state_from_decisions,
    build_permission_state_from_settings_context,
    apply_permission_update,
    build_anthropic_request_payload,
    build_anthropic_sdk_messages_params,
    build_model_client,
    build_model_provider_diagnostics,
    build_model_provider_config,
    build_tool_input_validation,
    build_usage_accounting,
    calculate_usage_cost_usd,
    first_party_name_to_canonical_model,
    estimate_usage_from_messages,
    format_cost_usd,
    filter_model_invocable_commands,
    find_command,
    build_context_state,
    load_claude_agent_definition,
    load_agent_runner,
    load_pipeline_runner,
    model_key_from_canonical,
    model_pricing_for_profile,
    parse_yaml_subset,
    resolve_model_profile,
    resolve_skill_specs,
    resolve_tool_specs,
    classify_anthropic_sdk_error,
    detect_anthropic_sdk_available,
    summarize_claude_transcript_entries,
    summarize_command_context,
    summarize_hook_invocations,
    summarize_handoffs,
    summarize_model_client_interaction,
    summarize_pipeline_skill_context,
    summarize_pipeline_task_states,
    summarize_pipeline_token_budgets,
    summarize_permission_decisions,
    summarize_permission_state,
    summarize_skill_context,
    summarize_tool_registry,
    summarize_usage_accounting,
    summarize_claude_messages,
    update_task_status,
    validate_claude_event_envelope,
    validate_claude_message_envelope,
    validate_claude_transcript_entries,
    replay_permission_decisions,
    parse_anthropic_response_payload,
    redact_model_provider_options,
    execute_slash_command,
    summarize_model_provider_config,
    validate_permission_state,
    validate_model_provider_config,
    validate_tool_call_input,
    validate_tool_input,
    validate_tool_registry,
)


def writable_tmp_dir(prefix: str) -> Path:
    root = PROJECT_ROOT / ".test-tmp" / f"{prefix}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


class ScriptedClaudeModelClient:
    provider = "fake"

    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.requests: list[ClaudeModelRequest] = []

    def complete(self, request: ClaudeModelRequest) -> ClaudeModelResponse:
        self.requests.append(request)
        index = len(self.requests) - 1
        response = self.responses[min(index, len(self.responses) - 1)]
        if isinstance(response, BaseException):
            raise response
        if callable(response):
            return response(request)
        return response


class TestClaudeAgentV0(unittest.TestCase):
    def test_claude_agent_facade_reexports_split_runtime_modules(self) -> None:
        self.assertIs(claude_agent.ClaudeToolCall, ModularClaudeToolCall)
        self.assertIs(claude_agent.ClaudeToolExecutor, ModularClaudeToolExecutor)
        self.assertIs(claude_agent.load_claude_agent_definition, modular_load_claude_agent_definition)
        self.assertIs(claude_agent.build_claude_hook_invocation, modular_build_claude_hook_invocation)
        self.assertIs(claude_agent.build_claude_message_envelope, modular_build_claude_message_envelope)
        self.assertIs(claude_agent.resolve_model_profile, modular_resolve_model_profile)
        self.assertIs(claude_agent.AnthropicClaudeModelClient, ModularAnthropicClaudeModelClient)
        self.assertIs(claude_agent.AnthropicSDKTransport, ModularAnthropicSDKTransport)
        self.assertIs(claude_agent.FakeClaudeModelClient, ModularFakeClaudeModelClient)
        self.assertIs(claude_agent.build_anthropic_request_payload, modular_build_anthropic_request_payload)
        self.assertIs(
            claude_agent.build_anthropic_sdk_messages_params,
            modular_build_anthropic_sdk_messages_params,
        )
        self.assertIs(claude_agent.build_model_client, modular_build_model_client)
        self.assertIs(claude_agent.build_model_provider_diagnostics, modular_build_model_provider_diagnostics)
        self.assertIs(claude_agent.build_model_provider_config, modular_build_model_provider_config)
        self.assertIs(claude_agent.classify_anthropic_sdk_error, modular_classify_anthropic_sdk_error)
        self.assertIs(claude_agent.detect_anthropic_sdk_available, modular_detect_anthropic_sdk_available)
        self.assertIs(claude_agent.parse_anthropic_response_payload, modular_parse_anthropic_response_payload)
        self.assertIs(claude_agent.redact_model_provider_options, modular_redact_model_provider_options)
        self.assertIs(
            claude_agent.summarize_model_client_interaction,
            modular_summarize_model_client_interaction,
        )
        self.assertIs(claude_agent.summarize_model_provider_config, modular_summarize_model_provider_config)
        self.assertIs(claude_agent.validate_model_provider_config, modular_validate_model_provider_config)
        self.assertIs(claude_agent.build_usage_accounting, modular_build_usage_accounting)
        self.assertIs(claude_agent.summarize_tool_registry, modular_summarize_tool_registry)
        self.assertIs(claude_agent.build_empty_permission_state, modular_build_empty_permission_state)
        self.assertIs(
            claude_agent.build_permission_state_from_settings_context,
            modular_build_permission_state_from_settings_context,
        )
        self.assertIs(claude_agent.summarize_skill_context, modular_summarize_skill_context)
        self.assertIs(claude_agent.summarize_command_context, modular_summarize_command_context)
        self.assertIs(claude_agent.execute_slash_command, modular_execute_slash_command)

    def test_model_provider_config_redacts_secrets_and_allows_fake_client_only(self) -> None:
        config = build_model_provider_config(
            {
                "provider": "fake",
                "model": "claude-sonnet-4-6",
                "api_key": "sk-secret-value",
                "api_key_env": "ANTHROPIC_API_KEY",
                "timeout_seconds": 12,
                "max_retries": 3,
            },
            env={"ANTHROPIC_API_KEY": "sk-env-secret"},
        )
        summary = summarize_model_provider_config(config)
        client = build_model_client(config)

        self.assertIsInstance(config, ClaudeModelProviderConfig)
        self.assertIsInstance(client, FakeClaudeModelClient)
        self.assertEqual(summary["schema_version"], "claude_model_provider_config_v0")
        self.assertEqual(summary["provider"], "fake")
        self.assertEqual(summary["model"], "claude-sonnet-4-6")
        self.assertEqual(summary["api_key_env"], "ANTHROPIC_API_KEY")
        self.assertTrue(summary["api_key_present"])
        self.assertFalse(summary["allow_network"])
        self.assertTrue(summary["executable"])
        self.assertTrue(summary["redacted"])
        self.assertTrue(summary["ok"], summary["errors"])
        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertNotIn("sk-secret-value", encoded)
        self.assertNotIn("sk-env-secret", encoded)
        self.assertEqual(summary["options"]["api_key"], "[REDACTED]")
        self.assertEqual(redact_model_provider_options({"bearer_token": "abc"})["bearer_token"], "[REDACTED]")

    def test_model_provider_config_blocks_real_provider_until_sdk_adapter_exists(self) -> None:
        config = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "allow_network": True,
            },
            env={"ANTHROPIC_API_KEY": "sk-env-secret"},
        )
        errors = validate_model_provider_config(config)
        summary = summarize_model_provider_config(config)

        self.assertIn("provider_not_executable:anthropic", errors)
        self.assertFalse(summary["ok"])
        self.assertFalse(summary["executable"])
        self.assertTrue(summary["api_key_present"])
        self.assertTrue(summary["allow_network"])
        with self.assertRaises(ModelProviderConfigurationError):
            build_model_client(config)

    def test_anthropic_adapter_requires_injected_non_network_transport(self) -> None:
        class NetworkTransport:
            network_enabled = True

            def complete(self, payload: dict[str, object], config: ClaudeModelProviderConfig) -> dict[str, object]:
                return {}

        config = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model": "claude-sonnet-4-6",
            },
            env={"ANTHROPIC_API_KEY": "sk-env-secret"},
        )
        summary = summarize_model_provider_config(config)

        self.assertFalse(summary["ok"])
        self.assertTrue(summary["adapter_available"])
        self.assertFalse(summary["executable"])
        self.assertEqual(summary["adapter"], "anthropic_messages_v0")
        self.assertFalse(summary["network_execution_enabled"])
        with self.assertRaises(ModelProviderConfigurationError) as missing_transport:
            build_model_client(config, enable_experimental_adapters=True)
        with self.assertRaises(ModelProviderConfigurationError) as network_transport:
            build_model_client(
                config,
                enable_experimental_adapters=True,
                transports={"anthropic": NetworkTransport()},
            )

        self.assertIn("anthropic_transport_missing", str(missing_transport.exception))
        self.assertIn("anthropic_network_transport_blocked", str(network_transport.exception))

    def test_anthropic_adapter_maps_mock_transport_response_without_secrets(self) -> None:
        class MockTransport:
            network_enabled = False

            def __init__(self) -> None:
                self.payload: dict[str, object] = {}

            def complete(self, payload: dict[str, object], config: ClaudeModelProviderConfig) -> dict[str, object]:
                self.payload = payload
                return {
                    "id": "msg_mock_001",
                    "model": "claude-sonnet-4-6",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "Reponse simulee du provider Anthropic."}],
                    "usage": {"input_tokens": 17, "output_tokens": 9},
                }

        transport = MockTransport()
        config = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key": "sk-not-in-payload",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model": "claude-sonnet-4-6",
            },
            env={"ANTHROPIC_API_KEY": "sk-env-secret"},
        )
        request = ClaudeModelRequest(
            agent_type="data-facts",
            model="claude-sonnet-4-6",
            system_prompt=["Systeme data facts"],
            messages=[{"role": "user", "content": "Evaluer le dossier synthetique."}],
            context={"case_id": "CASE-001"},
            tools=["read_case_file"],
            skills=["eval_immo_collecte_faits"],
            expected_outputs=["data_facts.json"],
            runtime_mode="claude_live_data_facts_v0",
        )
        expected_payload = build_anthropic_request_payload(request)
        client = build_model_client(
            config,
            enable_experimental_adapters=True,
            transports={"anthropic": transport},
        )
        response = client.complete(request)
        parsed = parse_anthropic_response_payload(request, response.as_dict())
        summary = summarize_model_client_interaction(request=request, response=response, enabled=True)
        encoded_payload = json.dumps(transport.payload, ensure_ascii=False)

        self.assertIsInstance(client, AnthropicClaudeModelClient)
        self.assertIsInstance(response, ClaudeModelResponse)
        self.assertEqual(transport.payload, expected_payload)
        self.assertEqual(transport.payload["schema_version"], "anthropic_messages_request_v0")
        self.assertEqual(transport.payload["metadata"]["agent_type"], "data-facts")
        self.assertEqual(transport.payload["metadata"]["runtime_mode"], "claude_live_data_facts_v0")
        self.assertEqual(response.provider, "anthropic")
        self.assertEqual(response.raw_response_id, "msg_mock_001")
        self.assertEqual(response.usage["input_tokens"], 17)
        self.assertEqual(response.usage["output_tokens"], 9)
        self.assertTrue(summary["ok"], summary["errors"])
        self.assertEqual(parsed.provider, "anthropic")
        self.assertNotIn("sk-not-in-payload", encoded_payload)
        self.assertNotIn("sk-env-secret", encoded_payload)

    def test_anthropic_sdk_detection_and_transport_guardrails(self) -> None:
        self.assertIsInstance(detect_anthropic_sdk_available(), bool)

        env = {"ANTHROPIC_API_KEY": "sk-env-secret"}
        config_missing_sdk = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "allow_network": True,
                "enable_sdk_execution": True,
            },
            env=env,
            sdk_available=False,
        )
        summary = summarize_model_provider_config(config_missing_sdk)

        self.assertEqual(summary["sdk"]["transport"], "anthropic_sdk_transport_v0")
        self.assertFalse(summary["sdk"]["available"])
        self.assertFalse(summary["network_execution_enabled"])
        self.assertIn("provider_not_executable:anthropic", summary["errors"])
        with self.assertRaises(ModelProviderConfigurationError) as missing_sdk:
            build_model_client(
                config_missing_sdk,
                enable_experimental_adapters=True,
                enable_sdk_execution=True,
                sdk_factory=lambda **kwargs: object(),
                env=env,
            )

        self.assertIn("anthropic_sdk_missing", str(missing_sdk.exception))

        config_no_network = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "enable_sdk_execution": True,
            },
            env=env,
            sdk_available=True,
        )
        config_no_sdk_flag = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "allow_network": True,
            },
            env=env,
            sdk_available=True,
        )
        config_no_env_key = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "allow_network": True,
                "enable_sdk_execution": True,
            },
            env={},
            sdk_available=True,
        )

        with self.assertRaises(ModelProviderConfigurationError) as missing_network:
            AnthropicSDKTransport(
                config_no_network,
                sdk_factory=lambda **kwargs: object(),
                env=env,
            )
        with self.assertRaises(ModelProviderConfigurationError) as missing_flag:
            AnthropicSDKTransport(
                config_no_sdk_flag,
                sdk_factory=lambda **kwargs: object(),
                env=env,
            )
        with self.assertRaises(ModelProviderConfigurationError) as missing_key:
            AnthropicSDKTransport(
                config_no_env_key,
                sdk_factory=lambda **kwargs: object(),
                env={},
            )

        self.assertIn("network_not_enabled", str(missing_network.exception))
        self.assertIn("sdk_execution_not_enabled", str(missing_flag.exception))
        self.assertIn("api_key_missing:ANTHROPIC_API_KEY", str(missing_key.exception))

    def test_model_provider_diagnostics_reports_guardrails_without_constructing_client(self) -> None:
        diagnostics = build_model_provider_diagnostics(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model": "claude-sonnet-4-6",
                "allow_network": True,
                "enable_sdk_execution": True,
            },
            env={"ANTHROPIC_API_KEY": "sk-env-secret"},
            sdk_available=True,
        )

        self.assertEqual(diagnostics["schema_version"], "claude_model_provider_diagnostics_v0")
        self.assertEqual(diagnostics["provider"], "anthropic")
        self.assertFalse(diagnostics["default_runtime"]["ready"])
        self.assertTrue(diagnostics["sdk_transport"]["ready"])
        self.assertFalse(diagnostics["api_runtime"]["ready"])
        self.assertFalse(diagnostics["sdk_transport"]["client_constructed"])
        self.assertFalse(diagnostics["api_runtime"]["client_constructed"])
        self.assertIn("provider_not_executable:anthropic", diagnostics["default_runtime"]["errors"])
        self.assertIn("operator_runtime_enabled", diagnostics["missing_guardrails"])
        self.assertEqual(
            diagnostics["api_runtime"]["operator_env_flag"],
            "EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME",
        )
        encoded = json.dumps(diagnostics, ensure_ascii=False)
        self.assertNotIn("sk-env-secret", encoded)

        ready_diagnostics = build_model_provider_diagnostics(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model": "claude-sonnet-4-6",
                "allow_network": True,
                "enable_sdk_execution": True,
            },
            env={
                "ANTHROPIC_API_KEY": "sk-env-secret",
                "EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME": "true",
            },
            sdk_available=True,
        )
        self.assertTrue(ready_diagnostics["sdk_transport"]["ready"])
        self.assertTrue(ready_diagnostics["api_runtime"]["ready"])
        self.assertNotIn("operator_runtime_enabled", ready_diagnostics["missing_guardrails"])

    def test_anthropic_sdk_transport_uses_mock_sdk_without_persisting_secrets(self) -> None:
        env = {"ANTHROPIC_API_KEY": "sk-env-secret"}
        sdk_instances: list[object] = []

        class MockSDKResponse:
            def model_dump(self) -> dict[str, object]:
                return {
                    "id": "msg_sdk_mock_001",
                    "model": "claude-sonnet-4-6",
                    "stop_reason": "end_turn",
                    "content": [{"type": "text", "text": "Reponse SDK simulee."}],
                    "usage": {"input_tokens": 21, "output_tokens": 7},
                }

        class MockMessages:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def create(self, **params: object) -> MockSDKResponse:
                self.calls.append(dict(params))
                return MockSDKResponse()

        class MockAnthropicSDK:
            def __init__(self, **kwargs: object) -> None:
                self.kwargs = dict(kwargs)
                self.messages = MockMessages()
                sdk_instances.append(self)

        config = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model": "claude-sonnet-4-6",
                "allow_network": True,
                "enable_sdk_execution": True,
                "timeout_seconds": 7,
                "max_retries": 4,
                "max_tokens": 1234,
            },
            env=env,
            sdk_available=True,
        )
        request = ClaudeModelRequest(
            agent_type="valuation-draft",
            model="claude-sonnet-4-6",
            system_prompt=["Systeme valuation"],
            messages=[{"role": "user", "content": "Produire une valeur."}],
            context={"case_id": "CASE-SDK-001"},
            tools=["write_artifact"],
            skills=["eval_immo_valorisation"],
            expected_outputs=["valuation-draft.brouillon_valeur.md"],
            runtime_mode="claude_live_valuation_draft_v0",
        )
        expected_params = build_anthropic_sdk_messages_params(
            build_anthropic_request_payload(request),
            config,
        )
        client = build_model_client(
            config,
            enable_experimental_adapters=True,
            enable_sdk_execution=True,
            sdk_factory=MockAnthropicSDK,
            env=env,
        )
        response = client.complete(request)
        summary = summarize_model_provider_config(config)
        sdk = sdk_instances[0]
        sdk_call = sdk.messages.calls[0]

        self.assertIsInstance(client, AnthropicClaudeModelClient)
        self.assertIsInstance(response, ClaudeModelResponse)
        self.assertEqual(sdk.kwargs["api_key"], "sk-env-secret")
        self.assertEqual(sdk.kwargs["timeout"], 7)
        self.assertEqual(sdk.kwargs["max_retries"], 4)
        self.assertEqual(sdk_call, expected_params)
        self.assertEqual(sdk_call["max_tokens"], 1234)
        self.assertNotIn("schema_version", sdk_call)
        self.assertNotIn("metadata", sdk_call)
        self.assertEqual(response.provider, "anthropic")
        self.assertEqual(response.raw_response_id, "msg_sdk_mock_001")
        self.assertEqual(response.usage["input_tokens"], 21)
        self.assertEqual(response.usage["output_tokens"], 7)
        self.assertFalse(summary["ok"])
        self.assertTrue(summary["network_execution_enabled"])
        self.assertTrue(summary["sdk_execution_enabled"])
        encoded_summary = json.dumps(summary, ensure_ascii=False)
        encoded_call = json.dumps(sdk_call, ensure_ascii=False)
        self.assertNotIn("sk-env-secret", encoded_summary)
        self.assertNotIn("sk-env-secret", encoded_call)

    def test_anthropic_sdk_transport_classifies_retryable_and_permanent_errors(self) -> None:
        class MockStatusError(Exception):
            def __init__(self, status_code: int) -> None:
                super().__init__(f"status={status_code}")
                self.status_code = status_code

        timeout_error = classify_anthropic_sdk_error(TimeoutError("timed out"), attempts=3)
        rate_limit_error = classify_anthropic_sdk_error(MockStatusError(429), attempts=2)
        auth_error = classify_anthropic_sdk_error(MockStatusError(401), attempts=1)

        self.assertEqual(timeout_error.code, "anthropic_sdk_timeout")
        self.assertTrue(timeout_error.retryable)
        self.assertEqual(rate_limit_error.code, "anthropic_sdk_retryable")
        self.assertTrue(rate_limit_error.retryable)
        self.assertEqual(auth_error.code, "anthropic_sdk_auth_error")
        self.assertFalse(auth_error.retryable)

        class FailingMessages:
            def create(self, **params: object) -> object:
                raise MockStatusError(529)

        class FailingAnthropicSDK:
            def __init__(self, **kwargs: object) -> None:
                self.messages = FailingMessages()

        env = {"ANTHROPIC_API_KEY": "sk-env-secret"}
        config = build_model_provider_config(
            {
                "provider": "anthropic",
                "api_key_env": "ANTHROPIC_API_KEY",
                "model": "claude-sonnet-4-6",
                "allow_network": True,
                "enable_sdk_execution": True,
                "max_retries": 3,
            },
            env=env,
            sdk_available=True,
        )
        request = ClaudeModelRequest(
            agent_type="data-facts",
            model="claude-sonnet-4-6",
            system_prompt=["Systeme"],
            messages=[{"role": "user", "content": "Dossier."}],
            context={},
            tools=[],
            skills=[],
            expected_outputs=["data-facts.fiche_bien.json"],
        )
        transport = AnthropicSDKTransport(
            config,
            sdk_factory=FailingAnthropicSDK,
            env=env,
        )

        with self.assertRaises(ModelProviderTransportError) as raised:
            transport.complete(build_anthropic_request_payload(request), config)

        self.assertEqual(raised.exception.code, "anthropic_sdk_server_error")
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(raised.exception.attempts, 4)
        self.assertEqual(raised.exception.as_dict()["provider"], "anthropic")

    def test_model_profile_resolves_claude_code_model_configs(self) -> None:
        profile = resolve_model_profile("claude-sonnet-4-6")

        self.assertEqual(first_party_name_to_canonical_model("claude-sonnet-4-6"), "claude-sonnet-4-6")
        self.assertEqual(model_key_from_canonical("claude-sonnet-4-6"), "sonnet46")
        self.assertEqual(profile.canonical_model, "claude-sonnet-4-6")
        self.assertEqual(profile.model_key, "sonnet46")
        self.assertEqual(profile.family, "sonnet")
        self.assertEqual(profile.provider_ids["firstParty"], "claude-sonnet-4-6")
        self.assertEqual(profile.context_window_tokens, 200000)
        self.assertGreaterEqual(profile.max_output_tokens, 10000)
        self.assertTrue(profile.supports_thinking)

        long_profile = resolve_model_profile("claude-opus-4-6[1m]")
        self.assertEqual(long_profile.canonical_model, "claude-opus-4-6")
        self.assertEqual(long_profile.context_window_tokens, 1000000)
        self.assertTrue(long_profile.supports_long_context)

    def test_token_budget_state_tracks_model_window_and_agent_budget(self) -> None:
        profile = resolve_model_profile("claude-sonnet-4-6")
        budget = build_token_budget_state(
            agent_type="data-facts",
            model_profile=profile,
            budgets=claude_agent.ClaudeAgentBudget(max_tokens=8192, max_total_tokens=25000, window_size=8),
            estimated_tokens=1200,
        )

        self.assertEqual(budget["schema_version"], "claude_token_budget_v0")
        self.assertEqual(budget["canonical_model"], "claude-sonnet-4-6")
        self.assertEqual(budget["estimated_tokens"], 1200)
        self.assertEqual(budget["remaining_total_tokens"], 23800)
        self.assertEqual(budget["remaining_context_tokens"], 198800)
        self.assertEqual(budget["warnings_count"], 0)
        self.assertTrue(budget["ok"])

        summary = summarize_pipeline_token_budgets({"data-facts": budget})
        self.assertEqual(summary["schema_version"], "claude_pipeline_token_budget_v0")
        self.assertEqual(summary["estimated_tokens"], 1200)
        self.assertEqual(summary["models"], ["claude-sonnet-4-6"])
        self.assertTrue(summary["ok"])

    def test_usage_accounting_calculates_sonnet_cost_from_message_tokens(self) -> None:
        profile = resolve_model_profile("claude-sonnet-4-6")
        messages = [
            build_claude_message_envelope(
                role="system",
                agent_type="data-facts",
                content=["System contract for data extraction."],
                sequence=1,
            ),
            build_claude_message_envelope(
                role="assistant",
                agent_type="data-facts",
                content=[
                    {
                        "type": "tool_use",
                        "id": "call-1",
                        "name": "read_file",
                        "input": {"path": "fixtures/case_nominal.json"},
                    }
                ],
                sequence=2,
            ),
            build_claude_message_envelope(
                role="user",
                agent_type="data-facts",
                content=[
                    {
                        "type": "tool_result",
                        "tool_use_id": "call-1",
                        "name": "read_file",
                        "ok": True,
                        "content": {"address": "123 rue Example", "price": 425000},
                    }
                ],
                sequence=3,
            ),
        ]
        pricing = model_pricing_for_profile(profile)
        usage = estimate_usage_from_messages(messages)
        token_budget = build_token_budget_state(
            agent_type="data-facts",
            model_profile=profile,
            budgets=claude_agent.ClaudeAgentBudget(max_tokens=8192, max_total_tokens=25000, window_size=8),
            messages=messages,
        )
        accounting = build_usage_accounting(
            agent_type="data-facts",
            model_profile=profile,
            messages=messages,
            token_budget=token_budget,
            wall_clock_seconds=0.25,
            tool_use_count=1,
        )
        summary = summarize_usage_accounting({"data-facts": accounting}, wall_clock_seconds=0.25)

        self.assertEqual(pricing["schema_version"], "claude_model_pricing_v0")
        self.assertEqual(pricing["input_tokens"], 3.0)
        self.assertEqual(pricing["output_tokens"], 15.0)
        self.assertGreater(usage["input_tokens"], 0)
        self.assertGreater(usage["output_tokens"], 0)
        self.assertEqual(accounting["schema_version"], "claude_usage_accounting_v0")
        self.assertEqual(accounting["pricing"]["input_tokens"], 3.0)
        self.assertEqual(accounting["cost_usd"], calculate_usage_cost_usd(pricing, usage))
        self.assertTrue(format_cost_usd(accounting["cost_usd"]).startswith("$"))
        self.assertTrue(accounting["ok"])
        self.assertEqual(summary["schema_version"], "claude_usage_summary_v0")
        self.assertEqual(summary["total_cost_usd"], accounting["cost_usd"])
        self.assertEqual(summary["model_usage"]["claude-sonnet-4-6"]["cost_usd"], accounting["cost_usd"])
        self.assertTrue(summary["ok"])

    def test_message_and_event_envelopes_are_validated(self) -> None:
        message = build_claude_message_envelope(
            role="assistant",
            agent_type="data-facts",
            content=[{"type": "tool_use", "id": "call-1", "name": "read_file", "input": {}}],
            sequence=1,
        )
        event = build_claude_event_envelope(
            "tool_start",
            agent_type="data-facts",
            sequence=1,
            payload={"tool": "read_file", "tool_call_id": "call-1"},
        )

        self.assertEqual(message["schema_version"], "claude_message_envelope_v0")
        self.assertEqual(message["content_block_types"], ["tool_use"])
        self.assertEqual(validate_claude_message_envelope(message, expected_sequence=1), [])
        self.assertEqual(event["schema_version"], "claude_runtime_event_v0")
        self.assertEqual(event["kind"], "runtime_event")
        self.assertEqual(validate_claude_event_envelope(event, expected_sequence=1), [])

        invalid_message = dict(message)
        invalid_message["role"] = "developer"
        self.assertIn("message_role_invalid", validate_claude_message_envelope(invalid_message, expected_sequence=1))

    def test_tool_executor_enforces_agent_allowed_tools(self) -> None:
        root = writable_tmp_dir("claude_tool_permission")
        try:
            executor = ClaudeToolExecutor(["read_file"], root)

            with self.assertRaises(ToolPermissionError):
                executor.execute(
                    ClaudeToolCall(
                        id="call-1",
                        name="write_file",
                        input={"path": "x.json", "content": {"x": 1}},
                        agent_type="data-facts",
                    )
                )
            self.assertEqual(len(executor.permission_decisions), 1)
            self.assertFalse(executor.permission_decisions[0]["allowed"])
            self.assertEqual(executor.permission_decisions[0]["reason"], "tool_not_allowed_for_agent")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_tool_registry_exports_strict_model_facing_schemas(self) -> None:
        errors = validate_tool_registry()
        summary = summarize_tool_registry(["read_file", "write_file", "run_calculation"])

        self.assertEqual(errors, [])
        self.assertEqual(summary["schema_version"], "claude_tool_registry_summary_v0")
        self.assertEqual(summary["tool_names"], ["read_file", "write_file", "run_calculation"])
        self.assertEqual(summary["strict_tools_count"], 3)
        self.assertEqual(summary["destructive_tools"], ["write_file"])
        self.assertIn("runtime_execute", summary["permissions"])
        model_schema = summary["model_facing_tools"][0]
        self.assertEqual(model_schema["name"], "read_file")
        self.assertTrue(model_schema["strict"])
        self.assertEqual(model_schema["input_schema"]["required"], ["path"])
        self.assertFalse(model_schema["input_schema"]["additionalProperties"])
        self.assertTrue(summary["ok"])

    def test_tool_executor_validates_inputs_before_calling_tools(self) -> None:
        root = writable_tmp_dir("claude_tool_schema")
        try:
            executor = ClaudeToolExecutor(["write_file", "run_calculation"], root)
            invalid_write = ClaudeToolCall(
                id="write-invalid",
                name="write_file",
                input={"path": "artifact.json", "content": "not an object"},
                agent_type="data-facts",
            )
            validation = build_tool_input_validation(invalid_write)
            self.assertFalse(validation["ok"])
            self.assertEqual(validate_tool_call_input(invalid_write), ["type_mismatch:content:expected_object"])
            self.assertEqual(
                validate_tool_input(
                    "run_calculation",
                    {"method": "mean", "values": [1, "bad"]},
                ),
                ["type_mismatch:values[1]:expected_number"],
            )

            result = executor.execute(invalid_write)
            self.assertFalse(result.ok)
            self.assertIn("ToolInputValidationError", result.error)
            self.assertEqual(result.output["schema_version"], "claude_tool_input_validation_v0")
            self.assertEqual(result.output["errors"], ["type_mismatch:content:expected_object"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_permission_policy_supports_plan_and_bypass_modes(self) -> None:
        write_call = ClaudeToolCall(
            id="call-write",
            name="write_file",
            input={"path": "x.json", "content": {"x": 1}},
            agent_type="data-facts",
        )
        plan_policy = ClaudePermissionPolicy(["write_file"], mode=ClaudePermissionPolicy.PLAN)
        plan_decision = plan_policy.decide(write_call)
        self.assertFalse(plan_decision.allowed)
        self.assertEqual(plan_decision.reason, "plan_mode_requires_approval")

        bypass_policy = ClaudePermissionPolicy([], mode=ClaudePermissionPolicy.BYPASS)
        bypass_decision = bypass_policy.decide(write_call)
        self.assertTrue(bypass_decision.allowed)
        self.assertEqual(bypass_decision.reason, "bypass_permissions")

        summary = summarize_permission_decisions(
            [plan_decision.as_dict(), bypass_decision.as_dict()],
            agent_type="data-facts",
        )
        self.assertEqual(summary["decisions_count"], 2)
        self.assertEqual(summary["allowed_count"], 1)
        self.assertEqual(summary["denied_count"], 1)
        self.assertFalse(summary["ok"])

    def test_permission_state_applies_rules_and_replays_decisions(self) -> None:
        write_call = ClaudeToolCall(
            id="call-write",
            name="write_file",
            input={"path": "artifact.json", "content": {"x": 1}},
            agent_type="data-facts",
        )
        read_call = ClaudeToolCall(
            id="call-read",
            name="read_file",
            input={"path": "artifact.json"},
            agent_type="data-facts",
        )
        state = build_empty_permission_state(
            agent_type="data-facts",
            mode=ClaudePermissionPolicy.PLAN,
            allowed_tools=["write_file", "read_file"],
        )
        state = apply_permission_update(
            state,
            {
                "type": "addRules",
                "destination": "session",
                "behavior": "allow",
                "rules": [{"toolName": "write_file"}],
            },
        )
        state = apply_permission_update(
            state,
            {
                "type": "addRules",
                "destination": "session",
                "behavior": "deny",
                "rules": [{"toolName": "read_file"}],
            },
        )
        policy = ClaudePermissionPolicy(
            ["write_file", "read_file"],
            mode=ClaudePermissionPolicy.PLAN,
            permission_state=state,
        )
        write_decision = policy.decide(write_call)
        read_decision = policy.decide(read_call)
        built_state = build_permission_state_from_decisions(
            [write_decision.as_dict(), read_decision.as_dict()],
            agent_type="data-facts",
            mode=ClaudePermissionPolicy.PLAN,
            allowed_tools=["write_file", "read_file"],
        )
        replay = replay_permission_decisions(
            built_state,
            [write_decision.as_dict(), read_decision.as_dict()],
            allowed_tools=["write_file", "read_file"],
        )
        state_summary = summarize_permission_state(built_state)

        self.assertTrue(write_decision.allowed)
        self.assertEqual(write_decision.reason, "permission_state_allow_rule")
        self.assertFalse(read_decision.allowed)
        self.assertEqual(read_decision.reason, "permission_state_deny_rule")
        self.assertEqual(validate_permission_state(built_state), [])
        self.assertEqual(state_summary["allow_rules_count"], 1)
        self.assertEqual(state_summary["deny_rules_count"], 1)
        self.assertTrue(replay["ok"])
        self.assertEqual(replay["matched_count"], 2)

    def test_tool_executor_writes_reads_and_lists_case_files(self) -> None:
        root = writable_tmp_dir("claude_tool_io")
        try:
            executor = ClaudeToolExecutor(["write_file", "read_file", "list_files"], root)

            write_result = executor.execute(
                ClaudeToolCall(
                    id="write-1",
                    name="write_file",
                    input={"path": "artifact.json", "content": {"value": 42}},
                    agent_type="data-facts",
                )
            )
            self.assertTrue(write_result.ok, write_result.error)

            read_result = executor.execute(
                ClaudeToolCall(
                    id="read-1",
                    name="read_file",
                    input={"path": "artifact.json"},
                    agent_type="data-facts",
                )
            )
            self.assertTrue(read_result.ok, read_result.error)
            self.assertIn('"value": 42', read_result.output["content"])

            list_result = executor.execute(
                ClaudeToolCall(id="list-1", name="list_files", input={}, agent_type="data-facts")
            )
            self.assertEqual(list_result.output["files"], ["artifact.json"])
            self.assertEqual(len(executor.permission_decisions), 3)
            self.assertTrue(all(decision["allowed"] for decision in executor.permission_decisions))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_conversation_state_detects_unpaired_tool_results(self) -> None:
        messages = [
            {
                "role": "user",
                "agent_type": "data-facts",
                "content": [{"type": "tool_result", "tool_use_id": "missing-call", "name": "read_file", "ok": True}],
            }
        ]

        state = summarize_claude_messages(
            messages,
            agent_type="data-facts",
            strict_tool_result_pairing=False,
        )

        self.assertFalse(state["ok"])
        self.assertEqual(state["orphan_tool_result_ids"], ["missing-call"])
        with self.assertRaises(ToolResultPairingError):
            summarize_claude_messages(messages, agent_type="data-facts")

    def test_context_state_preserves_recent_tool_results_when_compaction_needed(self) -> None:
        messages = []
        for index in range(5):
            messages.append(
                {
                    "role": "assistant",
                    "agent_type": "data-facts",
                    "content": [{"type": "tool_use", "id": f"call-{index}", "name": "read_file", "input": {}}],
                }
            )
            messages.append(
                {
                    "role": "user",
                    "agent_type": "data-facts",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": f"call-{index}",
                            "name": "read_file",
                            "ok": True,
                            "output": {"text": "x" * 200},
                        }
                    ],
                }
            )

        state = build_context_state(
            messages,
            agent_type="data-facts",
            threshold_tokens=1,
            preserve_recent_tool_results=2,
        )

        self.assertTrue(state["needs_compaction"])
        self.assertGreater(state["estimated_tokens"], 1)
        self.assertEqual(state["preserved_tool_result_ids"], ["call-3", "call-4"])
        self.assertEqual(state["dropped_tool_result_ids"], ["call-0", "call-1", "call-2"])

    def test_agent_task_state_tracks_artifact_progress(self) -> None:
        state = build_agent_task_state("data-facts", ["fiche_bien.json", "timeline_faits.json"])

        self.assertEqual(state["tasks_count"], 2)
        self.assertEqual(state["pending_count"], 2)
        self.assertFalse(state["ok"])

        update_task_status(state, "fiche_bien.json", "in_progress")
        self.assertEqual(state["current_task_id"], "data-facts:fiche_bien.json")
        self.assertEqual(state["in_progress_count"], 1)

        update_task_status(state, "fiche_bien.json", "completed")
        update_task_status(state, "timeline_faits.json", "completed")
        self.assertEqual(state["completed_count"], 2)
        self.assertTrue(state["ok"])

        summary = summarize_pipeline_task_states({"data-facts": state})
        self.assertEqual(summary["tasks_count"], 2)
        self.assertEqual(summary["completed_count"], 2)
        self.assertTrue(summary["ok"])

    def test_handoff_summary_tracks_artifacts_and_blockers(self) -> None:
        result = {
            "status": "OK",
            "artifact_dir": "out/case",
            "events": [
                {
                    "event": "artifact_written",
                    "artifact": "fiche_bien.json",
                    "path": "out/case/data-facts.fiche_bien.json",
                }
            ],
            "blocking_failures": [],
            "warnings": ["warning-a"],
            "task_state": {
                "tasks_count": 1,
                "completed_count": 1,
                "blocked_count": 0,
                "ok": True,
            },
            "permission_summary": {"ok": True, "decisions_count": 1},
            "context_state": {"estimated_tokens": 12, "needs_compaction": False},
        }

        handoff = build_agent_handoff_message("data-facts", "comps-market", result)
        summary = summarize_handoffs([handoff], agent_type="comps-market")

        self.assertEqual(handoff["schema_version"], "claude_agent_handoff_v0")
        self.assertEqual(handoff["from_agent"], "data-facts")
        self.assertEqual(handoff["to_agent"], "comps-market")
        self.assertEqual(handoff["artifacts_count"], 1)
        self.assertEqual(handoff["artifacts"][0]["artifact"], "fiche_bien.json")
        self.assertEqual(handoff["task_summary"]["completed_count"], 1)
        self.assertEqual(summary["handoffs_count"], 1)
        self.assertEqual(summary["from_agents"], ["data-facts"])
        self.assertEqual(summary["to_agents"], ["comps-market"])
        self.assertEqual(summary["warning_count"], 1)
        self.assertTrue(summary["ok"])

    def test_claude_transcript_entries_summarize_message_blocks(self) -> None:
        messages = [
            {
                "role": "system",
                "agent_type": "data-facts",
                "content": ["system prompt"],
            },
            {
                "role": "assistant",
                "agent_type": "data-facts",
                "content": [{"type": "tool_use", "id": "call-1", "name": "read_file", "input": {}}],
            },
            {
                "role": "user",
                "agent_type": "data-facts",
                "content": [{"type": "tool_result", "tool_use_id": "call-1", "name": "read_file", "ok": True}],
            },
            {
                "role": "user",
                "agent_type": "data-facts",
                "content": [{"type": "handoff", "handoffs": []}],
            },
        ]

        entries = build_claude_transcript_entries(
            messages,
            agent_type="data-facts",
            session_id="session-1",
            run_id="run-1",
        )
        summary = summarize_claude_transcript_entries(entries, agent_type="data-facts", path="transcript.jsonl")

        self.assertEqual(entries[0]["schema_version"], "claude_transcript_entry_v0")
        self.assertEqual(entries[0]["sequence"], 1)
        self.assertEqual(entries[0]["session_id"], "session-1")
        self.assertEqual(entries[0]["message_schema_version"], "claude_message_envelope_v0")
        self.assertEqual(entries[0]["message_sequence"], 1)
        self.assertEqual(summary["entries_count"], 4)
        self.assertEqual(summary["tool_use_count"], 1)
        self.assertEqual(summary["tool_result_count"], 1)
        self.assertEqual(summary["handoff_messages_count"], 1)
        self.assertTrue(summary["validation"]["ok"])
        self.assertTrue(summary["ok"])

    def test_claude_transcript_validation_detects_schema_and_sequence_drift(self) -> None:
        entries = build_claude_transcript_entries(
            [
                {
                    "role": "assistant",
                    "agent_type": "data-facts",
                    "content": [{"type": "tool_use", "id": "call-1", "name": "read_file", "input": {}}],
                }
            ],
            agent_type="data-facts",
            session_id="session-1",
            run_id="run-1",
        )
        self.assertTrue(
            validate_claude_transcript_entries(
                entries,
                agent_type="data-facts",
                session_id="session-1",
                run_id="run-1",
            )["ok"]
        )

        drifted = [dict(entries[0])]
        drifted[0]["sequence"] = 2
        drifted[0]["message_schema_version"] = "legacy"
        validation = validate_claude_transcript_entries(
            drifted,
            agent_type="data-facts",
            session_id="session-1",
            run_id="run-1",
        )

        self.assertFalse(validation["ok"])
        self.assertIn("sequence_invalid:1", validation["errors"])
        self.assertIn("message_schema_invalid:1", validation["errors"])

    def test_hook_invocation_summary_counts_claude_code_events(self) -> None:
        invocations = [
            build_claude_hook_invocation(
                "SessionStart",
                agent_type="data-facts",
                payload={"source": "runtime"},
                sequence=1,
            ),
            build_claude_hook_invocation(
                "PreToolUse",
                agent_type="data-facts",
                payload={"tool_name": "write_file", "tool_use_id": "call-1"},
                sequence=2,
            ),
            build_claude_hook_invocation(
                "PostToolUse",
                agent_type="data-facts",
                payload={"tool_name": "write_file", "tool_use_id": "call-1"},
                sequence=3,
            ),
        ]

        summary = summarize_hook_invocations(invocations, agent_type="data-facts")

        self.assertEqual(invocations[0]["schema_version"], "claude_hook_invocation_v0")
        self.assertEqual(summary["schema_version"], "claude_hook_summary_v0")
        self.assertEqual(summary["invocations_count"], 3)
        self.assertEqual(summary["hook_events"]["SessionStart"], 1)
        self.assertEqual(summary["hook_events"]["PreToolUse"], 1)
        self.assertEqual(summary["hook_events"]["PostToolUse"], 1)
        self.assertEqual(summary["agents"], ["data-facts"])
        self.assertTrue(summary["ok"])

    def test_data_facts_agent_config_loads_as_claude_style_definition(self) -> None:
        config_path = PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml"

        definition = load_claude_agent_definition(config_path, project_root=PROJECT_ROOT)

        self.assertEqual(definition.agent_type, "data-facts")
        self.assertEqual(definition.model, "claude-sonnet-4-6")
        self.assertEqual(definition.model_profile.canonical_model, "claude-sonnet-4-6")
        self.assertEqual(definition.model_profile.model_key, "sonnet46")
        self.assertEqual(definition.max_turns, 12)
        self.assertIn("read_file", definition.tools)
        self.assertIn("write_file", definition.tools)
        self.assertIn("analyse-extraction-faits", definition.skills)
        self.assertEqual(
            definition.outputs,
            ["fiche_bien.json", "timeline_faits.json", "source_index.json"],
        )
        self.assertTrue(definition.human_validation["required"])

    def test_data_facts_resolves_allowed_tools_and_project_skills(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )

        tools = resolve_tool_specs(definition)
        skills = resolve_skill_specs(definition, project_root=PROJECT_ROOT)

        self.assertEqual([tool.name for tool in tools], definition.tools)
        self.assertTrue(all(tool.permission.startswith("runtime_") for tool in tools))
        self.assertEqual(definition.tool_registry_summary["schema_version"], "claude_tool_registry_summary_v0")
        self.assertEqual(definition.tool_registry_summary["tool_names"], definition.tools)
        self.assertTrue(definition.tool_registry_summary["ok"])
        self.assertEqual(definition.skill_context["schema_version"], "claude_skill_context_v0")
        self.assertEqual(definition.skill_context["skills_count"], len(definition.skills))
        self.assertEqual(definition.skill_context["loaded_from"], ["skills"])
        self.assertEqual(definition.skill_context["plugins_count"], 0)
        self.assertTrue(definition.skill_context["ok"])
        self.assertEqual(definition.command_context["schema_version"], "claude_command_context_v0")
        self.assertGreater(definition.command_context["commands_count"], len(definition.skills))
        self.assertIn("compact", definition.command_context["command_names"])
        self.assertIn("analyse-extraction-faits", definition.command_context["model_invocable_command_names"])
        self.assertEqual(
            definition.command_context["model_invocable_commands_count"],
            len(definition.skills),
        )
        self.assertTrue(definition.command_context["ok"])
        self.assertEqual([skill.name for skill in skills], definition.skills)
        self.assertTrue(all(skill.path.startswith("skills/") for skill in skills))
        self.assertTrue(all(skill.loaded_from == "skills" for skill in skills))
        self.assertTrue(all(skill.source == "projectSettings" for skill in skills))
        self.assertTrue(all(skill.content_length > 0 for skill in skills))

    def test_project_skills_load_with_claude_style_metadata(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        skills = resolve_skill_specs(definition, project_root=PROJECT_ROOT)

        context = summarize_skill_context(skills, agent_type="data-facts")
        extraction = next(skill for skill in skills if skill.name == "analyse-extraction-faits")

        self.assertEqual(context["schema_version"], "claude_skill_context_v0")
        self.assertEqual(context["agent_type"], "data-facts")
        self.assertEqual(context["skills_count"], len(definition.skills))
        self.assertIn("analyse-extraction-faits", context["skill_names"])
        self.assertEqual(context["loaded_from_counts"], {"skills": len(definition.skills)})
        self.assertGreater(context["total_frontmatter_tokens"], 0)
        self.assertGreater(context["total_content_length"], 0)
        self.assertTrue(context["ok"])
        self.assertEqual(extraction.skill_root, "skills/analyse-extraction-faits")
        self.assertEqual(extraction.display_name, "analyse-extraction-faits")
        self.assertIn("data-facts", extraction.agents)
        self.assertTrue(extraction.has_analysis)
        self.assertGreater(extraction.frontmatter_tokens, 0)
        self.assertEqual(extraction.as_dict()["schema_version"], "claude_skill_spec_v0")

    def test_agent_commands_include_builtins_and_skill_prompt_commands(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        skills = resolve_skill_specs(definition, project_root=PROJECT_ROOT)

        commands = build_agent_command_specs(skills)
        context = summarize_command_context(commands, agent_type="data-facts")
        compact = find_command("compact", commands)
        extraction = find_command("analyse-extraction-faits", commands)
        model_invocable = filter_model_invocable_commands(commands)

        self.assertEqual(context["schema_version"], "claude_command_context_v0")
        self.assertEqual(context["agent_type"], "data-facts")
        self.assertEqual(context["unfiltered_commands_count"], context["commands_count"])
        self.assertEqual(context["settings_filtered_commands_count"], 0)
        self.assertEqual(context["commands_by_type"]["prompt"], len(definition.skills))
        self.assertGreaterEqual(context["commands_by_type"]["local-jsx"], 1)
        self.assertEqual(context["model_invocable_commands_count"], len(definition.skills))
        self.assertIn("skills", context["loaded_from"])
        self.assertTrue(context["ok"])
        self.assertIsNotNone(compact)
        self.assertTrue(compact.bridge_safe)
        self.assertIsNotNone(extraction)
        self.assertEqual(extraction.type, "prompt")
        self.assertEqual(extraction.loaded_from, "skills")
        self.assertEqual(extraction.skill_root, "skills/analyse-extraction-faits")
        self.assertGreater(extraction.content_length, 0)
        self.assertEqual(extraction.as_dict()["schema_version"], "claude_command_spec_v0")
        self.assertIn("analyse-extraction-faits", [command.name for command in model_invocable])

    def test_agent_commands_apply_settings_filters_like_claude_code(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        skills = resolve_skill_specs(definition, project_root=PROJECT_ROOT)

        all_commands = build_agent_command_specs(skills)
        filtered = build_agent_command_specs(
            skills,
            disabled_commands=["/compact", "analyse-extraction-faits"],
            enabled_commands=["compact", "analyse-extraction-faits", "recherche-baux-revenus"],
        )
        context = summarize_command_context(
            filtered,
            agent_type="data-facts",
            all_commands=all_commands,
            disabled_commands=["/compact", "analyse-extraction-faits"],
            enabled_commands=["compact", "analyse-extraction-faits", "recherche-baux-revenus"],
        )

        self.assertIsNone(find_command("/compact", filtered))
        self.assertIsNone(find_command("analyse-extraction-faits", filtered))
        self.assertIn("recherche-baux-revenus", context["command_names"])
        self.assertEqual(context["disabled_command_names"], ["compact", "analyse-extraction-faits"])
        self.assertIn("help", context["not_enabled_command_names"])
        self.assertIn("compact", context["settings_filtered_command_names"])
        self.assertGreater(context["settings_filtered_commands_count"], 2)
        self.assertEqual(context["model_invocable_commands_count"], 1)
        self.assertTrue(context["ok"])

    def test_claude_settings_context_merges_sources_like_claude_code(self) -> None:
        tmp = writable_tmp_dir("claude_settings")
        user_settings_path = tmp / "user-settings.json"
        try:
            (tmp / ".claude").mkdir(parents=True)
            user_settings_path.write_text(
                json.dumps(
                    {
                        "runtime": {"preserve_recent_tool_results": 1},
                        "commands": {"disabled": ["help"]},
                        "env": {"SECRET_TOKEN": "hidden"},
                    }
                ),
                encoding="utf-8",
            )
            (tmp / ".claude" / "settings.json").write_text(
                json.dumps(
                    {
                        "runtime": {"strict_tool_result_pairing": False},
                        "permissions": {
                            "defaultMode": "plan",
                            "allow": [{"toolName": "read_file"}],
                            "deny": ["write_file"],
                            "additionalDirectories": ["C:\\Users\\simon\\claude-code-project"],
                        },
                        "commands": {"disabled": ["status"]},
                    }
                ),
                encoding="utf-8",
            )
            (tmp / ".claude" / "settings.local.json").write_text(
                json.dumps({"runtime": {"preserve_recent_tool_results": 2}}),
                encoding="utf-8",
            )

            context = load_claude_settings(
                project_root=tmp,
                user_settings_path=user_settings_path,
                session_settings={
                    "runtime": {"context_compaction_threshold_tokens": 42},
                    "permissions": {"defaultMode": "bypass"},
                },
            )

            self.assertEqual(context["schema_version"], "claude_settings_context_v0")
            self.assertEqual(
                context["active_sources"],
                ["defaultSettings", "userSettings", "projectSettings", "localSettings", "sessionSettings"],
            )
            self.assertTrue(context["ok"])
            runtime = context["runtime_options"]
            self.assertFalse(runtime["strict_tool_result_pairing"])
            self.assertEqual(runtime["preserve_recent_tool_results"], 2)
            self.assertEqual(runtime["context_compaction_threshold_tokens"], 42)
            self.assertEqual(runtime["permission_mode"], "bypass")
            self.assertEqual(runtime["additional_directories"], ["C:\\Users\\simon\\claude-code-project"])
            self.assertEqual(runtime["disabled_commands"], ["help", "status"])
            self.assertEqual(runtime["env_keys"], ["SECRET_TOKEN"])
            self.assertEqual(context["effective"]["env"]["SECRET_TOKEN"], "<redacted>")
            self.assertTrue(validate_settings_context(context)["ok"])
            permission_state = build_permission_state_from_settings_context(
                context,
                agent_type="data-facts",
                mode=runtime["permission_mode"],
                allowed_tools=["read_file", "write_file"],
            )
            self.assertIn("read_file", permission_state["alwaysAllowRules"]["projectSettings"])
            self.assertIn("write_file", permission_state["alwaysDenyRules"]["projectSettings"])
            self.assertIn(
                {"path": "C:\\Users\\simon\\claude-code-project", "source": "projectSettings"},
                permission_state["additionalWorkingDirectories"],
            )
            self.assertEqual(permission_state["mode"], "bypass")
            self.assertEqual(validate_permission_state(permission_state), [])
            self.assertEqual(
                merge_settings({"a": [1], "b": {"c": 1}}, {"a": [1, 2], "b": {"d": 2}}),
                {"a": [1, 2], "b": {"c": 1, "d": 2}},
            )
            self.assertEqual(
                runtime_options_from_settings({"permissions": {"defaultMode": "plan"}})["permission_mode"],
                "plan",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_load_agent_runner_applies_claude_settings_runtime_options(self) -> None:
        settings_context = load_claude_settings(
            project_root=PROJECT_ROOT,
            session_settings={
                "runtime": {
                    "strict_tool_result_pairing": False,
                    "preserve_recent_tool_results": 1,
                    "context_compaction_threshold_tokens": 9,
                },
                "permissions": {"defaultMode": "plan"},
                "commands": {
                    "include_builtin": False,
                    "disabled": ["analyse-extraction-faits"],
                },
            },
        )

        runner = load_agent_runner(
            "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
            settings_context=settings_context,
        )

        self.assertFalse(runner.strict_tool_result_pairing)
        self.assertEqual(runner.preserve_recent_tool_results, 1)
        self.assertEqual(runner.context_compaction_threshold_tokens, 9)
        self.assertEqual(runner.permission_mode, "plan")
        self.assertEqual(runner.settings_context["active_sources"], ["defaultSettings", "projectSettings", "sessionSettings"])
        self.assertFalse(runner.command_context["include_builtin_commands"])
        self.assertNotIn("compact", runner.command_context["command_names"])
        self.assertNotIn("analyse-extraction-faits", runner.command_context["command_names"])
        self.assertEqual(runner.command_context["builtin_commands_count"], 0)
        self.assertEqual(runner.command_context["disabled_command_names"], ["analyse-extraction-faits"])
        self.assertEqual(runner.command_context["settings_filtered_commands_count"], 1)
        blocked = runner.execute_slash_command("/compact")
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["status"], "unavailable")
        self.assertEqual(blocked["errors"], ["command_not_available"])
        self.assertEqual(blocked["event"]["event"], "slash_command_blocked")

    def test_safe_local_slash_commands_execute_from_filtered_registry(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_local_commands")
        try:
            runtime_result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            cost = runner.execute_slash_command("/cost", runtime_result=runtime_result)
            status = runner.execute_slash_command("status", runtime_result=runtime_result)
            summary = runner.execute_slash_command("/summary", args="runtime", runtime_result=runtime_result)
            compact = runner.execute_slash_command(
                "/compact",
                args="preserve source and artifact decisions",
                runtime_result=runtime_result,
            )

            self.assertTrue(cost["ok"], cost["errors"])
            self.assertEqual(cost["schema_version"], "claude_command_execution_v0")
            self.assertEqual(cost["command_name"], "cost")
            self.assertEqual(cost["event"]["event"], "slash_command_executed")
            self.assertEqual(cost["message"]["role"], "assistant")
            self.assertEqual(cost["message"]["content_block_types"], ["local_command_output"])
            self.assertEqual(cost["message"]["content"][0]["command"], "/cost")
            self.assertEqual(cost["output"]["total_cost_usd"], runtime_result["metrics"]["total_cost_usd"])
            self.assertGreater(cost["output"]["input_tokens"], 0)

            self.assertTrue(status["ok"], status["errors"])
            self.assertEqual(status["command_type"], "local-jsx")
            self.assertEqual(status["output"]["status"], runtime_result["status"])
            self.assertEqual(status["output"]["commands_count"], runner.command_context["commands_count"])
            self.assertEqual(status["message"]["metadata"]["subtype"], "local_command")

            self.assertTrue(summary["ok"], summary["errors"])
            self.assertEqual(summary["output"]["instructions"], "runtime")
            self.assertEqual(summary["output"]["completed_tasks_count"], runtime_result["task_state"]["completed_count"])
            self.assertEqual(summary["output"]["tool_use_count"], runtime_result["metrics"]["tool_use_count"])

            self.assertTrue(compact["ok"], compact["errors"])
            self.assertFalse(compact["output"]["mutates_messages"])
            self.assertEqual(
                compact["output"]["compaction_result"]["summary"]["schema_version"],
                "claude_context_compact_summary_v0",
            )
            self.assertEqual(
                compact["output"]["compaction_result"]["summary"]["instructions"],
                "preserve source and artifact decisions",
            )
            self.assertEqual(
                compact["output"]["compaction_result"]["messages_before_compaction"],
                len(runtime_result["messages"]),
            )
            self.assertEqual(compact["message"]["content_block_types"], ["local_command_output"])

            prompt_command = runner.execute_slash_command(
                "/analyse-extraction-faits",
                runtime_result=runtime_result,
            )
            self.assertFalse(prompt_command["ok"])
            self.assertEqual(prompt_command["errors"], ["command_not_safe"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_pipeline_slash_command_execution_uses_aggregate_context(self) -> None:
        pipeline = load_pipeline_runner(project_root=PROJECT_ROOT)

        status = pipeline.execute_slash_command("/status")
        blocked = pipeline.execute_slash_command("/permissions")

        self.assertTrue(status["ok"], status["errors"])
        self.assertEqual(status["agent_type"], "claude-pipeline")
        self.assertEqual(status["output"]["scope"], "multi_agent:claude")
        self.assertGreater(status["output"]["commands_count"], 0)
        self.assertEqual(status["message"]["content"][0]["command"], "/status")
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["errors"], ["command_not_safe"])

    def test_comps_market_agent_config_loads_as_claude_style_definition(self) -> None:
        config_path = PROJECT_ROOT / "integration" / "AGENTCONFIG-COMPS-MARKET-V0.yaml"

        definition = load_claude_agent_definition(config_path, project_root=PROJECT_ROOT)

        self.assertEqual(definition.agent_type, "comps-market")
        self.assertEqual(definition.model, "claude-sonnet-4-6")
        self.assertEqual(definition.max_turns, 14)
        self.assertIn("search_comparables", definition.tools)
        self.assertIn("write_file", definition.tools)
        self.assertIn("analyse-selection-comparables", definition.skills)
        self.assertEqual(
            definition.outputs,
            ["comparables_proposes.json", "justifications_comparables.json", "source_index.json"],
        )
        self.assertTrue(definition.human_validation["required"])

    def test_valuation_draft_agent_config_loads_as_claude_style_definition(self) -> None:
        config_path = PROJECT_ROOT / "integration" / "AGENTCONFIG-VALUATION-DRAFT-V0.yaml"

        definition = load_claude_agent_definition(config_path, project_root=PROJECT_ROOT)

        self.assertEqual(definition.agent_type, "valuation-draft")
        self.assertEqual(definition.model, "claude-sonnet-4-6")
        self.assertEqual(definition.max_turns, 16)
        self.assertIn("run_calculation", definition.tools)
        self.assertIn("write_file", definition.tools)
        self.assertIn("analyse-approche-comparaison", definition.skills)
        self.assertEqual(
            definition.outputs,
            [
                "calculs_approche_comparative.json",
                "calculs_approche_cout.json",
                "calculs_approche_revenu.json",
                "hypotheses_explicites.json",
                "brouillon_valeur.md",
            ],
        )
        self.assertTrue(definition.human_validation["required"])

    def test_compliance_qa_agent_config_loads_as_claude_style_definition(self) -> None:
        config_path = PROJECT_ROOT / "integration" / "AGENTCONFIG-COMPLIANCE-QA-V0.yaml"

        definition = load_claude_agent_definition(config_path, project_root=PROJECT_ROOT)

        self.assertEqual(definition.agent_type, "compliance-qa")
        self.assertEqual(definition.model, "claude-sonnet-4-6")
        self.assertEqual(definition.max_turns, 10)
        self.assertIn("validate_schema", definition.tools)
        self.assertIn("write_file", definition.tools)
        self.assertIn("analyse-conformite", definition.skills)
        self.assertEqual(
            definition.outputs,
            ["rapport_non_conformites.json", "statut_sortie.json", "recommandations_corrections.md"],
        )
        self.assertTrue(definition.human_validation["required"])

    def test_redaction_agent_config_loads_as_claude_style_definition(self) -> None:
        config_path = PROJECT_ROOT / "integration" / "AGENTCONFIG-REDACTION-V0.yaml"

        definition = load_claude_agent_definition(config_path, project_root=PROJECT_ROOT)

        self.assertEqual(definition.agent_type, "redaction")
        self.assertEqual(definition.model, "claude-sonnet-4-6")
        self.assertEqual(definition.max_turns, 8)
        self.assertIn("format_document", definition.tools)
        self.assertIn("write_file", definition.tools)
        self.assertIn("redaction-rapport-evaluation", definition.skills)
        self.assertEqual(definition.outputs, ["brouillon_rapport.md", "annexe_sources.md"])
        self.assertTrue(definition.human_validation["required"])

    def test_data_facts_builds_prompt_with_dynamic_case_context(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)

        prompt = definition.build_system_prompt(
            runner.build_context(
                {
                    "dossier_id": "D-CLAUDE",
                    "date_reference": "2026-04-28",
                    "documents_list": ["fiche.pdf"],
                },
                "inline",
            )
        )

        self.assertEqual(len(prompt), 3)
        self.assertIn("Dossier: D-CLAUDE", prompt[1])
        self.assertIn("fiche.pdf", prompt[1])
        self.assertIn("tools_allowed: read_file", prompt[2])

    def test_data_facts_runner_writes_artifacts_with_claude_style_events(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_data_facts")
        try:
            result = runner.run_case_data(case, root, source_fixture="case_nominal.json", case_stem="case_nominal", case_subdir=True)

            self.assertEqual(result["agent_type"], "data-facts")
            self.assertEqual(result["metrics"]["tool_use_count"], 3)
            self.assertIn("analyse-extraction-faits", result["skills_by_agent"]["data-facts"])
            self.assertEqual(result["skill_context"]["schema_version"], "claude_skill_context_v0")
            self.assertEqual(result["skill_context"]["agent_type"], "data-facts")
            self.assertEqual(result["skill_context"]["skills_count"], len(definition.skills))
            self.assertEqual(result["skill_context"]["loaded_from"], ["skills"])
            self.assertEqual(result["skill_context"]["plugins_count"], 0)
            self.assertTrue(result["skill_context"]["ok"])
            self.assertEqual(result["settings_context"]["schema_version"], "claude_settings_context_v0")
            self.assertEqual(result["settings_context"]["runtime_options"]["permission_mode"], "default")
            self.assertTrue(result["settings_context"]["ok"])
            self.assertEqual(result["command_context"]["schema_version"], "claude_command_context_v0")
            self.assertEqual(result["command_context"]["agent_type"], "data-facts")
            self.assertIn("compact", result["command_context"]["command_names"])
            self.assertIn("analyse-extraction-faits", result["command_context"]["model_invocable_command_names"])
            self.assertTrue(result["command_context"]["ok"])
            self.assertIn("write_file", result["tools_by_agent"]["data-facts"])
            events = [event["event"] for event in result["events"]]
            self.assertEqual(events[0], "agent_session_start")
            self.assertTrue(all(event["schema_version"] == "claude_runtime_event_v0" for event in result["events"]))
            self.assertTrue(all(message["schema_version"] == "claude_message_envelope_v0" for message in result["messages"]))
            self.assertTrue(result["event_envelope_summary"]["ok"])
            self.assertTrue(result["message_envelope_summary"]["ok"])
            self.assertIn("system_prompt_built", events)
            self.assertEqual(events.count("tool_start"), 3)
            self.assertEqual(events.count("tool_end"), 3)
            self.assertIn("agent_session_done", events)
            assistant_tool_uses = [
                message
                for message in result["messages"]
                if message["role"] == "assistant" and message["content"][0]["type"] == "tool_use"
            ]
            user_tool_results = [
                message
                for message in result["messages"]
                if message["role"] == "user" and message["content"][0]["type"] == "tool_result"
            ]
            self.assertEqual(len(assistant_tool_uses), 3)
            self.assertEqual(len(user_tool_results), 3)
            self.assertTrue(all(message["content"][0]["ok"] for message in user_tool_results))
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["conversation_state"]["tool_use_count"], 3)
            self.assertEqual(result["conversation_state"]["tool_result_count"], 3)
            self.assertEqual(result["model_profile"]["canonical_model"], "claude-sonnet-4-6")
            self.assertEqual(result["model_profile"]["model_key"], "sonnet46")
            self.assertEqual(result["token_budget"]["agent_type"], "data-facts")
            self.assertEqual(result["token_budget"]["estimated_tokens"], result["context_state"]["estimated_tokens"])
            self.assertEqual(result["metrics"]["total_tokens"], result["token_budget"]["estimated_tokens"])
            self.assertTrue(result["token_budget"]["ok"])
            self.assertEqual(result["usage_accounting"]["schema_version"], "claude_usage_accounting_v0")
            self.assertEqual(result["usage_accounting"]["pricing"]["input_tokens"], 3.0)
            self.assertGreater(result["usage_accounting"]["usage"]["input_tokens"], 0)
            self.assertGreater(result["usage_accounting"]["usage"]["output_tokens"], 0)
            self.assertEqual(result["metrics"]["total_cost_usd"], result["usage_accounting"]["cost_usd"])
            self.assertFalse(result["context_state"]["needs_compaction"])
            self.assertGreater(result["context_state"]["estimated_tokens"], 0)
            self.assertEqual(result["permission_summary"]["decisions_count"], 3)
            self.assertEqual(result["permission_summary"]["allowed_count"], 3)
            self.assertEqual(result["permission_summary"]["denied_count"], 0)
            self.assertEqual(len(result["permission_decisions"]), 3)
            self.assertEqual(events.count("permission_decision"), 3)
            self.assertEqual(result["permission_state"]["schema_version"], "claude_permission_state_v0")
            self.assertEqual(result["permission_state_summary"]["allow_rules_count"], 1)
            self.assertEqual(result["permission_state_summary"]["deny_rules_count"], 0)
            self.assertTrue(result["permission_replay_summary"]["ok"])
            self.assertTrue(Path(result["permission_state_path"]).exists())
            self.assertEqual(result["tool_registry_summary"]["schema_version"], "claude_tool_registry_summary_v0")
            self.assertEqual(result["tool_registry_summary"]["tool_names"], result["tools_by_agent"]["data-facts"])
            self.assertTrue(result["tool_registry_summary"]["ok"])
            self.assertEqual(result["task_state"]["tasks_count"], 3)
            self.assertEqual(result["task_state"]["completed_count"], 3)
            self.assertEqual(result["task_state"]["pending_count"], 0)
            self.assertTrue(result["task_state"]["ok"])
            self.assertEqual(events.count("task_state_created"), 1)
            self.assertEqual(events.count("task_started"), 3)
            self.assertEqual(events.count("task_completed"), 3)
            self.assertEqual(result["handoffs_received"], [])
            self.assertEqual(result["handoff_summary"]["handoffs_count"], 0)
            self.assertEqual(result["handoff_summary"]["artifacts_count"], 0)
            transcript_path = Path(result["transcript_path"])
            self.assertTrue(transcript_path.exists())
            transcript_entries = [
                json.loads(line)
                for line in transcript_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(result["transcript_summary"]["entries_count"], len(result["messages"]))
            self.assertEqual(len(transcript_entries), len(result["messages"]))
            self.assertEqual(transcript_entries[0]["message_schema_version"], "claude_message_envelope_v0")
            self.assertTrue(result["transcript_summary"]["validation"]["ok"])
            self.assertEqual(result["transcript_summary"]["tool_use_count"], 3)
            self.assertEqual(result["transcript_summary"]["tool_result_count"], 3)
            self.assertEqual(result["hook_summary"]["invocations_count"], 8)
            self.assertEqual(result["hook_summary"]["hook_events"]["SessionStart"], 1)
            self.assertEqual(result["hook_summary"]["hook_events"]["PreToolUse"], 3)
            self.assertEqual(result["hook_summary"]["hook_events"]["PostToolUse"], 3)
            self.assertEqual(result["hook_summary"]["hook_events"]["SessionEnd"], 1)
            self.assertEqual(events.count("hook_invoked"), 8)
            self.assertIn("conversation_state_validated", events)

            artifact_dir = Path(result["artifact_dir"])
            fiche_path = artifact_dir / "data-facts.fiche_bien.json"
            self.assertTrue(fiche_path.exists())
            payload = json.loads(fiche_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["agent_config"], "AGENTCONFIG-DATA-FACTS-V0.yaml")
            self.assertEqual(payload["claude_style_runtime"]["agent_type"], "data-facts")
            self.assertIn("read_file", payload["claude_style_runtime"]["tools_allowed"])
            manifest = payload["extraction_manifest"]
            self.assertEqual(manifest["schema_version"], "data_facts_extraction_manifest_v1")
            self.assertEqual(manifest["source_fixture"], "case_nominal.json")
            self.assertEqual(manifest["source_ids"], ["SRC-1"])
            self.assertEqual(manifest["source_coverage_status"], "OK")
            self.assertEqual(manifest["extraction_completeness_status"], "A_COMPLETER")
            self.assertTrue(manifest["human_validation_required"])
            fields_by_name = {row["field"]: row for row in manifest["fields"]}
            self.assertTrue(fields_by_name["date_reference"]["present"])
            self.assertFalse(fields_by_name["surface"]["present"])
            self.assertIn("surface", manifest["missing_fields"])
            self.assertEqual(payload["source_coverage"]["source_ids"], ["SRC-1"])
            self.assertEqual(payload["tool_source"], "read_file+extract_text")

            source_index_path = artifact_dir / "data-facts.source_index.json"
            source_index = json.loads(source_index_path.read_text(encoding="utf-8"))
            self.assertEqual(source_index["coverage"]["source_coverage_status"], "OK")
            self.assertEqual(source_index["coverage"]["missing_fields"], manifest["missing_fields"])
            self.assertEqual(source_index["sources"][0]["source_id"], "SRC-1")
            self.assertIn("comparables", source_index["sources"][0]["referenced_by"])
            self.assertIn("ajustements", source_index["sources"][0]["referenced_by"])
            self.assertIn("comparables:C1", source_index["sources"][0]["records"])
            self.assertIn("ajustements:A1", source_index["sources"][0]["records"])

            timeline_path = artifact_dir / "data-facts.timeline_faits.json"
            timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
            self.assertEqual(timeline["source_coverage"]["source_ids"], ["SRC-1"])
            self.assertEqual(timeline["source_coverage"]["source_coverage_status"], "OK")
            self.assertEqual(timeline["events"][0]["source_reference"], "case_nominal.json")
            self.assertFalse(timeline["events"][0]["source_required"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_data_facts_runner_records_incoming_handoff_messages(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_handoff_received")
        incoming_handoff = {
            "schema_version": "claude_agent_handoff_v0",
            "from_agent": "upstream-agent",
            "to_agent": "data-facts",
            "status": "OK",
            "artifacts_count": 1,
            "artifacts": [{"artifact": "upstream.json", "path": "out/upstream.json"}],
            "blocking_failures": [],
            "warnings": [],
        }
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
                handoff_messages=[incoming_handoff],
            )

            events = [event["event"] for event in result["events"]]
            handoff_messages = [
                message
                for message in result["messages"]
                if message["role"] == "user"
                and isinstance(message.get("content"), list)
                and message["content"]
                and isinstance(message["content"][0], dict)
                and message["content"][0].get("type") == "handoff"
            ]
            self.assertEqual(result["handoffs_received"][0]["from_agent"], "upstream-agent")
            self.assertEqual(result["handoff_summary"]["handoffs_count"], 1)
            self.assertEqual(result["handoff_summary"]["from_agents"], ["upstream-agent"])
            self.assertEqual(result["handoff_summary"]["artifacts_count"], 1)
            self.assertIn("handoff_received", events)
            self.assertEqual(len(handoff_messages), 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_fake_model_client_records_live_adapter_messages_before_tools(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=FakeClaudeModelClient(),
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_data_facts")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            events = [event["event"] for event in result["events"]]
            self.assertEqual(result["agent_type"], "data-facts")
            self.assertEqual(result["model_client"]["schema_version"], "claude_model_client_summary_v0")
            self.assertTrue(result["model_client"]["enabled"])
            self.assertEqual(result["model_client"]["provider"], "fake")
            self.assertEqual(result["model_client"]["agent_type"], "data-facts")
            self.assertEqual(result["model_client"]["requests_count"], 1)
            self.assertEqual(result["model_client"]["responses_count"], 1)
            self.assertGreater(result["model_client"]["input_tokens"], 0)
            self.assertGreater(result["model_client"]["output_tokens"], 0)
            self.assertTrue(result["model_client"]["ok"], result["model_client"].get("errors"))
            self.assertEqual(result["model_request"]["schema_version"], "claude_model_request_v0")
            self.assertEqual(result["model_request"]["agent_type"], "data-facts")
            self.assertEqual(result["model_request"]["runtime_mode"], "claude_live_data_facts_v0")
            self.assertEqual(result["model_response"]["schema_version"], "claude_model_response_v0")
            self.assertEqual(result["model_response"]["provider"], "fake")
            self.assertEqual(result["model_response"]["content_block_types"], ["text"])
            self.assertIn("model_request_started", events)
            self.assertIn("model_response_received", events)
            self.assertLess(events.index("model_response_received"), events.index("tool_start"))
            self.assertTrue(
                any(message["metadata"].get("source") == "model_client_request" for message in result["messages"])
            )
            self.assertTrue(
                any(message["metadata"].get("source") == "model_client_response" for message in result["messages"])
            )
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["metrics"]["model_input_tokens"], result["model_client"]["input_tokens"])
            self.assertEqual(result["metrics"]["model_output_tokens"], result["model_client"]["output_tokens"])
            self.assertTrue((Path(result["artifact_dir"]) / "data-facts.fiche_bien.json").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_executes_tool_result_and_continues_to_completion(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        client = ScriptedClaudeModelClient(
            [
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[
                        {"type": "text", "text": "Inspecter le dossier."},
                        {"type": "tool_use", "id": "call-list", "name": "list_files", "input": {}},
                    ],
                    stop_reason="tool_use",
                    usage={"input_tokens": 10, "output_tokens": 5},
                ),
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[{"type": "text", "text": "Termine."}],
                    stop_reason="end_turn",
                    usage={"input_tokens": 7, "output_tokens": 3},
                ),
            ]
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_tool_loop_completion")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            live_loop = result["model_live_loop"]
            self.assertEqual(live_loop["schema_version"], "claude_live_tool_loop_v0")
            self.assertEqual(live_loop["stop_reason"], "completion")
            self.assertTrue(live_loop["ok"], live_loop.get("errors"))
            self.assertEqual(result["model_client"]["requests_count"], 2)
            self.assertEqual(result["model_client"]["responses_count"], 2)
            self.assertEqual(result["model_client"]["tool_calls_count"], 1)
            self.assertEqual(result["model_client"]["input_tokens"], 17)
            self.assertEqual(result["model_client"]["output_tokens"], 8)
            self.assertEqual(len(client.requests), 2)
            self.assertTrue(
                any(
                    message["role"] == "user"
                    and message["content"]
                    and isinstance(message["content"][0], dict)
                    and message["content"][0].get("type") == "tool_result"
                    and message["content"][0].get("tool_use_id") == "call-list"
                    for message in client.requests[1].messages
                )
            )
            events = [event["event"] for event in result["events"]]
            self.assertEqual(events.count("model_request_started"), 2)
            self.assertEqual(events.count("model_response_received"), 2)
            self.assertIn("model_live_tool_loop_completed", events)
            self.assertTrue(result["conversation_state"]["ok"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_adopts_declared_written_artifact_without_overwrite(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        live_payload = {
            "dossier_id": "D-001",
            "step": "data-facts",
            "artifact": "fiche_bien.json",
            "source_fixture": "case_nominal.json",
            "date_reference": "2026-04-28",
            "surface": {"value": 1000, "unit": "pi2"},
            "confidence": 0.91,
            "source_ids": ["SRC-LIVE"],
            "live_marker": "authored-by-model",
        }
        client = ScriptedClaudeModelClient(
            [
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[
                        {
                            "type": "tool_use",
                            "id": "call-live-write",
                            "name": "write_file",
                            "input": {"path": "fiche_bien.json", "content": live_payload},
                        }
                    ],
                    stop_reason="tool_use",
                    usage={"input_tokens": 8, "output_tokens": 6},
                ),
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[{"type": "text", "text": "Artefact principal produit."}],
                    stop_reason="end_turn",
                    usage={"input_tokens": 4, "output_tokens": 2},
                ),
            ]
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_artifact_adoption")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            artifact_path = Path(result["artifact_dir"]) / "data-facts.fiche_bien.json"
            authored = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(authored["live_marker"], "authored-by-model")
            self.assertNotIn("extraction_manifest", authored)
            self.assertEqual(result["model_live_loop"]["adopted_artifacts_count"], 1)
            self.assertEqual(result["live_authored_artifacts"][0]["artifact"], "fiche_bien.json")
            self.assertEqual(result["live_authored_artifacts"][0]["tool_call_id"], "call-live-write")
            events = [event for event in result["events"] if event.get("artifact") == "fiche_bien.json"]
            self.assertTrue(any(event["event"] == "artifact_written" and event.get("source") == "live_model" for event in events))
            self.assertTrue(any(event["event"] == "artifact_adopted" for event in events))
            deterministic_write_events = [
                event
                for event in events
                if event["event"] == "artifact_written" and event.get("source") != "live_model"
            ]
            self.assertEqual(deterministic_write_events, [])
            self.assertTrue((Path(result["artifact_dir"]) / "data-facts.timeline_faits.json").exists())
            self.assertTrue((Path(result["artifact_dir"]) / "data-facts.source_index.json").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_stops_on_contract_failure_without_writing_undeclared_file(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        client = ScriptedClaudeModelClient(
            [
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[
                        {
                            "type": "tool_use",
                            "id": "call-write-bad",
                            "name": "write_file",
                            "input": {"path": "bad.json", "content": {"x": 1}},
                        }
                    ],
                    stop_reason="tool_use",
                    usage={"input_tokens": 5, "output_tokens": 4},
                )
            ]
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_tool_loop_contract")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            self.assertEqual(result["model_live_loop"]["stop_reason"], "contract_failure")
            self.assertFalse(result["model_live_loop"]["ok"])
            self.assertFalse(result["model_client"]["ok"])
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertIn("CLAUDE_LIVE_LOOP:contract_failure", result["blocking_failures"])
            contract_events = [
                event for event in result["events"]
                if event["event"] == "contract_invalid" and event.get("tool_call_id") == "call-write-bad"
            ]
            self.assertEqual(len(contract_events), 1)
            self.assertIn("artifact_not_declared_for_agent", contract_events[0]["failures"])
            self.assertFalse((Path(result["artifact_dir"]) / "bad.json").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_stops_on_max_turns(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        definition = replace(
            definition,
            budgets=replace(definition.budgets, max_iterations=2),
        )

        def endless_tool_use(request: ClaudeModelRequest) -> ClaudeModelResponse:
            call_id = f"call-list-{len(client.requests)}"
            return ClaudeModelResponse(
                agent_type=request.agent_type,
                model=request.model,
                provider="fake",
                content=[{"type": "tool_use", "id": call_id, "name": "list_files", "input": {}}],
                stop_reason="tool_use",
                usage={"input_tokens": 2, "output_tokens": 1},
            )

        client = ScriptedClaudeModelClient([endless_tool_use])
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_tool_loop_max_turns")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            self.assertEqual(result["model_live_loop"]["stop_reason"], "max_turns")
            self.assertEqual(result["model_live_loop"]["requests_count"], 2)
            self.assertEqual(result["model_live_loop"]["tool_results_count"], 2)
            self.assertFalse(result["model_client"]["ok"])
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertIn("CLAUDE_LIVE_LOOP:max_turns", result["blocking_failures"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_reports_model_error(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        client = ScriptedClaudeModelClient([RuntimeError("mock model unavailable")])
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_tool_loop_model_error")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            self.assertEqual(result["model_live_loop"]["stop_reason"], "model_error")
            self.assertEqual(result["model_client"]["requests_count"], 1)
            self.assertEqual(result["model_client"]["responses_count"], 0)
            self.assertFalse(result["model_client"]["ok"])
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertIn("CLAUDE_LIVE_LOOP:model_error", result["blocking_failures"])
            self.assertIn("model_error", [event["event"] for event in result["events"]])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_reports_tool_error(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        client = ScriptedClaudeModelClient(
            [
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[
                        {
                            "type": "tool_use",
                            "id": "call-missing-read",
                            "name": "read_file",
                            "input": {"path": "missing.json"},
                        }
                    ],
                    stop_reason="tool_use",
                    usage={"input_tokens": 5, "output_tokens": 4},
                )
            ]
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_tool_loop_tool_error")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            self.assertEqual(result["model_live_loop"]["stop_reason"], "tool_error")
            self.assertFalse(result["model_client"]["ok"])
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertIn("CLAUDE_LIVE_LOOP:tool_error", result["blocking_failures"])
            tool_results = [
                message["content"][0]
                for message in result["messages"]
                if message["role"] == "user"
                and message["content"]
                and isinstance(message["content"][0], dict)
                and message["content"][0].get("tool_use_id") == "call-missing-read"
            ]
            self.assertEqual(len(tool_results), 1)
            self.assertFalse(tool_results[0]["ok"])
            self.assertIn("FileNotFoundError", tool_results[0]["error"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_live_model_tool_loop_surfaces_permission_required_for_ask_rule(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        permission_state = build_empty_permission_state(
            agent_type="data-facts",
            mode=ClaudePermissionPolicy.DEFAULT,
            allowed_tools=list(definition.tools),
        )
        permission_state = apply_permission_update(
            permission_state,
            {
                "type": "addRules",
                "destination": "session",
                "behavior": "ask",
                "rules": [{"toolName": "read_file"}],
            },
        )
        client = ScriptedClaudeModelClient(
            [
                ClaudeModelResponse(
                    agent_type="data-facts",
                    model=definition.model,
                    provider="fake",
                    content=[
                        {
                            "type": "tool_use",
                            "id": "call-ask-read",
                            "name": "read_file",
                            "input": {"path": "source.json"},
                        }
                    ],
                    stop_reason="tool_use",
                    usage={"input_tokens": 5, "output_tokens": 4},
                )
            ]
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=client,
            runtime_mode="claude_live_data_facts_v0",
            permission_state=permission_state,
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_tool_loop_permission_required")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            live_loop = result["model_live_loop"]
            self.assertEqual(live_loop["stop_reason"], "permission_required")
            self.assertFalse(live_loop["ok"])
            self.assertEqual(live_loop["permission_requests_count"], 1)
            self.assertEqual(live_loop["permission_requests"][0]["tool_call_id"], "call-ask-read")
            self.assertEqual(live_loop["permission_requests"][0]["permission"], "runtime_read")
            self.assertEqual(
                live_loop["permission_requests"][0]["recommended_update"]["rules"],
                [{"toolName": "read_file"}],
            )
            self.assertEqual(live_loop["failed_tool_calls"][0]["stop_reason"], "permission_required")
            self.assertTrue(live_loop["failed_tool_calls"][0]["retryable"])
            self.assertFalse(result["model_client"]["ok"])
            self.assertEqual(result["status"], "A_REVOIR")
            self.assertIn("CLAUDE_LIVE_LOOP:permission_required", result["blocking_failures"])
            self.assertEqual(result["permission_decisions"][0]["reason"], "permission_state_ask_rule")
            self.assertNotIn(
                "tool_start",
                [
                    event["event"]
                    for event in result["events"]
                    if event.get("tool_call_id") == "call-ask-read"
                ],
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_data_facts_runner_writes_compact_summary_when_context_threshold_is_exceeded(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            context_compaction_threshold_tokens=1,
            preserve_recent_tool_results=2,
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_context_compact")
        try:
            result = runner.run_case_data(case, root, source_fixture="case_nominal.json", case_stem="case_nominal", case_subdir=True)

            self.assertTrue(result["context_state"]["needs_compaction"])
            self.assertEqual(result["context_state"]["preserved_tool_result_ids"], ["data-facts:timeline_faits.json:write_file", "data-facts:source_index.json:write_file"])
            compact_path = Path(result["context_state"]["compact_summary_artifact"])
            self.assertTrue(compact_path.exists())
            compact = json.loads(compact_path.read_text(encoding="utf-8"))
            self.assertEqual(compact["schema_version"], "claude_context_compact_summary_v0")
            self.assertEqual(compact["agent_type"], "data-facts")
            self.assertEqual(compact["preserved_tool_result_ids"], result["context_state"]["preserved_tool_result_ids"])
            self.assertIn("context_compacted", [event["event"] for event in result["events"]])
            self.assertIn("context_compact_summary.json", [event.get("artifact") for event in result["events"] if event["event"] == "artifact_written"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_comps_market_runner_uses_search_tool_and_writes_ranked_artifacts(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-COMPS-MARKET-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_comps_market")
        try:
            result = runner.run_case_data(case, root, source_fixture="case_nominal.json", case_stem="case_nominal", case_subdir=True)

            self.assertEqual(result["agent_type"], "comps-market")
            self.assertEqual(result["metrics"]["tool_use_count"], 4)
            self.assertIn("analyse-selection-comparables", result["skills_by_agent"]["comps-market"])
            self.assertIn("search_comparables", result["tools_by_agent"]["comps-market"])
            tool_starts = [event["tool"] for event in result["events"] if event["event"] == "tool_start"]
            self.assertEqual(tool_starts[0], "search_comparables")
            self.assertEqual(tool_starts.count("write_file"), 3)

            artifact_dir = Path(result["artifact_dir"])
            comparables_path = artifact_dir / "comps-market.comparables_proposes.json"
            justifications_path = artifact_dir / "comps-market.justifications_comparables.json"
            source_index_path = artifact_dir / "comps-market.source_index.json"
            self.assertTrue(comparables_path.exists())
            self.assertTrue(justifications_path.exists())
            self.assertTrue(source_index_path.exists())
            comparables_payload = json.loads(comparables_path.read_text(encoding="utf-8"))
            justifications_payload = json.loads(justifications_path.read_text(encoding="utf-8"))
            source_index_payload = json.loads(source_index_path.read_text(encoding="utf-8"))
            self.assertEqual(comparables_payload["tool_source"], "search_comparables")
            self.assertEqual(comparables_payload["claude_style_runtime"]["agent_type"], "comps-market")
            self.assertIsInstance(comparables_payload["comparables"], list)
            if comparables_payload["comparables"]:
                self.assertIn("score_details", comparables_payload["comparables"][0])
            self.assertEqual(
                comparables_payload["selection_protocol"]["schema_version"],
                "comps_market_selection_protocol_v1",
            )
            self.assertIsInstance(comparables_payload["selection_protocol"]["selected_comparable_ids"], list)
            self.assertIn(comparables_payload["selection_protocol"]["source_coverage_status"], {"OK", "A_COMPLETER"})
            self.assertIsInstance(comparables_payload["selection_protocol"]["scoring_weights"], dict)
            self.assertEqual(
                comparables_payload["source_coverage"]["schema_version"],
                "comps_market_source_coverage_v1",
            )
            self.assertIsInstance(comparables_payload["source_coverage"]["selected_source_ids"], list)
            self.assertGreaterEqual(comparables_payload["source_coverage"]["missing_source_count"], 0)
            self.assertEqual(
                comparables_payload["human_review_gate"]["schema_version"],
                "comps_market_human_review_gate_v1",
            )
            self.assertIn("liste_finale_comparables", comparables_payload["human_review_gate"]["checkpoints"])
            self.assertEqual(justifications_payload["tool_source"], "search_comparables")
            self.assertIsInstance(justifications_payload["justifications"], list)
            self.assertEqual(
                justifications_payload["selection_protocol"]["schema_version"],
                "comps_market_selection_protocol_v1",
            )
            self.assertEqual(source_index_payload["tool_source"], "search_comparables")
            self.assertEqual(source_index_payload["coverage"]["schema_version"], "comps_market_source_coverage_v1")
            self.assertIsInstance(source_index_payload["sources"], list)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_fake_model_client_records_live_adapter_messages_for_comps_market(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-COMPS-MARKET-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=FakeClaudeModelClient(),
            runtime_mode="claude_live_comps_market_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_comps_market")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            events = [event["event"] for event in result["events"]]
            self.assertEqual(result["agent_type"], "comps-market")
            self.assertEqual(result["model_client"]["schema_version"], "claude_model_client_summary_v0")
            self.assertTrue(result["model_client"]["enabled"])
            self.assertEqual(result["model_client"]["provider"], "fake")
            self.assertEqual(result["model_client"]["agent_type"], "comps-market")
            self.assertEqual(result["model_client"]["requests_count"], 1)
            self.assertEqual(result["model_client"]["responses_count"], 1)
            self.assertEqual(result["model_request"]["schema_version"], "claude_model_request_v0")
            self.assertEqual(result["model_request"]["runtime_mode"], "claude_live_comps_market_v0")
            self.assertEqual(result["model_response"]["schema_version"], "claude_model_response_v0")
            self.assertEqual(result["model_response"]["provider"], "fake")
            self.assertIn("search_comparables", result["model_request"]["tools"])
            self.assertIn("model_request_started", events)
            self.assertIn("model_response_received", events)
            self.assertLess(events.index("model_response_received"), events.index("tool_start"))
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["metrics"]["model_input_tokens"], result["model_client"]["input_tokens"])
            self.assertTrue((Path(result["artifact_dir"]) / "comps-market.comparables_proposes.json").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_valuation_draft_runner_uses_calculation_tools_and_writes_traces(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-VALUATION-DRAFT-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = {
            "dossier_id": "D-CALC",
            "date_reference": "2026-04-28",
            "surface": {"value": 1000, "unit": "pi2"},
            "comparables": [
                {
                    "comparable_id": "C1",
                    "prix_vente": 300000,
                    "source_id": "SRC-1",
                    "date_vente": "2026-03-01",
                    "distance_km": 2,
                    "surface": {"value": 980, "unit": "pi2"},
                    "confidence": 0.9,
                },
                {
                    "comparable_id": "C2",
                    "prix_vente": 450000,
                    "source_id": "SRC-2",
                    "date_vente": "2025-10-01",
                    "distance_km": 18,
                    "surface": {"value": 1500, "unit": "pi2"},
                    "confidence": 0.7,
                },
            ],
            "ajustements": [
                {"ajustement_id": "A1", "montant": 10000, "source_id": "SRC-A", "validation_humaine": True},
                {"ajustement_id": "A2", "montant": 999999, "source_id": "SRC-B", "validation_humaine": False},
            ],
            "confidence": 0.85,
        }
        root = writable_tmp_dir("claude_valuation_draft")
        try:
            result = runner.run_case_data(case, root, source_fixture="inline", case_stem="case_calc", case_subdir=True)

            self.assertEqual(result["agent_type"], "valuation-draft")
            self.assertEqual(result["metrics"]["tool_use_count"], 8)
            self.assertIn("analyse-approche-comparaison", result["skills_by_agent"]["valuation-draft"])
            self.assertIn("run_calculation", result["tools_by_agent"]["valuation-draft"])
            tool_starts = [event["tool"] for event in result["events"] if event["event"] == "tool_start"]
            self.assertEqual(tool_starts[:3], ["run_calculation", "run_calculation", "run_calculation"])
            self.assertEqual(tool_starts.count("write_file"), 5)

            artifact_dir = Path(result["artifact_dir"])
            comparative_path = artifact_dir / "valuation-draft.calculs_approche_comparative.json"
            hypotheses_path = artifact_dir / "valuation-draft.hypotheses_explicites.json"
            draft_path = artifact_dir / "valuation-draft.brouillon_valeur.md"
            self.assertTrue(comparative_path.exists())
            self.assertTrue(hypotheses_path.exists())
            self.assertTrue(draft_path.exists())
            comparative = json.loads(comparative_path.read_text(encoding="utf-8"))
            hypotheses = json.loads(hypotheses_path.read_text(encoding="utf-8"))
            draft = draft_path.read_text(encoding="utf-8")
            self.assertEqual(comparative["tool_source"], "run_calculation")
            self.assertEqual(comparative["claude_style_runtime"]["agent_type"], "valuation-draft")
            self.assertEqual(comparative["method"], "weighted_mean_score_v0")
            self.assertEqual(comparative["input_count"], 2)
            self.assertGreater(comparative["value"], 0)
            self.assertEqual(comparative["trace"]["adjustment_total_validated"], 10000)
            self.assertEqual(len(comparative["trace"]["selected_comparables"]), 2)
            self.assertIn("score_details", comparative["trace"]["selected_comparables"][0])
            self.assertEqual(
                comparative["methodology_plan"]["schema_version"],
                "valuation_methodology_plan_v1",
            )
            self.assertEqual(comparative["methodology_plan"]["selected_comparable_ids"], ["C1", "C2"])
            self.assertEqual(comparative["methodology_plan"]["validated_adjustments_count"], 1)
            self.assertEqual(comparative["methodology_plan"]["excluded_adjustments"][0]["ajustement_id"], "A2")
            self.assertEqual(comparative["reconciliation"]["schema_version"], "valuation_reconciliation_v1")
            self.assertEqual(comparative["reconciliation"]["preferred_approach"], "approche_comparative")
            self.assertEqual(comparative["reconciliation"]["preliminary_value"], comparative["value"])
            self.assertEqual(comparative["source_coverage"]["schema_version"], "valuation_source_coverage_v1")
            self.assertEqual(comparative["source_coverage"]["selected_comparable_source_ids"], ["SRC-1", "SRC-2"])
            self.assertEqual(comparative["source_coverage"]["adjustment_source_ids"], ["SRC-A", "SRC-B"])
            self.assertEqual(
                comparative["human_review_gate"]["schema_version"],
                "valuation_human_review_gate_v1",
            )
            self.assertIn("reconciliation_preliminaire", comparative["human_review_gate"]["checkpoints"])
            self.assertEqual(hypotheses["hypothesis_policy"]["schema_version"], "valuation_hypothesis_policy_v1")
            self.assertTrue(hypotheses["hypothesis_policy"]["source_required"])
            self.assertIn("## tool_source", draft)
            self.assertIn("run_calculation", draft)
            self.assertIn(str(comparative["value"]), draft)
            self.assertIn("valuation_reconciliation_v1", draft)
            self.assertIn("valuation_human_review_gate_v1", draft)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_fake_model_client_records_live_adapter_messages_for_valuation_draft(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-VALUATION-DRAFT-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=FakeClaudeModelClient(),
            runtime_mode="claude_live_valuation_draft_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_valuation_draft")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            events = [event["event"] for event in result["events"]]
            self.assertEqual(result["agent_type"], "valuation-draft")
            self.assertEqual(result["model_client"]["schema_version"], "claude_model_client_summary_v0")
            self.assertTrue(result["model_client"]["enabled"])
            self.assertEqual(result["model_client"]["provider"], "fake")
            self.assertEqual(result["model_client"]["agent_type"], "valuation-draft")
            self.assertEqual(result["model_client"]["requests_count"], 1)
            self.assertEqual(result["model_client"]["responses_count"], 1)
            self.assertEqual(result["model_request"]["schema_version"], "claude_model_request_v0")
            self.assertEqual(result["model_request"]["runtime_mode"], "claude_live_valuation_draft_v0")
            self.assertEqual(result["model_response"]["schema_version"], "claude_model_response_v0")
            self.assertEqual(result["model_response"]["provider"], "fake")
            self.assertIn("run_calculation", result["model_request"]["tools"])
            self.assertIn("model_request_started", events)
            self.assertIn("model_response_received", events)
            self.assertLess(events.index("model_response_received"), events.index("tool_start"))
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["metrics"]["model_input_tokens"], result["model_client"]["input_tokens"])
            self.assertTrue(
                (Path(result["artifact_dir"]) / "valuation-draft.calculs_approche_comparative.json").exists()
            )
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_compliance_qa_runner_validates_outputs_before_writing_artifacts(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-COMPLIANCE-QA-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_compliance_qa")
        try:
            result = runner.run_case_data(case, root, source_fixture="case_nominal.json", case_stem="case_nominal", case_subdir=True)

            self.assertEqual(result["agent_type"], "compliance-qa")
            self.assertEqual(result["metrics"]["tool_use_count"], 6)
            self.assertIn("analyse-conformite", result["skills_by_agent"]["compliance-qa"])
            self.assertIn("validate_schema", result["tools_by_agent"]["compliance-qa"])
            tool_starts = [event["tool"] for event in result["events"] if event["event"] == "tool_start"]
            self.assertEqual(tool_starts.count("validate_schema"), 3)
            self.assertEqual(tool_starts.count("write_file"), 3)
            self.assertEqual(tool_starts[0], "validate_schema")

            artifact_dir = Path(result["artifact_dir"])
            rapport_path = artifact_dir / "compliance-qa.rapport_non_conformites.json"
            statut_path = artifact_dir / "compliance-qa.statut_sortie.json"
            recommandations_path = artifact_dir / "compliance-qa.recommandations_corrections.md"
            self.assertTrue(rapport_path.exists())
            self.assertTrue(statut_path.exists())
            self.assertTrue(recommandations_path.exists())
            rapport = json.loads(rapport_path.read_text(encoding="utf-8"))
            statut = json.loads(statut_path.read_text(encoding="utf-8"))
            recommandations = recommandations_path.read_text(encoding="utf-8")
            self.assertEqual(rapport["claude_style_runtime"]["agent_type"], "compliance-qa")
            self.assertTrue(rapport["schema_validation"]["ok"])
            self.assertEqual(rapport["schema_validation"]["tool"], "validate_schema")
            self.assertEqual(rapport["tool_source"], "validate_schema")
            self.assertEqual(rapport["compliance_decision_matrix"]["schema_version"], "compliance_decision_matrix_v1")
            self.assertEqual(rapport["compliance_decision_matrix"]["status"], "A_REVOIR")
            self.assertGreaterEqual(rapport["compliance_decision_matrix"]["active_findings_count"], 1)
            self.assertFalse(rapport["compliance_decision_matrix"]["ok"])
            self.assertEqual(rapport["evidence_map"]["schema_version"], "compliance_evidence_map_v1")
            self.assertEqual(rapport["evidence_map"]["source_ids"], ["SRC-1"])
            self.assertIn("calculs_approche_comparative.json", rapport["evidence_map"]["declared_inputs"])
            self.assertIn("source_index.json", rapport["evidence_map"]["expected_artifacts"])
            self.assertEqual(rapport["human_review_gate"]["schema_version"], "compliance_human_review_gate_v1")
            self.assertIn("statut_final", rapport["human_review_gate"]["checkpoints"])
            self.assertTrue(statut["schema_validation"]["ok"])
            self.assertEqual(statut["status"], "A_REVOIR")
            self.assertEqual(statut["release_gate"]["schema_version"], "compliance_release_gate_v1")
            self.assertFalse(statut["release_gate"]["ready_for_redaction"])
            self.assertFalse(statut["release_gate"]["ready_for_final_publication"])
            self.assertTrue(statut["release_gate"]["human_validation_required"])
            self.assertEqual(statut["handoff_context"]["schema_version"], "compliance_handoff_context_v1")
            self.assertIn("validate_schema", recommandations)
            self.assertIn("compliance_recommendation_plan_v1", recommandations)
            self.assertIn("corriger les anomalies sans inventer de donnees manquantes", recommandations)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_fake_model_client_records_live_adapter_messages_for_compliance_qa(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-COMPLIANCE-QA-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=FakeClaudeModelClient(),
            runtime_mode="claude_live_compliance_qa_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_compliance_qa")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            events = [event["event"] for event in result["events"]]
            self.assertEqual(result["agent_type"], "compliance-qa")
            self.assertEqual(result["model_client"]["schema_version"], "claude_model_client_summary_v0")
            self.assertTrue(result["model_client"]["enabled"])
            self.assertEqual(result["model_client"]["provider"], "fake")
            self.assertEqual(result["model_client"]["agent_type"], "compliance-qa")
            self.assertEqual(result["model_client"]["requests_count"], 1)
            self.assertEqual(result["model_client"]["responses_count"], 1)
            self.assertEqual(result["model_request"]["schema_version"], "claude_model_request_v0")
            self.assertEqual(result["model_request"]["runtime_mode"], "claude_live_compliance_qa_v0")
            self.assertEqual(result["model_response"]["schema_version"], "claude_model_response_v0")
            self.assertEqual(result["model_response"]["provider"], "fake")
            self.assertIn("validate_schema", result["model_request"]["tools"])
            self.assertIn("model_request_started", events)
            self.assertIn("model_response_received", events)
            self.assertLess(events.index("model_response_received"), events.index("tool_start"))
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["metrics"]["model_input_tokens"], result["model_client"]["input_tokens"])
            self.assertTrue((Path(result["artifact_dir"]) / "compliance-qa.statut_sortie.json").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_redaction_runner_formats_documents_before_writing_artifacts(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-REDACTION-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(definition, project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_redaction")
        try:
            result = runner.run_case_data(case, root, source_fixture="case_nominal.json", case_stem="case_nominal", case_subdir=True)

            self.assertEqual(result["agent_type"], "redaction")
            self.assertEqual(result["metrics"]["tool_use_count"], 4)
            self.assertIn("redaction-rapport-evaluation", result["skills_by_agent"]["redaction"])
            self.assertIn("format_document", result["tools_by_agent"]["redaction"])
            tool_starts = [event["tool"] for event in result["events"] if event["event"] == "tool_start"]
            self.assertEqual(tool_starts, ["format_document", "write_file", "format_document", "write_file"])

            artifact_dir = Path(result["artifact_dir"])
            rapport_path = artifact_dir / "redaction.brouillon_rapport.md"
            annexe_path = artifact_dir / "redaction.annexe_sources.md"
            self.assertTrue(rapport_path.exists())
            self.assertTrue(annexe_path.exists())
            rapport = rapport_path.read_text(encoding="utf-8")
            annexe = annexe_path.read_text(encoding="utf-8")
            self.assertIn("# BROUILLON DE RAPPORT D", rapport)
            self.assertIn("Validation et signature", rapport)
            self.assertIn("SRC-1", rapport)
            self.assertIn("annexe_sources.md", annexe)
            self.assertIn("redaction_citation_policy_v1", annexe)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_fake_model_client_records_live_adapter_messages_for_redaction(self) -> None:
        definition = load_claude_agent_definition(
            PROJECT_ROOT / "integration" / "AGENTCONFIG-REDACTION-V0.yaml",
            project_root=PROJECT_ROOT,
        )
        runner = ClaudeStyleAgentRunner(
            definition,
            project_root=PROJECT_ROOT,
            model_client=FakeClaudeModelClient(),
            runtime_mode="claude_live_redaction_v0",
        )
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_live_redaction")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            events = [event["event"] for event in result["events"]]
            self.assertEqual(result["agent_type"], "redaction")
            self.assertEqual(result["model_client"]["schema_version"], "claude_model_client_summary_v0")
            self.assertTrue(result["model_client"]["enabled"])
            self.assertEqual(result["model_client"]["provider"], "fake")
            self.assertEqual(result["model_client"]["agent_type"], "redaction")
            self.assertEqual(result["model_client"]["requests_count"], 1)
            self.assertEqual(result["model_client"]["responses_count"], 1)
            self.assertEqual(result["model_request"]["schema_version"], "claude_model_request_v0")
            self.assertEqual(result["model_request"]["runtime_mode"], "claude_live_redaction_v0")
            self.assertEqual(result["model_response"]["schema_version"], "claude_model_response_v0")
            self.assertEqual(result["model_response"]["provider"], "fake")
            self.assertIn("format_document", result["model_request"]["tools"])
            self.assertIn("model_request_started", events)
            self.assertIn("model_response_received", events)
            self.assertLess(events.index("model_response_received"), events.index("tool_start"))
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["metrics"]["model_input_tokens"], result["model_client"]["input_tokens"])
            self.assertTrue((Path(result["artifact_dir"]) / "redaction.brouillon_rapport.md").exists())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_claude_style_pipeline_runs_all_agents_into_shared_artifact_dir(self) -> None:
        runner = load_pipeline_runner(project_root=PROJECT_ROOT)
        case = json.loads((PROJECT_ROOT / "tests" / "fixtures" / "case_nominal.json").read_text(encoding="utf-8"))
        root = writable_tmp_dir("claude_pipeline")
        try:
            result = runner.run_case_data(
                case,
                root,
                source_fixture="case_nominal.json",
                case_stem="case_nominal",
                case_subdir=True,
            )

            expected_agents = [
                "mandat-intake",
                "data-facts",
                "amu-analyst",
                "comps-market",
                "valuation-draft",
                "compliance-qa",
                "redaction",
            ]
            self.assertEqual(result["agent_type"], "claude-pipeline")
            self.assertEqual(result["agents"], expected_agents)
            self.assertTrue(all(message["schema_version"] == "claude_message_envelope_v0" for message in result["messages"]))
            self.assertTrue(all(event["schema_version"] == "claude_runtime_event_v0" for event in result["events"]))
            self.assertTrue(result["message_envelope_summary"]["ok"])
            self.assertTrue(result["event_envelope_summary"]["ok"])
            self.assertTrue(result["conversation_state"]["ok"])
            self.assertEqual(result["metrics"]["tool_use_count"], result["conversation_state"]["tool_use_count"])
            self.assertEqual(result["conversation_state"]["tool_use_count"], result["conversation_state"]["tool_result_count"])
            self.assertFalse(result["context_state"]["needs_compaction"])
            self.assertEqual(set(result["context_state_by_agent"]), set(expected_agents))
            self.assertEqual(set(result["model_profiles_by_agent"]), set(expected_agents))
            self.assertEqual(set(result["token_budget_by_agent"]), set(expected_agents))
            self.assertEqual(result["token_budget"]["agents_count"], len(expected_agents))
            self.assertEqual(result["token_budget"]["models"], ["claude-sonnet-4-6"])
            self.assertEqual(result["metrics"]["total_tokens"], result["token_budget"]["estimated_tokens"])
            self.assertTrue(result["token_budget"]["ok"])
            self.assertEqual(set(result["usage_accounting_by_agent"]), set(expected_agents))
            self.assertEqual(result["usage_accounting"]["schema_version"], "claude_usage_summary_v0")
            self.assertEqual(result["usage_accounting"]["agents_count"], len(expected_agents))
            self.assertGreater(result["usage_accounting"]["input_tokens"], 0)
            self.assertGreater(result["usage_accounting"]["output_tokens"], 0)
            self.assertEqual(result["metrics"]["total_cost_usd"], result["usage_accounting"]["total_cost_usd"])
            self.assertEqual(
                result["usage_accounting"]["model_usage"]["claude-sonnet-4-6"]["cost_usd"],
                result["usage_accounting"]["total_cost_usd"],
            )
            self.assertEqual(set(result["tool_registry_summary_by_agent"]), set(expected_agents))
            self.assertEqual(result["tool_registry_summary"]["schema_version"], "claude_tool_registry_summary_v0")
            self.assertTrue(result["tool_registry_summary"]["ok"])
            self.assertIn("write_file", result["tool_registry_summary"]["destructive_tools"])
            self.assertEqual(result["permission_summary"]["decisions_count"], result["metrics"]["tool_use_count"])
            self.assertEqual(result["permission_summary"]["allowed_count"], result["metrics"]["tool_use_count"])
            self.assertEqual(result["permission_summary"]["denied_count"], 0)
            self.assertEqual(result["permission_state"]["schema_version"], "claude_permission_state_v0")
            self.assertEqual(set(result["permission_state_by_agent"]), set(expected_agents))
            self.assertEqual(set(result["permission_state_path_by_agent"]), set(expected_agents))
            self.assertTrue(result["permission_state_summary"]["ok"])
            self.assertTrue(result["permission_replay_summary"]["ok"])
            self.assertTrue(Path(result["permission_state_path"]).exists())
            self.assertEqual(set(result["permission_summary_by_agent"]), set(expected_agents))
            self.assertEqual(result["task_summary"]["tasks_count"], result["task_summary"]["completed_count"])
            self.assertGreaterEqual(result["task_summary"]["tasks_count"], 16)
            self.assertTrue(result["task_summary"]["ok"])
            self.assertEqual(set(result["task_state_by_agent"]), set(expected_agents))
            self.assertEqual(len(result["handoffs"]), len(expected_agents) - 1)
            self.assertEqual(result["handoff_summary"]["handoffs_count"], len(expected_agents) - 1)
            self.assertEqual(result["handoff_summary"]["from_agents"], expected_agents[:-1])
            self.assertEqual(result["handoff_summary"]["to_agents"], expected_agents[1:])
            self.assertEqual(result["handoffs"][0]["from_agent"], "mandat-intake")
            self.assertEqual(result["handoffs"][0]["to_agent"], "data-facts")
            self.assertEqual(result["handoffs_by_agent"]["mandat-intake"], [])
            self.assertEqual(result["handoffs_by_agent"]["data-facts"][0]["from_agent"], "mandat-intake")
            self.assertEqual(set(result["handoff_summary_by_agent"]), set(expected_agents))
            lineage = result["artifact_lineage"]
            self.assertEqual(lineage["schema_version"], "claude_pipeline_artifact_lineage_v1")
            self.assertTrue(lineage["ok"])
            self.assertEqual(lineage["agents"], expected_agents)
            self.assertEqual(lineage["artifacts_count"], len([event for event in result["events"] if event["event"] == "artifact_written"]))
            self.assertEqual(lineage["handoff_edges_count"], len(expected_agents) - 1)
            self.assertEqual(len(lineage["artifacts_by_agent"]["data-facts"]), 3)
            self.assertEqual(len(lineage["artifacts_by_agent"]["valuation-draft"]), 5)
            self.assertEqual(len(lineage["artifacts_by_agent"]["redaction"]), 2)
            self.assertEqual(lineage["handoff_edges"][0]["from_agent"], "mandat-intake")
            self.assertEqual(lineage["handoff_edges"][0]["to_agent"], "data-facts")
            data_facts_edge = next(edge for edge in lineage["handoff_edges"] if edge["from_agent"] == "data-facts")
            self.assertIn(
                "data-facts.source_index.json",
                [artifact["artifact_key"] for artifact in data_facts_edge["artifacts"]],
            )
            source_index_record = next(
                record
                for record in lineage["artifacts"]
                if record["artifact_key"] == "data-facts.source_index.json"
            )
            self.assertIn("amu-analyst", source_index_record["consumed_by"])
            self.assertFalse(source_index_record["terminal"])
            self.assertIn("redaction.brouillon_rapport.md", lineage["terminal_artifact_keys"])
            transcript_path = Path(result["transcript_path"])
            self.assertTrue(transcript_path.exists())
            self.assertEqual(result["transcript_summary"]["entries_count"], len(result["messages"]))
            self.assertEqual(result["transcript_summary"]["agents_count"], len(expected_agents))
            self.assertTrue(result["transcript_summary"]["validation"]["ok"])
            self.assertEqual(result["transcript_summary"]["tool_use_count"], result["metrics"]["tool_use_count"])
            self.assertEqual(result["transcript_summary"]["tool_result_count"], result["metrics"]["tool_use_count"])
            self.assertEqual(result["transcript_summary"]["handoff_messages_count"], len(expected_agents) - 1)
            self.assertEqual(set(result["transcript_summary_by_agent"]), set(expected_agents))
            self.assertEqual(result["hook_summary"]["invocations_count"], 2 * len(expected_agents) + 2 * result["metrics"]["tool_use_count"])
            self.assertEqual(result["hook_summary"]["hook_events"]["SessionStart"], len(expected_agents))
            self.assertEqual(result["hook_summary"]["hook_events"]["PreToolUse"], result["metrics"]["tool_use_count"])
            self.assertEqual(result["hook_summary"]["hook_events"]["PostToolUse"], result["metrics"]["tool_use_count"])
            self.assertEqual(result["hook_summary"]["hook_events"]["SessionEnd"], len(expected_agents))
            self.assertEqual(set(result["hook_summary_by_agent"]), set(expected_agents))
            self.assertEqual(len(result["agent_results"]), len(expected_agents))
            self.assertEqual(set(result["conversation_state_by_agent"]), set(expected_agents))
            self.assertEqual(
                [event["agent_type"] for event in result["events"] if event["event"] == "agent_session_start"],
                expected_agents,
            )
            self.assertEqual(len([event for event in result["events"] if event["event"] == "handoff_created"]), len(expected_agents) - 1)
            self.assertEqual(len([event for event in result["events"] if event["event"] == "handoff_received"]), len(expected_agents) - 1)
            self.assertEqual(len([event for event in result["events"] if event["event"] == "hook_invoked"]), result["hook_summary"]["invocations_count"])
            self.assertEqual(len([event for event in result["events"] if event["event"] == "artifact_written"]), lineage["artifacts_count"])
            self.assertIn("redaction", result["skills_by_agent"])
            self.assertEqual(result["skill_context"]["schema_version"], "claude_skill_pipeline_context_v0")
            self.assertEqual(result["skill_context"]["agents_count"], len(expected_agents))
            self.assertEqual(set(result["skill_context_by_agent"]), set(expected_agents))
            self.assertEqual(result["skill_context"]["loaded_from"], ["skills"])
            self.assertEqual(result["skill_context"]["plugins_count"], 0)
            self.assertTrue(result["skill_context"]["ok"])
            self.assertEqual(result["settings_context"]["schema_version"], "claude_settings_context_v0")
            self.assertTrue(result["settings_context"]["ok"])
            self.assertEqual(result["command_context"]["schema_version"], "claude_command_pipeline_context_v0")
            self.assertEqual(result["command_context"]["agents_count"], len(expected_agents))
            self.assertEqual(set(result["command_context_by_agent"]), set(expected_agents))
            self.assertIn("compact", result["command_context"]["command_names"])
            self.assertIn("redaction-rapport-evaluation", result["command_context"]["model_invocable_command_names"])
            self.assertTrue(result["command_context"]["ok"])

            artifact_dir = Path(result["artifact_dir"])
            self.assertTrue((artifact_dir / "data-facts.fiche_bien.json").exists())
            self.assertTrue((artifact_dir / "comps-market.comparables_proposes.json").exists())
            self.assertTrue((artifact_dir / "valuation-draft.calculs_approche_comparative.json").exists())
            self.assertTrue((artifact_dir / "compliance-qa.statut_sortie.json").exists())
            self.assertTrue((artifact_dir / "redaction.brouillon_rapport.md").exists())
            valuation_comparative = json.loads((artifact_dir / "valuation-draft.calculs_approche_comparative.json").read_text(encoding="utf-8"))
            self.assertEqual(valuation_comparative["handoff_context"]["schema_version"], "valuation_handoff_context_v1")
            self.assertEqual(valuation_comparative["handoff_context"]["from_agents"], ["comps-market"])
            self.assertIn(
                "comparables_proposes.json",
                [artifact["artifact"] for artifact in valuation_comparative["handoff_context"]["artifacts"]],
            )
            comps_source_index = json.loads((artifact_dir / "comps-market.source_index.json").read_text(encoding="utf-8"))
            self.assertEqual(comps_source_index["handoff_context"]["schema_version"], "comps_market_handoff_context_v1")
            self.assertEqual(comps_source_index["handoff_context"]["from_agents"], ["amu-analyst"])
            self.assertIn(
                "umpp_conclusion.json",
                [artifact["artifact"] for artifact in comps_source_index["handoff_context"]["artifacts"]],
            )
            compliance_status = json.loads((artifact_dir / "compliance-qa.statut_sortie.json").read_text(encoding="utf-8"))
            self.assertEqual(compliance_status["handoff_context"]["schema_version"], "compliance_handoff_context_v1")
            self.assertEqual(compliance_status["handoff_context"]["from_agents"], ["valuation-draft"])
            self.assertIn(
                "calculs_approche_comparative.json",
                [artifact["artifact"] for artifact in compliance_status["handoff_context"]["artifacts"]],
            )
            redaction_report = (artifact_dir / "redaction.brouillon_rapport.md").read_text(encoding="utf-8")
            self.assertIn("BROUILLON DE RAPPORT", redaction_report)
            self.assertIn("Validation et signature", redaction_report)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_unknown_tool_in_agent_config_is_rejected(self) -> None:
        tmp = writable_tmp_dir("claude_config_invalid")
        try:
            config_path = tmp / "AGENTCONFIG-BAD.yaml"
            source = (PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml").read_text(encoding="utf-8")
            config_path.write_text(source + "\ntools_allowed:\n  - outil_inconnu\n", encoding="utf-8")

            with self.assertRaises(AgentConfigError):
                load_claude_agent_definition(config_path, project_root=PROJECT_ROOT)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_invalid_tool_registry_is_rejected_by_agent_config(self) -> None:
        bad_registry = dict(TOOL_REGISTRY)
        original = TOOL_REGISTRY["read_file"]
        bad_registry["read_file"] = ToolSpec(
            name=original.name,
            description=original.description,
            permission="runtime_admin",
            input_schema=original.input_schema,
        )

        with self.assertRaises(AgentConfigError):
            load_claude_agent_definition(
                PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml",
                project_root=PROJECT_ROOT,
                tool_registry=bad_registry,
            )

    def test_yaml_subset_parser_keeps_block_prompts_and_nested_lists(self) -> None:
        parsed = parse_yaml_subset(PROJECT_ROOT / "integration" / "AGENTCONFIG-DATA-FACTS-V0.yaml")

        self.assertEqual(parsed["agent_id"], "data-facts")
        self.assertIn("max_tokens", parsed)
        self.assertIn("system_prompt", parsed)
        self.assertIn("expert en extraction", parsed["system_prompt"])
        self.assertEqual(parsed["skills_allowed"][0], "analyse-extraction-faits")


if __name__ == "__main__":
    unittest.main()
