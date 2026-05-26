from __future__ import annotations

from dataclasses import dataclass, field

from engine.claude.yamlish import render_template


@dataclass(frozen=True)
class ClaudeAgentBudget:
    max_iterations: int = 12
    max_tokens: int = 8192
    max_total_tokens: int = 25000
    window_size: int = 8
    max_wall_clock_seconds: int | None = None


@dataclass(frozen=True)
class ClaudeAgentFlags:
    thinking_enabled: bool = False
    long_cache: bool = False
    verification_checklist: str | None = None


@dataclass(frozen=True)
class ClaudeModelProfile:
    model: str
    canonical_model: str
    model_key: str
    family: str
    provider_ids: dict[str, str]
    context_window_tokens: int
    max_output_tokens: int
    supports_long_context: bool
    supports_thinking: bool
    source: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "claude_model_profile_v0",
            "model": self.model,
            "canonical_model": self.canonical_model,
            "model_key": self.model_key,
            "family": self.family,
            "provider_ids": dict(self.provider_ids),
            "context_window_tokens": self.context_window_tokens,
            "max_output_tokens": self.max_output_tokens,
            "supports_long_context": self.supports_long_context,
            "supports_thinking": self.supports_thinking,
            "source": self.source,
        }


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    permission: str
    input_schema: dict[str, object] = field(default_factory=dict)
    max_result_size_chars: int = 30000
    strict: bool = True
    read_only: bool = False
    destructive: bool = False
    concurrency_safe: bool = True
    search_hint: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "claude_tool_spec_v0",
            "name": self.name,
            "description": self.description,
            "permission": self.permission,
            "input_schema": dict(self.input_schema),
            "max_result_size_chars": self.max_result_size_chars,
            "strict": self.strict,
            "read_only": self.read_only,
            "destructive": self.destructive,
            "concurrency_safe": self.concurrency_safe,
            "search_hint": self.search_hint,
        }

    def model_facing_schema(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": dict(self.input_schema),
            "strict": self.strict,
        }


@dataclass(frozen=True)
class ClaudeToolCall:
    id: str
    name: str
    input: dict[str, object]
    agent_type: str

    def as_message_block(self) -> dict[str, object]:
        return {
            "type": "tool_use",
            "id": self.id,
            "name": self.name,
            "input": self.input,
        }


@dataclass(frozen=True)
class ClaudeToolResult:
    call_id: str
    name: str
    ok: bool
    output: object = None
    error: str | None = None
    permission: str | None = None

    def as_message_block(self) -> dict[str, object]:
        block: dict[str, object] = {
            "type": "tool_result",
            "tool_use_id": self.call_id,
            "name": self.name,
            "ok": self.ok,
        }
        if self.output is not None:
            block["output"] = self.output
        if self.error:
            block["error"] = self.error
        if self.permission:
            block["permission"] = self.permission
        return block


@dataclass(frozen=True)
class SkillSpec:
    name: str
    path: str
    description: str
    type: str
    sources: list[str]
    agents: list[str] = field(default_factory=list)
    loaded_from: str = "skills"
    source: str = "projectSettings"
    skill_root: str = ""
    plugin: str = ""
    display_name: str = ""
    when_to_use: str = ""
    version: str = ""
    model: str = ""
    argument_hint: str = ""
    arguments: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    context: list[str] = field(default_factory=list)
    effort: str = ""
    shell: str = ""
    content_length: int = 0
    frontmatter_tokens: int = 0
    has_analysis: bool = False
    user_invocable: bool = True
    disable_model_invocation: bool = False
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "claude_skill_spec_v0",
            "name": self.name,
            "path": self.path,
            "description": self.description,
            "type": self.type,
            "sources": list(self.sources),
            "agents": list(self.agents),
            "loaded_from": self.loaded_from,
            "source": self.source,
            "skill_root": self.skill_root,
            "plugin": self.plugin,
            "display_name": self.display_name,
            "when_to_use": self.when_to_use,
            "version": self.version,
            "model": self.model,
            "argument_hint": self.argument_hint,
            "arguments": list(self.arguments),
            "allowed_tools": list(self.allowed_tools),
            "paths": list(self.paths),
            "hooks": list(self.hooks),
            "context": list(self.context),
            "effort": self.effort,
            "shell": self.shell,
            "content_length": self.content_length,
            "frontmatter_tokens": self.frontmatter_tokens,
            "has_analysis": self.has_analysis,
            "user_invocable": self.user_invocable,
            "disable_model_invocation": self.disable_model_invocation,
            "ok": self.ok,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class CommandSpec:
    name: str
    type: str
    description: str
    source: str
    loaded_from: str = "builtin"
    aliases: list[str] = field(default_factory=list)
    argument_hint: str = ""
    progress_message: str = ""
    content_length: int = 0
    supports_non_interactive: bool = False
    immediate: bool = False
    is_hidden: bool = False
    is_sensitive: bool = False
    has_user_specified_description: bool = True
    allowed_tools: list[str] = field(default_factory=list)
    model: str = ""
    when_to_use: str = ""
    version: str = ""
    disable_model_invocation: bool = False
    user_invocable: bool = True
    plugin: str = ""
    skill_root: str = ""
    context: str = "inline"
    agent: str = ""
    effort: str = ""
    paths: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    availability: list[str] = field(default_factory=list)
    kind: str = ""
    bridge_safe: bool = False
    remote_safe: bool = False
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "claude_command_spec_v0",
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "source": self.source,
            "loaded_from": self.loaded_from,
            "aliases": list(self.aliases),
            "argument_hint": self.argument_hint,
            "progress_message": self.progress_message,
            "content_length": self.content_length,
            "supports_non_interactive": self.supports_non_interactive,
            "immediate": self.immediate,
            "is_hidden": self.is_hidden,
            "is_sensitive": self.is_sensitive,
            "has_user_specified_description": self.has_user_specified_description,
            "allowed_tools": list(self.allowed_tools),
            "model": self.model,
            "when_to_use": self.when_to_use,
            "version": self.version,
            "disable_model_invocation": self.disable_model_invocation,
            "user_invocable": self.user_invocable,
            "plugin": self.plugin,
            "skill_root": self.skill_root,
            "context": self.context,
            "agent": self.agent,
            "effort": self.effort,
            "paths": list(self.paths),
            "hooks": list(self.hooks),
            "availability": list(self.availability),
            "kind": self.kind,
            "bridge_safe": self.bridge_safe,
            "remote_safe": self.remote_safe,
            "ok": self.ok,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class ClaudeStyleAgentDefinition:
    agent_type: str
    model: str
    model_profile: ClaudeModelProfile
    system_prompt_static: str
    system_prompt_dynamic_template: str
    inputs: list[str]
    outputs: list[str]
    tools: list[str]
    tool_registry_summary: dict[str, object]
    skills: list[str]
    skill_context: dict[str, object]
    command_context: dict[str, object]
    budgets: ClaudeAgentBudget
    flags: ClaudeAgentFlags
    quality_gates: dict[str, list[str]]
    human_validation: dict[str, object]
    config_path: str

    @property
    def max_turns(self) -> int:
        return self.budgets.max_iterations

    def build_system_prompt(self, context: dict[str, object]) -> list[str]:
        dynamic = render_template(self.system_prompt_dynamic_template, context)
        contract = "\n".join(
            [
                "Contrat runtime agent:",
                f"- agent_type: {self.agent_type}",
                f"- model: {self.model}",
                f"- model_canonical: {self.model_profile.canonical_model}",
                f"- context_window_tokens: {self.model_profile.context_window_tokens}",
                f"- max_output_tokens: {self.model_profile.max_output_tokens}",
                f"- max_turns: {self.max_turns}",
                f"- tools_allowed: {', '.join(self.tools)}",
                f"- skills_allowed: {', '.join(self.skills)}",
                f"- skills_loaded_from: {', '.join(self.skill_context.get('loaded_from', [])) if isinstance(self.skill_context.get('loaded_from'), list) else 'unknown'}",
                f"- skill_context_ok: {bool(self.skill_context.get('ok'))}",
                f"- slash_commands_available: {self.command_context.get('commands_count', 0)}",
                f"- model_invocable_commands: {', '.join(self.command_context.get('model_invocable_command_names', [])) if isinstance(self.command_context.get('model_invocable_command_names'), list) else 'unknown'}",
                f"- outputs_required: {', '.join(self.outputs)}",
                f"- human_validation_required: {bool(self.human_validation.get('required'))}",
            ]
        )
        return [
            self.system_prompt_static.strip(),
            dynamic.strip(),
            contract.strip(),
        ]


@dataclass
class ClaudeAgentState:
    agent_type: str
    messages: list[dict[str, object]] = field(default_factory=list)
    events: list[dict[str, object]] = field(default_factory=list)
    handoffs_received: list[dict[str, object]] = field(default_factory=list)
    hook_invocations: list[dict[str, object]] = field(default_factory=list)
    permission_decisions: list[dict[str, object]] = field(default_factory=list)
    task_state: dict[str, object] = field(default_factory=dict)
    tool_use_count: int = 0
    token_budget_used: int = 0
