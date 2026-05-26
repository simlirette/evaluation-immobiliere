from __future__ import annotations

from engine.claude.context import estimate_message_tokens
from engine.claude.types import ClaudeAgentBudget, ClaudeModelProfile


MODEL_PROVIDER_CONFIGS: dict[str, dict[str, str]] = {
    "haiku35": {
        "firstParty": "claude-3-5-haiku-20241022",
        "bedrock": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "vertex": "claude-3-5-haiku@20241022",
        "foundry": "claude-3-5-haiku",
    },
    "haiku45": {
        "firstParty": "claude-haiku-4-5-20251001",
        "bedrock": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "vertex": "claude-haiku-4-5@20251001",
        "foundry": "claude-haiku-4-5",
    },
    "sonnet37": {
        "firstParty": "claude-3-7-sonnet-20250219",
        "bedrock": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "vertex": "claude-3-7-sonnet@20250219",
        "foundry": "claude-3-7-sonnet",
    },
    "sonnet40": {
        "firstParty": "claude-sonnet-4-20250514",
        "bedrock": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "vertex": "claude-sonnet-4@20250514",
        "foundry": "claude-sonnet-4",
    },
    "sonnet45": {
        "firstParty": "claude-sonnet-4-5-20250929",
        "bedrock": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "vertex": "claude-sonnet-4-5@20250929",
        "foundry": "claude-sonnet-4-5",
    },
    "sonnet46": {
        "firstParty": "claude-sonnet-4-6",
        "bedrock": "us.anthropic.claude-sonnet-4-6",
        "vertex": "claude-sonnet-4-6",
        "foundry": "claude-sonnet-4-6",
    },
    "opus40": {
        "firstParty": "claude-opus-4-20250514",
        "bedrock": "us.anthropic.claude-opus-4-20250514-v1:0",
        "vertex": "claude-opus-4@20250514",
        "foundry": "claude-opus-4",
    },
    "opus41": {
        "firstParty": "claude-opus-4-1-20250805",
        "bedrock": "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "vertex": "claude-opus-4-1@20250805",
        "foundry": "claude-opus-4-1",
    },
    "opus45": {
        "firstParty": "claude-opus-4-5-20251101",
        "bedrock": "us.anthropic.claude-opus-4-5-20251101-v1:0",
        "vertex": "claude-opus-4-5@20251101",
        "foundry": "claude-opus-4-5",
    },
    "opus46": {
        "firstParty": "claude-opus-4-6",
        "bedrock": "us.anthropic.claude-opus-4-6-v1",
        "vertex": "claude-opus-4-6",
        "foundry": "claude-opus-4-6",
    },
}

MODEL_FAMILY_BY_KEY = {
    "haiku35": "haiku",
    "haiku45": "haiku",
    "sonnet37": "sonnet",
    "sonnet40": "sonnet",
    "sonnet45": "sonnet",
    "sonnet46": "sonnet",
    "opus40": "opus",
    "opus41": "opus",
    "opus45": "opus",
    "opus46": "opus",
}

DEFAULT_CONTEXT_WINDOW_TOKENS = 200_000
LONG_CONTEXT_WINDOW_TOKENS = 1_000_000
DEFAULT_MAX_OUTPUT_TOKENS = 16_384


def first_party_name_to_canonical_model(model: str) -> str:
    name = model.lower().removesuffix("[1m]")
    ordered_needles = [
        "claude-opus-4-6",
        "claude-opus-4-5",
        "claude-opus-4-1",
        "claude-opus-4",
        "claude-sonnet-4-6",
        "claude-sonnet-4-5",
        "claude-sonnet-4",
        "claude-3-7-sonnet",
        "claude-haiku-4-5",
        "claude-3-5-haiku",
    ]
    for needle in ordered_needles:
        if needle in name:
            return needle
    return name


def model_key_from_canonical(canonical_model: str) -> str:
    lookup = {
        "claude-3-5-haiku": "haiku35",
        "claude-haiku-4-5": "haiku45",
        "claude-3-7-sonnet": "sonnet37",
        "claude-sonnet-4": "sonnet40",
        "claude-sonnet-4-5": "sonnet45",
        "claude-sonnet-4-6": "sonnet46",
        "claude-opus-4": "opus40",
        "claude-opus-4-1": "opus41",
        "claude-opus-4-5": "opus45",
        "claude-opus-4-6": "opus46",
    }
    # Most specific keys must win before their prefix variants.
    for canonical, key in sorted(lookup.items(), key=lambda item: len(item[0]), reverse=True):
        if canonical_model == canonical:
            return key
    return "custom"


def resolve_model_profile(model: str) -> ClaudeModelProfile:
    requested_long_context = model.lower().endswith("[1m]")
    canonical_model = first_party_name_to_canonical_model(model)
    model_key = model_key_from_canonical(canonical_model)
    provider_ids = MODEL_PROVIDER_CONFIGS.get(
        model_key,
        {
            "firstParty": canonical_model,
            "bedrock": canonical_model,
            "vertex": canonical_model,
            "foundry": canonical_model,
        },
    )
    family = MODEL_FAMILY_BY_KEY.get(model_key, "custom")
    supports_long_context = family in {"opus", "sonnet"} and requested_long_context
    return ClaudeModelProfile(
        model=model,
        canonical_model=canonical_model,
        model_key=model_key,
        family=family,
        provider_ids=provider_ids,
        context_window_tokens=LONG_CONTEXT_WINDOW_TOKENS if supports_long_context else DEFAULT_CONTEXT_WINDOW_TOKENS,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
        supports_long_context=supports_long_context,
        supports_thinking=family in {"opus", "sonnet"},
        source="claude_code_model_configs_adapted_v0",
    )


def build_token_budget_state(
    *,
    agent_type: str,
    model_profile: ClaudeModelProfile,
    budgets: ClaudeAgentBudget,
    messages: list[dict[str, object]] | None = None,
    estimated_tokens: int | None = None,
) -> dict[str, object]:
    used_tokens = int(estimated_tokens if estimated_tokens is not None else estimate_message_tokens(messages or []))
    max_total_tokens = int(budgets.max_total_tokens)
    context_window_tokens = int(model_profile.context_window_tokens)
    budget_ratio = round(used_tokens / max_total_tokens, 4) if max_total_tokens > 0 else 0.0
    context_ratio = round(used_tokens / context_window_tokens, 4) if context_window_tokens > 0 else 0.0
    warnings: list[str] = []
    if budgets.max_tokens > model_profile.max_output_tokens:
        warnings.append("agent_max_tokens_exceeds_model_output")
    if max_total_tokens > context_window_tokens:
        warnings.append("agent_total_budget_exceeds_context_window")
    if used_tokens > max_total_tokens:
        warnings.append("estimated_tokens_exceed_agent_total_budget")
    if used_tokens > context_window_tokens:
        warnings.append("estimated_tokens_exceed_context_window")

    return {
        "schema_version": "claude_token_budget_v0",
        "agent_type": agent_type,
        "model": model_profile.model,
        "canonical_model": model_profile.canonical_model,
        "model_key": model_profile.model_key,
        "estimated_tokens": used_tokens,
        "max_tokens": int(budgets.max_tokens),
        "max_total_tokens": max_total_tokens,
        "context_window_tokens": context_window_tokens,
        "max_output_tokens": int(model_profile.max_output_tokens),
        "remaining_total_tokens": max(0, max_total_tokens - used_tokens),
        "remaining_context_tokens": max(0, context_window_tokens - used_tokens),
        "budget_ratio": budget_ratio,
        "context_ratio": context_ratio,
        "window_size": int(budgets.window_size),
        "warnings": warnings,
        "warnings_count": len(warnings),
        "ok": not any(warning.endswith("_exceed_context_window") or warning.endswith("_exceed_agent_total_budget") for warning in warnings),
    }


def summarize_pipeline_token_budgets(
    token_budgets: dict[str, dict[str, object]],
    *,
    agent_type: str = "claude-pipeline",
) -> dict[str, object]:
    estimated_tokens = sum(int(budget.get("estimated_tokens", 0) or 0) for budget in token_budgets.values())
    max_total_tokens = sum(int(budget.get("max_total_tokens", 0) or 0) for budget in token_budgets.values())
    warnings = [
        f"{agent}:{warning}"
        for agent, budget in token_budgets.items()
        for warning in budget.get("warnings", [])
        if isinstance(warning, str)
    ]
    models = sorted({str(budget.get("canonical_model") or "") for budget in token_budgets.values() if budget.get("canonical_model")})
    return {
        "schema_version": "claude_pipeline_token_budget_v0",
        "agent_type": agent_type,
        "agents_count": len(token_budgets),
        "estimated_tokens": estimated_tokens,
        "max_total_tokens": max_total_tokens,
        "remaining_total_tokens": max(0, max_total_tokens - estimated_tokens),
        "budget_ratio": round(estimated_tokens / max_total_tokens, 4) if max_total_tokens > 0 else 0.0,
        "models": models,
        "warnings": warnings,
        "warnings_count": len(warnings),
        "ok": all(bool(budget.get("ok")) for budget in token_budgets.values()),
    }
