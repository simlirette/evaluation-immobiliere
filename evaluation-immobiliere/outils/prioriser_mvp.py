#!/usr/bin/env python3
"""Score les taches du fichier MATRICE-PRIORISATION-MVP.csv et retourne un classement."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

INPUT_DEFAULT = Path("evaluation-immobiliere/atelier/MATRICE-PRIORISATION-MVP.csv")


@dataclass
class TaskScore:
    task: str
    score: float
    details: dict[str, float | str | bool]


def to_float(value: str | None) -> float:
    value = (value or "").strip()
    if not value:
        return 0.0
    return float(value)


def to_bool(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"1", "true", "oui", "yes", "y"}


def compute_score(row: dict[str, str]) -> TaskScore:
    task = row.get("tache", "").strip() or "(sans_nom)"
    temps = to_float(row.get("temps_moyen_min"))
    frequence = to_float(row.get("frequence_par_mois"))
    douleur = to_float(row.get("douleur_1_5"))
    risque = to_float(row.get("risque_conformite_1_5"))
    auto = to_float(row.get("automatisation_potentielle_1_5"))
    complexite = to_float(row.get("complexite_technique_1_5"))
    donnees = to_float(row.get("disponibilite_donnees_1_5"))
    validation_humaine = to_bool(row.get("validation_humaine_obligatoire"))
    decision_non_delegable = to_bool(row.get("decision_non_delegable"))

    effort_inverse = max(6 - complexite, 0) if complexite else 0.0
    temps_normalise = min(temps / 30.0, 5)

    valeur_score = (
        frequence * 0.25
        + douleur * 0.25
        + auto * 0.20
        + risque * 0.15
        + temps_normalise * 0.15
    )
    readiness_score = (donnees * 0.60 + effort_inverse * 0.40) if donnees or complexite else 0.0
    risque_score = risque

    # Le jugement humain obligatoire ne tue pas une tache MVP: il signale plutot
    # que la cible doit etre un assistant/reviseur, pas une automatisation finale.
    gouvernance_penalty = 0.20 if decision_non_delegable and not validation_humaine else 0.0
    score = valeur_score * 0.55 + readiness_score * 0.25 + risque_score * 0.20 - gouvernance_penalty

    return TaskScore(
        task=task,
        score=round(score, 3),
        details={
            "phase": row.get("phase", "").strip(),
            "valeur_score": round(valeur_score, 3),
            "readiness_score": round(readiness_score, 3),
            "risque_score": round(risque_score, 3),
            "frequence": frequence,
            "douleur": douleur,
            "automatisation": auto,
            "risque": risque,
            "temps": temps,
            "complexite": complexite,
            "donnees": donnees,
            "validation_humaine": validation_humaine,
            "decision_non_delegable": decision_non_delegable,
        },
    )


def rank_tasks(csv_path: Path) -> list[TaskScore]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        scores = [compute_score(row) for row in reader]

    return sorted(scores, key=lambda x: x.score, reverse=True)


def main() -> None:
    ranked = rank_tasks(INPUT_DEFAULT)
    print("Classement MVP (score decroissant):")
    for idx, item in enumerate(ranked, start=1):
        phase = item.details.get("phase") or "-"
        print(f"{idx:02d}. {item.task}: {item.score} | phase={phase}")


if __name__ == "__main__":
    main()
