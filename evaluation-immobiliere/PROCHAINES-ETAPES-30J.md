# Prochaines étapes (30 jours) — adaptation Aston -> évaluation immobilière

## Objectif du mois
Passer de "simulateur validé" à "premier runtime interne exploitable sur dossiers anonymisés".

## Semaine 1 — Stabiliser le runtime
1. Brancher la lecture stricte de `PIPELINE-RUNTIME-ASTON-V0.yaml` (déjà fait) et ajouter validation des erreurs de parsing.
2. Ajouter un check de cohérence runtime dans un script de vérification unique.
3. Nettoyer le format des artefacts runtime (`.json.json` -> extension unique cohérente).

**Livrable:** runtime stable + conventions d'artefacts.

## Semaine 2 — Outillage métier minimal
1. Implémenter stubs outillés pour:
   - `search_comparables`
   - `run_calculation`
   - `validate_schema`
   - `append_audit_log`
2. Brancher ces stubs dans le runtime (au lieu d'écritures "dummy" seulement).
3. Ajouter tests unitaires pour ces outils.

**Livrable:** outils métier MVP v0 testés.

## Semaine 3 — API projet autonome
1. Créer une API locale minimale:
   - `POST /session`
   - `POST /start`
   - `GET /stream`
2. Exposer les events runtime existants (`step_start`, `step_done`, `blocking_detected`).
3. Persister les artefacts par dossier.

**Livrable:** exécution par API (sans UI complète).

## Semaine 4 — Dossiers pilotes
1. Préparer 2-3 dossiers anonymisés réels.
2. Exécuter pipeline complet et comparer:
   - temps de traitement
   - qualité de sortie
   - taux de blocage
3. Documenter écarts et corrections prioritaires.

**Livrable:** rapport pilote + backlog priorisé v1.

---

## Priorité immédiate (ordre recommandé)
1. Normaliser le format d'artefacts runtime.
2. Implémenter `append_audit_log` (traçabilité = critique conformité).
3. Ajouter un mode "strict" qui refuse toute sortie sans source.

## Définition de succès (fin 30 jours)
- Pipeline exécutable via API projet sur dossiers anonymisés.
- Sorties bloquantes correctement stoppées.
- Traçabilité complète présente dans les artefacts.
- Feedback évaluateur disponible sur au moins 1 cycle pilote.
