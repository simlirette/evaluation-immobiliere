# Phase 0 — Assainissement, conformité & sécurité immédiate

**Dépend de :** —
**Débloque :** tout usage réel sûr ; pré-requis premier client.
**Effort :** S–M
**Objectif :** retirer ce qui est non conforme ou dangereux *aujourd'hui*, sans nouvelles fonctionnalités. Rendre le système sûr à montrer/utiliser.

## Périmètre
**Inclus :** nettoyage contenu non OEAQ dans les livrables, fail-closed sécurité, conflit déterministe, lettre unique, application migrations prod, lancement Loi 25.
**Exclus :** RAG (P1), grille d'ajustements (P2), refactor (P6).

---

## Tâches

### T0.1 — Sortir le contenu non professionnel des livrables (A11, partie livrable)
Les ~25 sections « score d'investissement / qualité de vie / risque / climat / criminalité / projection 5 ans / ratio prix-loyer » sont injectées dans `amu_analyse.md` (`runtime.py` ~l.1506-1558) et risquent de fuiter dans le rapport.
- Retirer ces sections de `amu_analyse.md` : ne garder que zonage, CPTAQ, patrimoine, zone inondable, démographie/marché **pertinents à l'AMU**.
- Conserver le calcul en interne (pour l'UI marché si désiré) mais derrière un flag `INCLUDE_INVESTMENT_CONTEXT` (défaut off) — jamais dans les artefacts du rapport.
- **Fichiers :** `backend/engine/runtime.py` (bloc `amu_analyse.md`), éventuellement `data_enrichment.py` (gating de l'injection dans `enrich_case`).
- **DoD :** `amu_analyse.md` ne contient aucune section investissement/QdV/risque/climat ; un test vérifie l'absence de ces titres.

### T0.2 — Conflit d'intérêts déterministe (constat « conflit »)
Aujourd'hui `conflit_interets.json` = `conflit_detecte: False` en dur, détection réelle seulement si LLM présent.
- Implémenter `engine/compliance.py::check_conflit_interets(case)` déterministe : signaux structurés (lien déclaré commanditaire/évaluateur, mandat conditionnel à une valeur cible, intérêt dans la propriété) → `conflit_detecte` + motif.
- LLM en surcouche optionnelle (formulation), jamais seule source.
- **Fichiers :** `backend/engine/compliance.py`, `runtime.py` (bloc conflit + gate ligne ~1848).
- **DoD :** sans `OPENAI_API_KEY`, un cas avec lien déclaré → `conflit_detecte: True` + pipeline stoppé ; test unitaire par signal.

### T0.3 — Lettre de mandat : un seul chemin (constat « lettre »)
Garder le gabarit Jinja2 fixe (`templates/lettre_mandat_residentiels.md`, endpoint `/app/mandat/lettre`), supprimer l'artefact pipeline LLM redondant.
- Retirer `lettre_mandat.md` de la cible d'enrichissement LLM (`_LLM_TEXT_FIELD_BY_ARTIFACT`) et le générer par le template Jinja (ou retirer l'étape du pipeline si l'endpoint suffit).
- Ajouter des gabarits Jinja par type de mandat manquants (commercial, succession…) ou paramétrer le type de valeur (valeur marchande / JVM / valeur réelle).
- **Fichiers :** `runtime.py`, `backend/templates/`, `api.py` (`app_*` lettre).
- **DoD :** une seule source de lettre ; aucun placeholder non rempli quand les champs sont fournis ; type de valeur correct selon le mandat.

### T0.4 — Fail-closed sécurité prod (A7 fail-closed + CORS)
`_auth_context` retourne `authorized:True (local_dev)` si `EVAL_RUNTIME_API_TOKEN` absent → runtime ouvert.
- En prod (variable `ENV=production` ou `EVAL_RUNTIME_REQUIRE_AUTH=1`) : token absent → **refuser le démarrage** ou répondre 503 sur les routes privilégiées.
- Vérifier `EVAL_RUNTIME_ALLOWED_ORIGIN` ≠ `*` en prod (déjà checké en readiness → rendre bloquant).
- **Fichiers :** `backend/api.py` (`_auth_context`, `_send_cors_headers`, démarrage).
- **DoD :** déploiement sans token → échec explicite ; test : route privilégiée sans token en mode prod → 401/503.

### T0.5 — Appliquer les migrations Supabase en prod (A7 migrations)
Migrations 002-005 non appliquées (state.md, open issue).
- Appliquer 002 (sessions), 003 (profiles/roles), 004 (sirf_cache), 005 (storage RLS + rapport_versions) sur l'instance prod.
- Vérifier RLS active et politiques en place (tests d'accès manuels : un user ne voit pas les dossiers d'un autre).
- **Fichiers :** `supabase/migrations/*` (déjà écrits), procédure dans `DEPLOYMENT.md`.
- **DoD :** `supabase db push` prod OK ; smoke test RLS par utilisateur.
- **Note :** isolation **par bureau** = Phase 5 (le data model n'existe pas encore).

### T0.6 — Conformité Loi 25 (A7 Loi 25) — non technique, à démarrer maintenant
- Inventaire des données personnelles collectées (adresses, propriétaires, valeurs, comparables nominatifs SIRF vendeur/acheteur !).
- Politique de rétention + politique d'accès ; consultation avocat (même rendez-vous que §6.5 OEAQ).
- **Attention SIRF :** `registre_foncier.py` extrait `vendeur`/`acheteur` (noms) et les met en cache (disque + Supabase) → données personnelles à encadrer/masquer.
- **Fichiers :** `docs/CONFORMITE-LOI25.md` (nouveau), masquage noms dans `registre_foncier.py` si non requis.
- **DoD :** document Loi 25 rédigé ; noms SIRF masqués/encadrés ; avis juridique obtenu avant premier client.

---

## Dépendances externes à lancer en parallèle
- Rendez-vous avocat (Loi 25 + §6.5) — bloque le premier client, pas la démo.

## Critère de done de la phase
Aucun contenu non professionnel dans les artefacts livrés ; conflit détecté sans LLM ; une seule lettre fiable ; runtime fail-closed en prod ; migrations appliquées ; chantier Loi 25 ouvert avec masquage PII SIRF.
