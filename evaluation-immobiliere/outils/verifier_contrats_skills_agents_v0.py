from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engine.skills import build_skill_registry, load_agent_config_skills, parse_frontmatter

CONTRACT_DEFAULT = PROJECT_ROOT / "skills" / "AGENT-SKILLS-CONTRACTS.json"
SKILLS_DIR_DEFAULT = PROJECT_ROOT / "skills"
INTEGRATION_DIR_DEFAULT = PROJECT_ROOT / "integration"
EXPECTED_SCHEMA = "agent_skills_contracts_v0"


@dataclass(frozen=True)
class SkillDocument:
    name: str
    skill_type: str
    agents: list[str]
    skill_path: Path
    skill_text: str
    analysis_text: str


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def discover_skill_documents(skills_dir: Path = SKILLS_DIR_DEFAULT) -> dict[str, SkillDocument]:
    documents: dict[str, SkillDocument] = {}
    for skill_path in sorted(skills_dir.glob("*/SKILL.md")):
        meta = parse_frontmatter(skill_path)
        name = str(meta.get("name") or skill_path.parent.name)
        analysis_path = skill_path.parent / "analysis.md"
        documents[name] = SkillDocument(
            name=name,
            skill_type=str(meta.get("type") or ""),
            agents=as_str_list(meta.get("agents")),
            skill_path=skill_path,
            skill_text=skill_path.read_text(encoding="utf-8"),
            analysis_text=analysis_path.read_text(encoding="utf-8") if analysis_path.exists() else "",
        )
    return documents


def validate_agent_skill_contracts(
    project_root: Path = PROJECT_ROOT,
    *,
    contract_path: Path | None = None,
    skills_dir: Path | None = None,
    integration_dir: Path | None = None,
) -> dict[str, object]:
    contract_path = contract_path or project_root / "skills" / "AGENT-SKILLS-CONTRACTS.json"
    skills_dir = skills_dir or project_root / "skills"
    integration_dir = integration_dir or project_root / "integration"

    errors: list[str] = []
    warnings: list[str] = []
    contract = load_json(contract_path)
    if not contract:
        errors.append(f"{contract_path.as_posix()}: contrat introuvable ou invalide")
        return build_report(contract_path, 0, 0, 0, errors, warnings)
    if contract.get("schema_version") != EXPECTED_SCHEMA:
        errors.append(f"{contract_path.as_posix()}: schema_version attendu {EXPECTED_SCHEMA}")

    registry = build_skill_registry(skills_dir)
    skills_by_agent = registry.get("skills_by_agent", {}) if isinstance(registry.get("skills_by_agent"), dict) else {}
    documents = discover_skill_documents(skills_dir)
    forbidden_terms = [str(term) for term in as_list(nested(contract, "policy", "forbidden_in_skill_md"))]

    agents_checked = 0
    skills_checked: set[str] = set()
    anchors_checked = 0

    for agent_contract in list_dicts(contract.get("agents")):
        agents_checked += 1
        agent_type = str(agent_contract.get("agent_type") or "")
        config_name = str(agent_contract.get("agent_config") or "")
        if not agent_type:
            errors.append("Contrat agent sans agent_type")
            continue
        if agent_type not in skills_by_agent:
            errors.append(f"{agent_type}: agent absent du registre skills")
        config_path = integration_dir / config_name
        config_skills = load_agent_config_skills(config_path)
        if not config_name or not config_path.exists():
            errors.append(f"{agent_type}: AgentConfig introuvable {config_name}")
        if not config_skills:
            errors.append(f"{agent_type}: skills_allowed vide ou manquant")

        for skill_contract in list_dicts(agent_contract.get("required_skills")):
            skill_name = str(skill_contract.get("name") or "")
            document = documents.get(skill_name)
            if document is None:
                errors.append(f"{agent_type}: skill introuvable {skill_name}")
                continue
            skills_checked.add(skill_name)
            if skill_name not in config_skills:
                errors.append(f"{agent_type}: skill contractuel non autorise dans AgentConfig {skill_name}")
            if agent_type not in document.agents:
                errors.append(f"{agent_type}: skill {skill_name} ne declare pas cet agent dans son frontmatter")
            skill_normalized = normalize_text(document.skill_text)
            for term in forbidden_terms:
                if contains_term(skill_normalized, term):
                    errors.append(f"{agent_type}/{skill_name}: terme interdit dans SKILL.md: {term}")

            for anchor in list_dicts(skill_contract.get("required_anchors")):
                anchors_checked += 1
                anchor_id = str(anchor.get("id") or "anchor")
                scope = str(anchor.get("scope") or "skill")
                text = text_for_scope(document, scope)
                normalized = normalize_text(text)
                missing_terms = [str(term) for term in as_list(anchor.get("terms")) if not contains_term(normalized, str(term))]
                if missing_terms:
                    errors.append(f"{agent_type}/{skill_name}: ancre {anchor_id} incomplete, termes manquants {missing_terms}")

    return build_report(contract_path, agents_checked, len(skills_checked), anchors_checked, errors, warnings)


def text_for_scope(document: SkillDocument, scope: str) -> str:
    if scope == "analysis":
        return document.analysis_text
    if scope == "skill_and_analysis":
        return f"{document.skill_text}\n{document.analysis_text}"
    return document.skill_text


def contains_term(normalized_text: str, term: str) -> bool:
    return normalize_text(term) in normalized_text


def list_dicts(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def as_str_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def nested(payload: object, *keys: str) -> object:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def build_report(
    contract_path: Path,
    agents_checked: int,
    skills_checked: int,
    anchors_checked: int,
    errors: list[str],
    warnings: list[str],
) -> dict[str, object]:
    return {
        "schema_version": "agent_skills_contracts_report_v0",
        "ok": not errors,
        "contract_path": contract_path.as_posix(),
        "agents_checked": agents_checked,
        "skills_checked": skills_checked,
        "anchors_checked": anchors_checked,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie les contrats metier des skills critiques par agent.")
    parser.add_argument("--contract", type=Path, default=CONTRACT_DEFAULT)
    parser.add_argument("--skills-dir", type=Path, default=SKILLS_DIR_DEFAULT)
    parser.add_argument("--integration-dir", type=Path, default=INTEGRATION_DIR_DEFAULT)
    parser.add_argument("--report-out", default="", help="Chemin optionnel du rapport JSON")
    args = parser.parse_args()

    report = validate_agent_skill_contracts(
        PROJECT_ROOT,
        contract_path=args.contract,
        skills_dir=args.skills_dir,
        integration_dir=args.integration_dir,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
