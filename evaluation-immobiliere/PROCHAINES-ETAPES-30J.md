# Prochaines etapes 30 jours - adaptation Aston vers evaluation immobiliere

## Objectif du mois

Passer de simulateur valide a premier runtime interne exploitable sur dossiers anonymises.

## Semaine 1 - Stabiliser le runtime

Etat: largement complete.

1. Lecture stricte de `PIPELINE-RUNTIME-ASTON-V0.yaml`: fait.
2. Validation des erreurs de parsing runtime: fait.
3. Check de coherence runtime/AgentConfig/observability: fait dans `outils/verifier_coherence_runtime_v0.py`.
4. Conventions d'artefacts par dossier: fait pour le runtime et l'API.

Livrable: runtime stable, artefacts par dossier, audit enrichi.

## Semaine 2 - Outillage metier minimal

Etat: complete pour v0, a durcir avec donnees reelles.

1. `search_comparables`: filtre les comparables sources et calcule un score simple.
2. `run_calculation`: mean, median et weighted_mean.
3. `validate_schema`: champs simples et chemins imbriques.
4. `append_audit_log`: journal JSONL horodate.
5. Tests unitaires outils/runtime: ajoutes.

Livrable: outils MVP v0 branches dans le runtime.

## Semaine 3 - API projet autonome

Etat: premiere version livree.

1. `POST /session`: cree une session locale.
2. `POST /start`: execute une fixture ou un dossier inline.
3. `GET /stream`: expose les evenements au format SSE.
4. Persistance locale: `runtime_sessions/<session_id>/`.

Livrable: execution par API, sans UI complete.

## Semaine 4 - Dossiers pilotes

Etat: prochaine priorite.

1. Preparer 2-3 dossiers anonymises reels.
2. Mapper les champs vers le format fixture v0.
3. Executer via API.
4. Comparer:
   - temps de traitement
   - qualite des artefacts
   - taux de blocage
   - corrections demandees par evaluateur

Livrable: rapport pilote et backlog v1.

## Priorite immediate

1. Ajouter un template de dossier anonymise reel dans `tests/fixtures/`.
2. Ajouter une petite UI ou page HTML de pilotage si l'API v0 suffit techniquement.
3. Remplacer les stubs metier par des connecteurs de donnees/comparables selon les sources disponibles.
