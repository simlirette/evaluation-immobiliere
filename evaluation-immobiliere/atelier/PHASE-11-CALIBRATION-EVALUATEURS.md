# Phase 11 - Calibration evaluateurs et backlog v1

## Objectif

Transformer les retours evaluateurs sur les dossiers reels en decisions produit,
contrats QA, scoring comparables et backlog v1.

## Entrees

- `runtime_pilotes_reels/quality_report.json`
- `atelier/CALIBRATION-EVALUATEURS.csv`
- artefacts runtime des dossiers reels

## Sorties

- `runtime_pilotes_reels/calibration_evaluateurs.json`
- `runtime_pilotes_reels/RAPPORT-CALIBRATION-EVALUATEURS-V0.md`
- `runtime_pilotes_reels/BACKLOG-V1.md`

## Regle de phase

Tant que `CALIBRATION-EVALUATEURS.csv` ne contient aucune ligne active,
le statut reste `PRET_A_RECEVOIR_REPONSES`. Aucune calibration ne doit etre
inventee.

## Commande

```bash
python evaluation-immobiliere/outils/calibrer_reponses_evaluateurs_v0.py
```

