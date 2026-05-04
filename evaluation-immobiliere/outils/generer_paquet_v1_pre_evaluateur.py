#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
SUMMARY_DEFAULT = PROJECT_ROOT / "tests" / "runtime" / "runtime_summary.json"
OUT_DIR_DEFAULT = PROJECT_ROOT / "atelier" / "PAQUET-V1-PRE-EVALUATEUR"
PREFERRED_STATUS = "PRET_REVISION_FINALE"
PACKAGE_STATUS = "PRET_REVUE_EVALUATEUR_AGREE"

PACKAGE_FILES = {
    "index": "INDEX.md",
    "manifest": "DEMO-MANIFEST-V1.json",
    "rapport": "RAPPORT-EXEMPLE-V1.md",
    "questions": "QUESTIONS-REVUE-EVALUATEUR.md",
    "grille": "GRILLE-REVUE-EVALUATEUR.csv",
    "limites": "LIMITES-V1-PRE-EVALUATEUR.md",
}

GRID_FIELDS = ["section", "question_id", "question", "reponse_attendue", "obligatoire", "notes"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def normalize_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_summary(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def select_demo_case(summary: list[dict[str, Any]], dossier_id: str = "") -> dict[str, Any]:
    if dossier_id:
        for item in summary:
            if str(item.get("dossier_id") or "") == dossier_id:
                return item
        raise ValueError(f"dossier_id absent du runtime_summary: {dossier_id}")

    for item in summary:
        if item.get("status") == PREFERRED_STATUS:
            return item
    if summary:
        return summary[0]
    raise ValueError("runtime_summary vide")


def artifact_dir(case: dict[str, Any]) -> Path:
    raw = str(case.get("artifact_dir") or "").strip()
    if not raw:
        raise ValueError("artifact_dir absent du cas demo")
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def artifact_inventory(directory: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        items.append(
            {
                "name": path.name,
                "path": normalize_path(path),
                "kind": path.suffix.removeprefix(".") or "text",
            }
        )
    return items


def collect_context(case: dict[str, Any]) -> dict[str, Any]:
    directory = artifact_dir(case)
    status = read_json_dict(directory / "compliance-qa.statut_sortie.json")
    fiche = read_json_dict(directory / "data-facts.fiche_bien.json")
    comparables = read_json_dict(directory / "comps-market.comparables_proposes.json")
    justifications = read_json_dict(directory / "comps-market.justifications_comparables.json")
    valuation_docs = {
        "approche_comparative": read_json_dict(directory / "valuation-draft.calculs_approche_comparative.json"),
        "approche_cout": read_json_dict(directory / "valuation-draft.calculs_approche_cout.json"),
        "approche_revenu": read_json_dict(directory / "valuation-draft.calculs_approche_revenu.json"),
    }
    return {
        "case": case,
        "artifact_dir": directory,
        "inventory": artifact_inventory(directory),
        "status": status,
        "fiche": fiche,
        "comparables": comparables,
        "justifications": justifications,
        "valuation_docs": valuation_docs,
        "valuation_markdown": read_text(directory / "valuation-draft.brouillon_valeur.md"),
        "report_markdown": read_text(directory / "redaction.brouillon_rapport.md"),
        "annex_markdown": read_text(directory / "redaction.annexe_sources.md"),
        "recommendations_markdown": read_text(directory / "compliance-qa.recommandations_corrections.md"),
    }


def build_manifest(context: dict[str, Any]) -> dict[str, Any]:
    case = as_dict(context.get("case"))
    status = as_dict(context.get("status"))
    comparables = as_dict(context.get("comparables"))
    inventory = as_list(context.get("inventory"))
    return {
        "schema_version": "paquet_v1_pre_evaluateur_manifest_v1",
        "status": PACKAGE_STATUS,
        "target": "V1_PRE_EVALUATEUR",
        "field_validation": "NON_REVENDIQUEE",
        "dossier_id": case.get("dossier_id", ""),
        "runtime_status": case.get("status", "UNKNOWN"),
        "source_fixture": first_source_fixture(context),
        "artifact_dir": normalize_path(Path(str(context.get("artifact_dir")))),
        "artifacts_count": len(inventory),
        "comparables_count": len(as_list(comparables.get("comparables"))),
        "blocking_failures": case.get("blocking_failures", []),
        "warnings": case.get("warnings", []),
        "valuation_values": status.get("valuation_values", {}),
        "ui_routes": ["/review/ui", "/ui", "/ops/cockpit"],
        "api_routes": ["/fixtures", "/start", "/status", "/artifacts", "/review", "/resume"],
        "package_files": {key: str(value) for key, value in PACKAGE_FILES.items()},
    }


def first_source_fixture(context: dict[str, Any]) -> str:
    for payload_name in ("fiche", "comparables", "status"):
        payload = as_dict(context.get(payload_name))
        fixture = str(payload.get("source_fixture") or "").strip()
        if fixture:
            return fixture
    return ""


def format_money(value: Any) -> str:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{float(value):,.0f}".replace(",", " ")
    return "-"


def build_index_markdown(context: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# Paquet V1 pre-evaluateur agree",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Synthese",
        "",
        f"- Statut paquet: **{manifest['status']}**",
        f"- Cible: **{manifest['target']}**",
        f"- Validation terrain reelle: **{manifest['field_validation']}**",
        f"- Dossier demo: **{manifest.get('dossier_id', '-')}**",
        f"- Statut runtime: **{manifest.get('runtime_status', 'UNKNOWN')}**",
        f"- Fixture source: `{manifest.get('source_fixture', '-')}`",
        f"- Artefacts: **{manifest.get('artifacts_count', 0)}**",
        "",
        "## Fichiers du paquet",
        "",
        "| Fichier | Role |",
        "|---|---|",
        "| `RAPPORT-EXEMPLE-V1.md` | Rapport de demonstration a lire avant la revue. |",
        "| `QUESTIONS-REVUE-EVALUATEUR.md` | Questions ouvertes a faire trancher par l'evaluateur. |",
        "| `GRILLE-REVUE-EVALUATEUR.csv` | Grille vide de collecte, sans reponse inventee. |",
        "| `LIMITES-V1-PRE-EVALUATEUR.md` | Limites et hypotheses a presenter explicitement. |",
        "| `DEMO-MANIFEST-V1.json` | Manifest machine-readable du paquet. |",
        "",
        "## Parcours demo",
        "",
        "1. Demarrer l'API locale avec `python evaluation-immobiliere/outils/lancer_api_v0.py`.",
        "2. Ouvrir `/review/ui` pour la revue evaluateur.",
        "3. Ouvrir le dossier demo et inspecter les artefacts.",
        "4. Lire le rapport exemple et remplir la grille avec l'evaluateur.",
        "",
        "## Regle de portee",
        "",
        "Ce paquet sert a presenter une V1 pre-evaluateur. Il ne remplace pas une validation terrain reelle.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_report_markdown(context: dict[str, Any], manifest: dict[str, Any]) -> str:
    status = as_dict(context.get("status"))
    fiche = as_dict(context.get("fiche"))
    comparables_payload = as_dict(context.get("comparables"))
    comparables = [item for item in as_list(comparables_payload.get("comparables")) if isinstance(item, dict)]
    valuation_values = as_dict(status.get("valuation_values"))
    inventory = as_list(context.get("inventory"))
    lines = [
        "# Rapport exemple V1 pre-evaluateur",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Avertissement",
        "",
        "Rapport genere depuis une fixture de demonstration non sensible. Aucune validation terrain reelle ni reponse d'evaluateur n'est revendiquee.",
        "",
        "## Synthese dossier",
        "",
        f"- Dossier: **{manifest.get('dossier_id', '-')}**",
        f"- Date de reference: **{fiche.get('date_reference', '-')}**",
        f"- Statut runtime: **{manifest.get('runtime_status', 'UNKNOWN')}**",
        f"- Confiance fixture: **{fiche.get('confidence', '-')}**",
        f"- Sources referencees: **{len(as_list(fiche.get('source_ids')))}**",
        f"- Comparables proposes: **{len(comparables)}**",
        "",
        "## Valeurs indicatives",
        "",
        "| Approche | Valeur |",
        "|---|---:|",
    ]
    for approach in ("approche_comparative", "approche_cout", "approche_revenu"):
        lines.append(f"| {approach} | {format_money(valuation_values.get(approach))} |")

    lines.extend(["", "## Comparables proposes", "", "| ID | Prix vente | Score | Source |", "|---|---:|---:|---|"])
    if comparables:
        for comparable in comparables:
            lines.append(
                "| {id} | {price} | {score} | {source} |".format(
                    id=comparable.get("comparable_id", "-"),
                    price=format_money(comparable.get("prix_vente")),
                    score=comparable.get("score", "-"),
                    source=comparable.get("source_id", "-"),
                )
            )
    else:
        lines.append("| - | - | - | - |")

    lines.extend(["", "## Blocages et warnings", ""])
    lines.append(f"- Blocages: {format_items(as_list(manifest.get('blocking_failures')))}")
    lines.append(f"- Warnings: {format_items(as_list(manifest.get('warnings')))}")

    lines.extend(["", "## Artefacts disponibles", "", "| Artefact | Chemin |", "|---|---|"])
    for item in inventory:
        if isinstance(item, dict):
            lines.append(f"| {item.get('name', '-')} | `{item.get('path', '-')}` |")

    lines.extend(
        [
            "",
            "## Lecture attendue par l'evaluateur",
            "",
            "- Le statut final est-il comprehensible et justifie?",
            "- Les artefacts permettent-ils une revue professionnelle?",
            "- Les comparables et reserves sont-ils presentes au bon niveau de detail?",
            "- Les corrections humaines attendues sont-elles explicites?",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def review_questions() -> list[dict[str, str]]:
    return [
        {
            "section": "statut",
            "question_id": "Q-STATUT-001",
            "question": "Le statut runtime propose correspond-il a la lecture metier du dossier?",
            "reponse_attendue": "A REMPLIR PAR L'EVALUATEUR",
            "obligatoire": "oui",
            "notes": "",
        },
        {
            "section": "comparables",
            "question_id": "Q-COMP-001",
            "question": "Les comparables proposes sont-ils acceptables pour une premiere revue?",
            "reponse_attendue": "A REMPLIR PAR L'EVALUATEUR",
            "obligatoire": "oui",
            "notes": "",
        },
        {
            "section": "valeur",
            "question_id": "Q-VAL-001",
            "question": "Les approches de valeur et leurs traces sont-elles assez explicites?",
            "reponse_attendue": "A REMPLIR PAR L'EVALUATEUR",
            "obligatoire": "oui",
            "notes": "",
        },
        {
            "section": "rapport",
            "question_id": "Q-RAP-001",
            "question": "Le rapport exemple contient-il les sections attendues pour une revue professionnelle?",
            "reponse_attendue": "A REMPLIR PAR L'EVALUATEUR",
            "obligatoire": "oui",
            "notes": "",
        },
        {
            "section": "risques",
            "question_id": "Q-RISK-001",
            "question": "Quelles reserves doivent rester bloquantes avant usage sur dossier client?",
            "reponse_attendue": "A REMPLIR PAR L'EVALUATEUR",
            "obligatoire": "oui",
            "notes": "",
        },
    ]


def build_questions_markdown() -> str:
    lines = [
        "# Questions revue evaluateur",
        "",
        "Ces questions doivent etre completees avec l'evaluateur agree. Aucune reponse n'est pre-remplie.",
        "",
        "| ID | Section | Question |",
        "|---|---|---|",
    ]
    for row in review_questions():
        lines.append(f"| {row['question_id']} | {row['section']} | {row['question']} |")
    return "\n".join(lines).rstrip() + "\n"


def build_limits_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Limites V1 pre-evaluateur",
        "",
        "## Ce que la V1 prouve",
        "",
        "- Le runtime produit des artefacts structures et auditables sur un cas de demonstration.",
        "- L'API/UI permettent d'inspecter session, statut, artefacts et revue humaine.",
        "- Les gates CI prouvent que la chaine est reproductible.",
        "",
        "## Ce que la V1 ne revendique pas",
        "",
        "- Aucune validation terrain reelle.",
        "- Aucune approbation par evaluateur immobilier agree.",
        "- Aucun usage de dossier client sensible.",
        "- Aucun go production metier.",
        "",
        "## Prochaine revue",
        "",
        f"- Dossier demo: **{manifest.get('dossier_id', '-')}**",
        "- Faire remplir la grille par l'evaluateur.",
        "- Convertir les retours en backlog V2 avant toute validation terrain.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def format_items(items: list[Any]) -> str:
    values = [str(item) for item in items if str(item)]
    return "; ".join(values) if values else "-"


def write_grid(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GRID_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(review_questions())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_package(
    *,
    summary_path: Path = SUMMARY_DEFAULT,
    out_dir: Path = OUT_DIR_DEFAULT,
    dossier_id: str = "",
) -> dict[str, Any]:
    summary = load_summary(summary_path)
    case = select_demo_case(summary, dossier_id=dossier_id)
    context = collect_context(case)
    manifest = build_manifest(context)

    write_json(out_dir / PACKAGE_FILES["manifest"], manifest)
    write_text(out_dir / PACKAGE_FILES["index"], build_index_markdown(context, manifest))
    write_text(out_dir / PACKAGE_FILES["rapport"], build_report_markdown(context, manifest))
    write_text(out_dir / PACKAGE_FILES["questions"], build_questions_markdown())
    write_text(out_dir / PACKAGE_FILES["limites"], build_limits_markdown(manifest))
    write_grid(out_dir / PACKAGE_FILES["grille"])

    return {
        "status": PACKAGE_STATUS,
        "target": "V1_PRE_EVALUATEUR",
        "dossier_id": manifest["dossier_id"],
        "out_dir": normalize_path(out_dir),
        "files": {key: normalize_path(out_dir / filename) for key, filename in PACKAGE_FILES.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere le paquet V1 pre-evaluateur a partir d'un cas runtime.")
    parser.add_argument("--summary", type=Path, default=SUMMARY_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    parser.add_argument("--dossier-id", default="")
    args = parser.parse_args()

    outputs = generate_package(summary_path=args.summary, out_dir=args.out_dir, dossier_id=args.dossier_id)
    print(f"Paquet V1 pre-evaluateur: {outputs['out_dir']}")
    print(f"Statut: {outputs['status']}")
    print(f"Dossier demo: {outputs['dossier_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
