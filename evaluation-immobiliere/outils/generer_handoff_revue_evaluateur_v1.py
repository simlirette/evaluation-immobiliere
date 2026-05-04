#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
ATELIER_DIR = PROJECT_ROOT / "atelier"
PACKAGE_DIR_DEFAULT = ATELIER_DIR / "PAQUET-V1-PRE-EVALUATEUR"
STATUS_REPORT_DEFAULT = ATELIER_DIR / "STATUT-PHASES-PROJET-V1.json"
OUT_DIR_DEFAULT = ATELIER_DIR

PACKAGE_MANIFEST = "DEMO-MANIFEST-V1.json"
PACKAGE_GRID = "GRILLE-REVUE-EVALUATEUR.csv"
PACKAGE_STATUS = "PRET_REVUE_EVALUATEUR_AGREE"
HANDOFF_STATUS = "PRET_SEANCE_REVUE_EVALUATEUR_AGREE"
STOP_POINT = "ARRET_AVANT_INTEGRATION_REPONSES_EVALUATEUR"

HANDOFF_FILES = {
    "manifest": "HANDOFF-REVUE-EVALUATEUR-V1.json",
    "brief": "HANDOFF-REVUE-EVALUATEUR-V1.md",
    "agenda": "ORDRE-DU-JOUR-REVUE-EVALUATEUR-V1.md",
    "checklist": "CHECKLIST-SEANCE-EVALUATEUR-V1.md",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def normalize_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_review_grid(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [
            {str(key): str(value or "") for key, value in row.items()}
            for row in csv.DictReader(handle)
            if any(str(value or "").strip() for value in row.values())
        ]


def validate_inputs(package_manifest: dict[str, Any], status_report: dict[str, Any], questions: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if package_manifest.get("schema_version") != "paquet_v1_pre_evaluateur_manifest_v1":
        errors.append("schema paquet V1 invalide")
    if package_manifest.get("status") != PACKAGE_STATUS:
        errors.append(f"statut paquet invalide: {package_manifest.get('status') or 'UNKNOWN'}")
    if package_manifest.get("target") != "V1_PRE_EVALUATEUR":
        errors.append("target paquet invalide")
    if package_manifest.get("field_validation") != "NON_REVENDIQUEE":
        errors.append("validation terrain ne doit pas etre revendiquee")
    if not str(package_manifest.get("dossier_id") or "").strip():
        errors.append("dossier demo absent du paquet")
    if not questions:
        errors.append("grille de revue evaluateur vide")
    if status_report.get("ok") is not True:
        errors.append("statut projet non OK")
    if status_report.get("pre_evaluator_package_status") != PACKAGE_STATUS:
        errors.append("statut projet ne confirme pas le paquet pre-evaluateur")
    if int(status_report.get("response_active_rows", 0) or 0) != 0:
        errors.append("reponses evaluateurs deja actives")
    if int(status_report.get("calibration_active_rows", 0) or 0) != 0:
        errors.append("calibration evaluateurs deja active")
    return errors


def build_manifest(
    package_manifest: dict[str, Any],
    status_report: dict[str, Any],
    questions: list[dict[str, str]],
    package_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "handoff_revue_evaluateur_v1",
        "status": HANDOFF_STATUS,
        "target": "V1_PRE_EVALUATEUR",
        "package_status": package_manifest.get("status", "UNKNOWN"),
        "project_status": status_report.get("decision", "UNKNOWN"),
        "dossier_id": package_manifest.get("dossier_id", ""),
        "runtime_status": package_manifest.get("runtime_status", "UNKNOWN"),
        "field_validation": package_manifest.get("field_validation", "UNKNOWN"),
        "no_evaluator_responses_invented": True,
        "real_field_validation_claimed": False,
        "stop_point": STOP_POINT,
        "questions_count": len(questions),
        "questions": [
            {
                "question_id": row.get("question_id", ""),
                "section": row.get("section", ""),
                "obligatoire": row.get("obligatoire", ""),
            }
            for row in questions
        ],
        "documents": {key: normalize_path(out_dir / filename) for key, filename in HANDOFF_FILES.items()},
        "package_documents": {
            "index": normalize_path(package_dir / "INDEX.md"),
            "rapport": normalize_path(package_dir / "RAPPORT-EXEMPLE-V1.md"),
            "questions": normalize_path(package_dir / "QUESTIONS-REVUE-EVALUATEUR.md"),
            "grille": normalize_path(package_dir / "GRILLE-REVUE-EVALUATEUR.csv"),
            "limites": normalize_path(package_dir / "LIMITES-V1-PRE-EVALUATEUR.md"),
        },
        "expected_outputs_after_meeting": [
            "grille completee par l'evaluateur",
            "liste de reserves bloquantes",
            "backlog V2 issu des retours reels",
        ],
    }


def build_brief_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Handoff revue evaluateur V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Synthese",
        "",
        f"- Statut handoff: **{manifest['status']}**",
        f"- Cible: **{manifest['target']}**",
        f"- Dossier demo: **{manifest.get('dossier_id', '-')}**",
        f"- Statut runtime: **{manifest.get('runtime_status', 'UNKNOWN')}**",
        f"- Validation terrain reelle: **{manifest.get('field_validation', 'UNKNOWN')}**",
        f"- Point d'arret: **{manifest['stop_point']}**",
        "",
        "## Materiel a presenter",
        "",
        "- `PAQUET-V1-PRE-EVALUATEUR/INDEX.md`",
        "- `PAQUET-V1-PRE-EVALUATEUR/RAPPORT-EXEMPLE-V1.md`",
        "- `PAQUET-V1-PRE-EVALUATEUR/QUESTIONS-REVUE-EVALUATEUR.md`",
        "- `PAQUET-V1-PRE-EVALUATEUR/GRILLE-REVUE-EVALUATEUR.csv`",
        "- `PAQUET-V1-PRE-EVALUATEUR/LIMITES-V1-PRE-EVALUATEUR.md`",
        "",
        "## Regles strictes",
        "",
        "- Ne pas pre-remplir de reponse au nom de l'evaluateur.",
        "- Ne pas presenter la fixture comme un dossier terrain reel valide.",
        "- Ne pas ouvrir de go production pendant ou apres cette revue.",
        "- Capturer les retours reels dans la grille, puis convertir en backlog V2.",
        "",
        "## Sortie attendue",
        "",
        "- Une grille completee ou annotee par l'evaluateur.",
        "- Une liste de reserves bloquantes et non bloquantes.",
        "- Une decision de suite: corriger V1, demarrer V2, ou preparer une campagne terrain reelle.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_agenda_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Ordre du jour revue evaluateur V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "| Bloc | Duree | Objectif | Support |",
        "|---|---:|---|---|",
        "| 1. Cadrage | 10 min | Confirmer la portee V1 pre-evaluateur et les limites terrain. | `LIMITES-V1-PRE-EVALUATEUR.md` |",
        "| 2. Parcours demo | 15 min | Montrer l'API/UI et le dossier demo. | `/review/ui`, `/ui` |",
        "| 3. Rapport exemple | 20 min | Revoir statut, valeurs, comparables et reserves. | `RAPPORT-EXEMPLE-V1.md` |",
        "| 4. Questions metier | 20 min | Faire trancher les questions ouvertes. | `QUESTIONS-REVUE-EVALUATEUR.md` |",
        "| 5. Decisions de suite | 10 min | Identifier corrections, blocages et prochains dossiers. | `GRILLE-REVUE-EVALUATEUR.csv` |",
        "",
        "## Point d'arret",
        "",
        f"- Statut: **{manifest['stop_point']}**",
        "- Les reponses ne sont pas integrees automatiquement.",
        "- Toute calibration attend une trace explicite issue de la seance.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build_checklist_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Checklist seance evaluateur V1",
        "",
        "_As-of date: 2026-05-04 (UTC)_",
        "",
        "## Avant la seance",
        "",
        "- [ ] Confirmer que le paquet V1 est regenere par la CI.",
        "- [ ] Confirmer qu'aucune donnee sensible n'est partagee.",
        "- [ ] Confirmer que la grille est vide avant la revue.",
        "- [ ] Preparer l'acces local a `/review/ui` et aux artefacts.",
        "",
        "## Pendant la seance",
        "",
        "- [ ] Montrer les limites avant le rapport exemple.",
        "- [ ] Demander les decisions de l'evaluateur, sans suggerer de reponses.",
        "- [ ] Noter les reserves bloquantes separement des ameliorations.",
        "- [ ] Confirmer les seuils ou statuts qui demandent une correction.",
        "",
        "## Apres la seance",
        "",
        "- [ ] Versionner uniquement les syntheses autorisees et non sensibles.",
        "- [ ] Garder les reponses nominatives hors repo si necessaire.",
        "- [ ] Transformer les retours en backlog V2.",
        "- [ ] Garder la production bloquee tant que la Phase H reelle n'est pas faite.",
        "",
        "## Trace machine-readable",
        "",
        f"- Manifest: `{manifest['documents']['manifest']}`",
        f"- Statut: **{manifest['status']}**",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_handoff(
    *,
    package_dir: Path = PACKAGE_DIR_DEFAULT,
    status_report_path: Path = STATUS_REPORT_DEFAULT,
    out_dir: Path = OUT_DIR_DEFAULT,
) -> dict[str, Any]:
    package_manifest = read_json_dict(package_dir / PACKAGE_MANIFEST)
    status_report = read_json_dict(status_report_path)
    questions = read_review_grid(package_dir / PACKAGE_GRID)
    errors = validate_inputs(package_manifest, status_report, questions)
    if errors:
        raise ValueError("; ".join(errors))

    manifest = build_manifest(package_manifest, status_report, questions, package_dir, out_dir)
    write_json(out_dir / HANDOFF_FILES["manifest"], manifest)
    write_text(out_dir / HANDOFF_FILES["brief"], build_brief_markdown(manifest))
    write_text(out_dir / HANDOFF_FILES["agenda"], build_agenda_markdown(manifest))
    write_text(out_dir / HANDOFF_FILES["checklist"], build_checklist_markdown(manifest))
    return {
        "status": HANDOFF_STATUS,
        "target": manifest["target"],
        "dossier_id": manifest["dossier_id"],
        "out_dir": normalize_path(out_dir),
        "files": {key: normalize_path(out_dir / filename) for key, filename in HANDOFF_FILES.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genere le handoff de revue evaluateur V1 sans reponse inventee.")
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR_DEFAULT)
    parser.add_argument("--status-report", type=Path, default=STATUS_REPORT_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    args = parser.parse_args()

    outputs = generate_handoff(
        package_dir=args.package_dir,
        status_report_path=args.status_report,
        out_dir=args.out_dir,
    )
    print(f"Handoff revue evaluateur: {outputs['out_dir']}")
    print(f"Statut: {outputs['status']}")
    print(f"Dossier demo: {outputs['dossier_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
