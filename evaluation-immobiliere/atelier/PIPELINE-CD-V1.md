# PIPELINE CD V1

_As-of date: 2026-05-01 (UTC)_

## Objectif
Definir les promotions dev -> staging -> prod avec approbations et preuves minimales.

Statut Phase H: **GO_PROD_PREPARATION**. La preparation prod est autorisee; le go live reste bloque jusqu'au dress rehearsal staging.

## Environnements

| Environnement | Declencheur | Gates requis | Approbation | Statut actuel |
|---|---|---|---|---|
| dev | Pull request ou branche de travail | CI complet | Maintainer technique | Actif |
| staging | Merge `main` ou tag release-candidate | CI complet + docs Phase I | Product + Platform | A preparer |
| prod | Release approuvee | Phase H signee + ecarts fermes + Phase J homologuee | Lead Metier + Product + Platform | A preparer |

## Promotion

1. Dev: executer CI, tests unitaires, contrats, runtime smoke et gates ops.
2. Staging: figer un tag release-candidate, regenerer preuves, verifier compatibilite session/artefacts.
3. Prod: preparer seulement apres signature metier et fermeture d'ecarts; autoriser le go live apres dress rehearsal staging et runbook rollback relu.

## Artefacts de release

| Artefact | Source | Role |
|---|---|---|
| Commit SHA | GitHub | Version applicative |
| Tag release | GitHub | Point de rollback |
| Contrats YAML/JSON | `mvp/`, `schemas/`, `atelier/` | Compatibilite donnees |
| Rapports Phase G/H/I/J | `atelier/` | Preuves go/no-go |
| Workflow CI | `.github/workflows/validation.yml` | Gate automatisable |

## Gates de promotion

- CI vert sur le commit exact a promouvoir.
- Aucun P0/P1/P2 metier ouvert dans la matrice d'ecarts evaluateurs.
- Aucun `A_CORRIGER` dans les gates ops professionnels.
- Rollback teste ou simule avant staging, obligatoire avant prod.
