# Phase H - campagne terrain reelle v1

Objectif: demarrer la campagne terrain sur dossiers reels anonymises sans introduire de donnees sensibles dans le repo actif et sans inventer de reponses evaluateurs.

## Statut courant

- Statut: **EN_ATTENTE_ENTREES_TERRAIN_REELLES**
- Le runtime, les contrats, les revues synthetiques et la release candidate restent des preuves de preparation.
- La Phase H reelle ne commence que lorsque des dossiers anonymises valides sont fournis hors repo actif, ou dans `tests/fixtures_external/` ignore par Git pour une execution locale controlee.

## Flux strict

1. Validation anonymisation
   - Source de verite: dossier hors repo actif, par exemple une variable locale `PHASE_H_REAL_CASES_DIR`.
   - Aucun nom, courriel, telephone, adresse civique complete, code postal precis ou chemin utilisateur local.
   - Commandes:

```bash
python evaluation-immobiliere/outils/valider_fixtures_v0.py --input <PHASE_H_REAL_CASES_DIR>/case_pilote_reel_001.json --strict --report-out evaluation-immobiliere/runtime_pilotes_reels/validation_dossiers_reels.md
python evaluation-immobiliere/outils/auditer_anonymisation_v0.py --root <PHASE_H_REAL_CASES_DIR>
```

2. Ingestion et normalisation
   - Normaliser seulement les sources anonymisees.
   - Les textes extraits et traces restent dans `runtime_pilotes_reels/`, ignore par Git.

```bash
python evaluation-immobiliere/outils/preparer_ingestion_pdf_v0.py --fixtures-dir <PHASE_H_REAL_CASES_DIR>
```

3. Execution runtime pilotes reels
   - Le runtime refuse les fixtures qui echouent validation stricte ou audit anonymisation.

```bash
python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py --fixtures-dir <PHASE_H_REAL_CASES_DIR> --fail-on-contract-errors
```

4. Revue interne
   - Corriger les artefacts manquants et transformer les warnings restants en questions metier.

```bash
python evaluation-immobiliere/outils/preparer_revue_interne_pilotes_v0.py
```

5. Paquet evaluateurs
   - Generer le paquet uniquement apres runtime et revue interne.
   - Les CSV restent des gabarits vides a dupliquer par evaluateur.

```bash
python evaluation-immobiliere/outils/preparer_paquet_evaluateurs_v0.py
python evaluation-immobiliere/outils/valider_paquet_evaluateurs_v0.py
```

6. Point d'arret avant reponses
   - Ne pas saisir de `respondant_id`, score, decision ou commentaire tant que les reponses terrain ne sont pas recues.

```bash
python evaluation-immobiliere/outils/verifier_point_arret_reponses_v0.py
python evaluation-immobiliere/outils/verifier_campagne_terrain_reelle_v1.py
```

## Gate Phase H

Le gate `verifier_campagne_terrain_reelle_v1.py` accepte deux etats seulement:

- **EN_ATTENTE_ENTREES_TERRAIN_REELLES**: aucun `case_pilote_reel_*.json` actif; la CI prouve que la Phase H ne simule pas de terrain.
- **PRET_A_RECEVOIR_REPONSES_TERRAIN**: dossiers actifs valides, anonymises, normalises, executes, revus en interne, paquet pret, CSV reponses vide.

Tout autre etat est **NO_GO_CAMPAGNE_TERRAIN_REELLE**.

## Interdits

- Ne pas committer de dossiers reels, meme anonymises.
- Ne pas placer de `case_pilote_reel_*.json` dans `tests/fixtures/`.
- Ne pas inventer de reponses evaluateurs pour fermer la Phase H.
- Ne pas promouvoir en production sur la seule base des revues synthetiques ou fixtures externes.
