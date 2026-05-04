# Phase 4 - revue interne avant evaluateurs

Objectif: retirer les problemes evidents avant de demander du temps aux evaluateurs.

## Etat actuel

- Statut: **EN_ATTENTE_EXECUTION_PHASE_3**
- La revue interne depend des artefacts produits dans `evaluation-immobiliere/runtime_pilotes_reels/`.
- Aucun dossier reel execute n'est encore disponible.
- Le gate Phase H accepte cet etat seulement tant qu'aucun `case_pilote_reel_*.json` actif n'existe.

## Outil ajoute

```bash
python evaluation-immobiliere/outils/preparer_revue_interne_pilotes_v0.py --allow-empty
```

Quand la phase 3 aura produit `runtime_summary.json`, la meme commande sans `--allow-empty` generera:

```text
evaluation-immobiliere/runtime_pilotes_reels/REVUE-INTERNE-PILOTES-REELS-V0.md
```

## Ce que la revue verifie

- Presence des artefacts obligatoires:
  - `compliance-qa.statut_sortie.json`
  - `compliance-qa.rapport_non_conformites.json`
  - `compliance-qa.recommandations_corrections.md`
  - `redaction.brouillon_rapport.md` si le dossier n'est pas bloque.
- Blocages runtime qui doivent etre corriges ou expliques.
- Warnings qui doivent devenir des questions metier ou des points de validation.
- Classement de chaque dossier:
  - `A_CORRIGER_AVANT_EVALUATEURS`
  - `A_CLARIFIER_INTERNE`
  - `PRET_REVUE_EVALUATEUR`

## Critere de sortie phase 4

- Aucun artefact obligatoire manquant.
- Aucun blocage technique non explique.
- Les warnings restants sont transformes en questions claires pour les evaluateurs.
- Les dossiers prets sont selectionnes pour la revue evaluateur.
- `verifier_campagne_terrain_reelle_v1.py` ne doit pas retourner `NO_GO_CAMPAGNE_TERRAIN_REELLE` avant preparation du paquet evaluateurs.
