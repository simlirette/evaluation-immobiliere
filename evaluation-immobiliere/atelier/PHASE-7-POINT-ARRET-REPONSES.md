# Phase 7 - point d'arret avant reponses evaluateurs

Objectif: arreter le travail juste avant la saisie des reponses evaluateurs, sans inventer ni pre-remplir de donnees.

## Etat actuel

- Statut: **EN_ATTENTE_AVANT_REPONSES**
- `REPONSES-EVALUATEURS.csv` ne contient que l'en-tete.
- `RAPPORT-VALIDATION-REPONSES.md` est `PRET_A_RECEVOIR`.
- Le paquet evaluateurs est encore `EN_ATTENTE_DOSSIERS_REELS`, donc aucune reponse ne doit etre saisie.

## Outil ajoute

```bash
python evaluation-immobiliere/outils/verifier_point_arret_reponses_v0.py --allow-waiting
```

Le rapport local est ecrit dans:

```text
evaluation-immobiliere/paquets_evaluateurs/v0/POINT-ARRET-REPONSES-EVALUATEURS-V0.md
```

## Regles de blocage

- Ne pas inventer de `respondant_id`.
- Ne pas pre-remplir les notes de 1 a 5.
- Ne pas pre-remplir les champs `oui/non`.
- Ne pas ecrire de commentaires a la place des evaluateurs.
- Attendre les vraies reponses avant de modifier `REPONSES-EVALUATEURS.csv`.

## Quand les reponses arrivent

1. Ajouter les lignes recues dans `REPONSES-EVALUATEURS.csv`.
2. Lancer:

```bash
python evaluation-immobiliere/outils/valider_reponses_evaluateurs.py
python evaluation-immobiliere/outils/compiler_reponses_evaluateurs.py
python evaluation-immobiliere/outils/prioriser_mvp.py
```

## Critere de sortie phase 7

- Le CSV consolide est vide ou contient seulement des lignes gabarit inactives.
- Le rapport de validation est `PRET_A_RECEVOIR`.
- Le paquet evaluateurs est documente.
- Le projet attend explicitement les reponses externes.
