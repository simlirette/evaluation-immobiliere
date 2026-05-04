# READINESS EVIDENCE INDEX

_As-of date: 2026-05-04 (UTC)_

## Objectif

Indexer les preuves minimales de readiness client Aston-like et statuer
"deja pret" vs "a produire en terminal".

## Mapping Checklist Readiness -> Artefacts

| Axe checklist | Item | Artefact repo | Statut | Mode |
|---|---|---|---|---|
| Credibilite metier | 3 dossiers pilotes representatifs | `tests/runtime/case_pilote_residentiel_standard/`, `tests/runtime/case_pilote_confiance_limitee/`, `tests/runtime/case_pilote_revision_conformite/` | Partiel, comparaison IA vs evaluateur manquante | A produire en terminal |
| Credibilite metier | Provenance D-REEL declassee | `skills/SKILLS-PROVENANCE.md`, `skills/`, `tests/fixtures/` | Deja pret | Deja pret |
| Credibilite metier | Contrat des skills de redaction | `skills/REDACTION-SKILLS-CONTRACT.json`, `outils/verifier_contrat_redaction_skills_v0.py` | Deja pret | Deja pret |
| Credibilite metier | Contrats skills critiques par agent | `skills/AGENT-SKILLS-CONTRACTS.json`, `outils/verifier_contrats_skills_agents_v0.py` | Deja pret | Deja pret |
| Credibilite metier | Contrats artefacts metier par agent | `integration/AGENT-ARTIFACT-CONTRACTS-V0.json`, `outils/verifier_contrats_artefacts_agents_v0.py`, `tests/runtime/agent_artifact_contracts_evidence.json` | Deja pret | Deja pret |
| Credibilite metier | Homologation metier synthetique | `atelier/HOMOLOGATION-METIER-GRILLE-V1.json`, `outils/verifier_homologation_metier_v0.py`, `tests/runtime/homologation_metier_report.json`, `atelier/PV-HOMOLOGATION-V1.md` | Deja pret, revues terrain manquantes | Deja pret |
| Credibilite metier | Ecarts documentes et justifies | `atelier/RAPPORT-VALIDATION-DOSSIER-PILOTE.md` | Partiel | A produire en terminal |
| Credibilite metier | Criteres metier signes | Aucun artefact signe | Manquant | A produire en terminal |
| Tracabilite/auditabilite | Conclusion rattachee a source | `tests/runtime/*/data-facts.source_index.json` | Deja pret | Deja pret |
| Tracabilite/auditabilite | Audit runtime JSONL disponible | `tests/runtime/*/*.audit.jsonl` | Deja pret | Deja pret |
| Tracabilite/auditabilite | Skills propages dans audit/artefacts | `tests/runtime/skills_runtime_evidence.json`, `tests/runtime/SKILLS-RUNTIME-EVIDENCE-V0.md` | Deja pret | Deja pret |
| Tracabilite/auditabilite | Historique corrections humaines | `atelier/REPONSES-EVALUATEURS.csv` | Partiel | A produire en terminal |
| Qualite technique | Tests runtime/API/ops pass baseline | `tests/test_runtime_v0.py`, `tests/test_api_v0.py`, `tests/test_ops_professional_gates_v0.py` | Scripts prets, execution manquante | A produire en terminal |
| Qualite technique | Aucun echec bloquant contrat/schema | `outils/valider_contrats_runtime_v0.py`, `schemas/ops/*.json` | Script pret, rapport a regenerer | A produire en terminal |
| Qualite technique | Session/start/stream fonctionnelle | `api.py`, `ui/pilote_api.html` | Partiel, preuve run live manquante | A produire en terminal |
| Conformite/securite | RBAC minimal defini | `atelier/PLAN-INFRA-PRO-ASTON-AVANT-REPONSES.md` | Partiel | A produire en terminal |
| Conformite/securite | Secrets hors repo | `atelier/HANDOFF-TERMINAL-CHECKLIST.md` | Regle documentee | Deja pret |
| Conformite/securite | Retention et journal acces | `schemas/ops/infra_contracts_report_v0.schema.json` | Partiel | A produire en terminal |
| Exploitation ops | Runbook incident et rollback | `atelier/RUNBOOK-OPERATIONS-PRE-REPONSES.md` | Deja pret | Deja pret |
| Exploitation ops | Contact hypercare defini | `atelier/HYPERCARE-OWNERS-V1.md` | Partiel | A produire en terminal |
| Exploitation ops | Plan montee en charge progressive | `atelier/PLAN-DIRECTEUR-COMPLET-V1.md` | Partiel | A produire en terminal |

## Decisions Prises

- Toute preuve non horodatee par execution runtime recente est classee "a produire en terminal".
- Les artefacts existants sont conserves comme baseline mais non suffisants pour homologation finale.
- L'index readiness est aligne sur la checklist client et le vocabulaire Aston-like: runtime, scoring, homologation, hypercare.
- Les D-REEL sont declasses comme provenance externe; les skills et fixtures synthetiques portent la preuve active du repo.
- Les skills de redaction sont maintenant verifies par contrat d'ancres metier, afin d'eviter une regression silencieuse des regles issues de la calibration.
- Les skills critiques data-facts, comps-market, valuation-draft et compliance-qa sont verifies par contrats d'ancres metier.
- La propagation runtime des skills est verifiee sur audit logs, artefacts et resume par cas.
- Les artefacts runtime produits par agent sont verifies par contrats metier conditionnels au statut du dossier.
- L'homologation metier synthetique distingue la preparation runtime de la signature terrain: runtime pret, production bloquee tant que les revues externes ne sont pas fournies.

## Questions Ouvertes

- Format de signature des criteres metier et validation officielle hypercare a confirmer pendant l'homologation terminal/client.
- Aucune question web bloquante; signatures finales et validation client se feront en terminal/homologation.
