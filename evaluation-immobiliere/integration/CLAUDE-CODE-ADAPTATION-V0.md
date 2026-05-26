# Claude Code adaptation for eval-immo agents (v0)

This document tracks the local architecture now adapted from
`C:\Users\simon\claude-code-project` into eval-immo.

## Adapted surfaces

| Claude Code concept | eval-immo surface | Notes |
| --- | --- | --- |
| Agent config files | `integration/AGENTCONFIG-*-V0.yaml` | One config per role: `data-facts`, `comps-market`, `valuation-draft`, `compliance-qa`, `redaction`. |
| Static and dynamic system prompt | `/session/agent-prompts` | Renders static prompt, dynamic template, and runtime contract per agent. |
| Tool registry and model-facing schemas | `/session/tools` | Enforces allowed tools per agent and validates tool inputs. |
| Permission context | `/session/permissions` | Persists decisions, updates, replay validation, and additional working directories. |
| Claude settings merge order | `/session/settings` | Supports defaults, user, project, local, session, flags, and policy layers. |
| Slash commands | `/session/commands`, `/session/command`, `/session/command-history` | Includes built-ins and skill-backed prompt commands with settings filters. |
| Skills | `/session/skills` | Loads project skills lazily from the skills registry and exposes frontmatter metadata. |
| Transcript | `/session/transcript` | Stores Claude-style message envelopes and validates tool-use/tool-result pairing. |
| Hooks | `/session/hooks` | Records session, tool, and compaction hook invocations. |
| Task state | `/session/tasks` | Tracks per-agent artifact tasks and pipeline aggregate state. |
| Handoffs | `/session/handoffs` | Connects agent outputs to the next agent's context. |
| Runtime state and compaction | `/session/runtime-state` | Summarizes messages, estimated tokens, cost, and compaction pressure. |
| Model adapter surface | `/session/model-client` | Exposes request/response summaries for opt-in live-adapter runs. |
| Live tool-use loop | `claude_live_tool_loop_v0` | Executes model-emitted `tool_use` blocks through eval-immo tools, appends `tool_result`, enforces output artifact contracts, and reports explicit stop reasons. |
| Live replay surface | `/session/live-replay` | Validates transcript replay, permission replay, retry candidates, and `permission_state_ask_rule` requests for interrupted live loops. |
| Model provider config | `claude_model_provider_config_v0` | Redacts provider options, detects the optional Anthropic SDK, and keeps `fake` as the only default executable runtime provider. |
| Provider diagnostics | `/session/provider-diagnostics`, `claude_model_provider_diagnostics_v0` | Reports SDK availability, redacted config, default-runtime status, SDK-transport readiness, API-runtime guardrails, and missing guardrails without constructing a client. |
| Anthropic SDK adapter scaffold | `anthropic_messages_v0`, `anthropic_sdk_transport_v0` | Maps Claude-style requests/responses through injected transports and a guarded SDK transport; SDK execution requires explicit flags, `ANTHROPIC_API_KEY`, dependency availability, timeout/retry settings, and mocked tests before any live run. |
| Controller bundle | `/session/claude` | Frontend-ready aggregate for the product cockpit. |

## Project settings parity

eval-immo now understands the Claude Code permissions shape from settings:

```json
{
  "permissions": {
    "defaultMode": "default",
    "allow": [{ "toolName": "read_file" }],
    "deny": ["write_file"],
    "ask": [],
    "additionalDirectories": ["C:\\Users\\simon\\claude-code-project"]
  }
}
```

`permissions.additionalDirectories` is converted into the runtime
`additionalWorkingDirectories` permission state, preserving the setting source
such as `projectSettings`, `localSettings`, or `sessionSettings`.

## Runtime modes

| Mode | Scope |
| --- | --- |
| `claude_data_facts_v0` | Single data extraction agent. |
| `claude_comps_market_v0` | Single comparable market agent. |
| `claude_valuation_draft_v0` | Single valuation draft agent. |
| `claude_compliance_qa_v0` | Single compliance QA agent. |
| `claude_redaction_v0` | Single redaction agent. |
| `claude_pipeline_v0` | Sequential five-agent Claude-style pipeline. |
| `claude_live_data_facts_v0` | Opt-in data-facts live-adapter path backed by the model client contract. |
| `claude_live_comps_market_v0` | Opt-in comps-market live-adapter path backed by the same model client contract. |
| `claude_live_valuation_draft_v0` | Opt-in valuation-draft live-adapter path backed by the same model client contract. |
| `claude_live_compliance_qa_v0` | Opt-in compliance-qa live-adapter path backed by the same model client contract. |
| `claude_live_redaction_v0` | Opt-in redaction live-adapter path backed by the same model client contract. |
| `claude_live_pipeline_v0` | Opt-in five-agent live-adapter pipeline with aggregate model-client and per-agent live-loop summaries. |

## Boundary

The default v0 adaptation is deterministic and local. It mirrors Claude Code's
agent architecture, settings, permissions, commands, tools, transcript, hooks,
tasks, handoffs, and controller shape, but it does not call a live model provider
or run the TypeScript Claude Code UI.

The `claude_live_*_v0` modes are controlled bridges toward live agents for all
five eval-immo roles. They keep the same runner/tool/artifact contracts and run
a bounded model tool-use loop through a fake provider by default. Model-emitted
`tool_use` blocks execute through the existing registry and permission policy;
matching `tool_result` blocks are appended to the transcript before the next
turn; live `write_file` calls must target declared agent outputs and pass the
artifact contract preflight before any file is written. Declared artifacts
written by the live loop are adopted as the primary output and are not
overwritten by deterministic synthesis; deterministic outputs remain the
fallback for artifacts the model did not write. Provider options are
summarized through `claude_model_provider_config_v0`, secrets are redacted, and
non-fake providers remain rejected by API/runtime factory calls unless every
guardrail is explicitly satisfied. That gives the project the Claude-Code-shaped
adapter seam before any external SDK or billing-sensitive provider is enabled.

`claude_live_pipeline_v0` threads the same bounded loop through the five-agent
pipeline. The session result keeps aggregate model-client metrics plus
`model_client_by_agent` and `model_live_loop_by_agent`, so provider diagnostics,
permissions, handoffs, transcript, and artifact lineage can be audited at both
pipeline and agent scope.

The `anthropic_messages_v0` scaffold defines the request/response mapping for a
future Anthropic SDK transport. It can be exercised with an injected non-network
transport in tests, and `anthropic_sdk_transport_v0` adds the guarded real SDK
boundary: optional dependency detection, `ANTHROPIC_API_KEY` loading without
persistence, explicit `allow_network` + `enable_sdk_execution` flags, SDK
timeout/retry parameters, and a transport error taxonomy for timeout, retryable,
server, auth, bad-request, and connection failures. `/session/provider-diagnostics`
exposes that readiness without constructing a client.

API/runtime calls remain fake-only by default. Anthropic execution is available
only for `claude_live_*_v0` modes when the operator sets
`EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME`, the request explicitly uses
`allow_network` and `enable_sdk_execution`, `ANTHROPIC_API_KEY` is present, and
the SDK is available. Tests exercise that path through an injected mock SDK
factory; no live network test or billing-sensitive call is part of the suite.

Operator smoke execution lives outside CI in
`outils/claude_live_provider_smoke_v0.py` with the companion runbook
`integration/CLAUDE-LIVE-PROVIDER-SMOKE-RUNBOOK.md`. The harness defaults to
diagnostics-only, writes a redacted report, and requires
`EVAL_IMMO_RUN_LIVE_SMOKE`, `EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME`,
`--allow-network`, `--enable-sdk-execution`, and `--execute` before any real
provider runtime call.
