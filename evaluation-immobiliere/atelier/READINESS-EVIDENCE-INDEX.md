# READINESS EVIDENCE INDEX

_As-of date: 2026-04-30 (UTC)_

## Objectif
Indexer les preuves minimales de readiness client Aston et statuer "Déjà prêt" vs "À produire en terminal".

## Mapping checklist readiness → artefacts
| Axe checklist | Item | Artefact repo | Statut | Mode |
|---|---|---|---|---|
| Crédibilité métier | 3 dossiers pilotes représentatifs | `tests/runtime/case_pilote_residentiel_standard/`, `tests/runtime/case_pilote_confiance_limitee/`, `tests/runtime/case_pilote_revision_conformite/` | Partiel (comparaison IA vs évaluateur manquante) | À produire en terminal |
| Crédibilité métier | Écarts documentés et justifiés | `atelier/RAPPORT-VALIDATION-DOSSIER-PILOTE.md` | Partiel | À produire en terminal |
| Crédibilité métier | Critères métier signés | Aucun artefact signé | Manquant | À produire en terminal |
| Traçabilité/auditabilité | Conclusion rattachée à source | `tests/runtime/*/data-facts.source_index.json` | Déjà prêt | Déjà prêt |
| Traçabilité/auditabilité | Audit runtime JSONL disponible | `tests/runtime/*/*.audit.jsonl` | Déjà prêt | Déjà prêt |
| Traçabilité/auditabilité | Historique corrections humaines | `atelier/REPONSES-EVALUATEURS.csv` | Partiel | À produire en terminal |
| Qualité technique | Tests runtime/API/ops pass baseline | `tests/test_runtime_v0.py`, `tests/test_api_v0.py`, `tests/test_ops_professional_gates_v0.py` | Scripts prêts, exécution manquante | À produire en terminal |
| Qualité technique | Aucun échec bloquant contrat/schéma | `outils/valider_contrats_runtime_v0.py`, `schemas/ops/*.json` | Script prêt, rapport à régénérer | À produire en terminal |
| Qualité technique | Session/start/stream fonctionnelle | `api.py`, `ui/pilote_api.html` | Partiel (preuve run live manquante) | À produire en terminal |
| Conformité/sécurité | RBAC minimal défini | `atelier/PLAN-INFRA-PRO-ASTON-AVANT-REPONSES.md` | Partiel | À produire en terminal |
| Conformité/sécurité | Secrets hors repo | `atelier/HANDOFF-TERMINAL-CHECKLIST.md` | Règle documentée | Déjà prêt |
| Conformité/sécurité | Rétention + journal accès | `schemas/ops/infra_contracts_report_v0.schema.json` | Partiel | À produire en terminal |
| Exploitation ops | Runbook incident + rollback | `atelier/RUNBOOK-OPERATIONS-PRE-REPONSES.md` | Déjà prêt | Déjà prêt |
| Exploitation ops | Contact hypercare défini | `atelier/HYPERCARE-OWNERS-V1.md` (à créer) | Partiel | À produire en terminal |
| Exploitation ops | Plan montée en charge progressive | `atelier/PLAN-DIRECTEUR-COMPLET-V1.md` | Partiel | À produire en terminal |

## Décisions prises
- Toute preuve non horodatée par exécution runtime récente est classée "À produire en terminal".
- Les artefacts existants sont conservés comme baseline mais non suffisants pour homologation finale.
- L'index readiness est aligné sur la checklist client et le vocabulaire Aston (runtime, scoring, homologation, hypercare).

## Questions ouvertes
- Format de signature des critères métier et validation officielle hypercare à confirmer pendant l'homologation terminal/client.
- Aucune question bloquante web; signatures finales et validation client se feront en terminal/homologation.
