# BACKLOG EXECUTION PRIORISÉ (P0/P1/P2)

## Logique de priorisation
- **Impact business**: contribution directe à une valeur défendable en bureau d’évaluateurs.
- **Risque**: conformité, sécurité, traçabilité, erreur d’estimation.
- **Dépendances**: capacité à débloquer les phases D→L.

## Top 5 — exécution immédiate (mode web vs terminal)
| ID | Action | Mode recommandé | Pourquoi |
|---|---|---|---|
| P0-01 | Contrat d’intégration Aston exécutable V1 | Web maintenant | Travail de spécification/versionning/testabilité immédiatement réalisable |
| P0-02 | Branchement E2E runtime réel (1 dossier anonymisé) | Terminal | Nécessite exécution réelle, données, traces runtime |
| P0-03 | Persistance + streaming + reprise session | Terminal | Validation technique par run et contrôle d’intégrité |
| P0-04 | Baseline sécurité minimale exécutable | Hybride (web+terminal) | Design/politiques en web, preuve d’exécution en terminal |
| P0-05 | Calibration terrain mini-campagne | Terminal | Dépend dossiers réels + validation évaluateurs |

## P0 — tickets prêts à exécuter
| ID | Objectif mesurable | Critères d’acceptation | Dépendances | Risques | Owner |
|---|---|---|---|---|---|
| P0-01 | Contrats V1 versionnés | Session/events/artifacts + erreurs/retry + test compat pass | A,B | Divergence Aston réel | Lead Runtime |
| P0-02 | 1 run E2E réel complet | Audit JSONL + artefacts complets + rapport comparatif | B,C | Faux positif readiness | Lead Intégration |
| P0-03 | Resume session prouvé | Reprise réussie + intégrité event→artefact validée | C,D | Perte de traçabilité | Lead Plateforme |
| P0-04 | Baseline sécurité active | RBAC + secrets hors repo + journal accès + rétention validée | D,F | Non-conformité client | SecOps |
| P0-05 | Mini-calibration signée | Écarts IA/évaluateur documentés + seuils Go/No-Go signés | E,H | Rejet métier | Lead Métier |

## P1 — Professionnalisation
- UI évaluateur complète (revue/override/validation/historique).
- CI/CD avec gates bloquants runtime/ops/contrats.
- SLO/SLA + alerting + suivi coût.
- Pré-prod + homologation formelle.

## P2 — Scale & optimisation
- Optimisation coût/latence multi-dossiers.
- Réexécution incrémentale/cache.
- Hypercare industrialisé et roadmap v2.

## Template ticket (copier-coller)
```markdown
### Contexte
### Objectif mesurable
### In scope / Out of scope
### Entrées requises
### Tâches atomiques
### Critères d’acceptation (Given/When/Then)
### Preuves attendues (fichiers, rapports, logs)
### Dépendances
### Risques / mitigations
### Owner / reviewer / date cible
```

## Décisions prises
- Exécuter P0-01 immédiatement en web.
- Préparer tous les tickets P0 en format exécutable avant passage terminal.
- Bloquer P1/P2 tant que P0 non validé.

## Questions ouvertes
- Ordre exact P0-02 vs P0-03 selon contraintes Aston runtime ? **À valider**.
- Qui signe les seuils Go/No-Go métier pour P0-05 ? **À valider**.
