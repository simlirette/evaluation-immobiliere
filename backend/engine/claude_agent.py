from __future__ import annotations

from pathlib import Path
import time

from engine.audit import append_audit_log
from engine.claude.config import (
    load_claude_agent_definition,
    resolve_skill_specs,
    resolve_tool_specs,
)
from engine.claude.constants import CLAUDE_PIPELINE_AGENT_CONFIGS, PROJECT_ROOT
from engine.claude.context import build_context_compact_summary, build_context_state
from engine.claude.conversation import summarize_claude_messages
from engine.claude.commands import (
    build_agent_command_specs,
    filter_model_invocable_commands,
    find_command,
    summarize_command_context,
    summarize_pipeline_command_context,
    validate_command_context,
)
from engine.claude.command_execution import execute_slash_command
from engine.claude.envelopes import (
    build_claude_event_envelope,
    build_claude_message_envelope,
    summarize_envelope_validation,
    validate_claude_event_envelope,
    validate_claude_message_envelope,
)
from engine.claude.exceptions import AgentConfigError, ToolPermissionError, ToolResultPairingError
from engine.claude.handoffs import build_agent_handoff_message, summarize_handoffs
from engine.claude.hooks import CLAUDE_HOOK_EVENTS, build_claude_hook_invocation, summarize_hook_invocations
from engine.claude.model_client import (
    AnthropicClaudeModelClient,
    AnthropicSDKTransport,
    ClaudeModelClient,
    ClaudeModelProviderConfig,
    ClaudeModelRequest,
    ClaudeModelResponse,
    ClaudeProviderTransport,
    FakeClaudeModelClient,
    ModelProviderConfigurationError,
    ModelProviderTransportError,
    build_anthropic_request_payload,
    build_anthropic_sdk_messages_params,
    build_model_client,
    build_model_provider_diagnostics,
    build_model_provider_config,
    classify_anthropic_sdk_error,
    detect_anthropic_sdk_available,
    parse_anthropic_response_payload,
    redact_model_provider_options,
    summarize_model_client_interaction,
    summarize_model_provider_config,
    validate_model_provider_config,
)
from engine.claude.models import (
    build_token_budget_state,
    first_party_name_to_canonical_model,
    model_key_from_canonical,
    resolve_model_profile,
    summarize_pipeline_token_budgets,
)
from engine.claude.permissions import (
    ClaudePermissionDecision,
    ClaudePermissionPolicy,
    apply_permission_update,
    apply_permission_updates,
    build_empty_permission_state,
    build_permission_state_from_decisions,
    build_permission_state_from_settings_context,
    build_permission_updates_from_decisions,
    load_permission_state,
    normalize_permission_state,
    permission_rule_matches_tool_call,
    permission_rule_value_from_string,
    permission_rule_value_to_string,
    permission_state_behavior_for_call,
    replay_permission_decisions,
    summarize_permission_decisions,
    summarize_permission_state,
    validate_permission_state,
    validate_permission_update,
    write_permission_state,
)
from engine.claude.settings import load_claude_settings
from engine.claude.skills import summarize_pipeline_skill_context, summarize_skill_context, validate_skill_context
from engine.claude.tasks import build_agent_task_state, summarize_pipeline_task_states, update_task_status
from engine.claude.tools import (
    TOOL_REGISTRY,
    ClaudeToolExecutor,
    build_tool_input_validation,
    summarize_tool_registry,
    validate_tool_call_input,
    validate_tool_input,
    validate_tool_registry,
)
from engine.claude.transcript import (
    build_claude_transcript_entries,
    summarize_claude_transcript_entries,
    validate_claude_transcript_entries,
    write_claude_transcript,
)
from engine.claude.usage import (
    build_usage_accounting,
    calculate_usage_cost_usd,
    estimate_usage_from_messages,
    format_cost_usd,
    model_pricing_for_profile,
    summarize_usage_accounting,
)
from engine.claude.types import (
    ClaudeAgentBudget,
    ClaudeAgentFlags,
    ClaudeAgentState,
    CommandSpec,
    ClaudeModelProfile,
    ClaudeStyleAgentDefinition,
    ClaudeToolCall,
    ClaudeToolResult,
    SkillSpec,
    ToolSpec,
)
from engine.claude.yamlish import (
    _as_dict,
    _as_list,
    _as_optional_int,
    _handoff_string_list,
    _unique,
    parse_yaml_subset,
    render_template,
)
from engine.runtime import (
    REQUIRED_FIELDS_BY_ARTIFACT,
    RuntimeEngine,
    RuntimeStep,
    collect_source_ids,
    safe_path_id,
    validate_contract_rules,
    write_artifact_payload,
)
from engine.tools import search_comparables, validate_schema


class ClaudeStyleAgentRunner:
    """First eval-immo bridge toward Claude Code style agent execution."""

    def __init__(
        self,
        definition: ClaudeStyleAgentDefinition,
        *,
        project_root: Path | None = None,
        tool_registry: dict[str, ToolSpec] | None = None,
        strict_tool_result_pairing: bool | None = None,
        context_compaction_threshold_tokens: int | None = None,
        preserve_recent_tool_results: int | None = None,
        permission_mode: str | None = None,
        permission_state: dict[str, object] | None = None,
        settings_context: dict[str, object] | None = None,
        model_client: ClaudeModelClient | None = None,
        runtime_mode: str = "",
    ) -> None:
        self.definition = definition
        self.project_root = project_root or PROJECT_ROOT
        self.tool_registry = tool_registry or TOOL_REGISTRY
        self.model_client = model_client
        self.runtime_mode = runtime_mode
        self.settings_context = settings_context or load_claude_settings(project_root=self.project_root)
        self.runtime_settings = (
            self.settings_context.get("runtime_options", {})
            if isinstance(self.settings_context.get("runtime_options"), dict)
            else {}
        )
        self.strict_tool_result_pairing = (
            bool(strict_tool_result_pairing)
            if strict_tool_result_pairing is not None
            else bool(self.runtime_settings.get("strict_tool_result_pairing", True))
        )
        self.permission_mode = (
            permission_mode
            if permission_mode is not None
            else str(self.runtime_settings.get("permission_mode") or ClaudePermissionPolicy.DEFAULT)
        )
        self.initial_permission_state = normalize_permission_state(
            permission_state,
            agent_type=definition.agent_type,
            mode=self.permission_mode,
            allowed_tools=definition.tools,
        ) if permission_state else build_permission_state_from_settings_context(
            self.settings_context,
            agent_type=definition.agent_type,
            mode=self.permission_mode,
            allowed_tools=definition.tools,
        )
        self.context_compaction_threshold_tokens = (
            context_compaction_threshold_tokens
            if context_compaction_threshold_tokens is not None
            else (
                int(self.runtime_settings["context_compaction_threshold_tokens"])
                if self.runtime_settings.get("context_compaction_threshold_tokens") is not None
                else definition.budgets.max_total_tokens
            )
        )
        self.preserve_recent_tool_results = (
            int(preserve_recent_tool_results)
            if preserve_recent_tool_results is not None
            else int(self.runtime_settings.get("preserve_recent_tool_results", 3) or 0)
        )
        self.tools = resolve_tool_specs(definition, self.tool_registry)
        self.tool_registry_summary = summarize_tool_registry(definition.tools, self.tool_registry)
        if not self.tool_registry_summary["ok"]:
            raise AgentConfigError(f"{definition.config_path}: registre outils invalide")
        self.skills = resolve_skill_specs(definition, project_root=self.project_root)
        self.skill_context = summarize_skill_context(self.skills, agent_type=definition.agent_type)
        if not self.skill_context["ok"]:
            raise AgentConfigError(f"{definition.config_path}: skills invalides")
        self.include_builtin_commands = bool(self.runtime_settings.get("include_builtin_commands", True))
        self.disabled_commands = [
            str(command) for command in self.runtime_settings.get("disabled_commands", []) or []
        ]
        self.enabled_commands = [
            str(command) for command in self.runtime_settings.get("enabled_commands", []) or []
        ]
        self.unfiltered_commands = build_agent_command_specs(
            self.skills,
            include_builtin=self.include_builtin_commands,
        )
        self.commands = build_agent_command_specs(
            self.skills,
            include_builtin=self.include_builtin_commands,
            disabled_commands=self.disabled_commands,
            enabled_commands=self.enabled_commands,
        )
        self.command_context = summarize_command_context(
            self.commands,
            agent_type=definition.agent_type,
            all_commands=self.unfiltered_commands,
            include_builtin_commands=self.include_builtin_commands,
            disabled_commands=self.disabled_commands,
            enabled_commands=self.enabled_commands,
        )
        if not self.command_context["ok"]:
            raise AgentConfigError(f"{definition.config_path}: commandes invalides")
        self._runtime = RuntimeEngine(steps=[self.to_runtime_step()])

    def execute_slash_command(
        self,
        command_name: str,
        *,
        args: str = "",
        runtime_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return execute_slash_command(
            command_name,
            self.commands,
            args=args,
            context=self._slash_command_context(runtime_result),
        )

    def _slash_command_context(self, runtime_result: dict[str, object] | None = None) -> dict[str, object]:
        result = runtime_result if isinstance(runtime_result, dict) else {}
        return {
            "agent_type": self.definition.agent_type,
            "scope": f"single_agent:{self.definition.agent_type}",
            "status": result.get("status", "ready"),
            "model": self.definition.model,
            "canonical_model": self.definition.model_profile.canonical_model,
            "permission_mode": self.permission_mode,
            "messages": result.get("messages", []),
            "events": result.get("events", []),
            "metrics": result.get("metrics", {}),
            "conversation_state": result.get("conversation_state", {}),
            "context_state": result.get("context_state", {}),
            "context_compaction_threshold_tokens": self.context_compaction_threshold_tokens,
            "preserve_recent_tool_results": self.preserve_recent_tool_results,
            "token_budget": result.get("token_budget", {}),
            "usage_accounting": result.get("usage_accounting", {}),
            "task_state": result.get("task_state", {}),
            "handoff_summary": result.get("handoff_summary", {}),
            "blocking_failures": result.get("blocking_failures", []),
            "warnings": result.get("warnings", []),
            "settings_context": self.settings_context,
            "skill_context": self.skill_context,
            "command_context": self.command_context,
            "tool_registry_summary": self.tool_registry_summary,
            "tools_allowed": list(self.definition.tools),
            "skills_allowed": list(self.definition.skills),
        }

    def to_runtime_step(self) -> RuntimeStep:
        return RuntimeStep(
            self.definition.agent_type,
            self.definition.inputs,
            self.definition.outputs,
            self.definition.skills,
            Path(self.definition.config_path).name,
        )

    def build_context(
        self,
        case: dict,
        source_fixture: str,
        handoff_messages: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        handoff_messages = [
            dict(message)
            for message in (handoff_messages or [])
            if isinstance(message, dict)
        ]
        return {
            "dossier_id": case.get("dossier_id") or "unknown",
            "date_reference": case.get("date_reference") or "NON_FOURNI",
            "documents_list": case.get("documents_list") or case.get("documents_sources") or [],
            "rules_version": self.definition.flags.verification_checklist or "NON_FOURNI",
            "data_sources": case.get("data_sources") or collect_source_ids(case),
            "source_fixture": source_fixture,
            "type_bien": case.get("type_bien") or "NON_FOURNI",
            "zone": case.get("zone") or "NON_FOURNI",
            "comparables_count": len(case.get("comparables", [])) if isinstance(case.get("comparables"), list) else 0,
            "artifacts_list": case.get("artifacts_list") or self.definition.inputs,
            "compliance_status": case.get("compliance_status") or case.get("status") or "NON_FOURNI",
            "template_name": case.get("template_name") or "rapport_evaluation_v0",
            "handoff_messages_count": len(handoff_messages),
            "handoff_from_agents": [
                str(message.get("from_agent") or "")
                for message in handoff_messages
                if message.get("from_agent")
            ],
            "handoff_artifacts_count": sum(int(message.get("artifacts_count", 0) or 0) for message in handoff_messages),
        }

    def run_case_data(
        self,
        case: dict,
        out_dir: Path,
        *,
        source_fixture: str = "inline",
        case_stem: str | None = None,
        case_subdir: bool = False,
        handoff_messages: list[dict[str, object]] | None = None,
    ) -> dict:
        started_at = time.perf_counter()
        state = ClaudeAgentState(agent_type=self.definition.agent_type)
        state.handoffs_received = [
            dict(message)
            for message in (handoff_messages or [])
            if isinstance(message, dict)
        ]
        dossier_id = str(case.get("dossier_id") or "unknown")
        case_key = safe_path_id(case_stem or dossier_id)
        case_dir = out_dir / case_key if case_subdir else out_dir
        audit_log_path = case_dir / f"{case_key}.audit.jsonl"
        case_dir.mkdir(parents=True, exist_ok=True)
        executor = ClaudeToolExecutor(
            list(self.definition.tools),
            case_dir,
            audit_log_path=audit_log_path,
            tool_registry=self.tool_registry,
            permission_mode=self.permission_mode,
            permission_state=self.initial_permission_state,
        )

        context = self.build_context(case, source_fixture, state.handoffs_received)
        system_prompt = self.definition.build_system_prompt(context)
        self._append_message(state, "system", self.definition.agent_type, system_prompt)
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "agent_session_start",
                "agent_type": self.definition.agent_type,
                "model": self.definition.model,
                "canonical_model": self.definition.model_profile.canonical_model,
                "context_window_tokens": self.definition.model_profile.context_window_tokens,
                "max_turns": self.definition.max_turns,
                "setting_sources": self.settings_context.get("active_sources", []),
                "permission_mode": self.permission_mode,
                "tools_allowed": self.definition.tools,
                "skills_allowed": self.definition.skills,
                "skills_loaded_count": self.skill_context["skills_count"],
                "skills_loaded_from": self.skill_context["loaded_from"],
                "skills_plugins": self.skill_context["plugins"],
                "slash_commands_available": self.command_context["commands_count"],
                "model_invocable_commands": self.command_context["model_invocable_command_names"],
                "agent_config": self.definition.config_path,
            },
        )
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "system_prompt_built",
                "agent_type": self.definition.agent_type,
                "sections_count": len(system_prompt),
            },
        )
        self._invoke_hook(
            state,
            audit_log_path,
            "SessionStart",
            {
                "source": "runtime",
                "agent_type": self.definition.agent_type,
                "model": self.definition.model,
                "canonical_model": self.definition.model_profile.canonical_model,
                "tools_allowed": list(self.definition.tools),
                "skills_allowed": list(self.definition.skills),
                "skills_loaded_count": self.skill_context["skills_count"],
                "skills_loaded_from": self.skill_context["loaded_from"],
                "slash_commands_available": self.command_context["commands_count"],
                "setting_sources": self.settings_context.get("active_sources", []),
                "permission_mode": self.permission_mode,
            },
        )
        handoff_summary = summarize_handoffs(state.handoffs_received, agent_type=self.definition.agent_type)
        if state.handoffs_received:
            self._append_message(
                state,
                "user",
                self.definition.agent_type,
                [
                    {
                        "type": "handoff",
                        "handoffs": state.handoffs_received,
                    }
                ],
            )
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "handoff_received",
                    "agent_type": self.definition.agent_type,
                    "handoffs_count": handoff_summary["handoffs_count"],
                    "from_agents": handoff_summary["from_agents"],
                    "artifacts_count": handoff_summary["artifacts_count"],
                    "blocking_count": handoff_summary["blocking_count"],
                    "warning_count": handoff_summary["warning_count"],
                },
            )

        step = self.to_runtime_step()
        artifact_filenames = {
            artifact: f"{step.name}.{artifact}" if case_subdir else f"{case_key}.{step.name}.{artifact}"
            for artifact in step.writes
        }
        model_request, model_response, model_client_summary = self._maybe_invoke_model_client(
            state,
            audit_log_path,
            executor,
            system_prompt,
            context,
            step_outputs=list(self.definition.outputs),
            artifact_filenames=artifact_filenames,
            case_dir=case_dir,
        )
        status, blocking, warnings = self._runtime._compute_qa(case)
        live_loop_summary = (
            model_client_summary.get("live_tool_loop", {})
            if isinstance(model_client_summary, dict)
            else {}
        )
        live_stop_reason = str(live_loop_summary.get("stop_reason") or "")
        if live_stop_reason in {"max_turns", "model_error", "tool_error", "contract_failure", "permission_required"}:
            blocking = _unique([*blocking, f"CLAUDE_LIVE_LOOP:{live_stop_reason}"])
            status = "A_REVOIR"
        live_authored_artifacts = self._live_authored_artifacts_from_summary(live_loop_summary)
        valuation_values: dict[str, float] = {}
        tool_context = self._prepare_agent_tool_context(
            state,
            audit_log_path,
            executor,
            case,
            step,
            source_fixture=source_fixture,
            status=status,
            blocking=blocking,
            warnings=warnings,
        )
        state.task_state = build_agent_task_state(self.definition.agent_type, list(step.writes))
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "task_state_created",
                "agent_type": self.definition.agent_type,
                "tasks_count": state.task_state["tasks_count"],
                "pending_count": state.task_state["pending_count"],
                "artifacts": list(step.writes),
            },
        )

        for artifact in step.writes:
            update_task_status(state.task_state, artifact, "in_progress")
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "task_started",
                    "agent_type": step.name,
                    "task_id": state.task_state["current_task_id"],
                    "artifact": artifact,
                    "pending_count": state.task_state["pending_count"],
                    "completed_count": state.task_state["completed_count"],
                },
            )
            artifact_filename = f"{step.name}.{artifact}" if case_subdir else f"{case_key}.{step.name}.{artifact}"
            artifact_path = case_dir / artifact_filename
            live_artifact = live_authored_artifacts.get(artifact)
            if live_artifact:
                self._record_event(
                    state,
                    audit_log_path,
                    {
                        "event": "artifact_adopted",
                        "agent_type": step.name,
                        "step": step.name,
                        "artifact": artifact,
                        "path": live_artifact.get("path", artifact_path.as_posix()),
                        "source": "live_model",
                        "tool_call_id": live_artifact.get("tool_call_id", ""),
                    },
                )
                update_task_status(state.task_state, artifact, "completed")
                self._record_event(
                    state,
                    audit_log_path,
                    {
                        "event": "task_completed",
                        "agent_type": step.name,
                        "task_id": f"{step.name}:{artifact}",
                        "artifact": artifact,
                        "source": "live_model",
                        "pending_count": state.task_state["pending_count"],
                        "completed_count": state.task_state["completed_count"],
                    },
                )
                continue

            payload = self._runtime._artifact_payload(step.name, artifact, case, status, blocking, warnings, valuation_values)
            self._apply_tool_context_to_payload(step, artifact, payload, tool_context, case, status)
            payload["source_fixture"] = source_fixture
            payload["agent_config"] = step.agent_config
            payload["agent_skills_allowed"] = list(step.skills)
            payload["claude_style_runtime"] = {
                "agent_type": self.definition.agent_type,
                "model": self.definition.model,
                "tools_allowed": self.definition.tools,
                "max_turns": self.definition.max_turns,
            }
            schema_validation = self._validate_payload_before_write(
                state,
                audit_log_path,
                executor,
                step,
                artifact,
                payload,
                artifact_path,
            )
            if schema_validation:
                payload["schema_validation"] = schema_validation

            contract_failures = validate_contract_rules(artifact, payload)
            if contract_failures:
                blocking = _unique([*blocking, *contract_failures])
                status = "A_REVOIR"
                self._record_event(
                    state,
                    audit_log_path,
                    {
                        "event": "contract_invalid",
                        "agent_type": step.name,
                        "artifact": artifact,
                        "failures": contract_failures,
                    },
                )
            formatting = self._format_payload_before_write(
                state,
                audit_log_path,
                executor,
                step,
                artifact,
                artifact_path,
            )
            if formatting:
                payload["formatting"] = formatting

            result = self._execute_tool(
                state,
                audit_log_path,
                executor,
                ClaudeToolCall(
                    id=f"{step.name}:{artifact}:write_file",
                    name="write_file",
                    input={"path": artifact_filename, "content": payload},
                    agent_type=step.name,
                ),
                artifact=artifact,
                path=artifact_path,
            )
            if not result.ok:
                raise RuntimeError(result.error)
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "artifact_written",
                    "agent_type": step.name,
                    "step": step.name,
                    "artifact": artifact,
                    "path": artifact_path.as_posix(),
                    "skills_allowed": list(step.skills),
                },
            )
            update_task_status(state.task_state, artifact, "completed")
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "task_completed",
                    "agent_type": step.name,
                    "task_id": f"{step.name}:{artifact}",
                    "artifact": artifact,
                    "pending_count": state.task_state["pending_count"],
                    "completed_count": state.task_state["completed_count"],
                },
            )

        self._record_event(
            state,
            audit_log_path,
            {
                "event": "agent_session_done",
                "agent_type": self.definition.agent_type,
                "status": status,
                "tool_use_count": state.tool_use_count,
            },
        )
        conversation_state = summarize_claude_messages(
            state.messages,
            agent_type=self.definition.agent_type,
            strict_tool_result_pairing=self.strict_tool_result_pairing,
        )
        context_state = build_context_state(
            state.messages,
            agent_type=self.definition.agent_type,
            threshold_tokens=self.context_compaction_threshold_tokens,
            preserve_recent_tool_results=self.preserve_recent_tool_results,
        )
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "conversation_state_validated",
                "agent_type": self.definition.agent_type,
                "ok": conversation_state["ok"],
                "messages_count": conversation_state["messages_count"],
                "tool_use_count": conversation_state["tool_use_count"],
                "tool_result_count": conversation_state["tool_result_count"],
                "pending_tool_use_ids": conversation_state["pending_tool_use_ids"],
                "orphan_tool_result_ids": conversation_state["orphan_tool_result_ids"],
            },
        )
        if context_state["needs_compaction"]:
            self._write_context_compact_summary(
                state,
                audit_log_path,
                case_dir,
                case_key,
                case_subdir,
                context_state,
            )
        permission_summary = summarize_permission_decisions(
            state.permission_decisions,
            agent_type=self.definition.agent_type,
        )
        token_budget = build_token_budget_state(
            agent_type=self.definition.agent_type,
            model_profile=self.definition.model_profile,
            budgets=self.definition.budgets,
            messages=state.messages,
            estimated_tokens=int(context_state["estimated_tokens"]),
        )
        state.token_budget_used = int(token_budget["estimated_tokens"])
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "token_budget_evaluated",
                "agent_type": self.definition.agent_type,
                "model": self.definition.model,
                "canonical_model": self.definition.model_profile.canonical_model,
                "estimated_tokens": token_budget["estimated_tokens"],
                "max_total_tokens": token_budget["max_total_tokens"],
                "remaining_total_tokens": token_budget["remaining_total_tokens"],
                "warnings_count": token_budget["warnings_count"],
            },
        )
        self._invoke_hook(
            state,
            audit_log_path,
            "SessionEnd",
            {
                "reason": "complete",
                "status": status,
                "tool_use_count": state.tool_use_count,
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
            },
        )
        hook_summary = summarize_hook_invocations(
            state.hook_invocations,
            agent_type=self.definition.agent_type,
        )
        message_envelope_summary = summarize_envelope_validation(state.messages, kind="message")
        event_envelope_summary = summarize_envelope_validation(state.events, kind="runtime_event")
        transcript_filename = (
            f"{self.definition.agent_type}.claude_transcript.jsonl"
            if case_subdir
            else f"{case_key}.{self.definition.agent_type}.claude_transcript.jsonl"
        )
        transcript_path = case_dir / transcript_filename
        transcript_summary = write_claude_transcript(
            transcript_path,
            state.messages,
            agent_type=self.definition.agent_type,
        )
        permission_state_filename = (
            f"{self.definition.agent_type}.claude_permissions.json"
            if case_subdir
            else f"{case_key}.{self.definition.agent_type}.claude_permissions.json"
        )
        permission_state_path = case_dir / permission_state_filename
        permission_state = build_permission_state_from_decisions(
            state.permission_decisions,
            agent_type=self.definition.agent_type,
            mode=self.permission_mode,
            allowed_tools=list(self.definition.tools),
            base_state=self.initial_permission_state,
        )
        permission_replay_summary = replay_permission_decisions(
            permission_state,
            state.permission_decisions,
            allowed_tools=list(self.definition.tools),
            tool_registry=self.tool_registry,
        )
        permission_state["replay"] = permission_replay_summary
        permission_state = write_permission_state(permission_state_path, permission_state)
        permission_state_summary = summarize_permission_state(permission_state)

        wall_clock_seconds = round(time.perf_counter() - started_at, 4)
        usage_accounting = build_usage_accounting(
            agent_type=self.definition.agent_type,
            model_profile=self.definition.model_profile,
            messages=state.messages,
            token_budget=token_budget,
            wall_clock_seconds=wall_clock_seconds,
            tool_use_count=state.tool_use_count,
        )
        return {
            "agent_type": self.definition.agent_type,
            "dossier_id": dossier_id,
            "status": status,
            "blocking_failures": blocking,
            "warnings": warnings,
            "events": state.events,
            "messages": state.messages,
            "handoffs_received": state.handoffs_received,
            "handoff_summary": handoff_summary,
            "conversation_state": conversation_state,
            "message_envelope_summary": message_envelope_summary,
            "event_envelope_summary": event_envelope_summary,
            "context_state": context_state,
            "settings_context": self.settings_context,
            "model_client": model_client_summary,
            "model_request": model_request.as_dict() if model_request is not None else {},
            "model_response": model_response.as_dict() if model_response is not None else {},
            "model_requests": model_client_summary.get("requests", [])
            if isinstance(model_client_summary, dict)
            else [],
            "model_responses": model_client_summary.get("responses", [])
            if isinstance(model_client_summary, dict)
            else [],
            "model_live_loop": live_loop_summary,
            "live_authored_artifacts": list(live_authored_artifacts.values()),
            "model_profile": self.definition.model_profile.as_dict(),
            "token_budget": token_budget,
            "usage_accounting": usage_accounting,
            "transcript_path": transcript_path.as_posix(),
            "transcript_summary": transcript_summary,
            "hook_invocations": state.hook_invocations,
            "hook_summary": hook_summary,
            "permission_decisions": state.permission_decisions,
            "permission_summary": permission_summary,
            "permission_state": permission_state,
            "permission_state_path": permission_state_path.as_posix(),
            "permission_state_summary": permission_state_summary,
            "permission_replay_summary": permission_replay_summary,
            "task_state": state.task_state,
            "audit_log": audit_log_path.as_posix(),
            "artifact_dir": case_dir.as_posix(),
            "skills_by_agent": {self.definition.agent_type: list(self.definition.skills)},
            "skill_context": self.skill_context,
            "command_context": self.command_context,
            "tools_by_agent": {self.definition.agent_type: list(self.definition.tools)},
            "tool_registry_summary": self.tool_registry_summary,
            "metrics": {
                "wall_clock_seconds": wall_clock_seconds,
                "total_tokens": state.token_budget_used,
                "input_tokens": usage_accounting["usage"]["input_tokens"],
                "output_tokens": usage_accounting["usage"]["output_tokens"],
                "cache_read_input_tokens": usage_accounting["usage"]["cache_read_input_tokens"],
                "cache_creation_input_tokens": usage_accounting["usage"]["cache_creation_input_tokens"],
                "web_search_requests": usage_accounting["usage"]["web_search_requests"],
                "total_cost_usd": usage_accounting["cost_usd"],
                "formatted_total_cost": usage_accounting["formatted_cost"],
                "tool_use_count": state.tool_use_count,
                "model_input_tokens": model_client_summary.get("input_tokens", 0)
                if isinstance(model_client_summary, dict)
                else 0,
                "model_output_tokens": model_client_summary.get("output_tokens", 0)
                if isinstance(model_client_summary, dict)
                else 0,
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
            },
        }

    def _maybe_invoke_model_client(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        system_prompt: list[str],
        context: dict[str, object],
        *,
        step_outputs: list[str],
        artifact_filenames: dict[str, str],
        case_dir: Path,
    ) -> tuple[ClaudeModelRequest | None, ClaudeModelResponse | None, dict[str, object]]:
        if self.model_client is None:
            return None, None, summarize_model_client_interaction(
                request=None,
                response=None,
                enabled=False,
            )

        max_turns = max(1, int(self.definition.max_turns or 1))
        requests: list[ClaudeModelRequest] = []
        responses: list[ClaudeModelResponse] = []
        input_tokens = 0
        output_tokens = 0
        tool_calls_count = 0
        tool_results_count = 0
        errors: list[str] = []
        stop_reason = "max_turns"
        artifacts_written: list[dict[str, object]] = []
        failed_tool_calls: list[dict[str, object]] = []
        permission_requests: list[dict[str, object]] = []
        self._append_message(
            state,
            "user",
            self.definition.agent_type,
            [
                {
                    "type": "text",
                    "text": (
                        "Execute this eval-immo agent run. Produce the required artifacts "
                        "through the configured tools and respect the runtime contract."
                    ),
                    "expected_outputs": list(step_outputs),
                }
            ],
            metadata={"source": "model_client_request"},
        )
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "model_live_tool_loop_started",
                "agent_type": self.definition.agent_type,
                "provider": self.model_client.provider,
                "model": self.definition.model,
                "max_turns": max_turns,
                "expected_outputs": list(step_outputs),
            },
        )
        for turn in range(1, max_turns + 1):
            request = ClaudeModelRequest(
                agent_type=self.definition.agent_type,
                model=self.definition.model,
                system_prompt=system_prompt,
                messages=list(state.messages),
                context=context,
                tools=list(self.definition.tools),
                skills=list(self.definition.skills),
                expected_outputs=list(step_outputs),
                runtime_mode=self.runtime_mode,
            )
            requests.append(request)
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "model_request_started",
                    "agent_type": self.definition.agent_type,
                    "provider": self.model_client.provider,
                    "model": self.definition.model,
                    "turn": turn,
                    "messages_count": len(request.messages),
                    "expected_outputs": list(step_outputs),
                    "request": request.as_dict(),
                },
            )
            try:
                response = self.model_client.complete(request)
            except (ModelProviderConfigurationError, ModelProviderTransportError) as exc:
                stop_reason = "model_error"
                error_code = getattr(exc, "code", str(exc)) or type(exc).__name__
                errors.append(f"model_error:{error_code}")
                self._record_event(
                    state,
                    audit_log_path,
                    {
                        "event": "model_error",
                        "agent_type": self.definition.agent_type,
                        "provider": self.model_client.provider,
                        "turn": turn,
                        "error": error_code,
                    },
                )
                break
            except Exception as exc:
                stop_reason = "model_error"
                error_code = f"{type(exc).__name__}: {exc}"
                errors.append(f"model_error:{error_code}")
                self._record_event(
                    state,
                    audit_log_path,
                    {
                        "event": "model_error",
                        "agent_type": self.definition.agent_type,
                        "provider": self.model_client.provider,
                        "turn": turn,
                        "error": error_code,
                    },
                )
                break

            responses.append(response)
            usage = response.usage if isinstance(response.usage, dict) else {}
            input_tokens += int(usage.get("input_tokens", 0) or 0)
            output_tokens += int(usage.get("output_tokens", 0) or 0)
            interaction_summary = summarize_model_client_interaction(
                request=request,
                response=response,
                enabled=True,
                provider=self.model_client.provider,
            )
            response_errors = [
                str(error)
                for error in interaction_summary.get("errors", [])
                if str(error)
            ]
            if response.content:
                self._append_message(
                    state,
                    "assistant",
                    self.definition.agent_type,
                    response.content,
                    metadata={
                        "source": "model_client_response",
                        "provider": response.provider,
                        "stop_reason": response.stop_reason,
                        "usage": response.usage,
                        "turn": turn,
                    },
                )
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "model_response_received",
                    "agent_type": self.definition.agent_type,
                    "provider": response.provider,
                    "model": response.model,
                    "turn": turn,
                    "stop_reason": response.stop_reason,
                    "content_blocks_count": len(response.content),
                    "tool_calls_count": len(response.tool_calls),
                    "ok": not response_errors,
                    "input_tokens": int(usage.get("input_tokens", 0) or 0),
                    "output_tokens": int(usage.get("output_tokens", 0) or 0),
                    "response": response.as_dict(),
                    **({"errors": response_errors} if response_errors else {}),
                },
            )
            if response_errors:
                stop_reason = "model_error"
                errors.extend(f"response:{error}" for error in response_errors)
                break

            tool_calls = self._tool_calls_from_model_response(response)
            tool_calls_count += len(tool_calls)
            if not tool_calls:
                if response.stop_reason in {"end_turn", "stop_sequence"}:
                    stop_reason = "completion"
                else:
                    stop_reason = "model_error"
                    errors.append(f"model_stopped:{response.stop_reason}")
                break

            for call in tool_calls:
                artifact, path = self._live_tool_call_artifact_path(call, step_outputs)
                if call.name == "write_file" and artifact and artifact_filenames.get(artifact):
                    canonical_path = artifact_filenames[artifact]
                    call = ClaudeToolCall(
                        id=call.id,
                        name=call.name,
                        input={**call.input, "path": canonical_path},
                        agent_type=call.agent_type,
                    )
                    path = case_dir / canonical_path
                contract_failure = self._validate_live_tool_call_contract(
                    call,
                    step_outputs,
                    artifact=artifact,
                )
                result = self._execute_tool(
                    state,
                    audit_log_path,
                    executor,
                    call,
                    artifact=artifact,
                    path=path,
                    append_tool_call_message=False,
                    preflight_failure=contract_failure,
                    record_artifact_written=True,
                    artifact_source="live_model",
                )
                tool_results_count += 1
                if result.ok and call.name == "write_file" and artifact:
                    artifacts_written.append(
                        {
                            "artifact": artifact,
                            "path": path.as_posix() if path else str(call.input.get("path") or ""),
                            "tool_call_id": call.id,
                            "turn": turn,
                            "source": "live_model",
                            "adopted": True,
                        }
                    )
                if not result.ok:
                    stop_reason = self._live_tool_failure_stop_reason(
                        state,
                        call,
                        contract_failure=bool(contract_failure),
                    )
                    errors.append(result.error or stop_reason)
                    failed_tool_calls.append(
                        {
                            "tool_call_id": call.id,
                            "tool": call.name,
                            "input": dict(call.input),
                            "artifact": artifact or "",
                            "path": path.as_posix() if path else str(call.input.get("path") or ""),
                            "turn": turn,
                            "stop_reason": stop_reason,
                            "error": result.error or "",
                            "retryable": stop_reason in {"tool_error", "permission_required"},
                        }
                    )
                    if stop_reason == "permission_required":
                        permission_requests.append(
                            {
                                "tool_call_id": call.id,
                                "tool": call.name,
                                "agent_type": call.agent_type,
                                "permission": result.permission or "",
                                "reason": "permission_state_ask_rule",
                                "recommended_update": {
                                    "behavior": "allow",
                                    "scope": "project",
                                    "rules": [{"toolName": call.name}],
                                },
                            }
                        )
                    break
            if stop_reason in {"contract_failure", "tool_error", "permission_required"}:
                break

        live_loop_summary = {
            "schema_version": "claude_live_tool_loop_v0",
            "enabled": True,
            "provider": self.model_client.provider,
            "agent_type": self.definition.agent_type,
            "max_turns": max_turns,
            "turns_count": len(responses),
            "requests_count": len(requests),
            "responses_count": len(responses),
            "tool_calls_count": tool_calls_count,
            "tool_results_count": tool_results_count,
            "stop_reason": stop_reason,
            "artifacts_written": artifacts_written,
            "adopted_artifacts_count": len(artifacts_written),
            "failed_tool_calls": failed_tool_calls,
            "permission_requests": permission_requests,
            "permission_requests_count": len(permission_requests),
            "errors": errors,
            "ok": stop_reason == "completion" and not errors,
        }
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "model_live_tool_loop_completed",
                "agent_type": self.definition.agent_type,
                "provider": self.model_client.provider,
                "stop_reason": stop_reason,
                "turns_count": len(responses),
                "tool_calls_count": tool_calls_count,
                "tool_results_count": tool_results_count,
                "adopted_artifacts_count": len(artifacts_written),
                "permission_requests_count": len(permission_requests),
                "ok": live_loop_summary["ok"],
                **({"errors": errors} if errors else {}),
            },
        )
        request = requests[0] if requests else None
        response = responses[-1] if responses else None
        summary = {
            "schema_version": "claude_model_client_summary_v0",
            "enabled": True,
            "provider": response.provider if response else self.model_client.provider,
            "agent_type": self.definition.agent_type,
            "model": response.model if response else self.definition.model,
            "requests_count": len(requests),
            "responses_count": len(responses),
            "request_schema_version": "claude_model_request_v0" if request is not None else "",
            "response_schema_version": "claude_model_response_v0" if response is not None else "",
            "stop_reason": response.stop_reason if response else stop_reason,
            "content_blocks_count": len(response.content) if response else 0,
            "tool_calls_count": tool_calls_count,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "errors": errors,
            "ok": not errors and stop_reason == "completion",
            "requests": [item.as_dict() for item in requests],
            "responses": [item.as_dict() for item in responses],
            "live_tool_loop": live_loop_summary,
        }
        return request, response, summary

    def _live_authored_artifacts_from_summary(
        self,
        live_loop_summary: dict[str, object],
    ) -> dict[str, dict[str, object]]:
        adopted: dict[str, dict[str, object]] = {}
        records = live_loop_summary.get("artifacts_written", [])
        if not isinstance(records, list):
            return adopted
        for record in records:
            if not isinstance(record, dict) or not record.get("adopted", False):
                continue
            artifact = str(record.get("artifact") or "")
            path = Path(str(record.get("path") or ""))
            if artifact and path.exists() and path.is_file():
                adopted[artifact] = dict(record)
        return adopted

    def _live_tool_failure_stop_reason(
        self,
        state: ClaudeAgentState,
        call: ClaudeToolCall,
        *,
        contract_failure: bool,
    ) -> str:
        if contract_failure:
            return "contract_failure"
        for decision in reversed(state.permission_decisions):
            if decision.get("tool_call_id") != call.id:
                continue
            if decision.get("reason") == "permission_state_ask_rule":
                return "permission_required"
            if decision.get("reason") in {"tool_not_allowed_for_agent", "permission_state_deny_rule", "plan_mode_requires_approval"}:
                return "tool_error"
            break
        return "tool_error"

    def _tool_calls_from_model_response(self, response: ClaudeModelResponse) -> list[ClaudeToolCall]:
        raw_calls = [
            dict(call)
            for call in response.tool_calls
            if isinstance(call, dict)
        ]
        if not raw_calls:
            raw_calls = [
                dict(block)
                for block in response.content
                if isinstance(block, dict) and block.get("type") == "tool_use"
            ]
        calls: list[ClaudeToolCall] = []
        for index, raw_call in enumerate(raw_calls, start=1):
            raw_input = raw_call.get("input", {})
            calls.append(
                ClaudeToolCall(
                    id=str(raw_call.get("id") or raw_call.get("tool_use_id") or f"model-tool-{index}"),
                    name=str(raw_call.get("name") or ""),
                    input=dict(raw_input) if isinstance(raw_input, dict) else {},
                    agent_type=self.definition.agent_type,
                )
            )
        return calls

    def _live_tool_call_artifact_path(
        self,
        call: ClaudeToolCall,
        expected_outputs: list[str],
    ) -> tuple[str | None, Path | None]:
        if call.name != "write_file":
            return None, None
        raw_path = str(call.input.get("path") or "")
        if not raw_path:
            return None, None
        path_name = Path(raw_path).name
        for artifact in expected_outputs:
            if path_name == artifact or path_name.endswith(f".{artifact}"):
                return artifact, Path(raw_path)
        return None, Path(raw_path)

    def _validate_live_tool_call_contract(
        self,
        call: ClaudeToolCall,
        expected_outputs: list[str],
        *,
        artifact: str | None,
    ) -> dict[str, object] | None:
        if call.name != "write_file":
            return None
        failures: list[str] = []
        if artifact is None:
            failures.append("artifact_not_declared_for_agent")
        content = call.input.get("content")
        if not isinstance(content, dict):
            failures.append("content_not_object")
        if artifact and isinstance(content, dict):
            required_fields = REQUIRED_FIELDS_BY_ARTIFACT.get(artifact, REQUIRED_FIELDS_BY_ARTIFACT["default"])
            ok, missing = validate_schema(content, required_fields)
            if not ok:
                failures.append(f"SCHEMA: champs manquants {missing}")
            failures.extend(validate_contract_rules(artifact, content))
        if not failures:
            return None
        return {
            "schema_version": "claude_live_tool_contract_validation_v0",
            "tool_call_id": call.id,
            "tool": call.name,
            "agent_type": call.agent_type,
            "artifact": artifact or "",
            "path": str(call.input.get("path") or ""),
            "expected_outputs": list(expected_outputs),
            "failures": _unique(failures),
            "ok": False,
        }

    def _write_context_compact_summary(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        case_dir: Path,
        case_key: str,
        case_subdir: bool,
        context_state: dict[str, object],
    ) -> None:
        artifact = "context_compact_summary.json"
        artifact_filename = f"{self.definition.agent_type}.{artifact}" if case_subdir else f"{case_key}.{self.definition.agent_type}.{artifact}"
        artifact_path = case_dir / artifact_filename
        self._invoke_hook(
            state,
            audit_log_path,
            "PreCompact",
            {
                "trigger": "auto",
                "estimated_tokens": context_state["estimated_tokens"],
                "threshold_tokens": context_state["threshold_tokens"],
                "preserve_recent_tool_results": context_state["preserve_recent_tool_results"],
            },
        )
        payload = build_context_compact_summary(
            state.messages,
            context_state,
            agent_type=self.definition.agent_type,
        )
        write_artifact_payload(artifact_path, payload)
        context_state["compact_summary_artifact"] = artifact_path.as_posix()
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "context_compacted",
                "agent_type": self.definition.agent_type,
                "estimated_tokens": context_state["estimated_tokens"],
                "threshold_tokens": context_state["threshold_tokens"],
                "preserved_tool_result_ids": context_state["preserved_tool_result_ids"],
                "path": artifact_path.as_posix(),
            },
        )
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "artifact_written",
                "agent_type": self.definition.agent_type,
                "step": self.definition.agent_type,
                "artifact": artifact,
                "path": artifact_path.as_posix(),
                "skills_allowed": list(self.definition.skills),
            },
        )
        self._invoke_hook(
            state,
            audit_log_path,
            "PostCompact",
            {
                "trigger": "auto",
                "estimated_tokens": context_state["estimated_tokens"],
                "threshold_tokens": context_state["threshold_tokens"],
                "compact_summary_artifact": artifact_path.as_posix(),
            },
        )

    def _prepare_agent_tool_context(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        case: dict,
        step: RuntimeStep,
        *,
        source_fixture: str,
        status: str,
        blocking: list[str],
        warnings: list[str],
    ) -> dict[str, object]:
        if step.name == "data-facts":
            return self._prepare_data_facts_context(case, step, source_fixture)
        if step.name == "comps-market" and "search_comparables" in self.definition.tools:
            return self._prepare_comps_market_context(
                state,
                audit_log_path,
                executor,
                case,
                step,
                source_fixture,
                state.handoffs_received,
            )
        if step.name == "valuation-draft" and "run_calculation" in self.definition.tools:
            return self._prepare_valuation_context(
                state,
                audit_log_path,
                executor,
                case,
                step,
                source_fixture,
                state.handoffs_received,
            )
        if step.name == "compliance-qa":
            return self._prepare_compliance_qa_context(
                case,
                step,
                source_fixture,
                status,
                blocking,
                warnings,
                state.handoffs_received,
            )
        if step.name == "redaction":
            return self._prepare_redaction_context(case, step, source_fixture, state.handoffs_received)
        return {}

    def _prepare_data_facts_context(
        self,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
    ) -> dict[str, object]:
        source_lineage = self._build_data_facts_source_lineage(case)
        manifest = self._build_data_facts_extraction_manifest(
            case,
            step,
            source_fixture=source_fixture,
            source_lineage=source_lineage,
        )
        return {
            "source_lineage": source_lineage,
            "extraction_manifest": manifest,
        }

    def _build_data_facts_source_lineage(self, case: dict) -> list[dict[str, object]]:
        source_ids = collect_source_ids(case)
        lineage_by_id: dict[str, dict[str, object]] = {}

        def append_unique(values: list[str], value: str) -> None:
            if value and value not in values:
                values.append(value)

        def source_row(source_id: str) -> dict[str, object]:
            if source_id not in lineage_by_id:
                lineage_by_id[source_id] = {
                    "source_id": source_id,
                    "source_type": "case_source_id",
                    "referenced_by": [],
                    "records": [],
                    "reliability_level": "A_VALIDER",
                }
            return lineage_by_id[source_id]

        def add_reference(source_id: object, section: str, record_id: object | None = None) -> None:
            source_id_text = str(source_id or "").strip()
            if not source_id_text:
                return
            row = source_row(source_id_text)
            append_unique(row["referenced_by"], section)  # type: ignore[arg-type]
            if record_id is not None:
                append_unique(row["records"], f"{section}:{record_id}")  # type: ignore[arg-type]

        for comparable in case.get("comparables", []):
            if isinstance(comparable, dict):
                add_reference(comparable.get("source_id"), "comparables", comparable.get("comparable_id"))

        for ajustement in case.get("ajustements", []):
            if isinstance(ajustement, dict):
                add_reference(ajustement.get("source_id"), "ajustements", ajustement.get("ajustement_id"))

        for index, hypothese in enumerate(case.get("hypotheses", []), start=1):
            if not isinstance(hypothese, dict):
                continue
            record_id = hypothese.get("hypothese_id") or hypothese.get("id") or index
            raw_source_ids = hypothese.get("source_ids", [])
            if isinstance(raw_source_ids, list):
                for source_id in raw_source_ids:
                    add_reference(source_id, "hypotheses", record_id)

        for index, event in enumerate(case.get("timeline", []), start=1):
            if isinstance(event, dict):
                record_id = event.get("event_id") or event.get("type") or index
                add_reference(event.get("source_id"), "timeline", record_id)

        ordered_lineage = [lineage_by_id[source_id] for source_id in source_ids if source_id in lineage_by_id]
        for source_id, row in lineage_by_id.items():
            if source_id not in source_ids:
                ordered_lineage.append(row)
        return ordered_lineage

    def _build_data_facts_extraction_manifest(
        self,
        case: dict,
        step: RuntimeStep,
        *,
        source_fixture: str,
        source_lineage: list[dict[str, object]],
    ) -> dict[str, object]:
        source_ids = [str(row["source_id"]) for row in source_lineage if row.get("source_id")]

        def value_present(value: object) -> bool:
            if value is None:
                return False
            if isinstance(value, str):
                return bool(value.strip())
            if isinstance(value, (list, dict)):
                return bool(value)
            return True

        tracked_fields = {
            "dossier_id": case.get("dossier_id"),
            "date_reference": case.get("date_reference"),
            "surface": case.get("surface"),
            "type_bien": case.get("type_bien"),
            "zone": case.get("zone"),
            "adresse_anonymisee": case.get("adresse_anonymisee"),
            "confidence": case.get("confidence"),
            "source_ids": source_ids,
        }
        fields = [
            {
                "field": field,
                "present": value_present(value),
                "source_reference": source_fixture,
                "source_ids": source_ids if value_present(value) else [],
                "confidence": case.get("confidence"),
            }
            for field, value in tracked_fields.items()
        ]
        missing_fields = [str(row["field"]) for row in fields if not row["present"]]
        unsourced_fields = [
            str(row["field"])
            for row in fields
            if row["present"] and not row["source_ids"] and not row["source_reference"]
        ]
        source_coverage_status = "OK" if source_ids or source_fixture else "A_COMPLETER"
        extraction_completeness_status = "OK" if not missing_fields else "A_COMPLETER"
        return {
            "schema_version": "data_facts_extraction_manifest_v1",
            "agent_type": step.name,
            "source_fixture": source_fixture,
            "source_ids": source_ids,
            "fields": fields,
            "missing_fields": missing_fields,
            "unsourced_fields": unsourced_fields,
            "source_coverage_status": source_coverage_status,
            "extraction_completeness_status": extraction_completeness_status,
            "human_validation_required": True,
            "policy": [
                "Aucune valeur absente n'est simulee.",
                "Toute valeur critique sans source reste a valider par un evaluateur.",
            ],
            "ok": source_coverage_status == "OK" and not unsourced_fields,
        }

    def _prepare_comps_market_context(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        handoffs: list[dict[str, object]],
    ) -> dict[str, object]:
        pool = case.get("comparables", [])
        if not isinstance(pool, list):
            pool = []
        result = self._execute_tool(
            state,
            audit_log_path,
            executor,
            ClaudeToolCall(
                id=f"{step.name}:search_comparables",
                name="search_comparables",
                input={
                    "pool": pool,
                    "subject": case,
                    "date_reference": case.get("date_reference") or "",
                    "max_items": 5,
                },
                agent_type=step.name,
            ),
        )
        if not result.ok:
            raise RuntimeError(result.error)
        search_output = result.output if isinstance(result.output, dict) else {}
        selected_comparables = search_output.get("comparables", [])
        if not isinstance(selected_comparables, list):
            selected_comparables = []
        selection_protocol = self._build_comps_market_selection_protocol(
            case,
            step,
            source_fixture,
            pool,
            selected_comparables,
        )
        source_coverage = self._build_comps_market_source_coverage(pool, selected_comparables, source_fixture)
        return {
            "search_comparables": search_output,
            "market_selection_protocol": selection_protocol,
            "market_source_coverage": source_coverage,
            "market_handoff_context": self._build_comps_market_handoff_context(handoffs),
            "market_human_review_gate": self._build_comps_market_human_review_gate(selection_protocol),
        }

    def _build_comps_market_selection_protocol(
        self,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        pool: list[object],
        selected_comparables: list[object],
    ) -> dict[str, object]:
        selected_ids_in_order = [
            str(comparable.get("comparable_id") or "")
            for comparable in selected_comparables
            if isinstance(comparable, dict)
        ]
        selected_ids = set(selected_ids_in_order)
        rejected: list[dict[str, object]] = []
        sourced_candidate_count = 0
        for comparable in pool:
            if not isinstance(comparable, dict):
                continue
            comparable_id = str(comparable.get("comparable_id") or "")
            source_id = str(comparable.get("source_id") or "")
            if source_id:
                sourced_candidate_count += 1
            if comparable_id in selected_ids:
                continue
            reason = "source manquante" if not source_id else "non retenu par le classement des comparables"
            rejected.append(
                {
                    "comparable_id": comparable_id,
                    "source_id": source_id,
                    "decision": "rejete",
                    "reason": reason,
                }
            )

        score_details = {}
        for comparable in selected_comparables:
            if isinstance(comparable, dict) and isinstance(comparable.get("score_details"), dict):
                score_details = comparable["score_details"]
                break

        selected_source_ids = [
            str(comparable.get("source_id"))
            for comparable in selected_comparables
            if isinstance(comparable, dict) and comparable.get("source_id")
        ]
        source_coverage_status = "OK" if selected_comparables and len(selected_source_ids) == len(selected_comparables) else "A_COMPLETER"
        return {
            "schema_version": "comps_market_selection_protocol_v1",
            "agent_type": step.name,
            "source_fixture": source_fixture,
            "date_reference": case.get("date_reference"),
            "candidate_pool_count": len([item for item in pool if isinstance(item, dict)]),
            "sourced_candidate_count": sourced_candidate_count,
            "selected_count": len(selected_comparables),
            "rejected_count": len(rejected),
            "selected_comparable_ids": [comparable_id for comparable_id in selected_ids_in_order if comparable_id],
            "rejected_comparables": rejected,
            "scoring_weights": score_details.get("weights", {}) if isinstance(score_details, dict) else {},
            "source_coverage_status": source_coverage_status,
            "human_validation_required": True,
            "policy": [
                "Ne jamais inventer de vente comparable.",
                "Exclure les comparables sans source_id avant tout classement.",
                "Conserver les raisons de selection ou de rejet pour revision humaine.",
            ],
            "ok": source_coverage_status == "OK",
        }

    def _build_comps_market_source_coverage(
        self,
        pool: list[object],
        selected_comparables: list[object],
        source_fixture: str,
    ) -> dict[str, object]:
        selected_source_ids = [
            str(comparable.get("source_id"))
            for comparable in selected_comparables
            if isinstance(comparable, dict) and comparable.get("source_id")
        ]
        pool_source_ids = [
            str(comparable.get("source_id"))
            for comparable in pool
            if isinstance(comparable, dict) and comparable.get("source_id")
        ]
        missing_source_count = len(
            [comparable for comparable in pool if isinstance(comparable, dict) and not comparable.get("source_id")]
        )
        source_rows = []
        for source_id in _unique([*selected_source_ids, *pool_source_ids]):
            selected_ids = [
                str(comparable.get("comparable_id") or "")
                for comparable in selected_comparables
                if isinstance(comparable, dict) and str(comparable.get("source_id") or "") == source_id
            ]
            pool_ids = [
                str(comparable.get("comparable_id") or "")
                for comparable in pool
                if isinstance(comparable, dict) and str(comparable.get("source_id") or "") == source_id
            ]
            source_rows.append(
                {
                    "source_id": source_id,
                    "used_by": ["comparables_proposes.json"] if selected_ids else ["justifications_comparables.json"],
                    "selected_comparable_ids": [item for item in selected_ids if item],
                    "candidate_comparable_ids": [item for item in pool_ids if item],
                    "validation_status": "A_VALIDER",
                }
            )
        return {
            "schema_version": "comps_market_source_coverage_v1",
            "source_fixture": source_fixture,
            "selected_source_ids": _unique(selected_source_ids),
            "candidate_source_ids": _unique(pool_source_ids),
            "missing_source_count": missing_source_count,
            "sources": source_rows,
            "coverage_status": "OK" if selected_source_ids and missing_source_count == 0 else "A_COMPLETER",
        }

    def _build_comps_market_handoff_context(self, handoffs: list[dict[str, object]]) -> dict[str, object]:
        valid_handoffs = [handoff for handoff in handoffs if isinstance(handoff, dict)]
        artifacts: list[dict[str, object]] = []
        for handoff in valid_handoffs:
            from_agent = str(handoff.get("from_agent") or "")
            for artifact in handoff.get("artifacts", []):
                if isinstance(artifact, dict):
                    artifacts.append(
                        {
                            "from_agent": from_agent,
                            "artifact": str(artifact.get("artifact") or ""),
                            "path": str(artifact.get("path") or ""),
                        }
                    )
        return {
            "schema_version": "comps_market_handoff_context_v1",
            "handoffs_count": len(valid_handoffs),
            "from_agents": _unique(
                [str(handoff.get("from_agent") or "") for handoff in valid_handoffs if handoff.get("from_agent")]
            ),
            "artifacts_count": len(artifacts),
            "artifacts": artifacts,
        }

    def _build_comps_market_human_review_gate(self, selection_protocol: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "comps_market_human_review_gate_v1",
            "required": bool(self.definition.human_validation.get("required", True)),
            "checkpoints": list(self.definition.human_validation.get("checkpoints", [])),
            "status": "A_VALIDER",
            "selected_count": selection_protocol.get("selected_count", 0),
            "blocking_policy": "liste_finale_comparables_a_valider",
        }

    def _prepare_valuation_context(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        handoffs: list[dict[str, object]],
    ) -> dict[str, object]:
        comparable_pool = case.get("comparables", [])
        if not isinstance(comparable_pool, list):
            comparable_pool = []
        adjustment_rows = case.get("ajustements", [])
        if not isinstance(adjustment_rows, list):
            adjustment_rows = []

        comparables = [
            comparable.__dict__
            for comparable in search_comparables(
                comparable_pool,
                max_items=5,
                subject=case,
                date_reference=case.get("date_reference"),
            )
        ]
        prices = [float(comparable["prix_vente"]) for comparable in comparables if comparable.get("prix_vente")]
        weights = [max(float(comparable.get("score", 0)), 0.01) for comparable in comparables if comparable.get("prix_vente")]
        adjustment_total = sum(float(item.get("montant", 0) or 0) for item in adjustment_rows if isinstance(item, dict) and item.get("validation_humaine", False))

        calculation_plan = {
            "approche_comparative": {
                "tool_method": "weighted_mean",
                "artifact_method": "weighted_mean_score_v0",
                "weights": weights,
            },
            "approche_cout": {
                "tool_method": "mean",
                "artifact_method": "proxy_mean_cost_v0",
                "weights": None,
            },
            "approche_revenu": {
                "tool_method": "median",
                "artifact_method": "proxy_median_income_v0",
                "weights": None,
            },
        }
        traces: dict[str, dict[str, object]] = {}
        for approach, plan in calculation_plan.items():
            tool_input: dict[str, object] = {
                "method": plan["tool_method"],
                "values": prices,
            }
            if plan["weights"] is not None:
                tool_input["weights"] = plan["weights"]
            result = self._execute_tool(
                state,
                audit_log_path,
                executor,
                ClaudeToolCall(
                    id=f"{step.name}:{approach}:run_calculation",
                    name="run_calculation",
                    input=tool_input,
                    agent_type=step.name,
                ),
            )
            if not result.ok:
                raise RuntimeError(result.error)
            output = result.output if isinstance(result.output, dict) else {}
            base_value = float(output.get("value") or 0.0)
            traces[approach] = self._valuation_trace_payload(
                approach,
                str(plan["artifact_method"]),
                base_value,
                prices,
                weights,
                adjustment_total,
                comparables,
            )
        methodology_plan = self._build_valuation_methodology_plan(
            case,
            step,
            source_fixture,
            comparables,
            adjustment_rows,
            calculation_plan,
        )
        reconciliation = self._build_valuation_reconciliation(traces)
        source_coverage = self._build_valuation_source_coverage(
            comparable_pool,
            comparables,
            adjustment_rows,
            case.get("hypotheses", []),
            source_fixture,
        )
        return {
            "valuation_traces": traces,
            "valuation_methodology_plan": methodology_plan,
            "valuation_reconciliation": reconciliation,
            "valuation_source_coverage": source_coverage,
            "valuation_handoff_context": self._build_valuation_handoff_context(handoffs),
            "valuation_human_review_gate": self._build_valuation_human_review_gate(reconciliation),
        }

    def _valuation_trace_payload(
        self,
        approach: str,
        method: str,
        base_value: float,
        prices: list[float],
        weights: list[float],
        adjustment_total: float,
        comparables: list[dict[str, object]],
    ) -> dict[str, object]:
        return {
            "approach": approach,
            "method": method,
            "value": round(base_value + adjustment_total, 2) if prices else 0.0,
            "input_count": len(prices),
            "trace": {
                "base_value": round(base_value, 2) if prices else 0.0,
                "adjustment_total_validated": round(adjustment_total, 2),
                "selected_comparables": comparables,
                "weights_used": [round(weight, 4) for weight in weights],
                "calculation_policy": [
                    "Les comparables sans source_id sont exclus avant calcul.",
                    "L'approche comparative utilise une moyenne ponderee par score explicable.",
                    "Les approches cout/revenu restent des proxys v0 tant que les tables metier ne sont pas calibrees.",
                    "Seuls les ajustements avec validation_humaine=true sont appliques.",
                ],
            },
        }

    def _build_valuation_methodology_plan(
        self,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        comparables: list[dict[str, object]],
        adjustment_rows: list[object],
        calculation_plan: dict[str, dict[str, object]],
    ) -> dict[str, object]:
        validated_adjustments = [
            adjustment
            for adjustment in adjustment_rows
            if isinstance(adjustment, dict) and adjustment.get("validation_humaine", False)
        ]
        excluded_adjustments = [
            {
                "ajustement_id": str(adjustment.get("ajustement_id") or ""),
                "source_id": str(adjustment.get("source_id") or ""),
                "reason": "validation_humaine_absente",
            }
            for adjustment in adjustment_rows
            if isinstance(adjustment, dict) and not adjustment.get("validation_humaine", False)
        ]
        return {
            "schema_version": "valuation_methodology_plan_v1",
            "agent_type": step.name,
            "source_fixture": source_fixture,
            "date_reference": case.get("date_reference"),
            "approaches": [
                {
                    "approach": approach,
                    "tool_method": str(plan.get("tool_method") or ""),
                    "artifact_method": str(plan.get("artifact_method") or ""),
                    "input_source": "comparables_confirmes",
                    "human_validation_required": approach == "approche_comparative",
                }
                for approach, plan in calculation_plan.items()
            ],
            "selected_comparable_ids": [
                str(comparable.get("comparable_id") or "")
                for comparable in comparables
                if comparable.get("comparable_id")
            ],
            "selected_comparables_count": len(comparables),
            "validated_adjustments_count": len(validated_adjustments),
            "excluded_adjustments": excluded_adjustments,
            "policy": [
                "Les calculs ne creent aucune vente comparable.",
                "Les ajustements non valides humainement sont exclus du total applique.",
                "La reconciliation reste preliminaire tant que la revision humaine est requise.",
            ],
        }

    def _build_valuation_reconciliation(self, traces: dict[str, dict[str, object]]) -> dict[str, object]:
        values = {
            approach: float(trace.get("value") or 0.0)
            for approach, trace in traces.items()
            if isinstance(trace, dict)
        }
        non_zero_values = [value for value in values.values() if value > 0]
        min_value = min(non_zero_values) if non_zero_values else 0.0
        max_value = max(non_zero_values) if non_zero_values else 0.0
        delta_ratio = round((max_value - min_value) / min_value, 4) if min_value else 0.0
        preliminary_value = values.get("approche_comparative") or (round(sum(non_zero_values) / len(non_zero_values), 2) if non_zero_values else 0.0)
        return {
            "schema_version": "valuation_reconciliation_v1",
            "approach_values": {approach: round(value, 2) for approach, value in values.items()},
            "preliminary_value": round(preliminary_value, 2),
            "preferred_approach": "approche_comparative",
            "min_value": round(min_value, 2),
            "max_value": round(max_value, 2),
            "delta_ratio": delta_ratio,
            "status": "A_VALIDER",
            "human_validation_required": True,
            "policy": [
                "L'approche comparative est preferee en v0 lorsque des comparables sources existent.",
                "Les approches cout et revenu demeurent des proxys jusqu'au calibrage metier.",
            ],
        }

    def _build_valuation_source_coverage(
        self,
        comparable_pool: list[object],
        selected_comparables: list[dict[str, object]],
        adjustment_rows: list[object],
        hypotheses: object,
        source_fixture: str,
    ) -> dict[str, object]:
        selected_source_ids = [
            str(comparable.get("source_id"))
            for comparable in selected_comparables
            if comparable.get("source_id")
        ]
        pool_source_ids = [
            str(comparable.get("source_id"))
            for comparable in comparable_pool
            if isinstance(comparable, dict) and comparable.get("source_id")
        ]
        adjustment_source_ids = [
            str(adjustment.get("source_id"))
            for adjustment in adjustment_rows
            if isinstance(adjustment, dict) and adjustment.get("source_id")
        ]
        hypothesis_source_ids: list[str] = []
        if isinstance(hypotheses, list):
            for hypothese in hypotheses:
                if not isinstance(hypothese, dict):
                    continue
                raw_source_ids = hypothese.get("source_ids", [])
                if isinstance(raw_source_ids, list):
                    hypothesis_source_ids.extend(str(source_id) for source_id in raw_source_ids if source_id)
        missing_comparable_source_count = len(
            [comparable for comparable in comparable_pool if isinstance(comparable, dict) and not comparable.get("source_id")]
        )
        unvalidated_adjustments = [
            {
                "ajustement_id": str(adjustment.get("ajustement_id") or ""),
                "source_id": str(adjustment.get("source_id") or ""),
            }
            for adjustment in adjustment_rows
            if isinstance(adjustment, dict) and not adjustment.get("validation_humaine", False)
        ]
        source_ids = _unique([*selected_source_ids, *pool_source_ids, *adjustment_source_ids, *hypothesis_source_ids])
        return {
            "schema_version": "valuation_source_coverage_v1",
            "source_fixture": source_fixture,
            "source_ids": source_ids,
            "selected_comparable_source_ids": _unique(selected_source_ids),
            "adjustment_source_ids": _unique(adjustment_source_ids),
            "hypothesis_source_ids": _unique(hypothesis_source_ids),
            "missing_comparable_source_count": missing_comparable_source_count,
            "unvalidated_adjustments": unvalidated_adjustments,
            "coverage_status": "OK" if selected_source_ids and missing_comparable_source_count == 0 else "A_COMPLETER",
        }

    def _build_valuation_handoff_context(self, handoffs: list[dict[str, object]]) -> dict[str, object]:
        valid_handoffs = [handoff for handoff in handoffs if isinstance(handoff, dict)]
        artifacts: list[dict[str, object]] = []
        for handoff in valid_handoffs:
            from_agent = str(handoff.get("from_agent") or "")
            for artifact in handoff.get("artifacts", []):
                if isinstance(artifact, dict):
                    artifacts.append(
                        {
                            "from_agent": from_agent,
                            "artifact": str(artifact.get("artifact") or ""),
                            "path": str(artifact.get("path") or ""),
                        }
                    )
        return {
            "schema_version": "valuation_handoff_context_v1",
            "handoffs_count": len(valid_handoffs),
            "from_agents": _unique(
                [str(handoff.get("from_agent") or "") for handoff in valid_handoffs if handoff.get("from_agent")]
            ),
            "artifacts_count": len(artifacts),
            "artifacts": artifacts,
        }

    def _build_valuation_human_review_gate(self, reconciliation: dict[str, object]) -> dict[str, object]:
        return {
            "schema_version": "valuation_human_review_gate_v1",
            "required": bool(self.definition.human_validation.get("required", True)),
            "checkpoints": list(self.definition.human_validation.get("checkpoints", [])),
            "status": "A_VALIDER",
            "preliminary_value": reconciliation.get("preliminary_value", 0.0),
            "blocking_policy": "reconciliation_preliminaire_a_valider",
        }

    def _prepare_compliance_qa_context(
        self,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        status: str,
        blocking: list[str],
        warnings: list[str],
        handoffs: list[dict[str, object]],
    ) -> dict[str, object]:
        evidence_map = self._build_compliance_evidence_map(case, step, source_fixture, handoffs)
        decision_matrix = self._build_compliance_decision_matrix(status, blocking, warnings)
        handoff_context = self._build_compliance_handoff_context(handoffs)
        return {
            "compliance_decision_matrix": decision_matrix,
            "compliance_evidence_map": evidence_map,
            "compliance_handoff_context": handoff_context,
            "compliance_human_review_gate": self._build_compliance_human_review_gate(status, decision_matrix),
        }

    def _build_compliance_evidence_map(
        self,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        handoffs: list[dict[str, object]],
    ) -> dict[str, object]:
        upstream_artifacts: list[dict[str, object]] = []
        for handoff in handoffs:
            if not isinstance(handoff, dict):
                continue
            from_agent = str(handoff.get("from_agent") or "")
            for artifact in handoff.get("artifacts", []):
                if isinstance(artifact, dict):
                    upstream_artifacts.append(
                        {
                            "from_agent": from_agent,
                            "artifact": str(artifact.get("artifact") or ""),
                            "path": str(artifact.get("path") or ""),
                        }
                    )
        source_ids = collect_source_ids(case)
        expected_artifacts = [
            "calculs_approche_comparative.json",
            "calculs_approche_cout.json",
            "calculs_approche_revenu.json",
            "hypotheses_explicites.json",
            "source_index.json",
        ]
        return {
            "schema_version": "compliance_evidence_map_v1",
            "agent_type": step.name,
            "source_fixture": source_fixture,
            "source_ids": source_ids,
            "source_count": len(source_ids),
            "declared_inputs": list(step.reads),
            "expected_artifacts": expected_artifacts,
            "upstream_artifacts_count": len(upstream_artifacts),
            "upstream_artifacts": upstream_artifacts,
            "coverage_status": "OK" if source_ids or source_fixture or upstream_artifacts else "A_COMPLETER",
            "policy": [
                "Chaque anomalie doit conserver son niveau BLOQUANT ou WARNING.",
                "Le statut de sortie doit rester derive des anomalies detectees.",
                "La validation humaine finale reste requise pour les decisions critiques.",
            ],
        }

    def _build_compliance_decision_matrix(
        self,
        status: str,
        blocking: list[str],
        warnings: list[str],
    ) -> dict[str, object]:
        active_findings = [*blocking, *warnings]

        def finding_code(finding: str) -> str:
            return str(finding).split(":", 1)[0].strip()

        active_codes = [finding_code(finding) for finding in active_findings]

        def gate_row(gate: str, severity: str) -> dict[str, object]:
            matched = [
                finding
                for finding in active_findings
                if finding_code(str(finding)) == gate or str(finding).startswith(f"{gate}:")
            ]
            return {
                "gate": gate,
                "severity": severity,
                "status": "triggered" if matched else "clear",
                "findings": matched,
            }

        rows = [
            gate_row(str(gate), "BLOQUANT")
            for gate in self.definition.quality_gates.get("blocking", [])
        ]
        rows.extend(
            gate_row(str(gate), "WARNING")
            for gate in self.definition.quality_gates.get("warnings", [])
        )
        configured_codes = {str(row["gate"]) for row in rows}
        for code in active_codes:
            if code in configured_codes:
                continue
            rows.append(
                {
                    "gate": code,
                    "severity": "BLOQUANT" if code.startswith(("B", "STRICT", "SCHEMA", "CONF")) else "WARNING",
                    "status": "triggered",
                    "findings": [finding for finding in active_findings if finding_code(str(finding)) == code],
                }
            )
            configured_codes.add(code)

        return {
            "schema_version": "compliance_decision_matrix_v1",
            "agent_type": self.definition.agent_type,
            "status": status,
            "blocking_failures": list(blocking),
            "warnings": list(warnings),
            "active_findings_count": len(active_findings),
            "rows": rows,
            "ok": not blocking,
        }

    def _build_compliance_handoff_context(self, handoffs: list[dict[str, object]]) -> dict[str, object]:
        valid_handoffs = [handoff for handoff in handoffs if isinstance(handoff, dict)]
        artifacts: list[dict[str, object]] = []
        for handoff in valid_handoffs:
            from_agent = str(handoff.get("from_agent") or "")
            for artifact in handoff.get("artifacts", []):
                if isinstance(artifact, dict):
                    artifacts.append(
                        {
                            "from_agent": from_agent,
                            "artifact": str(artifact.get("artifact") or ""),
                            "path": str(artifact.get("path") or ""),
                        }
                    )
        return {
            "schema_version": "compliance_handoff_context_v1",
            "handoffs_count": len(valid_handoffs),
            "from_agents": _unique(
                [str(handoff.get("from_agent") or "") for handoff in valid_handoffs if handoff.get("from_agent")]
            ),
            "artifacts_count": len(artifacts),
            "artifacts": artifacts,
            "blocking_count": sum(len(_handoff_string_list(handoff.get("blocking_failures"))) for handoff in valid_handoffs),
            "warning_count": sum(len(_handoff_string_list(handoff.get("warnings"))) for handoff in valid_handoffs),
        }

    def _build_compliance_human_review_gate(
        self,
        status: str,
        decision_matrix: dict[str, object],
    ) -> dict[str, object]:
        return {
            "schema_version": "compliance_human_review_gate_v1",
            "required": bool(self.definition.human_validation.get("required", True)),
            "checkpoints": list(self.definition.human_validation.get("checkpoints", [])),
            "status": "A_VALIDER",
            "runtime_status": status,
            "active_findings_count": decision_matrix.get("active_findings_count", 0),
            "blocking_policy": "classification_anomalies_et_statut_final_a_valider",
        }

    def _prepare_redaction_context(
        self,
        case: dict,
        step: RuntimeStep,
        source_fixture: str,
        handoffs: list[dict[str, object]],
    ) -> dict[str, object]:
        source_appendix = self._build_redaction_source_appendix(case, source_fixture)
        handoff_context = self._build_redaction_handoff_context(handoffs)
        report_plan = self._build_redaction_report_plan(case, step, source_appendix, handoff_context)
        return {
            "report_assembly_plan": report_plan,
            "source_appendix": source_appendix,
            "handoff_context": handoff_context,
        }

    def _build_redaction_source_appendix(self, case: dict, source_fixture: str) -> dict[str, object]:
        source_ids = collect_source_ids(case)
        return {
            "schema_version": "redaction_source_appendix_v1",
            "source_fixture": source_fixture,
            "source_ids": source_ids,
            "source_count": len(source_ids),
            "coverage_status": "OK" if source_ids or source_fixture else "A_COMPLETER",
            "sources": [
                {
                    "source_id": source_id,
                    "used_in": ["brouillon_rapport.md", "annexe_sources.md"],
                    "citation_required": True,
                    "validation_status": "A_VALIDER",
                }
                for source_id in source_ids
            ],
            "policy": [
                "Le brouillon ne doit pas ajouter de fait absent des artefacts amont.",
                "Chaque conclusion metier doit rester reliee a une source ou a une validation humaine.",
            ],
        }

    def _build_redaction_handoff_context(self, handoffs: list[dict[str, object]]) -> dict[str, object]:
        valid_handoffs = [handoff for handoff in handoffs if isinstance(handoff, dict)]
        artifacts: list[dict[str, object]] = []
        for handoff in valid_handoffs:
            from_agent = str(handoff.get("from_agent") or "")
            for artifact in handoff.get("artifacts", []):
                if not isinstance(artifact, dict):
                    continue
                artifacts.append(
                    {
                        "from_agent": from_agent,
                        "artifact": str(artifact.get("artifact") or ""),
                        "path": str(artifact.get("path") or ""),
                    }
                )
        return {
            "schema_version": "redaction_handoff_context_v1",
            "handoffs_count": len(valid_handoffs),
            "from_agents": _unique(
                [str(handoff.get("from_agent") or "") for handoff in valid_handoffs if handoff.get("from_agent")]
            ),
            "artifacts_count": len(artifacts),
            "artifacts": artifacts,
            "blocking_count": sum(len(_handoff_string_list(handoff.get("blocking_failures"))) for handoff in valid_handoffs),
            "warning_count": sum(len(_handoff_string_list(handoff.get("warnings"))) for handoff in valid_handoffs),
            "ok": all(str(handoff.get("status") or "").upper() != "A_REVOIR" for handoff in valid_handoffs),
        }

    def _build_redaction_report_plan(
        self,
        case: dict,
        step: RuntimeStep,
        source_appendix: dict[str, object],
        handoff_context: dict[str, object],
    ) -> dict[str, object]:
        has_sources = bool(source_appendix.get("source_ids") or source_appendix.get("source_fixture"))
        has_handoff = bool(handoff_context.get("handoffs_count"))
        return {
            "schema_version": "redaction_report_plan_v1",
            "agent_type": step.name,
            "ready_for_draft": True,
            "handoff_required_for_final": True,
            "handoff_present": has_handoff,
            "source_coverage_status": source_appendix.get("coverage_status", "A_COMPLETER"),
            "sections": [
                {
                    "id": "identification_dossier",
                    "title": "Identification du dossier",
                    "required_inputs": ["dossier_id", "date_reference", "type_bien", "zone"],
                    "status": "pret" if case.get("dossier_id") and case.get("date_reference") else "a_completer",
                    "source_policy": "reprendre uniquement les faits extraits",
                },
                {
                    "id": "faits_et_sources",
                    "title": "Faits et sources",
                    "required_inputs": ["fiche_bien.json", "timeline_faits.json", "source_index.json"],
                    "status": "pret" if has_sources else "a_completer",
                    "source_policy": "aucun fait sans source ou fixture declaree",
                },
                {
                    "id": "analyse_marche",
                    "title": "Analyse du marche",
                    "required_inputs": ["comparables_proposes.json", "justifications_comparables.json"],
                    "status": "a_reviser",
                    "source_policy": "conserver les decisions de selection des comparables",
                },
                {
                    "id": "estimation_valeur",
                    "title": "Estimation de valeur",
                    "required_inputs": [
                        "calculs_approche_comparative.json",
                        "calculs_approche_cout.json",
                        "calculs_approche_revenu.json",
                    ],
                    "status": "a_reviser",
                    "source_policy": "ne pas modifier les traces de calcul",
                },
                {
                    "id": "conformite_revision",
                    "title": "Conformite et revision",
                    "required_inputs": ["rapport_non_conformites.json", "statut_sortie.json"],
                    "status": "pret" if has_handoff and handoff_context.get("ok") else "a_reviser",
                    "source_policy": "le rapport reste brouillon tant que la validation humaine est requise",
                },
            ],
            "quality_gates": [
                "sections_obligatoires_presentes",
                "sources_annexees",
                "aucune_donnee_nouvelle_non_sourcee",
                "validation_humaine_finale_requise",
            ],
        }

    def _validate_payload_before_write(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        step: RuntimeStep,
        artifact: str,
        payload: dict,
        path: Path,
    ) -> dict[str, object] | None:
        if step.name != "compliance-qa" or "validate_schema" not in self.definition.tools:
            return None

        required_fields = REQUIRED_FIELDS_BY_ARTIFACT.get(artifact, REQUIRED_FIELDS_BY_ARTIFACT["default"])
        result = self._execute_tool(
            state,
            audit_log_path,
            executor,
            ClaudeToolCall(
                id=f"{step.name}:{artifact}:validate_schema",
                name="validate_schema",
                input={"payload": payload, "required_fields": required_fields},
                agent_type=step.name,
            ),
            artifact=artifact,
            path=path,
        )
        if not result.ok:
            raise RuntimeError(result.error)
        output = result.output if isinstance(result.output, dict) else {}
        return {
            "tool": "validate_schema",
            "ok": bool(output.get("ok")),
            "missing": output.get("missing", []),
            "required_fields": list(required_fields),
        }

    def _format_payload_before_write(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        step: RuntimeStep,
        artifact: str,
        path: Path,
    ) -> dict[str, object] | None:
        if step.name != "redaction" or "format_document" not in self.definition.tools:
            return None

        result = self._execute_tool(
            state,
            audit_log_path,
            executor,
            ClaudeToolCall(
                id=f"{step.name}:{artifact}:format_document",
                name="format_document",
                input={"path": path.name, "artifact": artifact},
                agent_type=step.name,
            ),
            artifact=artifact,
            path=path,
        )
        if not result.ok:
            raise RuntimeError(result.error)
        output = result.output if isinstance(result.output, dict) else {}
        return {
            "tool": "format_document",
            "status": output.get("status", "unknown"),
            "path": output.get("path", path.as_posix()),
        }

    def _apply_tool_context_to_payload(
        self,
        step: RuntimeStep,
        artifact: str,
        payload: dict,
        tool_context: dict[str, object],
        case: dict,
        status: str,
    ) -> None:
        if step.name == "data-facts":
            self._apply_data_facts_context_to_payload(artifact, payload, tool_context)
            return

        if step.name == "comps-market":
            self._apply_comps_market_context_to_payload(artifact, payload, tool_context, case)
            return

        if step.name == "valuation-draft":
            self._apply_valuation_context_to_payload(artifact, payload, tool_context, status)
            return

        if step.name == "compliance-qa":
            self._apply_compliance_qa_context_to_payload(artifact, payload, tool_context)
            return

        if step.name == "redaction":
            self._apply_redaction_context_to_payload(artifact, payload, tool_context)
            return

    def _apply_data_facts_context_to_payload(
        self,
        artifact: str,
        payload: dict,
        tool_context: dict[str, object],
    ) -> None:
        manifest = tool_context.get("extraction_manifest")
        source_lineage = tool_context.get("source_lineage")
        if not isinstance(manifest, dict):
            manifest = {}
        if not isinstance(source_lineage, list):
            source_lineage = []

        source_ids = [str(row.get("source_id")) for row in source_lineage if isinstance(row, dict) and row.get("source_id")]
        source_coverage = {
            "schema_version": "data_facts_source_coverage_v1",
            "source_fixture": manifest.get("source_fixture"),
            "source_ids": source_ids,
            "source_coverage_status": manifest.get("source_coverage_status", "A_COMPLETER"),
            "missing_fields": manifest.get("missing_fields", []),
            "unsourced_fields": manifest.get("unsourced_fields", []),
            "human_validation_required": manifest.get("human_validation_required", True),
        }

        if artifact == "fiche_bien.json":
            payload["extraction_manifest"] = manifest
            payload["source_coverage"] = source_coverage
            payload["tool_source"] = "read_file+extract_text"

        if artifact == "timeline_faits.json":
            normalized_events: list[dict[str, object]] = []
            for event in payload.get("events", []):
                row = dict(event) if isinstance(event, dict) else {"type": "event", "value": event}
                event_source_id = str(row.get("source_id") or "").strip()
                if event_source_id:
                    row["source_ids"] = [event_source_id]
                    row["source_required"] = False
                else:
                    row["source_reference"] = manifest.get("source_fixture")
                    row["source_required"] = not bool(manifest.get("source_fixture"))
                normalized_events.append(row)
            payload["events"] = normalized_events
            payload["source_coverage"] = source_coverage
            payload["tool_source"] = "read_file+extract_text"

        if artifact == "source_index.json":
            payload["sources"] = source_lineage
            payload["coverage"] = source_coverage
            payload["tool_source"] = "read_file+extract_text"

    def _apply_comps_market_context_to_payload(
        self,
        artifact: str,
        payload: dict,
        tool_context: dict[str, object],
        case: dict,
    ) -> None:
        search_output = tool_context.get("search_comparables")
        comparables = search_output.get("comparables", []) if isinstance(search_output, dict) else []
        if not isinstance(comparables, list):
            comparables = []
        selection_protocol = tool_context.get("market_selection_protocol")
        source_coverage = tool_context.get("market_source_coverage")
        handoff_context = tool_context.get("market_handoff_context")
        human_review_gate = tool_context.get("market_human_review_gate")
        if not isinstance(selection_protocol, dict):
            selection_protocol = {}
        if not isinstance(source_coverage, dict):
            source_coverage = {}
        if not isinstance(handoff_context, dict):
            handoff_context = {}
        if not isinstance(human_review_gate, dict):
            human_review_gate = {}

        if artifact == "comparables_proposes.json":
            payload["date_reference"] = case.get("date_reference")
            payload["comparables"] = comparables
            payload["selection_protocol"] = selection_protocol
            payload["source_coverage"] = source_coverage
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate
            payload["tool_source"] = "search_comparables"

        if artifact == "justifications_comparables.json":
            payload["justifications"] = self._build_comparable_justifications(case, comparables)
            payload["selection_protocol"] = selection_protocol
            payload["source_coverage"] = source_coverage
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate
            payload["tool_source"] = "search_comparables"

        if artifact == "source_index.json":
            payload["sources"] = source_coverage.get("sources", [])
            payload["coverage"] = source_coverage
            payload["selection_protocol"] = selection_protocol
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate
            payload["tool_source"] = "search_comparables"

    def _apply_valuation_context_to_payload(
        self,
        artifact: str,
        payload: dict,
        tool_context: dict[str, object],
        status: str,
    ) -> None:
        traces = tool_context.get("valuation_traces")
        if not isinstance(traces, dict):
            return
        methodology_plan = tool_context.get("valuation_methodology_plan")
        reconciliation = tool_context.get("valuation_reconciliation")
        source_coverage = tool_context.get("valuation_source_coverage")
        handoff_context = tool_context.get("valuation_handoff_context")
        human_review_gate = tool_context.get("valuation_human_review_gate")
        if not isinstance(methodology_plan, dict):
            methodology_plan = {}
        if not isinstance(reconciliation, dict):
            reconciliation = {}
        if not isinstance(source_coverage, dict):
            source_coverage = {}
        if not isinstance(handoff_context, dict):
            handoff_context = {}
        if not isinstance(human_review_gate, dict):
            human_review_gate = {}
        approach_by_artifact = {
            "calculs_approche_comparative.json": "approche_comparative",
            "calculs_approche_cout.json": "approche_cout",
            "calculs_approche_revenu.json": "approche_revenu",
        }
        if artifact in approach_by_artifact:
            trace = traces.get(approach_by_artifact[artifact])
            if isinstance(trace, dict):
                payload.update(trace)
                payload["methodology_plan"] = methodology_plan
                payload["reconciliation"] = reconciliation
                payload["source_coverage"] = source_coverage
                payload["handoff_context"] = handoff_context
                payload["human_review_gate"] = human_review_gate
                payload["tool_source"] = "run_calculation"

        if artifact == "hypotheses_explicites.json":
            payload["methodology_plan"] = methodology_plan
            payload["source_coverage"] = source_coverage
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate
            payload["hypothesis_policy"] = {
                "schema_version": "valuation_hypothesis_policy_v1",
                "source_required": True,
                "single_source_hypothesis_requires_warning": True,
                "human_validation_required": human_review_gate.get("required", True),
            }
            payload["tool_source"] = "run_calculation"

        if artifact == "brouillon_valeur.md":
            comparative = traces.get("approche_comparative")
            if isinstance(comparative, dict):
                payload["summary"] = {
                    "approche_comparative": comparative.get("value"),
                    "comparables_count": comparative.get("input_count"),
                    "status": status,
                    "preliminary_value": reconciliation.get("preliminary_value"),
                    "preferred_approach": reconciliation.get("preferred_approach"),
                }
                payload["methodology_plan"] = methodology_plan
                payload["reconciliation"] = reconciliation
                payload["source_coverage"] = source_coverage
                payload["handoff_context"] = handoff_context
                payload["human_review_gate"] = human_review_gate
                payload["tool_source"] = "run_calculation"

    def _apply_compliance_qa_context_to_payload(
        self,
        artifact: str,
        payload: dict,
        tool_context: dict[str, object],
    ) -> None:
        decision_matrix = tool_context.get("compliance_decision_matrix")
        evidence_map = tool_context.get("compliance_evidence_map")
        handoff_context = tool_context.get("compliance_handoff_context")
        human_review_gate = tool_context.get("compliance_human_review_gate")
        if not isinstance(decision_matrix, dict):
            decision_matrix = {}
        if not isinstance(evidence_map, dict):
            evidence_map = {}
        if not isinstance(handoff_context, dict):
            handoff_context = {}
        if not isinstance(human_review_gate, dict):
            human_review_gate = {}

        payload["tool_source"] = "validate_schema"

        if artifact == "rapport_non_conformites.json":
            payload["compliance_decision_matrix"] = decision_matrix
            payload["evidence_map"] = evidence_map
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate

        if artifact == "statut_sortie.json":
            payload["release_gate"] = {
                "schema_version": "compliance_release_gate_v1",
                "status": payload.get("status"),
                "ready_for_redaction": payload.get("status") in {"BROUILLON", "PRET_REVISION_FINALE"},
                "ready_for_final_publication": False,
                "human_validation_required": human_review_gate.get("required", True),
                "active_findings_count": decision_matrix.get("active_findings_count", 0),
                "blocking_failures_count": len(payload.get("blocking_failures", [])),
                "warnings_count": len(payload.get("warnings", [])),
            }
            payload["compliance_decision_matrix"] = decision_matrix
            payload["evidence_map"] = evidence_map
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate

        if artifact == "recommandations_corrections.md":
            recommendations = payload.get("recommendations", [])
            if not isinstance(recommendations, list):
                recommendations = []
            payload["recommendation_plan"] = {
                "schema_version": "compliance_recommendation_plan_v1",
                "status": decision_matrix.get("status"),
                "items_count": len(recommendations),
                "items": recommendations,
                "source_policy": "corriger les anomalies sans inventer de donnees manquantes",
                "human_validation_required": human_review_gate.get("required", True),
            }
            payload["compliance_decision_matrix"] = decision_matrix
            payload["evidence_map"] = evidence_map
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate

    def _apply_redaction_context_to_payload(
        self,
        artifact: str,
        payload: dict,
        tool_context: dict[str, object],
    ) -> None:
        report_plan = tool_context.get("report_assembly_plan")
        source_appendix = tool_context.get("source_appendix")
        handoff_context = tool_context.get("handoff_context")
        if not isinstance(report_plan, dict):
            report_plan = {}
        if not isinstance(source_appendix, dict):
            source_appendix = {}
        if not isinstance(handoff_context, dict):
            handoff_context = {}

        human_review_gate = {
            "schema_version": "redaction_human_review_gate_v1",
            "required": True,
            "checkpoints": list(self.definition.human_validation.get("checkpoints", [])),
            "status": "A_VALIDER",
            "blocking_policy": "ne_pas_publier_sans_revision_humaine",
        }

        if artifact == "brouillon_rapport.md":
            payload["report_assembly_plan"] = report_plan
            payload["source_appendix"] = source_appendix
            payload["handoff_context"] = handoff_context
            payload["human_review_gate"] = human_review_gate
            payload["tool_source"] = "format_document"

        if artifact == "annexe_sources.md":
            payload["source_appendix"] = source_appendix
            payload["handoff_context"] = handoff_context
            payload["citation_policy"] = {
                "schema_version": "redaction_citation_policy_v1",
                "source_required": True,
                "allow_unsourced_claims": False,
                "fixture_reference": source_appendix.get("source_fixture"),
                "human_validation_required": True,
            }
            payload["human_review_gate"] = human_review_gate
            payload["tool_source"] = "format_document"

    def _build_comparable_justifications(self, case: dict, selected_comparables: list[object]) -> list[dict[str, object]]:
        selected_by_id = {
            str(comparable.get("comparable_id") or ""): comparable
            for comparable in selected_comparables
            if isinstance(comparable, dict)
        }
        source_rows = case.get("comparables", [])
        if not isinstance(source_rows, list):
            source_rows = []

        justifications: list[dict[str, object]] = []
        for comparable in source_rows:
            if not isinstance(comparable, dict):
                continue
            comparable_id = str(comparable.get("comparable_id") or "")
            selected = selected_by_id.get(comparable_id)
            source_id = str(comparable.get("source_id") or "")
            if selected:
                score_details = selected.get("score_details", {}) if isinstance(selected, dict) else {}
                rationale = score_details.get("rationale", []) if isinstance(score_details, dict) else []
                justifications.append(
                    {
                        "comparable_id": comparable_id,
                        "source_id": source_id,
                        "decision": "retenu",
                        "raison": "; ".join(str(item) for item in rationale) or "score de similarite calcule",
                        "score": selected.get("score") if isinstance(selected, dict) else None,
                    }
                )
                continue

            justifications.append(
                {
                    "comparable_id": comparable_id,
                    "source_id": source_id,
                    "decision": "rejete",
                    "raison": "source manquante" if not source_id else "non retenu par le classement des comparables",
                }
            )
        return justifications

    def _append_message(
        self,
        state: ClaudeAgentState,
        role: str,
        agent_type: str,
        content: object,
        *,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        message = build_claude_message_envelope(
            role=role,
            agent_type=agent_type,
            content=content,
            sequence=len(state.messages) + 1,
            metadata=metadata,
        )
        state.messages.append(message)
        return message

    def _record_event(self, state: ClaudeAgentState, audit_log_path: Path, event: dict) -> None:
        event_name = str(event.get("event") or "")
        agent_type = str(event.get("agent_type") or self.definition.agent_type)
        envelope = build_claude_event_envelope(
            event_name,
            agent_type=agent_type,
            sequence=len(state.events) + 1,
            payload=event,
        )
        state.events.append(envelope)
        append_audit_log(audit_log_path, envelope)

    def _invoke_hook(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        hook_event: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        invocation = build_claude_hook_invocation(
            hook_event,
            agent_type=self.definition.agent_type,
            payload=payload,
            sequence=len(state.hook_invocations) + 1,
        )
        state.hook_invocations.append(invocation)
        payload = payload or {}
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "hook_invoked",
                "agent_type": self.definition.agent_type,
                "hook_event": hook_event,
                "hook_sequence": invocation["sequence"],
                "status": invocation["status"],
                "blocking": invocation["blocking"],
                **({"tool": payload.get("tool_name")} if payload.get("tool_name") else {}),
                **({"tool_call_id": payload.get("tool_use_id")} if payload.get("tool_use_id") else {}),
            },
        )
        return invocation

    def _execute_tool(
        self,
        state: ClaudeAgentState,
        audit_log_path: Path,
        executor: ClaudeToolExecutor,
        call: ClaudeToolCall,
        *,
        artifact: str | None = None,
        path: Path | None = None,
        append_tool_call_message: bool = True,
        preflight_failure: dict[str, object] | None = None,
        record_artifact_written: bool = False,
        artifact_source: str = "",
    ) -> ClaudeToolResult:
        if append_tool_call_message:
            self._append_message(state, "assistant", call.agent_type, [call.as_message_block()])
        self._invoke_hook(
            state,
            audit_log_path,
            "PreToolUse",
            {
                "tool_name": call.name,
                "tool_input": call.input,
                "tool_use_id": call.id,
                "agent_type": call.agent_type,
            },
        )
        decision = executor.decide(call)
        state.permission_decisions.append(decision.as_dict())
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "permission_decision",
                "agent_type": call.agent_type,
                "tool": call.name,
                "tool_call_id": call.id,
                "permission": decision.permission,
                "permission_mode": decision.mode,
                "allowed": decision.allowed,
                "reason": decision.reason,
                **({"artifact": artifact} if artifact else {}),
                **({"path": path.as_posix()} if path else {}),
            },
        )
        if not decision.allowed:
            self._invoke_hook(
                state,
                audit_log_path,
                "PermissionDenied",
                {
                    "tool_name": call.name,
                    "tool_input": call.input,
                    "tool_use_id": call.id,
                    "reason": decision.reason,
                    "permission": decision.permission,
                },
            )
            result = ClaudeToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                error=f"ToolPermissionError: {decision.reason}",
                permission=decision.permission,
            )
            self._append_message(state, "user", call.agent_type, [result.as_message_block()])
            return result
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "tool_start",
                "agent_type": call.agent_type,
                "tool": call.name,
                "tool_call_id": call.id,
                **({"artifact": artifact} if artifact else {}),
                **({"path": path.as_posix()} if path else {}),
            },
        )
        state.tool_use_count += 1
        if preflight_failure:
            failures = [
                str(failure)
                for failure in preflight_failure.get("failures", [])
                if str(failure)
            ]
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "contract_invalid",
                    "agent_type": call.agent_type,
                    "tool": call.name,
                    "tool_call_id": call.id,
                    "artifact": artifact or preflight_failure.get("artifact", ""),
                    "path": path.as_posix() if path else preflight_failure.get("path", ""),
                    "failures": failures,
                },
            )
            result = ClaudeToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=preflight_failure,
                error=f"ContractValidationError: {failures}",
                permission=decision.permission,
            )
        else:
            result = executor.execute(call, decision=decision)
        post_hook_event = "PostToolUse" if result.ok else "PostToolUseFailure"
        self._invoke_hook(
            state,
            audit_log_path,
            post_hook_event,
            {
                "tool_name": call.name,
                "tool_input": call.input,
                "tool_use_id": call.id,
                "response": result.as_message_block(),
                **({"error": result.error} if result.error else {}),
            },
        )
        self._record_event(
            state,
            audit_log_path,
            {
                "event": "tool_end",
                "agent_type": call.agent_type,
                "tool": call.name,
                "tool_call_id": call.id,
                "status": "ok" if result.ok else "error",
                "permission": result.permission,
                **({"artifact": artifact} if artifact else {}),
                **({"path": path.as_posix()} if path else {}),
                **({"error": result.error} if result.error else {}),
            },
        )
        if result.ok and record_artifact_written and call.name == "write_file" and artifact:
            self._record_event(
                state,
                audit_log_path,
                {
                    "event": "artifact_written",
                    "agent_type": call.agent_type,
                    "step": call.agent_type,
                    "artifact": artifact,
                    "path": path.as_posix() if path else str(call.input.get("path") or ""),
                    "source": artifact_source or "tool",
                    "tool_call_id": call.id,
                },
            )
        self._append_message(state, "user", call.agent_type, [result.as_message_block()])
        return result


class ClaudeStylePipelineRunner:
    """Sequential Claude Code style orchestration across eval-immo agents."""

    def __init__(
        self,
        agent_config_names: list[str] | None = None,
        *,
        project_root: Path | None = None,
        tool_registry: dict[str, ToolSpec] | None = None,
        strict_tool_result_pairing: bool | None = None,
        context_compaction_threshold_tokens: int | None = None,
        preserve_recent_tool_results: int | None = None,
        permission_mode: str | None = None,
        permission_state: dict[str, object] | None = None,
        settings_context: dict[str, object] | None = None,
        model_client: ClaudeModelClient | None = None,
        runtime_mode: str = "",
    ) -> None:
        self.project_root = project_root or PROJECT_ROOT
        self.tool_registry = tool_registry or TOOL_REGISTRY
        self.agent_config_names = list(agent_config_names or CLAUDE_PIPELINE_AGENT_CONFIGS)
        self.model_client = model_client
        self.runtime_mode = runtime_mode
        self.settings_context = settings_context or load_claude_settings(project_root=self.project_root)
        self.runtime_settings = (
            self.settings_context.get("runtime_options", {})
            if isinstance(self.settings_context.get("runtime_options"), dict)
            else {}
        )
        self.strict_tool_result_pairing = (
            bool(strict_tool_result_pairing)
            if strict_tool_result_pairing is not None
            else bool(self.runtime_settings.get("strict_tool_result_pairing", True))
        )
        self.permission_mode = (
            permission_mode
            if permission_mode is not None
            else str(self.runtime_settings.get("permission_mode") or ClaudePermissionPolicy.DEFAULT)
        )
        self.initial_permission_state = normalize_permission_state(
            permission_state,
            agent_type="claude-pipeline",
            mode=self.permission_mode,
            allowed_tools=[],
        ) if permission_state else build_permission_state_from_settings_context(
            self.settings_context,
            agent_type="claude-pipeline",
            mode=self.permission_mode,
            allowed_tools=[],
        )
        self.preserve_recent_tool_results = (
            int(preserve_recent_tool_results)
            if preserve_recent_tool_results is not None
            else int(self.runtime_settings.get("preserve_recent_tool_results", 3) or 0)
        )
        self.runners = [
            ClaudeStyleAgentRunner(
                load_claude_agent_definition(
                    self.project_root / "integration" / agent_config_name,
                    project_root=self.project_root,
                    tool_registry=self.tool_registry,
                ),
                project_root=self.project_root,
                tool_registry=self.tool_registry,
                strict_tool_result_pairing=self.strict_tool_result_pairing,
                context_compaction_threshold_tokens=context_compaction_threshold_tokens,
                preserve_recent_tool_results=self.preserve_recent_tool_results,
                permission_mode=self.permission_mode,
                permission_state=self.initial_permission_state,
                settings_context=self.settings_context,
                model_client=self.model_client,
                runtime_mode=self.runtime_mode,
            )
            for agent_config_name in self.agent_config_names
        ]
        self.context_compaction_threshold_tokens = (
            context_compaction_threshold_tokens
            if context_compaction_threshold_tokens is not None
            else (
                int(self.runtime_settings["context_compaction_threshold_tokens"])
                if self.runtime_settings.get("context_compaction_threshold_tokens") is not None
                else sum(runner.definition.budgets.max_total_tokens for runner in self.runners)
            )
        )

    def execute_slash_command(
        self,
        command_name: str,
        *,
        args: str = "",
        runtime_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return execute_slash_command(
            command_name,
            self._unique_commands(),
            args=args,
            context=self._slash_command_context(runtime_result),
        )

    def _unique_commands(self) -> list[CommandSpec]:
        commands_by_name: dict[str, CommandSpec] = {}
        for runner in self.runners:
            for command in runner.commands:
                commands_by_name.setdefault(command.name, command)
        return list(commands_by_name.values())

    def _slash_command_context(self, runtime_result: dict[str, object] | None = None) -> dict[str, object]:
        result = runtime_result if isinstance(runtime_result, dict) else {}
        command_context = result.get("command_context")
        if not isinstance(command_context, dict):
            command_context = summarize_pipeline_command_context(
                {runner.definition.agent_type: runner.command_context for runner in self.runners}
            )
        skill_context = result.get("skill_context")
        if not isinstance(skill_context, dict):
            skill_context = summarize_pipeline_skill_context(
                {runner.definition.agent_type: runner.skill_context for runner in self.runners}
            )
        tool_registry_summary = result.get("tool_registry_summary")
        if not isinstance(tool_registry_summary, dict):
            tool_names = sorted({tool for runner in self.runners for tool in runner.definition.tools})
            tool_registry_summary = summarize_tool_registry(tool_names, self.tool_registry)
        return {
            "agent_type": "claude-pipeline",
            "scope": "multi_agent:claude",
            "status": result.get("status", "ready"),
            "model": "claude-pipeline",
            "canonical_model": ",".join(sorted({runner.definition.model_profile.canonical_model for runner in self.runners})),
            "permission_mode": self.permission_mode,
            "messages": result.get("messages", []),
            "events": result.get("events", []),
            "metrics": result.get("metrics", {}),
            "conversation_state": result.get("conversation_state", {}),
            "context_state": result.get("context_state", {}),
            "context_compaction_threshold_tokens": self.context_compaction_threshold_tokens,
            "preserve_recent_tool_results": self.preserve_recent_tool_results,
            "token_budget": result.get("token_budget", {}),
            "usage_accounting": result.get("usage_accounting", {}),
            "task_state": result.get("task_summary", {}),
            "handoff_summary": result.get("handoff_summary", {}),
            "blocking_failures": result.get("blocking_failures", []),
            "warnings": result.get("warnings", []),
            "settings_context": self.settings_context,
            "skill_context": skill_context,
            "command_context": command_context,
            "tool_registry_summary": tool_registry_summary,
            "tools_allowed": sorted({tool for runner in self.runners for tool in runner.definition.tools}),
            "skills_allowed": sorted({skill for runner in self.runners for skill in runner.definition.skills}),
        }

    def _build_pipeline_artifact_lineage(
        self,
        events: list[dict[str, object]],
        handoffs: list[dict[str, object]],
        agents: list[str],
        task_summary: dict[str, object],
    ) -> dict[str, object]:
        artifact_records: list[dict[str, object]] = []
        records_by_key: dict[str, dict[str, object]] = {}
        for event in events:
            if event.get("event") != "artifact_written" or not event.get("artifact"):
                continue
            agent_type = str(event.get("agent_type") or event.get("step") or "")
            artifact = str(event.get("artifact") or "")
            artifact_key = f"{agent_type}.{artifact}" if agent_type else artifact
            path = str(event.get("path") or event.get("artifact_path") or "")
            record = {
                "artifact_key": artifact_key,
                "agent_type": agent_type,
                "step": str(event.get("step") or agent_type),
                "artifact": artifact,
                "path": path,
                "event_sequence": int(event.get("event_sequence", 0) or 0),
                "exists": Path(path).exists() if path else False,
                "consumed_by": [],
                "handoff_targets": [],
                "terminal": False,
            }
            artifact_records.append(record)
            records_by_key[artifact_key] = record

        handoff_edges: list[dict[str, object]] = []
        for handoff in handoffs:
            from_agent = str(handoff.get("from_agent") or "")
            to_agent = str(handoff.get("to_agent") or "")
            artifacts = []
            for artifact in handoff.get("artifacts", []):
                if not isinstance(artifact, dict):
                    continue
                artifact_name = str(artifact.get("artifact") or "")
                artifact_key = f"{from_agent}.{artifact_name}" if from_agent else artifact_name
                artifacts.append(
                    {
                        "artifact_key": artifact_key,
                        "artifact": artifact_name,
                        "path": str(artifact.get("path") or ""),
                    }
                )
                record = records_by_key.get(artifact_key)
                if record is not None:
                    consumed_by = record["consumed_by"]
                    handoff_targets = record["handoff_targets"]
                    if isinstance(consumed_by, list) and to_agent and to_agent not in consumed_by:
                        consumed_by.append(to_agent)
                    if isinstance(handoff_targets, list) and to_agent and to_agent not in handoff_targets:
                        handoff_targets.append(to_agent)
            handoff_edges.append(
                {
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "status": str(handoff.get("status") or "UNKNOWN"),
                    "artifacts_count": len(artifacts),
                    "artifacts": artifacts,
                }
            )

        for record in artifact_records:
            record["terminal"] = not bool(record.get("consumed_by"))

        artifacts_by_agent = {
            agent: [
                record
                for record in artifact_records
                if record.get("agent_type") == agent
            ]
            for agent in agents
        }
        terminal_artifact_keys = [
            str(record["artifact_key"])
            for record in artifact_records
            if record.get("terminal")
        ]
        completed_count = int(task_summary.get("completed_count", 0) or 0)
        return {
            "schema_version": "claude_pipeline_artifact_lineage_v1",
            "agents": agents,
            "agents_count": len(agents),
            "artifacts_count": len(artifact_records),
            "handoff_edges_count": len(handoff_edges),
            "handoff_edges": handoff_edges,
            "artifacts": artifact_records,
            "artifacts_by_agent": artifacts_by_agent,
            "terminal_artifact_keys": terminal_artifact_keys,
            "ok": (
                len(artifact_records) == completed_count
                and len(handoff_edges) == max(len(agents) - 1, 0)
                and all(bool(record.get("exists")) for record in artifact_records)
            ),
        }

    def run_case_data(
        self,
        case: dict,
        out_dir: Path,
        *,
        source_fixture: str = "inline",
        case_stem: str | None = None,
        case_subdir: bool = False,
    ) -> dict:
        started_at = time.perf_counter()
        dossier_id = str(case.get("dossier_id") or "unknown")
        events: list[dict[str, object]] = []
        messages: list[dict[str, object]] = []
        skills_by_agent: dict[str, list[str]] = {}
        skill_context_by_agent: dict[str, dict[str, object]] = {}
        command_context_by_agent: dict[str, dict[str, object]] = {}
        tools_by_agent: dict[str, list[str]] = {}
        blocking: list[str] = []
        warnings: list[str] = []
        agent_results: list[dict[str, object]] = []
        conversation_state_by_agent: dict[str, dict[str, object]] = {}
        context_state_by_agent: dict[str, dict[str, object]] = {}
        permission_decisions: list[dict[str, object]] = []
        permission_summary_by_agent: dict[str, dict[str, object]] = {}
        permission_state_by_agent: dict[str, dict[str, object]] = {}
        permission_state_path_by_agent: dict[str, str] = {}
        permission_replay_summary_by_agent: dict[str, dict[str, object]] = {}
        task_state_by_agent: dict[str, dict[str, object]] = {}
        handoffs: list[dict[str, object]] = []
        incoming_handoffs: list[dict[str, object]] = []
        handoffs_by_agent: dict[str, list[dict[str, object]]] = {}
        handoff_summary_by_agent: dict[str, dict[str, object]] = {}
        transcript_summary_by_agent: dict[str, dict[str, object]] = {}
        hook_invocations: list[dict[str, object]] = []
        hook_summary_by_agent: dict[str, dict[str, object]] = {}
        model_profiles_by_agent: dict[str, dict[str, object]] = {}
        model_client_by_agent: dict[str, dict[str, object]] = {}
        model_live_loop_by_agent: dict[str, dict[str, object]] = {}
        token_budget_by_agent: dict[str, dict[str, object]] = {}
        usage_accounting_by_agent: dict[str, dict[str, object]] = {}
        tool_registry_summary_by_agent: dict[str, dict[str, object]] = {}
        audit_log = ""
        artifact_dir = ""
        status = "UNKNOWN"
        tool_use_count = 0

        for index, runner in enumerate(self.runners):
            result = runner.run_case_data(
                case,
                out_dir,
                source_fixture=source_fixture,
                case_stem=case_stem,
                case_subdir=case_subdir,
                handoff_messages=incoming_handoffs,
            )
            metrics = result.get("metrics", {}) if isinstance(result.get("metrics"), dict) else {}
            agent_tool_count = int(metrics.get("tool_use_count", 0) or 0)
            result_agent_type = str(result.get("agent_type") or runner.definition.agent_type)
            agent_results.append(
                {
                    "agent_type": result_agent_type,
                    "status": result.get("status", "UNKNOWN"),
                    "artifact_dir": result.get("artifact_dir", ""),
                    "tool_use_count": agent_tool_count,
                    "estimated_tokens": int(metrics.get("total_tokens", 0) or 0),
                    "skills_count": int(result.get("skill_context", {}).get("skills_count", 0) or 0)
                    if isinstance(result.get("skill_context"), dict)
                    else len(result.get("skills_by_agent", {}).get(result_agent_type, [])),
                    "commands_count": int(result.get("command_context", {}).get("commands_count", 0) or 0)
                    if isinstance(result.get("command_context"), dict)
                    else 0,
                    "handoffs_received_count": len(incoming_handoffs),
                }
            )
            for event in result.get("events", []):
                if not isinstance(event, dict):
                    continue
                item = dict(event)
                if item.get("schema_version") == "claude_runtime_event_v0":
                    item["event_sequence"] = len(events) + 1
                events.append(item)
            for message in result.get("messages", []):
                if not isinstance(message, dict):
                    continue
                item = dict(message)
                if item.get("schema_version") == "claude_message_envelope_v0":
                    item["message_sequence"] = len(messages) + 1
                messages.append(item)
            skills_by_agent.update(result.get("skills_by_agent", {}))
            result_skill_context = result.get("skill_context")
            if isinstance(result_skill_context, dict):
                skill_context_by_agent[result_agent_type] = result_skill_context
            result_command_context = result.get("command_context")
            if isinstance(result_command_context, dict):
                command_context_by_agent[result_agent_type] = result_command_context
            tools_by_agent.update(result.get("tools_by_agent", {}))
            blocking = _unique([*blocking, *result.get("blocking_failures", [])])
            warnings = _unique([*warnings, *result.get("warnings", [])])
            audit_log = str(result.get("audit_log") or audit_log)
            artifact_dir = str(result.get("artifact_dir") or artifact_dir)
            status = str(result.get("status") or status)
            tool_use_count += agent_tool_count
            conversation_state = result.get("conversation_state")
            if isinstance(conversation_state, dict):
                conversation_state_by_agent[result_agent_type] = conversation_state
            context_state = result.get("context_state")
            if isinstance(context_state, dict):
                context_state_by_agent[result_agent_type] = context_state
            result_permission_decisions = result.get("permission_decisions", [])
            if isinstance(result_permission_decisions, list):
                permission_decisions.extend(
                    decision for decision in result_permission_decisions if isinstance(decision, dict)
                )
            permission_summary = result.get("permission_summary")
            if isinstance(permission_summary, dict):
                permission_summary_by_agent[result_agent_type] = permission_summary
            result_permission_state = result.get("permission_state")
            if isinstance(result_permission_state, dict):
                permission_state_by_agent[result_agent_type] = result_permission_state
            result_permission_state_path = str(result.get("permission_state_path") or "")
            if result_permission_state_path:
                permission_state_path_by_agent[result_agent_type] = result_permission_state_path
            result_permission_replay_summary = result.get("permission_replay_summary")
            if isinstance(result_permission_replay_summary, dict):
                permission_replay_summary_by_agent[result_agent_type] = result_permission_replay_summary
            task_state = result.get("task_state")
            if isinstance(task_state, dict):
                task_state_by_agent[result_agent_type] = task_state
            result_handoffs_received = result.get("handoffs_received", [])
            handoffs_by_agent[result_agent_type] = [
                handoff for handoff in result_handoffs_received if isinstance(handoff, dict)
            ] if isinstance(result_handoffs_received, list) else []
            result_handoff_summary = result.get("handoff_summary")
            if isinstance(result_handoff_summary, dict):
                handoff_summary_by_agent[result_agent_type] = result_handoff_summary
            result_transcript_summary = result.get("transcript_summary")
            if isinstance(result_transcript_summary, dict):
                transcript_summary_by_agent[result_agent_type] = result_transcript_summary
            result_hook_invocations = result.get("hook_invocations", [])
            if isinstance(result_hook_invocations, list):
                hook_invocations.extend(
                    invocation for invocation in result_hook_invocations if isinstance(invocation, dict)
                )
            result_hook_summary = result.get("hook_summary")
            if isinstance(result_hook_summary, dict):
                hook_summary_by_agent[result_agent_type] = result_hook_summary
            result_tool_registry_summary = result.get("tool_registry_summary")
            if isinstance(result_tool_registry_summary, dict):
                tool_registry_summary_by_agent[result_agent_type] = result_tool_registry_summary
            result_model_profile = result.get("model_profile")
            if isinstance(result_model_profile, dict):
                model_profiles_by_agent[result_agent_type] = result_model_profile
            result_model_client = result.get("model_client")
            if isinstance(result_model_client, dict):
                model_client_by_agent[result_agent_type] = result_model_client
                result_live_loop = result_model_client.get("live_tool_loop")
                if isinstance(result_live_loop, dict):
                    model_live_loop_by_agent[result_agent_type] = result_live_loop
            result_token_budget = result.get("token_budget")
            if isinstance(result_token_budget, dict):
                token_budget_by_agent[result_agent_type] = result_token_budget
            result_usage_accounting = result.get("usage_accounting")
            if isinstance(result_usage_accounting, dict):
                usage_accounting_by_agent[result_agent_type] = result_usage_accounting

            if index + 1 < len(self.runners):
                to_agent = self.runners[index + 1].definition.agent_type
                handoff = build_agent_handoff_message(result_agent_type, to_agent, result)
                handoffs.append(handoff)
                events.append(
                    build_claude_event_envelope(
                        "handoff_created",
                        agent_type=result_agent_type,
                        sequence=len(events) + 1,
                        payload={
                            "from_agent": result_agent_type,
                            "to_agent": to_agent,
                            "artifacts_count": handoff["artifacts_count"],
                            "blocking_count": len(_handoff_string_list(handoff.get("blocking_failures"))),
                            "warning_count": len(_handoff_string_list(handoff.get("warnings"))),
                        },
                    )
                )
                incoming_handoffs = [handoff]
            else:
                incoming_handoffs = []

        if blocking:
            status = "A_REVOIR"

        conversation_state = summarize_claude_messages(
            messages,
            agent_type="claude-pipeline",
            strict_tool_result_pairing=self.strict_tool_result_pairing,
        )
        context_state = build_context_state(
            messages,
            agent_type="claude-pipeline",
            threshold_tokens=self.context_compaction_threshold_tokens,
            preserve_recent_tool_results=self.preserve_recent_tool_results,
        )
        permission_summary = summarize_permission_decisions(
            permission_decisions,
            agent_type="claude-pipeline",
        )
        task_summary = summarize_pipeline_task_states(task_state_by_agent)
        skill_context = summarize_pipeline_skill_context(skill_context_by_agent)
        command_context = summarize_pipeline_command_context(command_context_by_agent)
        handoff_summary = summarize_handoffs(handoffs, agent_type="claude-pipeline")
        agents = [runner.definition.agent_type for runner in self.runners]
        artifact_lineage = self._build_pipeline_artifact_lineage(events, handoffs, agents, task_summary)
        hook_summary = summarize_hook_invocations(hook_invocations, agent_type="claude-pipeline")
        model_client_summary = self._summarize_pipeline_model_clients(model_client_by_agent)
        token_budget = summarize_pipeline_token_budgets(token_budget_by_agent)
        pipeline_tool_names = sorted(
            {
                tool
                for agent_tools in tools_by_agent.values()
                if isinstance(agent_tools, list)
                for tool in agent_tools
                if isinstance(tool, str)
            }
        )
        tool_registry_summary = summarize_tool_registry(pipeline_tool_names, self.tool_registry)
        case_key = safe_path_id(case_stem or dossier_id)
        case_dir = Path(artifact_dir) if artifact_dir else (out_dir / case_key if case_subdir else out_dir)
        permission_state = build_permission_state_from_decisions(
            permission_decisions,
            agent_type="claude-pipeline",
            mode=self.permission_mode,
            allowed_tools=pipeline_tool_names,
            base_state=self.initial_permission_state,
        )
        permission_replay_summary = replay_permission_decisions(
            permission_state,
            permission_decisions,
            allowed_tools=pipeline_tool_names,
            tool_registry=self.tool_registry,
        )
        permission_state["replay"] = permission_replay_summary
        permission_state_filename = (
            "claude-pipeline.claude_permissions.json"
            if case_subdir
            else f"{case_key}.claude-pipeline.claude_permissions.json"
        )
        permission_state_path = case_dir / permission_state_filename
        permission_state = write_permission_state(permission_state_path, permission_state)
        permission_state_summary = summarize_permission_state(permission_state)
        transcript_filename = (
            "claude-pipeline.claude_transcript.jsonl"
            if case_subdir
            else f"{case_key}.claude-pipeline.claude_transcript.jsonl"
        )
        transcript_path = case_dir / transcript_filename
        transcript_summary = write_claude_transcript(
            transcript_path,
            messages,
            agent_type="claude-pipeline",
        )
        message_envelope_summary = summarize_envelope_validation(messages, kind="message")
        event_envelope_summary = summarize_envelope_validation(events, kind="runtime_event")
        wall_clock_seconds = round(time.perf_counter() - started_at, 4)
        usage_accounting = summarize_usage_accounting(
            usage_accounting_by_agent,
            agent_type="claude-pipeline",
            wall_clock_seconds=wall_clock_seconds,
        )
        return {
            "agent_type": "claude-pipeline",
            "agents": agents,
            "agent_results": agent_results,
            "dossier_id": dossier_id,
            "status": status,
            "blocking_failures": blocking,
            "warnings": warnings,
            "events": events,
            "messages": messages,
            "conversation_state": conversation_state,
            "message_envelope_summary": message_envelope_summary,
            "event_envelope_summary": event_envelope_summary,
            "conversation_state_by_agent": conversation_state_by_agent,
            "context_state": context_state,
            "context_state_by_agent": context_state_by_agent,
            "settings_context": self.settings_context,
            "model_profiles_by_agent": model_profiles_by_agent,
            "model_client": model_client_summary,
            "model_client_by_agent": model_client_by_agent,
            "model_live_loop_by_agent": model_live_loop_by_agent,
            "token_budget": token_budget,
            "token_budget_by_agent": token_budget_by_agent,
            "usage_accounting": usage_accounting,
            "usage_accounting_by_agent": usage_accounting_by_agent,
            "permission_decisions": permission_decisions,
            "permission_summary": permission_summary,
            "permission_summary_by_agent": permission_summary_by_agent,
            "permission_state": permission_state,
            "permission_state_path": permission_state_path.as_posix(),
            "permission_state_summary": permission_state_summary,
            "permission_state_by_agent": permission_state_by_agent,
            "permission_state_path_by_agent": permission_state_path_by_agent,
            "permission_replay_summary": permission_replay_summary,
            "permission_replay_summary_by_agent": permission_replay_summary_by_agent,
            "task_state_by_agent": task_state_by_agent,
            "task_summary": task_summary,
            "skill_context": skill_context,
            "skill_context_by_agent": skill_context_by_agent,
            "command_context": command_context,
            "command_context_by_agent": command_context_by_agent,
            "handoffs": handoffs,
            "handoffs_by_agent": handoffs_by_agent,
            "handoff_summary": handoff_summary,
            "handoff_summary_by_agent": handoff_summary_by_agent,
            "artifact_lineage": artifact_lineage,
            "transcript_path": transcript_path.as_posix(),
            "transcript_summary": transcript_summary,
            "transcript_summary_by_agent": transcript_summary_by_agent,
            "hook_invocations": hook_invocations,
            "hook_summary": hook_summary,
            "hook_summary_by_agent": hook_summary_by_agent,
            "audit_log": audit_log,
            "artifact_dir": artifact_dir,
            "skills_by_agent": skills_by_agent,
            "tools_by_agent": tools_by_agent,
            "tool_registry_summary": tool_registry_summary,
            "tool_registry_summary_by_agent": tool_registry_summary_by_agent,
            "metrics": {
                "wall_clock_seconds": wall_clock_seconds,
                "total_tokens": token_budget["estimated_tokens"],
                "input_tokens": usage_accounting["input_tokens"],
                "output_tokens": usage_accounting["output_tokens"],
                "cache_read_input_tokens": usage_accounting["cache_read_input_tokens"],
                "cache_creation_input_tokens": usage_accounting["cache_creation_input_tokens"],
                "web_search_requests": usage_accounting["web_search_requests"],
                "total_cost_usd": usage_accounting["total_cost_usd"],
                "formatted_total_cost": usage_accounting["formatted_total_cost"],
                "tool_use_count": tool_use_count,
                "model_input_tokens": model_client_summary.get("input_tokens", 0),
                "model_output_tokens": model_client_summary.get("output_tokens", 0),
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
            },
        }

    def _summarize_pipeline_model_clients(
        self,
        model_client_by_agent: dict[str, dict[str, object]],
    ) -> dict[str, object]:
        enabled_summaries = [
            summary
            for summary in model_client_by_agent.values()
            if isinstance(summary, dict) and summary.get("enabled")
        ]
        if not enabled_summaries:
            return summarize_model_client_interaction(
                request=None,
                response=None,
                enabled=False,
                provider=getattr(self.model_client, "provider", "") if self.model_client is not None else "",
            )
        errors: list[str] = []
        providers: list[str] = []
        stop_reasons: list[str] = []
        live_loops: list[dict[str, object]] = []
        for summary in enabled_summaries:
            provider = str(summary.get("provider") or "")
            if provider and provider not in providers:
                providers.append(provider)
            stop_reason = str(summary.get("stop_reason") or "")
            if stop_reason and stop_reason not in stop_reasons:
                stop_reasons.append(stop_reason)
            summary_errors = summary.get("errors", [])
            if isinstance(summary_errors, list):
                errors.extend(str(error) for error in summary_errors if str(error))
            live_loop = summary.get("live_tool_loop")
            if isinstance(live_loop, dict):
                live_loops.append(live_loop)
        return {
            "schema_version": "claude_pipeline_model_client_summary_v0",
            "enabled": True,
            "provider": ",".join(providers),
            "providers": providers,
            "agent_type": "claude-pipeline",
            "agents_count": len(enabled_summaries),
            "model": ",".join(
                sorted({str(summary.get("model") or "") for summary in enabled_summaries if summary.get("model")})
            ),
            "requests_count": sum(int(summary.get("requests_count", 0) or 0) for summary in enabled_summaries),
            "responses_count": sum(int(summary.get("responses_count", 0) or 0) for summary in enabled_summaries),
            "tool_calls_count": sum(int(summary.get("tool_calls_count", 0) or 0) for summary in enabled_summaries),
            "input_tokens": sum(int(summary.get("input_tokens", 0) or 0) for summary in enabled_summaries),
            "output_tokens": sum(int(summary.get("output_tokens", 0) or 0) for summary in enabled_summaries),
            "stop_reason": ",".join(stop_reasons),
            "live_tool_loop": {
                "schema_version": "claude_pipeline_live_tool_loop_v0",
                "enabled": True,
                "agents_count": len(live_loops),
                "turns_count": sum(int(loop.get("turns_count", 0) or 0) for loop in live_loops),
                "requests_count": sum(int(loop.get("requests_count", 0) or 0) for loop in live_loops),
                "responses_count": sum(int(loop.get("responses_count", 0) or 0) for loop in live_loops),
                "tool_calls_count": sum(int(loop.get("tool_calls_count", 0) or 0) for loop in live_loops),
                "tool_results_count": sum(int(loop.get("tool_results_count", 0) or 0) for loop in live_loops),
                "adopted_artifacts_count": sum(int(loop.get("adopted_artifacts_count", 0) or 0) for loop in live_loops),
                "permission_requests_count": sum(int(loop.get("permission_requests_count", 0) or 0) for loop in live_loops),
                "stop_reasons": stop_reasons,
                "ok": all(bool(loop.get("ok")) for loop in live_loops),
            },
            "errors": errors,
            "ok": not errors and all(bool(summary.get("ok")) for summary in enabled_summaries),
        }


def load_agent_runner(
    agent_config_name: str,
    *,
    project_root: Path | None = None,
    strict_tool_result_pairing: bool | None = None,
    context_compaction_threshold_tokens: int | None = None,
    preserve_recent_tool_results: int | None = None,
    permission_mode: str | None = None,
    permission_state: dict[str, object] | None = None,
    settings_context: dict[str, object] | None = None,
    model_client: ClaudeModelClient | None = None,
    runtime_mode: str = "",
) -> ClaudeStyleAgentRunner:
    root = project_root or PROJECT_ROOT
    config_path = root / "integration" / agent_config_name
    return ClaudeStyleAgentRunner(
        load_claude_agent_definition(config_path, project_root=root),
        project_root=root,
        strict_tool_result_pairing=strict_tool_result_pairing,
        context_compaction_threshold_tokens=context_compaction_threshold_tokens,
        preserve_recent_tool_results=preserve_recent_tool_results,
        permission_mode=permission_mode,
        permission_state=permission_state,
        settings_context=settings_context,
        model_client=model_client,
        runtime_mode=runtime_mode,
    )


def load_pipeline_runner(
    *,
    project_root: Path | None = None,
    strict_tool_result_pairing: bool | None = None,
    context_compaction_threshold_tokens: int | None = None,
    preserve_recent_tool_results: int | None = None,
    permission_mode: str | None = None,
    permission_state: dict[str, object] | None = None,
    settings_context: dict[str, object] | None = None,
    model_client: ClaudeModelClient | None = None,
    runtime_mode: str = "",
) -> ClaudeStylePipelineRunner:
    return ClaudeStylePipelineRunner(
        project_root=project_root or PROJECT_ROOT,
        strict_tool_result_pairing=strict_tool_result_pairing,
        context_compaction_threshold_tokens=context_compaction_threshold_tokens,
        preserve_recent_tool_results=preserve_recent_tool_results,
        permission_mode=permission_mode,
        permission_state=permission_state,
        settings_context=settings_context,
        model_client=model_client,
        runtime_mode=runtime_mode,
    )
