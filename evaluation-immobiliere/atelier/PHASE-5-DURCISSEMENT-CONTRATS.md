# Phase 5 - durcissement des contrats

Objectif: ajuster les contrats v0 a partir des dossiers reels, sans modifier les seuils sur intuition.

## Etat actuel

- Statut: **EN_ATTENTE_SORTIES_PHASE_3**
- Les seuils actuels sont dans `evaluation-immobiliere/mvp/CONTRATS-DONNEES-V0.yaml`.
- Aucun dossier reel execute n'est encore disponible pour justifier un changement de seuil.

## Outil ajoute

```bash
python evaluation-immobiliere/outils/preparer_durcissement_contrats_v0.py --allow-empty
```

Quand les dossiers reels auront ete executes, lancer:

```bash
python evaluation-immobiliere/outils/preparer_durcissement_contrats_v0.py
```

Le rapport sera ecrit dans:

```text
evaluation-immobiliere/runtime_pilotes_reels/DURCISSEMENT-CONTRATS-PILOTES-REELS-V0.md
```

## Seuils a surveiller

- `max_comparable_distance_km_warning`
- `ajustement_sensible_montant_min`
- `confidence_min_warning`
- `valuation_inter_approach_max_delta_ratio`
- `date_vente_max_delta_days`
- `similarite_score_range`
- `status_decision`

## Regle de modification

- Ne pas changer un seuil sans evidence issue d'un dossier reel.
- Chaque changement de contrat doit avoir un test runtime associe.
- Les artefacts runtime doivent etre regeneres apres modification.
- Un dossier reel valide qui bloque a tort est un signal de durcissement ou d'assouplissement.
- Un dossier reel faible qui passe trop facilement est un signal de durcissement.

## Critere de sortie phase 5

- Les ecarts repetes sont classes par seuil ou regle.
- Les modifications de contrat retenues sont documentees.
- Les tests couvrent chaque changement.
- La simulation runtime reste deterministe apres regeneration.
