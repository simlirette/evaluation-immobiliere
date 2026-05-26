# Claude Code integration handoff

Date: 2026-05-26

## Objective

Continue adapting `C:\Users\simon\claude-code-project` architecture into
`eval-immo`, one agent/surface slice at a time, while keeping the eval-immo
business runtime deterministic and guarded.

The architecture direction is Claude-Code-style agents adapted to eval-immo
roles, not a generic rewrite. Preserve the existing eval-immo/Aston runtime
contracts and add Claude Code surfaces around them.

## Current checkout

Repo path:
`C:\Users\simon\Documents\Codex\2026-04-28\evaluation-immobiliere\evaluation-immobiliere`

Reference project:
`C:\Users\simon\claude-code-project`

Important note: the worktree contains many uncommitted changes from prior
slices. Do not revert them. They are intentional integration work.

## Completed Claude Code adaptation surfaces

- Split Claude-style runtime modules under `engine/claude/`.
- Added `engine/claude_agent.py` as the compatibility facade and runner layer.
- Added agent configs for all five eval-immo roles:
  `data-facts`, `comps-market`, `valuation-draft`, `compliance-qa`, `redaction`.
- Added Claude-style runtime modes:
  `claude_data_facts_v0`,
  `claude_comps_market_v0`,
  `claude_valuation_draft_v0`,
  `claude_compliance_qa_v0`,
  `claude_redaction_v0`,
  `claude_pipeline_v0`.
- Added opt-in live-adapter modes for all five roles:
  `claude_live_data_facts_v0`,
  `claude_live_comps_market_v0`,
  `claude_live_valuation_draft_v0`,
  `claude_live_compliance_qa_v0`,
  `claude_live_redaction_v0`.
- Added Claude-style surfaces and API/controller endpoints:
  settings, permissions, commands, command history, skills, tools, prompts,
  transcript, hooks, tasks, handoffs, runtime state, artifact lineage,
  model client, live replay, controller bundle, controller actions, action
  snapshots.
- Updated `ui/product_cockpit.html` to surface the Claude controller state.
- Added integration docs:
  `integration/CLAUDE-CODE-ADAPTATION-V0.md`,
  updated `integration/ORCHESTRATION-CHECKLIST-V0.md`,
  updated `integration/README-INTEGRATION.md`.

## Current provider boundary

The latest completed slices hardened the model-provider seam:

- `claude_model_provider_config_v0` summarizes provider options.
- Secrets are redacted from provider summaries and errors.
- `fake` remains the only executable provider in API/runtime calls.
- Real providers such as `anthropic` are rejected by default.
- `anthropic_messages_v0` scaffold exists for request/response mapping.
- `AnthropicClaudeModelClient` can only be exercised with an injected
  non-network mock transport in tests.
- `anthropic_sdk_transport_v0` now exists as the guarded real SDK boundary.
- Anthropic SDK dependency detection is optional and does not require the SDK in
  tests.
- `ANTHROPIC_API_KEY` is read only at SDK transport construction time and is not
  persisted into summaries or payloads.
- Real SDK construction requires explicit guardrails: `allow_network`,
  `enable_sdk_execution`, SDK availability, env key presence, and the
  `build_model_client(..., enable_sdk_execution=True)` call path.
- SDK timeout/max-retry options are mapped into the SDK client factory.
- SDK failures are classified into timeout, retryable, server, auth,
  bad-request, connection, and fallback error codes.
- `/session/provider-diagnostics` reports SDK availability, redacted config,
  default-runtime status, SDK-transport readiness, API-runtime readiness, and
  missing guardrails without constructing a client.
- Runtime/API still blocks real SDK/network execution by default.
- Anthropic execution is now wired for `claude_live_*_v0` only when the operator
  sets `EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME`, request options set
  `allow_network` and `enable_sdk_execution`, `ANTHROPIC_API_KEY` is present,
  and the SDK is available.
- Tests cover the runtime Anthropic path with an injected mock SDK factory only;
  no live network call was added.
- Operator smoke execution is isolated in
  `outils/claude_live_provider_smoke_v0.py` with
  `integration/CLAUDE-LIVE-PROVIDER-SMOKE-RUNBOOK.md`. It defaults to
  diagnostics-only and requires `EVAL_IMMO_RUN_LIVE_SMOKE`,
  `EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME`, `--allow-network`,
  `--enable-sdk-execution`, and `--execute` for any real provider runtime call.

## Current live-loop boundary

The latest completed slice moved the `claude_live_*_v0` adapter from a single
request/response probe to a bounded tool-use loop:

- Model responses with `tool_use` blocks now execute through the existing
  eval-immo tool registry and permission policy.
- The loop appends matching `tool_result` messages and sends the expanded
  transcript back to the model on the next turn.
- `write_file` calls are preflighted against the agent's declared output
  artifacts, required artifact fields, and contract rules before any file is
  written.
- Stop reasons are explicit: `completion`, `max_turns`, `model_error`,
  `tool_error`, `contract_failure`, and `permission_required`.
- Declared artifacts written by the live model are adopted as primary outputs
  and are not overwritten by deterministic synthesis; deterministic artifacts
  remain the fallback for outputs the model did not write.
- `claude_live_pipeline_v0` runs the same bounded loop across all five agents,
  preserving aggregate model-client metrics plus per-agent model and live-loop
  summaries.
- `/session/live-replay` exposes transcript replay validation, permission replay
  validation, failed tool-call retry candidates, and operator permission
  requests from `permission_state_ask_rule`.
- Requests, responses, tool calls, tool results, loop summary, and stop reason
  are available through the runner result, `/session/model-client`,
  `/session/live-replay`, `/session/claude`, audit events, and transcript
  surfaces.
- Tests use scripted fake/mock model clients only; no live network test was
  added.

## Last verified test state

From this checkout:

- Claude/API regression:
  `python -m unittest tests.test_claude_agent_v0 tests.test_api_v0 -v`
  passed with 116 tests.
- Full discovery from the outer checkout:
  `python -m unittest discover -s evaluation-immobiliere\tests -p "test_*.py" -v`
  passed with 282 tests.
- `git diff --check` was clean except Git LF-to-CRLF normalization warnings.
- Generated `__pycache__` folders were removed after path verification.

## Known worktree shape

Expected modified tracked files include:

- `api.py`
- `integration/ORCHESTRATION-CHECKLIST-V0.md`
- `integration/README-INTEGRATION.md`
- `tests/test_api_v0.py`
- `ui/product_cockpit.html`

Expected untracked integration files/directories include:

- `.claude/`
- `engine/claude/`
- `engine/claude_agent.py`
- `integration/CLAUDE-CODE-ADAPTATION-V0.md`
- `integration/CLAUDE-CODE-HANDOFF.md`
- `integration/CLAUDE-LIVE-PROVIDER-SMOKE-RUNBOOK.md`
- `outils/claude_live_provider_smoke_v0.py`
- `tests/test_claude_agent_v0.py`

## Remaining slices before full adaptation

The four substantive slices from the prior checkpoint are implemented:

1. Live-authored declared artifacts are adopted with deterministic fallback.
2. The live loop is threaded through the five-agent pipeline.
3. Operator replay/resume surfaces are exposed through `/session/live-replay`
   and the `live_replay` controller action.
4. The real-provider smoke harness and runbook are present outside CI.

Remaining work is verification, cleanup, and any operator-requested live smoke.
