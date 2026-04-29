# Rapport pilote runtime v0

## Baseline

- Cas executes: **8**
- Prets revision finale: **2**
- Brouillons: **2**
- A revoir: **4**
- Blocages detectes: **12**
- Warnings detectes: **5**
- Evenements runtime: **203**

## Distribution des statuts

- PRET_REVISION_FINALE: 2
- BROUILLON: 2
- A_REVOIR: 4

## Cas pilotes

| Cas | Dossier | Statut | Blocages | Warnings | Artefacts |
|---|---|---|---:|---:|---|
| case_low_confidence | D-005 | BROUILLON | 0 | 1 | `evaluation-immobiliere/tests/runtime/case_low_confidence` |
| case_missing_source | D-002 | A_REVOIR | 5 | 0 | `evaluation-immobiliere/tests/runtime/case_missing_source` |
| case_nominal | D-001 | PRET_REVISION_FINALE | 0 | 0 | `evaluation-immobiliere/tests/runtime/case_nominal` |
| case_pilote_confiance_limitee | D-PILOTE-RES-002 | BROUILLON | 0 | 3 | `evaluation-immobiliere/tests/runtime/case_pilote_confiance_limitee` |
| case_pilote_residentiel_standard | D-PILOTE-RES-001 | PRET_REVISION_FINALE | 0 | 0 | `evaluation-immobiliere/tests/runtime/case_pilote_residentiel_standard` |
| case_pilote_revision_conformite | D-PILOTE-RES-003 | A_REVOIR | 5 | 1 | `evaluation-immobiliere/tests/runtime/case_pilote_revision_conformite` |
| case_sensitive_no_validation | D-003 | A_REVOIR | 1 | 0 | `evaluation-immobiliere/tests/runtime/case_sensitive_no_validation` |
| case_unit_incoherence | D-004 | A_REVOIR | 1 | 0 | `evaluation-immobiliere/tests/runtime/case_unit_incoherence` |

## Blocages et warnings

### case_low_confidence
- Warnings: W001: confiance faible

### case_missing_source
- Blocages: B002: comparable sans source_id; B002: ajustement sans source_id; STRICT: sortie refusee, comparable sans source; CONF001: fiche_bien sans source_ids; CONF002: aucun comparable propose

### case_pilote_confiance_limitee
- Warnings: W002: comparable eloigne; W001: confiance faible; W003: hypothese non corroboree par une deuxieme source

### case_pilote_revision_conformite
- Blocages: B003: vente comparable future vs date_reference; B002: comparable sans source_id; B005: ajustement sensible sans validation_humaine; B002: ajustement sans source_id; STRICT: sortie refusee, comparable sans source
- Warnings: W003: hypothese non corroboree par une deuxieme source

### case_sensitive_no_validation
- Blocages: B005: ajustement sensible sans validation_humaine

### case_unit_incoherence
- Blocages: B004: unite incoherente sujet/comparables

## Lecture produit

- Les cas `PRET_REVISION_FINALE` servent de reference positive pour les dossiers pilotes reels.
- Les cas `BROUILLON` indiquent que les donnees sont exploitables mais demandent encore jugement humain ou confiance accrue.
- Les cas `A_REVOIR` valident que les garde-fous bloquants stoppent les dossiers incomplets ou incoherents.
