# BENCH PERF COUT V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Etablir la baseline Phase G performance, fiabilite et cout a partir des sorties runtime pilotes deja produites.

## Synthese

| Indicateur | Valeur |
|---|---:|
| Dossiers analyses | 3 |
| Evenements runtime | 78 |
| Evenements moyens / dossier | 26 |
| P95 evenements / dossier | 26.90 |
| P95 wall-clock / dossier | n/d |
| Completion artefacts | 95.8% |
| Erreurs contrat | 1 |
| Regressions delta | 0 |
| Sources analysees | 118 pages / 203516 chars |
| Cout proxy total | 359.91 unites |
| Cout proxy / dossier | 119.97 unites |
| Decision Phase G | GO_CONDITIONNEL |

## Limite de mesure

- Les runs actuels sont deterministes: la latence wall-clock n'est pas encore une mesure exploitable.
- Le cout est un proxy reproductible, pas une facture tokens/provider: kchar sources + KB artefacts dossier + evenements runtime.
- Le prochain run Phase G doit activer des durees par dossier et par etape avant de figer les SLO finaux.

## Charge par etape

| Etape | step_start | artifact_written | step_done | blocking_detected | warning_detected | contract_invalid |
|---|---:|---:|---:|---:|---:|---:|
| compliance-qa | 3 | 9 | 3 | 1 | 0 | 0 |
| comps-market | 3 | 9 | 3 | 0 | 0 | 1 |
| data-facts | 3 | 9 | 3 | 0 | 0 | 0 |
| redaction | 2 | 4 | 2 | 0 | 0 | 0 |
| session | 0 | 0 | 0 | 0 | 2 | 0 |
| valuation-draft | 3 | 15 | 3 | 0 | 0 | 0 |

## Dossiers

| Dossier | Statut | Events | Artefacts | Completion | Blocages | Warnings | Contrats | Sources | Wall-clock |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| D-REEL-001 | PRET_REVISION_FINALE | 26 | 16/16 | 100.0% | 0 | 0 | 0 | 48 p | n/d |
| D-REEL-002 | BROUILLON | 27 | 16/16 | 100.0% | 0 | 1 | 0 | 35 p | n/d |
| D-REEL-003 | A_REVOIR | 25 | 14/16 | 87.5% | 2 | 1 | 1 | 35 p | n/d |

## Decision et conditions

- Condition: Mesure wall-clock par dossier/etape requise avant SLO final.
- Condition: Separer erreurs contrat attendues des cas garde-fous et regressions bloquantes.
- Condition: Porter la completion artefacts a la cible Phase G ou documenter l'exception du cas negatif.
