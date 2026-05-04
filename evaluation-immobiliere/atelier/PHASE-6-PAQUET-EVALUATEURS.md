# Phase 6 - paquet evaluateurs

Objectif: preparer le materiel a remettre aux evaluateurs sans saisir de reponses a leur place.

## Etat actuel

- Statut: **EN_ATTENTE_DOSSIERS_REELS**
- Les phases 3, 4 et 5 sont outillees mais en attente des dossiers reels anonymises.
- Le paquet peut deja etre genere en mode attente.
- Aucune reponse evaluateur ne doit etre saisie pour rendre le paquet "pret".

## Outil ajoute

```bash
python evaluation-immobiliere/outils/preparer_paquet_evaluateurs_v0.py --allow-empty
```

Le paquet local est ecrit dans:

```text
evaluation-immobiliere/paquets_evaluateurs/v0/
```

Ce repertoire est ignore par Git.

## Contenu du paquet

- `PAQUET-EVALUATEURS-V0.md`: index du paquet.
- `CHECKLIST-ENVOI-EVALUATEURS.md`: controles avant partage.
- `REPONSES-EVALUATEURS-A-REMPLIR.csv`: copie locale du gabarit a dupliquer par evaluateur.
- `MANIFESTE-CAS-PILOTES.csv`: liste des dossiers et artefacts runtime quand ils existent.

## Commande apres execution des dossiers reels

```bash
python evaluation-immobiliere/outils/preparer_paquet_evaluateurs_v0.py
python evaluation-immobiliere/outils/verifier_point_arret_reponses_v0.py
python evaluation-immobiliere/outils/verifier_campagne_terrain_reelle_v1.py --fixtures-dir <PHASE_H_REAL_CASES_DIR>
```

## Critere de sortie phase 6

- Les dossiers reels selectionnes sont listes dans le manifeste.
- Les artefacts a relire sont presents.
- La revue interne phase 4 est terminee.
- Les decisions de contrat phase 5 sont documentees.
- Le CSV de reponses est pret a etre duplique par evaluateur.
- Aucune reponse evaluateur n'est inventee ou pre-remplie.
- Le gate Phase H retourne `PRET_A_RECEVOIR_REPONSES_TERRAIN`, pas seulement une readiness synthetique.
