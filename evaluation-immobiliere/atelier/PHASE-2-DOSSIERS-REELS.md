# Phase 2 - preparation des dossiers reels anonymises

Objectif: preparer 2-3 dossiers reels anonymises avant de les faire relire par des evaluateurs, sans les versionner dans le repo actif.

## Emplacement autorise

- Source de verite: dossier hors repo actif, par exemple `<PHASE_H_REAL_CASES_DIR>`.
- Repertoire local tolere pour execution controlee: `evaluation-immobiliere/tests/fixtures_external/`, ignore par Git sauf fixtures synthetiques whitelistees.
- Repertoire interdit: `evaluation-immobiliere/tests/fixtures/` pour tout `draft_dossier_reel_*.json` ou `case_pilote_reel_*.json`.

Les fichiers restent en `draft_` tant que l'anonymisation n'est pas signee. Seuls les fichiers `case_pilote_reel_*.json` valides peuvent alimenter le runtime reel, et ils doivent rester hors versionnement.

## Regles de remplissage

- Remplacer les adresses precises par une zone ou un secteur.
- Remplacer les noms de clients, proprietaires, firmes et evaluateurs par des identifiants internes.
- Conserver les dates utiles a l'evaluation, mais retirer les dates inutiles au test.
- Conserver les prix, surfaces, distances et ajustements necessaires au calcul.
- Donner un `source_id` a chaque comparable, ajustement, hypothese et evenement de timeline.
- Garder les unites coherentes entre le sujet et les comparables: `pi2` ou `m2`.
- Mettre `validation_humaine: true` pour tout ajustement sensible deja valide.
- Ne jamais inscrire de courriel, numero de telephone ou adresse civique complete.

## Validation d'un brouillon

```bash
python evaluation-immobiliere/outils/valider_fixtures_v0.py --input <PHASE_H_REAL_CASES_DIR>/draft_dossier_reel_001.json --strict --report-out evaluation-immobiliere/runtime_pilotes_reels/validation_dossiers_reels.md
python evaluation-immobiliere/outils/auditer_anonymisation_v0.py --root <PHASE_H_REAL_CASES_DIR>
```

Repeter pour `draft_dossier_reel_002.json` et `draft_dossier_reel_003.json`. Un dossier qui echoue l'audit anonymisation ne doit pas etre renomme en `case_pilote_reel_*.json`.

## Activation pour le runtime

Quand un brouillon passe en strict avec 0 erreur:

1. Renommer `draft_dossier_reel_001.json` en `case_pilote_reel_001.json` seulement apres validation stricte et audit anonymisation OK.
2. Executer l'ingestion/normalisation.
3. Lancer le runtime pilotes reels.
4. Regenerer les gates Phase H.

```bash
python evaluation-immobiliere/outils/preparer_ingestion_pdf_v0.py --fixtures-dir <PHASE_H_REAL_CASES_DIR>
python evaluation-immobiliere/outils/executer_dossiers_pilotes_reels_v0.py --fixtures-dir <PHASE_H_REAL_CASES_DIR> --fail-on-contract-errors
python evaluation-immobiliere/outils/verifier_campagne_terrain_reelle_v1.py --fixtures-dir <PHASE_H_REAL_CASES_DIR>
```

## Critere de sortie phase 2

- 2-3 fichiers `case_pilote_reel_*.json` valides en mode strict.
- Aucun renseignement nominatif detecte.
- Chaque dossier produit un statut runtime interpretable.
- Les artefacts de sortie sont prets pour la revue evaluateur: `statut_sortie.json`, `rapport_non_conformites.json`, `recommandations_corrections.md`, et `brouillon_rapport.md` si le dossier n'est pas bloque.
