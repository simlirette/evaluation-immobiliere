# Rapport ecarts evaluateurs externes V1

_As-of date: 2026-05-04 (UTC)_

## Decision

- Gate: **GO_CONDITIONNEL_ECARTS_EVALUATEURS**
- Source: `evaluation-immobiliere/tests/fixtures_external/homologation_evaluateurs_v1.json`
- Ecarts P0: **0**
- Ecarts P1: **1**
- Ecarts P2: **2**
- Desaccords statut: **0**

## Synthese des ecarts

| Priorite | Dossier | Cible | Statut | Recommandation | Evidence |
|---|---|---|---|---|---|
| P1 | D-PILOTE-RES-003 | comps-market.justifications_comparables.json | A_TRAITER_AVANT_GO | Fermer le blocage de conformite ou documenter son acceptation metier. | Le dossier pilote revision conformite contient un blocage temporel. |
| P2 | D-PILOTE-RES-002 | compliance-qa.recommandations_corrections.md | A_PLANIFIER | Ajouter une phrase de reserve metier avant signature finale. | Le dossier reste en BROUILLON et non en PRET_REVISION_FINALE. |
| P2 | D-PILOTE-RES-003 | redaction.brouillon_rapport.md | A_PLANIFIER | Maintenir l'arret de redaction et exposer la raison dans les recommandations. | La redaction finale n'est pas requise pour un retour correction obligatoire. |

## Regles de sortie

- P0, rejet evaluateur ou desaccord statut: NO_GO revues externes.
- P1/P2 documentes sans desaccord statut: GO conditionnel, correction a planifier avant signature metier finale.
- Aucun ecart et couverture minimale atteinte: GO revues externes.
