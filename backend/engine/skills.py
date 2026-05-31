from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ProjectSkill:
    name: str
    path: str
    description: str
    type: str
    agents: list[str]
    sources: list[str]
    has_analysis: bool


DEFAULT_SKILLS_BY_AGENT: dict[str, list[str]] = {
    "mandat-intake": [
        "redaction-lettre-mandat",
        "recherche-cadre-legal",
        "recherche-normes-professionnelles",
    ],
    "data-facts": [
        "analyse-extraction-faits",
        "recherche-baux-revenus",
        "recherche-cadre-legal",
        "recherche-domaines-specialises",
        "recherche-marche-donnees",
        "recherche-mefq-methodologie",
        "recherche-normes-professionnelles",
        "recherche-registre-cadastre",
        "recherche-urbanisme-construction",
        "redaction-fiches-techniques",
    ],
    "amu-analyst": [
        "analyse-amu",
        "recherche-normes-professionnelles",
        "recherche-urbanisme-construction",
    ],
    "comps-market": [
        "analyse-selection-comparables",
        "recherche-marche-donnees",
        "recherche-mefq-methodologie",
        "recherche-normes-professionnelles",
        "recherche-registre-cadastre",
    ],
    "valuation-draft": [
        "analyse-approche-comparaison",
        "analyse-approche-cout",
        "analyse-approche-fta",
        "analyse-approche-revenu",
        "analyse-reconciliation-valeur",
        "recherche-baux-revenus",
        "recherche-domaines-specialises",
        "recherche-mefq-methodologie",
        "recherche-normes-professionnelles",
    ],
    "compliance-qa": [
        "analyse-conformite",
        "recherche-cadre-legal",
        "recherche-domaines-specialises",
        "recherche-jurisprudence-discipline",
        "recherche-mefq-methodologie",
        "recherche-normes-professionnelles",
        "redaction-rapport-conformite",
    ],
    "redaction": [
        "recherche-normes-professionnelles",
        "redaction-analyse-marche",
        "redaction-rapport-evaluation",
    ],
}


def parse_frontmatter(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)

    meta: dict[str, object] = {}
    current_key: str | None = None
    block_key: str | None = None
    block_lines: list[str] = []

    def flush_block() -> None:
        nonlocal block_key, block_lines
        if block_key:
            meta[block_key] = " ".join(part.strip() for part in block_lines if part.strip()).strip()
        block_key = None
        block_lines = []

    for raw in body:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            if block_key:
                block_lines.append("")
            continue

        if not line.startswith(" ") and ":" in line:
            flush_block()
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value in {">", "|"}:
                block_key = key
                block_lines = []
            elif value == "[]":
                meta[key] = []
            elif value:
                meta[key] = _strip_quotes(value)
            else:
                meta[key] = []
            continue

        if stripped.startswith("-") and current_key and block_key is None:
            value = _strip_quotes(stripped[1:].strip())
            existing = meta.get(current_key)
            if not isinstance(existing, list):
                existing = []
                meta[current_key] = existing
            existing.append(value)
            continue

        if block_key:
            block_lines.append(stripped)

    flush_block()
    return meta


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def discover_project_skills(skills_dir: Path | None = None) -> list[ProjectSkill]:
    root = skills_dir or PROJECT_ROOT / "skills"
    skills: list[ProjectSkill] = []
    for skill_md in sorted(root.glob("*/SKILL.md")):
        meta = parse_frontmatter(skill_md)
        name = str(meta.get("name") or skill_md.parent.name)
        agents = _as_list(meta.get("agents"))
        sources = _as_list(meta.get("sources"))
        skills.append(
            ProjectSkill(
                name=name,
                path=skill_md.relative_to(PROJECT_ROOT).as_posix(),
                description=str(meta.get("description") or ""),
                type=str(meta.get("type") or "non-classe"),
                agents=agents,
                sources=sources,
                has_analysis=(skill_md.parent / "analysis.md").exists(),
            )
        )
    return skills


def build_skill_registry(skills_dir: Path | None = None) -> dict:
    skills = discover_project_skills(skills_dir)
    by_agent: dict[str, list[str]] = {agent: [] for agent in DEFAULT_SKILLS_BY_AGENT}
    for skill in skills:
        for agent in skill.agents:
            by_agent.setdefault(agent, []).append(skill.name)
    for agent, defaults in DEFAULT_SKILLS_BY_AGENT.items():
        merged = [*by_agent.get(agent, []), *defaults]
        by_agent[agent] = sorted(dict.fromkeys(merged))
    return {
        "version": "1.0",
        "purpose": "Registre Aston-like des skills agents du projet evaluation-immobiliere.",
        "skills_root": "skills",
        "skills": [skill.__dict__ for skill in skills],
        "skills_by_agent": by_agent,
    }


def load_agent_config_skills(config_path: Path) -> list[str]:
    if not config_path.exists():
        return []
    lines = config_path.read_text(encoding="utf-8").splitlines()
    skills: list[str] = []
    mode = False
    for raw in lines:
        stripped = raw.strip()
        if stripped == "skills_allowed:":
            mode = True
            continue
        if mode:
            if stripped.startswith("-"):
                skills.append(stripped[1:].strip())
                continue
            if stripped and not raw.startswith(" "):
                break
    return skills


def load_agent_system_prompt(config_path: Path) -> str:
    """Extrait le system_prompt d'un fichier AGENTCONFIG YAML (bloc | ou >)."""
    if not config_path.exists():
        return ""
    lines = config_path.read_text(encoding="utf-8").splitlines()
    prompt_lines: list[str] = []
    mode = False
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("system_prompt:"):
            mode = True
            continue
        if mode:
            if raw.startswith(" ") or raw.startswith("\t"):
                prompt_lines.append(stripped)
            elif stripped:
                break
    return "\n".join(prompt_lines).strip()


def load_skill_registry(registry_path: Path | None = None) -> dict:
    path = registry_path or PROJECT_ROOT / "skills" / "SKILLS-REGISTRY.json"
    if not path.exists():
        return build_skill_registry(PROJECT_ROOT / "skills")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if isinstance(value, str) and value:
        return [value]
    return []


def load_skill_knowledge(skill_name: str, max_chars: int = 2000) -> str:
    """Charge le contenu de connaissance d'un skill.

    Priorité : analysis.md complet > sections 2+4 du SKILL.md.
    Retourne texte tronqué à max_chars. Silencieux si fichier absent.
    """
    skill_dir = PROJECT_ROOT / "skills" / skill_name

    analysis_path = skill_dir / "analysis.md"
    if analysis_path.exists():
        try:
            content = analysis_path.read_text(encoding="utf-8").strip()
            return content[:max_chars] if len(content) > max_chars else content
        except OSError:
            pass

    skill_path = skill_dir / "SKILL.md"
    if not skill_path.exists():
        return ""
    try:
        text = skill_path.read_text(encoding="utf-8")
    except OSError:
        return ""

    sections: list[str] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## 2.") or line.startswith("## 4."):
            current = [line]
        elif line.startswith("## ") and current is not None:
            sections.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    if current:
        sections.append("\n".join(current))

    combined = "\n\n".join(sections).strip()
    return combined[:max_chars] if len(combined) > max_chars else combined
