# MATRICE COMPATIBILITÉ CONTRATS ↔ TESTS V1

## Couverture
Mapping entre clauses du contrat Aston runtime V1 et preuves de tests/scripts existants.

| Clause contrat V1 | Fichier/contrôle | Type preuve | Statut |
|---|---|---|---|
| Séquence steps data-facts→redaction | `integration/PIPELINE-RUNTIME-ASTON-V0.yaml` + `tests/test_runtime_v0.py` | Spécification + test runtime | Couvert |
| Validation artefacts runtime | `outils/valider_contrats_runtime_v0.py` + `tests/test_valider_contrats_runtime_v0.py` | Script + unit test | Couvert |
| Intégrité event→artefact | `outils/analyser_integrite_runtime_v0.py` + `tests/runtime/integrity_report.json` | Script + rapport | Partiel (exécution terminal) |
| Qualité runtime/scoring | `outils/analyser_qualite_runtime_v0.py` + `tests/test_qualite_runtime_v0.py` | Script + test | Partiel (exécution terminal) |
| Gates homologation ops | `tests/test_ops_professional_gates_v0.py` | Test | Couvert |
| Sessions et reprise runtime | `engine/runtime.py` + `outils/generer_registry_runtime_v0.py` | Implémentation + script | Partiel (preuve run réel manquante) |
| Hypercare readiness | `atelier/READINESS-PRESENTATION-BUREAUX.md` + `atelier/HANDOFF-TERMINAL-CHECKLIST.md` | Checklists | Partiel (preuves J+7 manquantes) |

## Gaps à traiter en terminal
- Produire `tests/runtime/contracts_report.json` à jour via validation contrats runtime.
- Régénérer `tests/runtime/integrity_report.json` sur run récent.
- Rejouer la baseline tests runtime/api/ops pour statut homologation.

## Décisions prises
- Une clause sans test scriptable est classée "Partiel" même si documentée.
- Les preuves terminal sont séparées pour éviter un faux Go web.

## Questions ouvertes
- Quelle cadence de rerun est retenue pour maintenir la compatibilité contractuelle ?
- Faut-il ajouter un test dédié à l'hypercare (KPI J+7) ?
