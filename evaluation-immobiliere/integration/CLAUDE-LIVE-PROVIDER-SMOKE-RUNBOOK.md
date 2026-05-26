# Claude live provider smoke runbook

This runbook covers the operator-only smoke path for real Anthropic-backed
`claude_live_*_v0` runtimes. The default harness mode is diagnostics-only and
does not construct a live SDK client.

## Harness

Script:

```powershell
python outils\claude_live_provider_smoke_v0.py
```

Default behavior:

- provider diagnostics only
- no network execution
- redacted JSON report at `runtime_pilotes_reels/claude_live_provider_smoke_v0.json`
- nonzero exit when provider/API guardrails are missing

Useful readiness check:

```powershell
$env:ANTHROPIC_API_KEY = "<operator-secret>"
$env:EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME = "true"
python outils\claude_live_provider_smoke_v0.py --allow-network --enable-sdk-execution
```

This still does not execute the runtime because `--execute` is absent.

## Execute A Live Smoke

Execution requires all of the following:

- `ANTHROPIC_API_KEY` present, or another key name supplied with `--api-key-env`
- `EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME=true`
- `EVAL_IMMO_RUN_LIVE_SMOKE=true`
- `--allow-network`
- `--enable-sdk-execution`
- `--execute`

Example:

```powershell
$env:ANTHROPIC_API_KEY = "<operator-secret>"
$env:EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME = "true"
$env:EVAL_IMMO_RUN_LIVE_SMOKE = "true"
python outils\claude_live_provider_smoke_v0.py --allow-network --enable-sdk-execution --execute --runtime-mode claude_live_data_facts_v0 --fixture case_nominal.json
```

## Acceptance Criteria

- The report has `schema_version: claude_live_provider_smoke_report_v0`.
- `diagnostics.redacted` is true.
- `diagnostics.missing_guardrails` is empty before any execution.
- In execute mode, `execution.attempted` is true and `execution.ok` is true.
- The resulting session exposes `/session/model-client`, `/session/live-replay`,
  `/session/provider-diagnostics`, and `/session/claude`.

## Failure Handling

- If diagnostics list missing guardrails, do not run `--execute`.
- If the smoke run returns `A_REVOIR`, inspect `/session/live-replay` first for
  retry candidates, failed tool calls, permission requests, and transcript replay
  validation.
- If a permission request has reason `permission_state_ask_rule`, apply the
  recommended allow rule only after operator review.
- If provider errors are auth, quota, timeout, or connection related, stop the
  smoke and keep the deterministic/fake runtime path as the working baseline.

## Rollback

No code rollback is required after a failed smoke. Remove only the temporary
operator environment variables and keep using deterministic modes or fake
`claude_live_*_v0` modes:

```powershell
Remove-Item Env:\EVAL_IMMO_RUN_LIVE_SMOKE -ErrorAction SilentlyContinue
Remove-Item Env:\EVAL_IMMO_ALLOW_ANTHROPIC_SDK_RUNTIME -ErrorAction SilentlyContinue
Remove-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
```

The harness is not part of CI and should not be run with `--execute` from an
automated test job.
