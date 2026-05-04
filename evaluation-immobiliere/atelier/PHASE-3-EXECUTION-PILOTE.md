# Phase 3 - execution des dossiers pilotes reels

Objectif: executer les dossiers reels anonymises dans le runtime v0 et produire les artefacts a relire.

## Etat actuel

- Statut: **BLOQUE_PAR_ABSENCE_DE_DOSSIERS_REELS**
- Les dossiers reels anonymises doivent rester hors repo actif ou dans `tests/fixtures_external/` ignore par Git.
- Aucun fichier `case_pilote_reel_*.json` n'est encore disponible.

## Garde-fou ajoute

L'outil `evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py` execute seulement les fixtures nommees:

```text
evaluation-immobiliere/tests/fixtures_external/case_pilote_reel_*.json
```

En Phase H reelle, passer le repertoire hors repo avec `--fixtures-dir <PHASE_H_REAL_CASES_DIR>`. Le script valide chaque fixture en strict et lance un audit anonymisation avant tout runtime. Les sorties sont ecrites dans `evaluation-immobiliere/runtime_pilotes_reels/`, qui est ignore par Git.

## Precondition ingestion

Avant execution runtime, normaliser les sources anonymisees:

```bash
python evaluation-immobiliere/outils/preparer_ingestion_pdf_v0.py --fixtures-dir <PHASE_H_REAL_CASES_DIR>
```

Le gate Phase H exige `runtime_pilotes_reels/ingestion_v0/MANIFESTE-INGESTION-PDF-V0.json` sans erreur quand des dossiers terrain actifs existent.

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

1. Remplir les brouillons `draft_dossier_reel_*.json` hors repo actif.
2. Valider chaque brouillon en mode strict et audit anonymisation.
3. Renommer les dossiers valides en `case_pilote_reel_001.json`, `case_pilote_reel_002.json`, etc.
4. Normaliser les sources anonymisees.
5. Executer:

```bash
python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py --fixtures-dir <PHASE_H_REAL_CASES_DIR> --fail-on-contract-errors
python evaluation-immobiliere/outils/verifier_campagne_terrain_reelle_v1.py --fixtures-dir <PHASE_H_REAL_CASES_DIR>
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
