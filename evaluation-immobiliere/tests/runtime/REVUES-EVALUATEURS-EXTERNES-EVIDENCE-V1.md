# Revues evaluateurs externes Evidence V1

## Synthese

- OK gate strict: **true**
- Decision: **GO_CONDITIONNEL_ECARTS_EVALUATEURS**
- Source: `evaluation-immobiliere/tests/fixtures_external/homologation_evaluateurs_v1.json`
- Reviews: **3**
- Evaluateurs: **2**
- Dossiers pilotes revus: **3**
- Ecarts: **3**
- Desaccords statut: **0**
- Erreurs: **0**
- Warnings: **3**

## Couverture

| Dossier | Statut runtime | Statuts attendus | Evaluateurs | Decisions | Ecarts |
|---|---|---|---|---|---:|
| D-PILOTE-RES-001 | PRET_REVISION_FINALE | PRET_REVISION_FINALE | EV-EXT-01 | ACCEPTE=1 | 0 |
| D-PILOTE-RES-002 | BROUILLON | BROUILLON | EV-EXT-01 | A_REVOIR=1 | 1 |
| D-PILOTE-RES-003 | A_REVOIR | A_REVOIR | EV-EXT-02 | A_REVOIR=1 | 2 |

## Ecarts

| Priorite | Dossier | Cible | Statut | Recommandation | Evidence |
|---|---|---|---|---|---|
| P1 | D-PILOTE-RES-003 | comps-market.justifications_comparables.json | A_TRAITER_AVANT_GO | Fermer le blocage de conformite ou documenter son acceptation metier. | Le dossier pilote revision conformite contient un blocage temporel. |
| P2 | D-PILOTE-RES-002 | compliance-qa.recommandations_corrections.md | A_PLANIFIER | Ajouter une phrase de reserve metier avant signature finale. | Le dossier reste en BROUILLON et non en PRET_REVISION_FINALE. |
| P2 | D-PILOTE-RES-003 | redaction.brouillon_rapport.md | A_PLANIFIER | Maintenir l'arret de redaction et exposer la raison dans les recommandations. | La redaction finale n'est pas requise pour un retour correction obligatoire. |

## Erreurs

- Aucune.

## Warnings

- D-PILOTE-RES-002: EXT-GAP-001: ecart conditionnel P2
- D-PILOTE-RES-003: EXT-GAP-002: ecart conditionnel P1
- D-PILOTE-RES-003: EXT-GAP-003: ecart conditionnel P2
