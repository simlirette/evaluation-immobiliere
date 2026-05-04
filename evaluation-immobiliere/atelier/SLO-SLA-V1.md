# SLO SLA V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Fixer les SLO/SLA initiaux Phase G et les alertes minimales avant la campagne terrain Phase H.

Decision de phase: **GO_CONDITIONNEL**.

## SLO initiaux

| SLO | Courant | Cible | Statut | Owner | Preuve |
|---|---:|---:|---|---|---|
| latence_p95_dossier | n/d | <= 900 sec | INSTRUMENTATION_REQUISE | Platform | `runtime_summary.json metrics.wall_clock_seconds` |
| completion_artefacts | 95.8% | >= 0.98 | A_TRAITER | QA/Runtime | `quality_report.json totals` |
| couverture_champs_sources | 100.0% | >= 0.95 | OK | Data/Ops | `quality_report.json averages.sourced_field_rate` |
| erreurs_contrat | 1 | <= 0 | A_TRAITER | QA/Platform | `quality_report.json totals.contract_errors` |
| regressions_delta_runtime | 0 | <= 0 | OK | Platform | `runtime_delta_report.json regressions` |
| cout_proxy_par_dossier | 119.97 | baseline v0; alerte si +25% vs dernier run stable | BASELINE | Product/Platform | `perf_cost_phase_g_report.json cost_proxy` |

## SLA operationnel v1

| Flux | Engagement initial | Escalade |
|---|---|---|
| Run pilote batch | Rapport perf/cout disponible le meme jour ouvre | Platform si rapport absent |
| Regression delta | Triage en moins de 1 jour ouvre | QA/Platform si `A_CONTROLER` |
| Erreur contrat non attendue | Correction ou exception documentee avant Phase H | Lead Runtime + Lead Metier |
| Depassement budget cout proxy | Revue prompt/outils avant nouveau lot | Product + Platform |

## Alertes minimales

- Alerte `runtime_delta_regression` si `runtime_delta_report.status == A_CONTROLER`.
- Alerte `artifact_completion_low` si completion artefacts < 98% hors cas garde-fou documente.
- Alerte `contract_errors_unclassified` si erreurs contrat > 0 sans classification attendu/non-attendu.
- Alerte `cost_proxy_growth` si cout proxy par dossier augmente de 25% vs dernier run stable.
- Alerte `wall_clock_missing` tant que p95 wall-clock n'est pas mesure sur un run non deterministe.
