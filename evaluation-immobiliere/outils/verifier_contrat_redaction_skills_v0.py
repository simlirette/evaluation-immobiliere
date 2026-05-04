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

from engine.skills import parse_frontmatter

CONTRACT_DEFAULT = PROJECT_ROOT / "skills" / "REDACTION-SKILLS-CONTRACT.json"
SKILLS_DIR_DEFAULT = PROJECT_ROOT / "skills"
EXPECTED_SCHEMA = "redaction_skills_contract_v0"


@dataclass(frozen=True)
class SkillDocument:
    name: str
    skill_type: str
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
            skill_path=skill_path,
            skill_text=skill_path.read_text(encoding="utf-8"),
            analysis_text=analysis_path.read_text(encoding="utf-8") if analysis_path.exists() else "",
        )
    return documents


def validate_redaction_skill_contract(
    project_root: Path = PROJECT_ROOT,
    *,
    contract_path: Path | None = None,
    skills_dir: Path | None = None,
) -> dict[str, object]:
    contract_path = contract_path or project_root / "skills" / "REDACTION-SKILLS-CONTRACT.json"
    skills_dir = skills_dir or project_root / "skills"

    errors: list[str] = []
    warnings: list[str] = []
    contract = load_json(contract_path)
    if not contract:
        errors.append(f"{contract_path.as_posix()}: contrat introuvable ou invalide")
        return build_report(contract_path, 0, 0, errors, warnings)
    if contract.get("schema_version") != EXPECTED_SCHEMA:
        errors.append(f"{contract_path.as_posix()}: schema_version attendu {EXPECTED_SCHEMA}")

    documents = discover_skill_documents(skills_dir)
    redaction_skill_names = {name for name, doc in documents.items() if doc.skill_type == "redaction"}
    required_skills = list_dicts(contract.get("required_skills"))
    contract_skill_names = {str(item.get("name") or "") for item in required_skills}

    missing_contracts = sorted(redaction_skill_names - contract_skill_names)
    if missing_contracts:
        errors.append(f"Contrat incomplet: skills de redaction sans ancres {missing_contracts}")

    unknown_contracts = sorted(contract_skill_names - set(documents))
    if unknown_contracts:
        errors.append(f"Contrat reference des skills introuvables {unknown_contracts}")

    non_redaction_contracts = sorted(
        name for name in contract_skill_names & set(documents) if documents[name].skill_type != "redaction"
    )
    if non_redaction_contracts:
        errors.append(f"Contrat reference des skills non-redaction {non_redaction_contracts}")

    anchors_checked = 0
    forbidden_terms = [str(term) for term in as_list(nested(contract, "policy", "forbidden_in_skill_md"))]
    for skill_contract in required_skills:
        skill_name = str(skill_contract.get("name") or "")
        document = documents.get(skill_name)
        if document is None:
            continue
        skill_normalized = normalize_text(document.skill_text)
        for term in forbidden_terms:
            if contains_term(skill_normalized, term):
                errors.append(f"{skill_name}: terme interdit dans SKILL.md: {term}")
        for anchor in list_dicts(skill_contract.get("required_anchors")):
            anchors_checked += 1
            anchor_id = str(anchor.get("id") or "anchor")
            scope = str(anchor.get("scope") or "skill")
            text = text_for_scope(document, scope)
            normalized = normalize_text(text)
            missing_terms = [str(term) for term in as_list(anchor.get("terms")) if not contains_term(normalized, str(term))]
            if missing_terms:
                errors.append(f"{skill_name}: ancre {anchor_id} incomplete, termes manquants {missing_terms}")

    provenance = contract.get("provenance")
    if isinstance(provenance, dict):
        provenance_path = project_root / str(provenance.get("path") or "")
        if not provenance_path.exists():
            errors.append(f"{provenance_path.as_posix()}: provenance skills introuvable")
        else:
            provenance_normalized = normalize_text(provenance_path.read_text(encoding="utf-8"))
            for term in as_list(provenance.get("required_terms")):
                if not contains_term(provenance_normalized, str(term)):
                    errors.append(f"{provenance_path.as_posix()}: terme de provenance manquant {term}")

    return build_report(contract_path, len(contract_skill_names & set(documents)), anchors_checked, errors, warnings)


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


def nested(payload: object, *keys: str) -> object:
    current = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def build_report(contract_path: Path, skills_checked: int, anchors_checked: int, errors: list[str], warnings: list[str]) -> dict[str, object]:
    return {
        "schema_version": "redaction_skills_contract_report_v0",
        "ok": not errors,
        "contract_path": contract_path.as_posix(),
        "skills_checked": skills_checked,
        "anchors_checked": anchors_checked,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifie le contrat comportemental des skills de redaction.")
    parser.add_argument("--contract", type=Path, default=CONTRACT_DEFAULT)
    parser.add_argument("--skills-dir", type=Path, default=SKILLS_DIR_DEFAULT)
    parser.add_argument("--report-out", default="", help="Chemin optionnel du rapport JSON")
    args = parser.parse_args()

    report = validate_redaction_skill_contract(PROJECT_ROOT, contract_path=args.contract, skills_dir=args.skills_dir)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.report_out:
        out_path = Path(args.report_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
