"""LLM routing — modèle par type de tâche.

Usage:
    from engine.llm_routing import get_llm_model, estimate_llm_cost

    model = get_llm_model("redaction_rapport")   # → "gpt-4o"
    cost  = estimate_llm_cost("gpt-4o", 2000, 1500)
"""
from __future__ import annotations

import os

# ── Routing par tâche ─────────────────────────────────────────────────────────
# Chaque tâche peut être surchargée via env var OPENAI_MODEL_<TASK_UPPER>
# ou globalement via OPENAI_MODEL (fallback final : LLM_ROUTING).
LLM_ROUTING: dict[str, str] = {
    "extraction_pdf":      "gpt-4o",       # Vision obligatoire (PDF → image)
    "parse_structured":    "gpt-4o-mini",  # Extraction JSON structurée (texte)
    "compliance_warnings": "gpt-4o-mini",  # W001-W005 non-bloquants
    "amu_analyse":         "gpt-4o-mini",  # Raisonnement sur données structurées
    "redaction_rapport":   "gpt-4o",       # Prose professionnelle (rapport final)
    "assistant_qa":        "gpt-4o-mini",  # Q&A rapide sur artefacts
}

_FALLBACK_MODEL = "gpt-4o-mini"


def get_llm_model(task: str) -> str:
    """Retourne le modèle OpenAI pour une tâche donnée.

    Priorité :
    1. OPENAI_MODEL_<TASK_UPPER>  (ex. OPENAI_MODEL_REDACTION_RAPPORT=gpt-4o-128k)
    2. OPENAI_MODEL               (override global, ex. en test)
    3. LLM_ROUTING[task]          (routing par défaut)
    4. _FALLBACK_MODEL            (gpt-4o-mini)
    """
    # Task-specific override
    env_key = f"OPENAI_MODEL_{task.upper()}"
    task_override = os.environ.get(env_key, "").strip()
    if task_override:
        return task_override

    # Global override (rétrocompatibilité)
    global_override = os.environ.get("OPENAI_MODEL", "").strip()
    if global_override:
        return global_override

    return LLM_ROUTING.get(task, _FALLBACK_MODEL)


# ── Estimation du coût ────────────────────────────────────────────────────────
# Tarifs OpenAI (mai 2026) — en USD pour 1 000 tokens (approximatif)
_COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o":           {"input": 0.005,   "output": 0.015},
    "gpt-4o-mini":      {"input": 0.000150, "output": 0.000600},
    "gpt-4o-128k":      {"input": 0.005,   "output": 0.015},
    "gpt-4-turbo":      {"input": 0.010,   "output": 0.030},
    "gpt-3.5-turbo":    {"input": 0.0005,  "output": 0.0015},
}

_FALLBACK_COST = {"input": 0.005, "output": 0.015}  # gpt-4o si modèle inconnu


def estimate_llm_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estime le coût en USD pour un appel LLM (input + output tokens)."""
    rates = _COST_PER_1K_TOKENS.get(model, _FALLBACK_COST)
    cost = (tokens_in / 1000) * rates["input"] + (tokens_out / 1000) * rates["output"]
    return round(cost, 6)
