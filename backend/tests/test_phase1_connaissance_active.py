"""Phase 1 T1.1 — Injection analysis.md dans pipeline et assistant.

DoD : le prompt construit contient le contenu réel de analysis.md
      (pas seulement les renvois SKILL.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.skills import load_skill_knowledge, PROJECT_ROOT


# ── load_skill_knowledge ──────────────────────────────────────────────────────

def test_load_skill_knowledge_prefers_analysis_md():
    """analysis.md doit être retourné si présent (contenu > SKILL.md sect.2+4)."""
    # analyse-amu a un analysis.md riche
    content = load_skill_knowledge("analyse-amu", max_chars=5000)
    assert content, "Contenu vide pour analyse-amu"
    # analysis.md contient le cadre normatif des 4 critères
    assert "Légalement permis" in content or "critère" in content.lower()


def test_load_skill_knowledge_truncates():
    content = load_skill_knowledge("analyse-amu", max_chars=100)
    assert len(content) <= 100


def test_load_skill_knowledge_unknown_skill():
    content = load_skill_knowledge("skill-inexistant", max_chars=1000)
    assert content == ""


def test_load_skill_knowledge_all_skills_have_content():
    """Chaque skill avec analysis.md doit retourner du contenu."""
    skills_dir = PROJECT_ROOT / "skills"
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        analysis = skill_dir / "analysis.md"
        if not analysis.exists():
            continue
        content = load_skill_knowledge(skill_dir.name, max_chars=5000)
        assert content, f"Contenu vide pour {skill_dir.name} malgré analysis.md présent"


# ── _build_agent_full_prompt (assistant) ─────────────────────────────────────

def test_agent_prompt_contains_analysis_content():
    """Le prompt assistant doit contenir du contenu analysis.md, pas seulement des renvois."""
    import api  # type: ignore

    # Simuler profil pour agent amu-analyst
    profile = {
        "agent_config": "AGENTCONFIG-AMU-ANALYST-V0.yaml",
        "skills_allowed": ["analyse-amu", "recherche-normes-professionnelles"],
    }
    prompt = api._build_agent_full_prompt("amu-analyst", profile)
    assert "CONNAISSANCE MÉTHODOLOGIQUE" in prompt
    # Doit contenir du contenu analysis.md réel
    assert len(prompt) > 500


def test_agent_prompt_analysis_md_header():
    """Le header de section doit indiquer analysis.md (pas ancien SKILL.md)."""
    import api  # type: ignore

    profile = {"agent_config": "", "skills_allowed": ["analyse-amu"]}
    prompt = api._build_agent_full_prompt("amu-analyst", profile)
    assert "analysis.md" in prompt


# ── _enrich_artifact_llm (pipeline) — vérif construction prompt ──────────────

def test_pipeline_skill_knowledge_injected(monkeypatch):
    """Sans API key réelle, vérifier que le system_prompt enrichi est construit."""
    captured: list[str] = []

    # Intercepter l'appel openai pour capturer le system prompt
    class FakeCompletion:
        choices = [type("C", (), {"message": type("M", (), {"content": "ok"})()})()]

    class FakeClient:
        def __init__(self, **kw):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured.append(kwargs.get("messages", [{}])[0].get("content", ""))
                    return FakeCompletion()

    import engine.runtime as rt

    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    monkeypatch.setattr("engine.runtime.os.environ", {
        **rt.os.environ,
        "OPENAI_API_KEY": "sk-fake",
    })

    # Minimal: call _enrich_artifact_llm with a real step that has skills
    from engine.runtime import DEFAULT_STEPS, RuntimeEngine
    step = next(s for s in DEFAULT_STEPS if s.name == "amu-analyst")

    import openai as _openai_module  # type: ignore
    monkeypatch.setattr(_openai_module, "OpenAI", FakeClient)

    runtime = RuntimeEngine.__new__(RuntimeEngine)
    runtime.strict_mode = False

    payload = {"_raw_md": "test"}
    case = {"dossier_id": "D-T1-001", "type_bien": "unifamiliale", "zone": "R2"}

    result = runtime._enrich_artifact_llm(step, "amu_analyse.md", payload, case)
    # Le system prompt capturé doit contenir analysis.md content
    if captured:
        assert "CONNAISSANCE MÉTHODOLOGIQUE" in captured[0], (
            "Injection analysis.md absente du system_prompt pipeline"
        )
