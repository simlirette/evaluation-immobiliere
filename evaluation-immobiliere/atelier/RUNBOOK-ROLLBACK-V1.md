# RUNBOOK ROLLBACK V1

_As-of date: 2026-05-01 (UTC)_

## Objectif
Fournir une procedure de retour arriere applicative, contrats et donnees sessionnelles.

Contexte Phase H: **EN_ATTENTE_ENTREES_TERRAIN_REELLES**. Aucun rollback prod reel n'est execute tant que la prod n'est pas ouverte.

## Declencheurs

| Declencheur | Niveau | Action | Owner |
|---|---|---|---|
| Regression CI apres merge | dev/main | Revert PR ou hotfix | Platform |
| Contrat de donnees incompatible | staging/prod | Restaurer version contrat + bloquer promotion | QA/Platform |
| Erreur runtime critique | staging/prod | Revenir au tag precedent | Runtime |
| Rejet metier terrain | staging/prod | Suspendre release + ouvrir backlog P0 | Product + Lead Metier |

## Procedure applicative

1. Identifier le commit ou tag sain precedent.
2. Geler toute promotion en cours.
3. Creer un revert non destructif ou rediriger le deploiement vers le tag sain.
4. Reexecuter CI complet et gates ops.
5. Documenter incident, impact, decision et owner.

## Procedure contrats et donnees

- Ne jamais modifier retroactivement un artefact de session deja produit.
- Versionner tout changement de schema/contrat avec compatibilite explicite.
- Si migration incomplete: bloquer reprise session, conserver lecture seule, ouvrir correction P0.
- Les snapshots de connaissance et index d'artefacts doivent rester correlables au `run_id` initial.

## Checklist de sortie rollback

- [ ] CI vert sur version restauree.
- [ ] Aucun gate ops en `A_CORRIGER`.
- [ ] Sessions/artefacts existants lisibles ou explicitement bloques avec message utilisateur.
- [ ] Product + Platform informes.
- [ ] Post-mortem cree avant nouvelle promotion.
