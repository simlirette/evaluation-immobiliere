# Paquet V1 pre-evaluateur agree

_As-of date: 2026-05-04 (UTC)_

## Synthese

- Statut paquet: **PRET_REVUE_EVALUATEUR_AGREE**
- Cible: **V1_PRE_EVALUATEUR**
- Validation terrain reelle: **NON_REVENDIQUEE**
- Reponses evaluateur externe incluses: **False**
- Dossier demo: **D-001**
- Statut runtime: **PRET_REVISION_FINALE**
- Fixture source: `case_nominal.json`
- Artefacts: **17**

## Fichiers du paquet

| Fichier | Role |
|---|---|
| `RAPPORT-EXEMPLE-V1.md` | Rapport de demonstration a lire avant la revue. |
| `QUESTIONS-REVUE-EVALUATEUR.md` | Questions ouvertes a faire trancher par l'evaluateur. |
| `GRILLE-REVUE-EVALUATEUR.csv` | Grille vide de collecte, sans reponse inventee. |
| `LIMITES-V1-PRE-EVALUATEUR.md` | Limites et hypotheses a presenter explicitement. |
| `DEMO-MANIFEST-V1.json` | Manifest machine-readable du paquet. |

## Parcours demo

1. Demarrer l'API locale avec `python evaluation-immobiliere/outils/lancer_api_v0.py`.
2. Ouvrir `/review/ui` pour la revue evaluateur.
3. Ouvrir le dossier demo et inspecter les artefacts.
4. Lire le rapport exemple et remplir la grille avec l'evaluateur.

## Regle de portee

Ce paquet sert a presenter une V1 pre-evaluateur. Il ne remplace pas une validation terrain reelle.
Il ne contient aucune reponse d'evaluateur agree et ne doit pas en simuler.
