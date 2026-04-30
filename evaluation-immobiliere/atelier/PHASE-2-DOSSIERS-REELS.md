# Phase 2 - preparation des dossiers reels anonymises

Objectif: preparer 2-3 dossiers reels anonymises avant de les faire relire par des evaluateurs.

## Brouillons crees

- `evaluation-immobiliere/tests/fixtures/draft_dossier_reel_001.json`: cas simple attendu propre.
- `evaluation-immobiliere/tests/fixtures/draft_dossier_reel_002.json`: cas exploitable avec confiance ou donnees limitees.
- `evaluation-immobiliere/tests/fixtures/draft_dossier_reel_003.json`: cas avec anomalie ou revision conformite.

Ces fichiers restent volontairement en `draft_` pour ne pas etre inclus par `simuler_runtime_engine_v0.py`, qui charge seulement les fichiers `case_*.json`.
Ils sont aussi ignores par Git tant qu'ils restent en `draft_`, afin d'eviter de versionner un dossier reel en cours de nettoyage.

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
python evaluation-immobiliere/outils/valider_fixtures_v0.py --input evaluation-immobiliere/tests/fixtures/draft_dossier_reel_001.json --strict --report-out evaluation-immobiliere/atelier/RAPPORT-VALIDATION-DOSSIER-PILOTE.md
```

Repeter pour `draft_dossier_reel_002.json` et `draft_dossier_reel_003.json`.

## Activation pour le runtime

Quand un brouillon passe en strict avec 0 erreur:

1. Renommer `draft_dossier_reel_001.json` en `case_pilote_reel_001.json`.
2. Lancer la simulation runtime.
3. Regenerer le rapport pilote runtime.

```bash
python evaluation-immobiliere/outils/simuler_runtime_engine_v0.py
python evaluation-immobiliere/outils/analyser_integrite_runtime_v0.py
python evaluation-immobiliere/outils/generer_rapport_pilote_runtime_v0.py
```

## Critere de sortie phase 2

- 2-3 fichiers `case_pilote_reel_*.json` valides en mode strict.
- Aucun renseignement nominatif detecte.
- Chaque dossier produit un statut runtime interpretable.
- Les artefacts de sortie sont prets pour la revue evaluateur: `statut_sortie.json`, `rapport_non_conformites.json`, `recommandations_corrections.md`, et `brouillon_rapport.md` si le dossier n'est pas bloque.
