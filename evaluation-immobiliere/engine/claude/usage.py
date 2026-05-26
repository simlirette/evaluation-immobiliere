from __future__ import annotations

from engine.claude.context import estimate_message_tokens
from engine.claude.types import ClaudeModelProfile


MODEL_COSTS_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-3-5-haiku": {
        "input_tokens": 0.8,
        "output_tokens": 4.0,
        "cache_creation_input_tokens": 1.0,
        "cache_read_input_tokens": 0.08,
        "web_search_requests": 0.01,
    },
    "claude-haiku-4-5": {
        "input_tokens": 1.0,
        "output_tokens": 5.0,
        "cache_creation_input_tokens": 1.25,
        "cache_read_input_tokens": 0.1,
        "web_search_requests": 0.01,
    },
    "claude-3-7-sonnet": {
        "input_tokens": 3.0,
        "output_tokens": 15.0,
        "cache_creation_input_tokens": 3.75,
        "cache_read_input_tokens": 0.3,
        "web_search_requests": 0.01,
    },
    "claude-sonnet-4": {
        "input_tokens": 3.0,
        "output_tokens": 15.0,
        "cache_creation_input_tokens": 3.75,
        "cache_read_input_tokens": 0.3,
        "web_search_requests": 0.01,
    },
    "claude-sonnet-4-5": {
        "input_tokens": 3.0,
        "output_tokens": 15.0,
        "cache_creation_input_tokens": 3.75,
        "cache_read_input_tokens": 0.3,
        "web_search_requests": 0.01,
    },
    "claude-sonnet-4-6": {
        "input_tokens": 3.0,
        "output_tokens": 15.0,
        "cache_creation_input_tokens": 3.75,
        "cache_read_input_tokens": 0.3,
        "web_search_requests": 0.01,
    },
    "claude-opus-4": {
        "input_tokens": 15.0,
        "output_tokens": 75.0,
        "cache_creation_input_tokens": 18.75,
        "cache_read_input_tokens": 1.5,
        "web_search_requests": 0.01,
    },
    "claude-opus-4-1": {
        "input_tokens": 15.0,
        "output_tokens": 75.0,
        "cache_creation_input_tokens": 18.75,
        "cache_read_input_tokens": 1.5,
        "web_search_requests": 0.01,
    },
    "claude-opus-4-5": {
        "input_tokens": 5.0,
        "output_tokens": 25.0,
        "cache_creation_input_tokens": 6.25,
        "cache_read_input_tokens": 0.5,
        "web_search_requests": 0.01,
    },
    "claude-opus-4-6": {
        "input_tokens": 5.0,
        "output_tokens": 25.0,
        "cache_creation_input_tokens": 6.25,
        "cache_read_input_tokens": 0.5,
        "web_search_requests": 0.01,
    },
}


def model_pricing_for_profile(model_profile: ClaudeModelProfile) -> dict[str, object]:
    pricing = MODEL_COSTS_PER_MTOK.get(model_profile.canonical_model)
    unknown = pricing is None
    if pricing is None:
        pricing = MODEL_COSTS_PER_MTOK["claude-opus-4-6"]
    return {
        "schema_version": "claude_model_pricing_v0",
        "model": model_profile.model,
        "canonical_model": model_profile.canonical_model,
        "model_key": model_profile.model_key,
        "unit": "usd_per_million_tokens",
        "input_tokens": pricing["input_tokens"],
        "output_tokens": pricing["output_tokens"],
        "cache_creation_input_tokens": pricing["cache_creation_input_tokens"],
        "cache_read_input_tokens": pricing["cache_read_input_tokens"],
        "web_search_requests": pricing["web_search_requests"],
        "unknown_model_cost": unknown,
        "source": "claude_code_modelCost_adapted_v0",
    }


def estimate_usage_from_messages(messages: list[dict[str, object]]) -> dict[str, int]:
    input_messages = [
        message
        for message in messages
        if isinstance(message, dict) and message.get("role") in {"system", "user"}
    ]
    output_messages = [
        message
        for message in messages
        if isinstance(message, dict) and message.get("role") == "assistant"
    ]
    input_tokens = estimate_message_tokens(input_messages) if input_messages else 0
    output_tokens = estimate_message_tokens(output_messages) if output_messages else 0
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
        "web_search_requests": 0,
    }


def calculate_usage_cost_usd(pricing: dict[str, object], usage: dict[str, int]) -> float:
    input_cost = (int(usage.get("input_tokens", 0)) / 1_000_000) * float(pricing["input_tokens"])
    output_cost = (int(usage.get("output_tokens", 0)) / 1_000_000) * float(pricing["output_tokens"])
    cache_read_cost = (int(usage.get("cache_read_input_tokens", 0)) / 1_000_000) * float(pricing["cache_read_input_tokens"])
    cache_write_cost = (int(usage.get("cache_creation_input_tokens", 0)) / 1_000_000) * float(pricing["cache_creation_input_tokens"])
    web_search_cost = int(usage.get("web_search_requests", 0)) * float(pricing["web_search_requests"])
    return round(input_cost + output_cost + cache_read_cost + cache_write_cost + web_search_cost, 8)


def format_cost_usd(cost: float, max_decimal_places: int = 4) -> str:
    return f"${cost:.2f}" if cost > 0.5 else f"${cost:.{max_decimal_places}f}"


def build_usage_accounting(
    *,
    agent_type: str,
    model_profile: ClaudeModelProfile,
    messages: list[dict[str, object]],
    token_budget: dict[str, object],
    wall_clock_seconds: float,
    tool_use_count: int,
) -> dict[str, object]:
    pricing = model_pricing_for_profile(model_profile)
    usage = estimate_usage_from_messages(messages)
    total_tokens = int(usage["input_tokens"] + usage["output_tokens"])
    cost_usd = calculate_usage_cost_usd(pricing, usage)
    return {
        "schema_version": "claude_usage_accounting_v0",
        "agent_type": agent_type,
        "model": model_profile.model,
        "canonical_model": model_profile.canonical_model,
        "model_key": model_profile.model_key,
        "pricing": pricing,
        "usage": {
            **usage,
            "total_tokens": total_tokens,
            "estimated_transcript_tokens": int(token_budget.get("estimated_tokens", total_tokens) or total_tokens),
        },
        "cost_usd": cost_usd,
        "formatted_cost": format_cost_usd(cost_usd),
        "wall_clock_seconds": wall_clock_seconds,
        "api_duration_seconds": 0.0,
        "tool_use_count": tool_use_count,
        "estimation_basis": "local_transcript_token_estimate_v0",
        "unknown_model_cost": bool(pricing.get("unknown_model_cost")),
        "ok": not bool(pricing.get("unknown_model_cost")),
    }


def summarize_usage_accounting(
    usage_by_agent: dict[str, dict[str, object]],
    *,
    agent_type: str = "claude-pipeline",
    wall_clock_seconds: float = 0.0,
) -> dict[str, object]:
    model_usage: dict[str, dict[str, object]] = {}
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_read_tokens = 0
    total_cache_write_tokens = 0
    total_web_search_requests = 0
    total_tool_use_count = 0
    unknown_model_cost = False

    for usage_summary in usage_by_agent.values():
        if not isinstance(usage_summary, dict):
            continue
        canonical_model = str(usage_summary.get("canonical_model") or "unknown")
        usage = usage_summary.get("usage", {})
        if not isinstance(usage, dict):
            usage = {}
        cost_usd = float(usage_summary.get("cost_usd", 0.0) or 0.0)
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cache_read_tokens = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_write_tokens = int(usage.get("cache_creation_input_tokens", 0) or 0)
        web_search_requests = int(usage.get("web_search_requests", 0) or 0)
        tool_use_count = int(usage_summary.get("tool_use_count", 0) or 0)
        total_cost += cost_usd
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_cache_read_tokens += cache_read_tokens
        total_cache_write_tokens += cache_write_tokens
        total_web_search_requests += web_search_requests
        total_tool_use_count += tool_use_count
        unknown_model_cost = unknown_model_cost or bool(usage_summary.get("unknown_model_cost"))

        bucket = model_usage.setdefault(
            canonical_model,
            {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "web_search_requests": 0,
                "cost_usd": 0.0,
                "agents": [],
            },
        )
        bucket["input_tokens"] = int(bucket["input_tokens"]) + input_tokens
        bucket["output_tokens"] = int(bucket["output_tokens"]) + output_tokens
        bucket["cache_read_input_tokens"] = int(bucket["cache_read_input_tokens"]) + cache_read_tokens
        bucket["cache_creation_input_tokens"] = int(bucket["cache_creation_input_tokens"]) + cache_write_tokens
        bucket["web_search_requests"] = int(bucket["web_search_requests"]) + web_search_requests
        bucket["cost_usd"] = round(float(bucket["cost_usd"]) + cost_usd, 8)
        agent = str(usage_summary.get("agent_type") or "")
        if agent and agent not in bucket["agents"]:
            bucket["agents"].append(agent)

    rounded_total_cost = round(total_cost, 8)
    return {
        "schema_version": "claude_usage_summary_v0",
        "agent_type": agent_type,
        "agents_count": len(usage_by_agent),
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "cache_read_input_tokens": total_cache_read_tokens,
        "cache_creation_input_tokens": total_cache_write_tokens,
        "web_search_requests": total_web_search_requests,
        "total_tokens": total_input_tokens + total_output_tokens,
        "tool_use_count": total_tool_use_count,
        "total_cost_usd": rounded_total_cost,
        "formatted_total_cost": format_cost_usd(rounded_total_cost),
        "wall_clock_seconds": wall_clock_seconds,
        "api_duration_seconds": 0.0,
        "model_usage": model_usage,
        "unknown_model_cost": unknown_model_cost,
        "estimation_basis": "local_transcript_token_estimate_v0",
        "ok": not unknown_model_cost,
    }
