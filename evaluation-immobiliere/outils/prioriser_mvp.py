#!/usr/bin/env python3
"""Score les tâches du fichier MATRICE-PRIORISATION-MVP.csv et retourne un classement."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

INPUT_DEFAULT = Path("evaluation-immobiliere/atelier/MATRICE-PRIORISATION-MVP.csv")


@dataclass
class TaskScore:
    task: str
    score: float
    details: dict[str, float]


def to_float(value: str) -> float:
    value = (value or "").strip()
    if not value:
        return 0.0
    return float(value)


def compute_score(row: dict[str, str]) -> TaskScore:
    task = row.get("tache", "").strip() or "(sans_nom)"
    temps = to_float(row.get("temps_moyen_min", ""))
    frequence = to_float(row.get("frequence_par_mois", ""))
    douleur = to_float(row.get("douleur_1_5", ""))
    risque = to_float(row.get("risque_conformite_1_5", ""))
    auto = to_float(row.get("automatisation_potentielle_1_5", ""))

    # Heuristique simple orientée MVP:
    # plus la tâche est fréquente/douloureuse/automatisable, plus son score monte.
    # risque conformité augmente la priorité (sécuriser tôt).
    score = (
        frequence * 0.30
        + douleur * 0.20
        + auto * 0.30
        + risque * 0.15
        + min(temps / 30.0, 5) * 0.05
    )

    return TaskScore(
        task=task,
        score=round(score, 3),
        details={
            "frequence": frequence,
            "douleur": douleur,
            "automatisation": auto,
            "risque": risque,
            "temps": temps,
        },
    )


def rank_tasks(csv_path: Path) -> list[TaskScore]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        scores = [compute_score(row) for row in reader]

    return sorted(scores, key=lambda x: x.score, reverse=True)


def main() -> None:
    ranked = rank_tasks(INPUT_DEFAULT)
    print("Classement MVP (score décroissant):")
    for idx, item in enumerate(ranked, start=1):
        print(f"{idx:02d}. {item.task}: {item.score}")


if __name__ == "__main__":
    main()
