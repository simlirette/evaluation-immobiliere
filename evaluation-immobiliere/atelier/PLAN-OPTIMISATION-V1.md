# PLAN OPTIMISATION V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Transformer la baseline Phase G en actions d'optimisation mesurables sans degrader la qualite de justification.

## Constats de depart

- Delta runtime: **STABLE** avec 0 regression(s).
- Completion artefacts: **95.8%**.
- Erreurs contrat: **1**.
- Evenements moyens par dossier: **26**.
- Cout proxy par dossier: **119.97** unites.

## Actions P0

| Action | Resultat attendu | Owner | Preuve de fermeture |
|---|---|---|---|
| Instrumenter wall-clock par dossier et par etape | p50/p95 reels disponibles | Platform | `runtime_summary.json.metrics` non nul + bench regenere |
| Classifier les erreurs contrat attendues vs regressions | Cas garde-fou ne brouille plus les gates | QA/Runtime | matrice erreurs contrat + test cible |
| Definir commande benchmark batch | Run reproductible N dossiers / N iterations | Platform | script CLI + rapport Phase G |
| Fixer budget cout reel tokens/provider | Cout proxy relie aux couts reels | Product/Platform | table cout unitaire + seuil alerte |

## Actions P1

| Action | Resultat attendu | Owner | Preuve de fermeture |
|---|---|---|---|
| Cache ingestion/source_index | Moins de recalcul source sur rerun | Data/Ops | baisse cout proxy source/output |
| Paralleliser calculs valuation compatibles | Reduction p95 sans perte audit | Runtime | traces calcul completes + p95 ameliore |
| Compresser ou archiver artefacts verbeux | Baisse stockage et transfert | Platform | baisse KB artefacts dossier |
| Ajouter alerte qualite/cout dans readiness | Gate avant campagne Phase H | QA/Platform | readiness inclut SLO Phase G |

## Actions P2

- Reexecution incrementale par dossier et par etape modifiee.
- Budget adaptatif par type de dossier et complexite source.
- Drift detection sur cout proxy, qualite comparables et taux de revue humaine.

## Dependances Phase H

- Aucun passage Phase H sans p95 wall-clock mesure.
- Les erreurs contrat du cas negatif doivent etre classees comme attendues ou corrigees.
- Les SLO doivent etre revus avec au moins un evaluateur avant campagne terrain.
