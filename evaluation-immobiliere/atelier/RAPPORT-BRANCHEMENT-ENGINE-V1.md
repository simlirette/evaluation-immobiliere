# RAPPORT BRANCHEMENT ENGINE V1

_As-of date: 2026-04-30 (UTC)_

## Statut Phase C
Phase C démarrée sur P0-02 avec exécution du runtime local déterministe sur les dossiers anonymisés `case_pilote_reel_*.json`.

Décision actuelle: **GO CONDITIONNEL vers poursuite Phase C**, pas encore Go final Aston natif.

## Commande principale exécutée
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py
```

Résultat: **exit code 0**.

## Commande stricte de diagnostic
```powershell
& 'C:\Users\simon\Documents\Codex\2026-04-26\contexte-je-veux-un-review-complet\.tools\poetry-envs\resilio-xN2RUnV3-py3.13\Scripts\python.exe' evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py --fail-on-contract-errors
```

Résultat: **exit code 1**, car `case_pilote_reel_003` contient une erreur contrat attendue pour valider le stop compliance.

## Résultat d'exécution
| Élément | Résultat |
|---|---|
| Dossiers actifs | 3 |
| Pipeline chargé | 5 steps depuis `integration/PIPELINE-RUNTIME-ASTON-V0.yaml` |
| Statuts | 1 `PRET_REVISION_FINALE`, 1 `BROUILLON`, 1 `A_REVOIR` |
| Événements runtime | 78 |
| Artefacts attendus | 48 |
| Artefacts produits | 46 |
| Traces calcul complètes | 3/3 |
| Ingestion PDF/source text disponible | 3/3 |
| Taux champs sourcés | 1.0 |
| Erreurs contrat | 1 |
| Exit code commande principale | 0 |
| Exit code diagnostic strict | 1 |

## Lecture du résultat
| Cas | Statut | Blocages | Warnings | Lecture Phase C |
|---|---|---:|---:|---|
| `case_pilote_reel_001` | `PRET_REVISION_FINALE` | 0 | 0 | Chemin positif complet avec 16/16 artefacts |
| `case_pilote_reel_002` | `BROUILLON` | 0 | 1 | Chemin faible confiance correctement retenu en brouillon |
| `case_pilote_reel_003` | `A_REVOIR` | 2 | 1 | Chemin garde-fou: stop après compliance, redaction non produite |

Blocages `case_pilote_reel_003`:
- `B003: vente comparable future vs date_reference`
- `CONF005: comparable[2] hors fenetre temporelle`

Warning `case_pilote_reel_003`:
- `W002: comparable eloigne`

## Artefacts de preuve locaux
Ces fichiers sont générés localement et ignorés par git via `.gitignore`; les synthèses sont versionnées dans `atelier/`.

| Preuve | Chemin |
|---|---|
| Résumé runtime | `evaluation-immobiliere/runtime_pilotes_reels/runtime_summary.json` |
| Rapport runtime | `evaluation-immobiliere/runtime_pilotes_reels/RAPPORT-PILOTE-REEL-RUNTIME-V0.md` |
| Rapport contrats | `evaluation-immobiliere/runtime_pilotes_reels/contracts_report.json` |
| Rapport qualité | `evaluation-immobiliere/runtime_pilotes_reels/quality_report.json` |
| Validation dossiers | `evaluation-immobiliere/runtime_pilotes_reels/validation_dossiers_reels.md` |

## Écart avec la cible Aston réelle
| Domaine | Couvert maintenant | Écart restant |
|---|---|---|
| Agent loop | Orchestration locale `RuntimeEngine` sur 5 étapes | Boucle Aston native avec budgets/retries/session lifecycle |
| Dossiers réels anonymisés | Fixtures `case_pilote_reel_*` validées strictement | Entrée live et stockage central de documents |
| Audit | JSONL append-only par cas | Event stream central corrélé session/run/user |
| Artefacts | JSON/Markdown générés par étape | Artifact store Aston avec checksum, ACL et version |
| Outils externes | Pools fournis par fixture, ingestion déjà matérialisée | Connecteurs OCR/comparables/registres réels |

## Décision Go/No-Go
Décision: **GO CONDITIONNEL** pour continuer Phase C.

Conditions avant Go final Phase C:
- brancher au moins un connecteur documentaire réel ou wrapper Aston équivalent;
- décider si les cas `A_REVOIR` doivent faire échouer la commande stricte ou être acceptés comme tests de garde-fous;
- produire une preuve signée IA vs évaluateur pour au moins un dossier;
- définir l'owner de signature Go/No-Go Phase C.

## Prochaine action
Traiter le point de conception `--fail-on-contract-errors`: séparer les erreurs contrat attendues des cas négatifs de celles qui doivent bloquer toute exécution P0-02.
