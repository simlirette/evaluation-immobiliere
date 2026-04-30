# Phase 3 - execution des dossiers pilotes reels

Objectif: executer les dossiers reels anonymises dans le runtime v0 et produire les artefacts a relire.

## Etat actuel

- Statut: **BLOQUE_PAR_ABSENCE_DE_DOSSIERS_REELS**
- Les brouillons `draft_dossier_reel_*.json` existent localement pour la phase 2.
- Aucun fichier `case_pilote_reel_*.json` n'est encore disponible.

## Garde-fou ajoute

L'outil `evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py` execute seulement les fixtures nommees:

```text
evaluation-immobiliere/tests/fixtures/case_pilote_reel_*.json
```

Les sorties sont ecrites dans `evaluation-immobiliere/runtime_pilotes_reels/`, qui est ignore par Git.

## Commande d'attente

Cette commande confirme que la phase 3 est prete mais en attente de dossiers:

```bash
python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py --allow-empty
```

Elle produit un rapport local d'attente:

```text
evaluation-immobiliere/runtime_pilotes_reels/RAPPORT-PILOTE-REEL-RUNTIME-V0.md
```

## Commande quand les dossiers sont fournis

1. Remplir les brouillons `draft_dossier_reel_*.json`.
2. Valider chaque brouillon en mode strict.
3. Renommer les dossiers valides en `case_pilote_reel_001.json`, `case_pilote_reel_002.json`, etc.
4. Executer:

```bash
python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py
```

## Artefacts attendus

- `runtime_summary.json`
- `RAPPORT-PILOTE-REEL-RUNTIME-V0.md`
- `validation_dossiers_reels.md`
- `contracts_report.json`
- Un sous-dossier d'artefacts par dossier reel.

## Critere de sortie phase 3

- 2-3 dossiers reels anonymises executes.
- Chaque dossier a un statut runtime interpretable.
- Les blocages et warnings sont expliques.
- Les artefacts sont prets pour revue evaluateur.
