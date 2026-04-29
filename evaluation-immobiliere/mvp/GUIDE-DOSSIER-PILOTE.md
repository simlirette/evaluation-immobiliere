# Guide dossier pilote anonymise

Objectif: convertir 2-3 dossiers reels en entrees JSON compatibles runtime v0, sans information nominative.

## Regles d'anonymisation

- Remplacer toute adresse precise par une zone ou un secteur.
- Remplacer les noms de personnes, firmes et clients par des identifiants internes.
- Conserver seulement les dates utiles a l'evaluation.
- Conserver les prix, surfaces et ajustements si leur usage est necessaire au test.
- Chaque fait utilise doit avoir un `source_id`.

## Champs minimum

- `dossier_id`
- `date_reference`
- `surface.value`
- `surface.unit`
- `comparables[].comparable_id`
- `comparables[].prix_vente`
- `comparables[].source_id`
- `ajustements[].montant`
- `ajustements[].source_id`
- `ajustements[].validation_humaine`
- `confidence`

## Gabarit

Copier `tests/fixtures/template_dossier_anonymise.json`, remplir les champs, puis lancer:

```bash
python evaluation-immobiliere/outils/lancer_api_v0.py
python evaluation-immobiliere/outils/demo_api_v0.py --fixture votre_fixture.json
```

Pour une fixture pilote versionnee, nommer le fichier avec le prefixe `case_` afin que `simuler_runtime_engine_v0.py` l'inclue automatiquement.

## Revue evaluateur

Apres execution, verifier en priorite:

- `compliance-qa.statut_sortie.json`
- `compliance-qa.rapport_non_conformites.json`
- `compliance-qa.recommandations_corrections.md`
- `redaction.brouillon_rapport.md` si le dossier n'est pas bloque

Les ecarts observes doivent alimenter le backlog MVP v1.
