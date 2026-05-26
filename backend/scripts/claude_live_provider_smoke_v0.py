#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import api
from engine.claude.model_client import build_model_provider_diagnostics


RUN_LIVE_SMOKE_ENV_FLAG = "EVAL_IMMO_RUN_LIVE_SMOKE"
OUT_JSON_DEFAULT = PROJECT_ROOT / "runtime_pilotes_reels" / "claude_live_provider_smoke_v0.json"


def truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "oui", "on"}


def provider_options(args: argparse.Namespace) -> dict[str, object]:
    options: dict[str, object] = {
        "provider": args.provider,
        "api_key_env": args.api_key_env,
        "allow_network": args.allow_network,
        "enable_sdk_execution": args.enable_sdk_execution,
        "timeout_seconds": args.timeout_seconds,
        "max_retries": args.max_retries,
    }
    if args.model:
        options["model"] = args.model
    return options


def build_report(args: argparse.Namespace, diagnostics: dict[str, object], execution: dict[str, object] | None) -> dict[str, object]:
    return {
        "schema_version": "claude_live_provider_smoke_report_v0",
        "mode": "execute" if args.execute else "diagnostics",
        "fixture": args.fixture,
        "runtime_mode": args.runtime_mode,
        "provider": diagnostics.get("provider", ""),
        "diagnostics": diagnostics,
        "execution": execution or {},
        "guardrails": {
            "run_live_smoke_env_flag": RUN_LIVE_SMOKE_ENV_FLAG,
            "run_live_smoke_env_enabled": truthy(os.environ.get(RUN_LIVE_SMOKE_ENV_FLAG)),
            "operator_runtime_env_flag": api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG,
            "operator_runtime_env_enabled": truthy(os.environ.get(api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG)),
            "allow_network": bool(args.allow_network),
            "enable_sdk_execution": bool(args.enable_sdk_execution),
        },
        "redacted": True,
        "ok": not diagnostics.get("missing_guardrails") and (not args.execute or bool(execution and execution.get("ok"))),
    }


def validate_execute_guardrails(args: argparse.Namespace, diagnostics: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if not truthy(os.environ.get(RUN_LIVE_SMOKE_ENV_FLAG)):
        errors.append(f"env_missing:{RUN_LIVE_SMOKE_ENV_FLAG}")
    if not truthy(os.environ.get(api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG)):
        errors.append(f"env_missing:{api.ANTHROPIC_SDK_RUNTIME_ENV_FLAG}")
    if not args.allow_network:
        errors.append("flag_missing:--allow-network")
    if not args.enable_sdk_execution:
        errors.append("flag_missing:--enable-sdk-execution")
    missing_guardrails = diagnostics.get("missing_guardrails", [])
    if isinstance(missing_guardrails, list):
        errors.extend(f"provider_guardrail_missing:{item}" for item in missing_guardrails)
    return errors


def run_live_smoke(args: argparse.Namespace, diagnostics: dict[str, object]) -> dict[str, object]:
    errors = validate_execute_guardrails(args, diagnostics)
    if errors:
        return {
            "schema_version": "claude_live_provider_smoke_execution_v0",
            "attempted": False,
            "errors": errors,
            "ok": False,
        }

    payload = api.start_runtime(
        {
            "fixture": args.fixture,
            "runtime_mode": args.runtime_mode,
            "strict_mode": True,
            "claude_model_provider": provider_options(args),
        }
    )
    session = payload.get("session", {}) if isinstance(payload.get("session"), dict) else {}
    result = payload.get("result", {}) if isinstance(payload.get("result"), dict) else {}
    model_client = result.get("model_client", {}) if isinstance(result.get("model_client"), dict) else {}
    live_loop = result.get("model_live_loop", {}) if isinstance(result.get("model_live_loop"), dict) else {}
    return {
        "schema_version": "claude_live_provider_smoke_execution_v0",
        "attempted": True,
        "session_id": session.get("session_id", ""),
        "run_id": session.get("run_id", ""),
        "status": result.get("status", ""),
        "model_client": model_client,
        "live_tool_loop": live_loop,
        "blocking_failures": result.get("blocking_failures", []),
        "warnings": result.get("warnings", []),
        "ok": bool(model_client.get("ok", False)) and result.get("status") != "A_REVOIR",
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnostics-first smoke harness for guarded Claude live provider runs."
    )
    parser.add_argument("--provider", default="anthropic")
    parser.add_argument("--model", default="")
    parser.add_argument("--api-key-env", default="ANTHROPIC_API_KEY")
    parser.add_argument("--fixture", default="case_nominal.json")
    parser.add_argument("--runtime-mode", default=api.RUNTIME_MODE_CLAUDE_LIVE_DATA_FACTS_V0)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=0)
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--enable-sdk-execution", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json-out", type=Path, default=OUT_JSON_DEFAULT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    diagnostics = build_model_provider_diagnostics(provider_options(args), env=os.environ)
    execution = run_live_smoke(args, diagnostics) if args.execute else None
    report = build_report(args, diagnostics, execution)
    write_report(args.json_out, report)

    print(f"Claude live provider smoke report: {args.json_out}")
    print(f"Mode: {report['mode']}")
    print(f"Provider: {report['provider']}")
    print(f"Missing guardrails: {diagnostics.get('missing_guardrails', [])}")
    if execution:
        print(f"Execution attempted: {execution.get('attempted', False)}")
        print(f"Execution ok: {execution.get('ok', False)}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
