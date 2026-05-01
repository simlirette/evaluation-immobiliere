# CRITERES ACCEPTATION METIER V1

_As-of date: 2026-04-30 (UTC)_

## Objectif
Fixer les seuils de passage Phase H vers industrialisation CI/CD sans confondre preparation et validation terrain signee.

Statut courant: **EN_ATTENTE_REPONSES_TERRAIN**.

## Criteres

| Critere | Courant | Cible | Statut |
|---|---:|---:|---|
| Panel evaluateurs | 0 | >= 2 | A_TRAITER |
| Couverture dossiers | 0 | >= 3 | A_TRAITER |
| Desaccords statut | 0 | 0 | OK |
| Backlog P0 metier | 0 | 0 | OK |
| Saisie valide | PRET_A_RECEVOIR_REPONSES | != A_CORRIGER | OK |
| Signature metier | A_SIGNER | SIGNE | A_TRAITER |

## Regles Go/No-Go

- **GO**: tous les criteres sont OK et la signature metier est obtenue.
- **GO_CONDITIONNEL**: aucun P0 metier ouvert, mais des P1/P2 restent planifies.
- **NO_GO_METIER**: desaccord statut non resolu, P0 metier ouvert ou rejet evaluateur majeur.
- **EN_ATTENTE_REPONSES_TERRAIN**: aucune reponse evaluateur exploitable; ne pas conclure.

## Owners de signature

| Role | Owner | Statut |
|---|---|---|
| Lead Metier | A nommer | A_SIGNER |
| Product | A nommer | A_SIGNER |
| QA/Platform | A nommer | A_SIGNER |
