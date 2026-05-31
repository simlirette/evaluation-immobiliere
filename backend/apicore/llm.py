"""apicore/llm.py — Fonctions LLM pour l'assistant (T6.1 C2).

Extrait de api.py. Dépendances :
  - apicore.llm_config (_OPENAI_MODEL_DEFAULT, _AGENT_SYSTEM_PROMPTS, etc.)
  - engine.skills (DEFAULT_SKILLS_BY_AGENT, load_skill_knowledge, load_agent_system_prompt)
  - openai (optionnel — import lazy)
  - os.environ (OPENAI_API_KEY, OPENAI_MODEL)

PAS de dépendance sur SESSIONS_DIR ni session I/O → zéro cycle.
"""
from __future__ import annotations

import os
from pathlib import Path

from apicore.llm_config import (
    _OPENAI_MODEL_DEFAULT,
    _AGENT_SYSTEM_LIMITS,
    _AGENT_SYSTEM_PROMPTS,
)


ROOT = Path(__file__).resolve().parent.parent


def llm_client():
    """Retourne un client OpenAI si OPENAI_API_KEY est défini, sinon None."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    try:
        import openai  # type: ignore
        return openai.OpenAI(api_key=api_key)
    except ImportError:
        return None


def extract_skill_knowledge(skill_name: str, max_chars: int = 2000) -> str:
    """Charge la connaissance d'un skill (analysis.md prioritaire sur SKILL.md 2+4)."""
    from engine.skills import load_skill_knowledge  # type: ignore
    return load_skill_knowledge(skill_name, max_chars=max_chars)


def build_agent_full_prompt(agent: str, profile: dict) -> str:
    """Construit le system prompt complet pour un agent assistant.

    1. Charge system_prompt depuis AGENTCONFIG YAML
    2. Appende connaissances des SKILL.md autorisés (analysis.md)
    """
    from engine.skills import load_agent_system_prompt, DEFAULT_SKILLS_BY_AGENT  # type: ignore

    agent_config_file = profile.get("agent_config", "")
    base_prompt = ""

    if agent_config_file and not agent_config_file.startswith("SUPERVISOR"):
        config_path = ROOT / "integration" / agent_config_file
        base_prompt = load_agent_system_prompt(config_path)

    if not base_prompt:
        base_prompt = _AGENT_SYSTEM_PROMPTS.get(agent, (
            "Tu es un assistant IA expert en évaluation immobilière québécoise.\n"
            "Répondre avec précision à partir des données fournies uniquement."
        ))

    skill_names = DEFAULT_SKILLS_BY_AGENT.get(agent, [])
    if not skill_names:
        return base_prompt

    skill_blocks: list[str] = []
    budget = 5000
    used = 0
    for skill_name in skill_names:
        if used >= budget:
            break
        remaining = budget - used
        block = extract_skill_knowledge(skill_name, max_chars=min(2000, remaining))
        if block:
            skill_blocks.append(f"### {skill_name}\n{block}")
            used += len(block)

    if not skill_blocks:
        return base_prompt

    skills_section = (
        "\n\n---\nCONNAISSANCE MÉTHODOLOGIQUE (analysis.md) :\n"
        + "\n\n".join(skill_blocks)
    )
    return base_prompt + skills_section + _AGENT_SYSTEM_LIMITS
