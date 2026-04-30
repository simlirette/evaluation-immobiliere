# READINESS EVIDENCE INDEX

_As-of date: 2026-04-30 (UTC)_

## Objectif
Indexer les preuves minimales de readiness client Aston et statuer "Déjà prêt" vs "À produire en terminal".

## Mapping checklist readiness → artefacts
| Axe checklist | Item | Artefact repo | Statut | Mode |
|---|---|---|---|---|
| Crédibilité métier | 3 dossiers pilotes représentatifs | `tests/runtime/case_pilote_residentiel_standard/`, `tests/runtime/case_pilote_confiance_limitee/`, `tests/runtime/case_pilote_revision_conformite/` | Partiel | À produire en terminal |
| Crédibilité métier | Écarts documentés et justifiés | `atelier/RAPPORT-VALIDATION-DOSSIER-PILOTE.md` | Partiel | À produire en terminal |
| Crédibilité métier | Critères métier signés | Aucun artefact signé | Manquant | À produire en terminal |
| Traçabilité/auditabilité | Conclusion rattachée à source | `tests/runtime/*/data-facts.source_index.json` | Déjà prêt | Déjà prêt |
| Traçabilité/auditabilité | Audit runtime JSONL disponible | `tests/runtime/*/*.audit.jsonl` | Déjà prêt | Déjà prêt |
| Qualité technique | Tests runtime/API/ops pass baseline | `tests/test_runtime_v0.py`, `tests/test_api_v0.py`, `tests/test_ops_professional_gates_v0.py` | Scripts prêts, exécution manquante | À produire en terminal |
| Conformité/sécurité | Secrets hors repo | `atelier/HANDOFF-TERMINAL-CHECKLIST.md` | Règle documentée | Déjà prêt |
| Exploitation ops | Runbook incident + rollback | `atelier/RUNBOOK-OPERATIONS-PRE-REPONSES.md` | Déjà prêt | Déjà prêt |
| Exploitation ops | Contact hypercare défini | `atelier/HYPERCARE-OWNERS-V1.md` (à créer) | Partiel | À produire en terminal |

## Décisions prises
- Toute preuve non horodatée par run récent reste classée "À produire en terminal".
- L’index readiness reste aligné sur runtime, scoring, homologation, hypercare.

## Questions ouvertes
- Aucune question bloquante web; signatures finales et validation client se feront en terminal/homologation.
