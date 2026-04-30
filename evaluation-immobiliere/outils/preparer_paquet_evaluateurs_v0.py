#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

RUNTIME_DIR_DEFAULT = Path("evaluation-immobiliere/runtime_pilotes_reels")
OUT_DIR_DEFAULT = Path("evaluation-immobiliere/paquets_evaluateurs/v0")
ATELIER_DIR = Path("evaluation-immobiliere/atelier")
SUMMARY_NAME = "runtime_summary.json"
PACKAGE_INDEX_NAME = "PAQUET-EVALUATEURS-V0.md"
SEND_CHECKLIST_NAME = "CHECKLIST-ENVOI-EVALUATEURS.md"
RESPONSE_TEMPLATE_SOURCE = ATELIER_DIR / "REPONSES-EVALUATEURS-TEMPLATE.csv"
RESPONSE_TEMPLATE_COPY = "REPONSES-EVALUATEURS-A-REMPLIR.csv"
QUESTIONNAIRE_SOURCE = ATELIER_DIR / "QUESTIONNAIRE-EVALUATEURS.md"
GUIDE_SOURCE = ATELIER_DIR / "GUIDE-COMPILATION-REPONSES.md"
REVIEW_REPORT_NAME = "REVUE-INTERNE-PILOTES-REELS-V0.md"
HARDENING_REPORT_NAME = "DURCISSEMENT-CONTRATS-PILOTES-REELS-V0.md"
RUNTIME_REPORT_NAME = "RAPPORT-PILOTE-REEL-RUNTIME-V0.md"
REQUIRED_ARTIFACTS = [
    "compliance-qa.statut_sortie.json",
    "compliance-qa.rapport_non_conformites.json",
    "compliance-qa.recommandations_corrections.md",
]
OPTIONAL_ARTIFACTS = [
    "redaction.brouillon_rapport.md",
    "redaction.annexe_sources.md",
]


def load_summary(runtime_dir: Path) -> list[dict] | None:
    summary_path = runtime_dir / SUMMARY_NAME
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def artifact_exists(case: dict, artifact_name: str) -> bool:
    artifact_dir = Path(str(case.get("artifact_dir", "")))
    return bool(artifact_dir) and (artifact_dir / artifact_name).exists()


def missing_required_artifacts(case: dict) -> list[str]:
    return [name for name in REQUIRED_ARTIFACTS if not artifact_exists(case, name)]


def package_status(summary: list[dict] | None, runtime_dir: Path) -> str:
    if summary is None:
        return "EN_ATTENTE_DOSSIERS_REELS"
    if any(missing_required_artifacts(case) for case in summary):
        return "A_COMPLETER_AVANT_ENVOI"
    if not (runtime_dir / REVIEW_REPORT_NAME).exists():
        return "A_REVOIR_INTERNE_AVANT_ENVOI"
    return "PRET_A_ENVOYER"


def reset_output_dir(out_dir: Path) -> None:
    if out_dir.exists():
        for path in out_dir.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)


def copy_response_template(out_dir: Path, source: Path = RESPONSE_TEMPLATE_SOURCE) -> Path:
    target = out_dir / RESPONSE_TEMPLATE_COPY
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def build_case_rows(summary: list[dict] | None) -> list[dict[str, str]]:
    if summary is None:
        return []
    rows: list[dict[str, str]] = []
    for case in summary:
        artifact_dir = str(case.get("artifact_dir", ""))
        case_name = Path(artifact_dir).name if artifact_dir else "-"
        rows.append(
            {
                "cas": case_name,
                "dossier_id": str(case.get("dossier_id", "-")),
                "statut_runtime": str(case.get("status", "UNKNOWN")),
                "blocages": str(len(case.get("blocking_failures", []))),
                "warnings": str(len(case.get("warnings", []))),
                "artefacts": artifact_dir or "-",
            }
        )
    return rows


def write_case_manifest(out_dir: Path, summary: list[dict] | None) -> Path:
    target = out_dir / "MANIFESTE-CAS-PILOTES.csv"
    fieldnames = ["cas", "dossier_id", "statut_runtime", "blocages", "warnings", "artefacts"]
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(build_case_rows(summary))
    return target


def build_waiting_index(runtime_dir: Path, status: str) -> str:
    return "\n".join(
        [
            "# Paquet evaluateurs v0",
            "",
            f"- Statut: **{status}**",
            f"- Repertoire runtime attendu: `{runtime_dir.as_posix()}`",
            f"- Fichier requis: `{SUMMARY_NAME}`",
            "",
            "## Inclus maintenant",
            "",
            f"- Questionnaire source: `{QUESTIONNAIRE_SOURCE.as_posix()}`",
            f"- Guide compilation: `{GUIDE_SOURCE.as_posix()}`",
            f"- Gabarit reponses: `{RESPONSE_TEMPLATE_SOURCE.as_posix()}`",
            "",
            "## Prochaine action",
            "",
            "Executer les phases 3, 4 et 5 sur les dossiers reels anonymises avant envoi aux evaluateurs.",
            "",
        ]
    )


def build_package_index(summary: list[dict], runtime_dir: Path, status: str) -> str:
    lines = [
        "# Paquet evaluateurs v0",
        "",
        f"- Statut: **{status}**",
        f"- Dossiers pilotes reels: **{len(summary)}**",
        f"- Repertoire runtime: `{runtime_dir.as_posix()}`",
        "",
        "## Documents de collecte",
        "",
        f"- Questionnaire: `{QUESTIONNAIRE_SOURCE.as_posix()}`",
        f"- Guide compilation: `{GUIDE_SOURCE.as_posix()}`",
        f"- CSV a remplir: `{RESPONSE_TEMPLATE_COPY}`",
        f"- Manifeste des cas: `MANIFESTE-CAS-PILOTES.csv`",
        "",
        "## Rapports internes a consulter avant envoi",
        "",
        f"- `{(runtime_dir / RUNTIME_REPORT_NAME).as_posix()}`",
        f"- `{(runtime_dir / REVIEW_REPORT_NAME).as_posix()}`",
        f"- `{(runtime_dir / HARDENING_REPORT_NAME).as_posix()}`",
        "",
        "## Cas et artefacts a montrer",
        "",
        "| Cas | Dossier | Statut | Blocages | Warnings | Artefacts obligatoires manquants | Artefacts dossier |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for case in summary:
        artifact_dir = str(case.get("artifact_dir", ""))
        case_name = Path(artifact_dir).name if artifact_dir else "-"
        missing = missing_required_artifacts(case)
        lines.append(
            "| {case_name} | {dossier_id} | {status} | {blocking} | {warnings} | {missing} | `{artifact_dir}` |".format(
                case_name=case_name,
                dossier_id=case.get("dossier_id", "-"),
                status=case.get("status", "UNKNOWN"),
                blocking=len(case.get("blocking_failures", [])),
                warnings=len(case.get("warnings", [])),
                missing=", ".join(missing) if missing else "-",
                artifact_dir=artifact_dir or "-",
            )
        )

    lines.extend(
        [
            "",
            "## Questions ciblees pendant la revue",
            "",
            "- Les statuts runtime correspondent-ils au jugement professionnel attendu?",
            "- Les blocages sont-ils de vrais blocages ou des warnings trop stricts?",
            "- Les warnings sont-ils suffisants pour guider une correction interne?",
            "- Le brouillon de rapport contient-il assez de sources et d'explications pour etre relu efficacement?",
            "- Quelles taches doivent entrer dans `REPONSES-EVALUATEURS-A-REMPLIR.csv` avec priorite?",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_send_checklist(status: str) -> str:
    checked = "[ ]"
    return "\n".join(
        [
            "# Checklist envoi evaluateurs",
            "",
            f"- Statut paquet: **{status}**",
            "",
            f"- {checked} Dossiers reels anonymises valides en mode strict.",
            f"- {checked} Phase 3 executee et artefacts runtime disponibles.",
            f"- {checked} Phase 4 revue interne completee.",
            f"- {checked} Phase 5 decisions de contrats documentees.",
            f"- {checked} Questionnaire relu.",
            f"- {checked} CSV reponses duplique par evaluateur avec `respondant_id` anonymise.",
            f"- {checked} Artefacts sensibles revus avant partage.",
            "",
        ]
    )


def write_package(runtime_dir: Path, out_dir: Path) -> str:
    reset_output_dir(out_dir)
    summary = load_summary(runtime_dir)
    status = package_status(summary, runtime_dir)
    copy_response_template(out_dir)
    write_case_manifest(out_dir, summary)

    index = build_waiting_index(runtime_dir, status) if summary is None else build_package_index(summary, runtime_dir, status)
    (out_dir / PACKAGE_INDEX_NAME).write_text(index, encoding="utf-8")
    (out_dir / SEND_CHECKLIST_NAME).write_text(build_send_checklist(status), encoding="utf-8")
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare le paquet d'envoi aux evaluateurs.")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME_DIR_DEFAULT)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Retourne exit code 0 quand aucun dossier reel n'a encore ete execute.",
    )
    args = parser.parse_args()

    status = write_package(args.runtime_dir, args.out_dir)
    print(f"Paquet evaluateurs: {args.out_dir / PACKAGE_INDEX_NAME}")
    print(f"Statut: {status}")
    if status == "EN_ATTENTE_DOSSIERS_REELS" and not args.allow_empty:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
