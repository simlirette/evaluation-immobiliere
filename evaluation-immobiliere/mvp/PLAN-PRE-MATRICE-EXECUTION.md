# Plan pré-matrice — étapes concrètes à exécuter maintenant

Objectif: avancer au maximum **sans attendre** les réponses des évaluateurs.

## Phase 1 — Cadrage technique (jour 1)

### 1.1 Geler le périmètre MVP provisoire
- Cas d'usage provisoire: résidentiel standard (maison unifamiliale).
- Sortie attendue: brouillon de rapport + checklist conformité + journal de sources.

**Livrable:** `SCOPE-MVP-PROVISOIRE.md`.

### 1.2 Définir le modèle de données minimal
- Entités: dossier, bien, comparable, ajustement, hypothèse, source, décision_humaine.
- Champs obligatoires d'audit alignés avec `AGENT-CONTRACTS-V0.yaml`.

**Livrable:** `DATA-MODEL-MINIMAL.yaml`.

## Phase 2 — Architecture d'exécution (jour 1-2)

### 2.1 Définir les I/O de pipeline inter-agents
- Contrat de passage d'un agent à l'autre en JSON/YAML.
- Validation de schéma pour éviter les sorties incomplètes.

**Livrable:** `PIPELINE-IO-SCHEMAS/`.

### 2.2 Définir la stratégie de traçabilité
- Règle: chaque conclusion doit référencer au moins une source.
- Format journal: `task_id`, `source_id`, `value`, `confidence`, `human_decision`, `rationale`.

**Livrable:** `TRACEABILITY-SPEC.md`.

## Phase 3 — Qualité et garde-fous (jour 2)

### 3.1 Transformer la checklist conformité en contrôles exécutables
- Règles bloquantes (sections manquantes, unité/date incohérente).
- Règles non-bloquantes (qualité rédactionnelle, lisibilité).

**Livrable:** `RULES-CONFORMITE-V0.yaml`.

### 3.2 Définir le workflow de validation humaine
- Qui valide quoi et à quel moment.
- Seuils de confiance qui forcent une validation explicite.

**Livrable:** `HUMAN-IN-THE-LOOP-WORKFLOW.md`.

## Phase 4 — Données et tests (jour 2-3)

### 4.1 Préparer un jeu de dossiers tests anonymisés
- 5 dossiers synthétiques: simple -> complexe.
- Inclure cas incomplets pour tester les erreurs.

**Livrable:** `tests/fixtures/`.

### 4.2 Définir les tests de non-régression métier
- Complétude des sections obligatoires.
- Présence des liens source -> conclusion.
- Statut final valide.

**Livrable:** `TEST-PLAN-V0.md`.

## Phase 5 — Démo interne avant workshop (jour 3-4)

### 5.1 Construire un “dry run” manuel
- Injecter un dossier test.
- Produire une sortie de chaque agent (même partiellement manuelle).
- Vérifier la chaîne complète et les points de friction.

**Livrable:** `DEMO-DRY-RUN-REPORT.md`.

### 5.2 Instrumenter les métriques de base
- Temps par étape.
- Nombre de corrections humaines.
- Nombre de non-conformités bloquantes.

**Livrable:** `METRICS-BASELINE.md`.

---

## Ordre d'exécution recommandé (si tu me donnes le GO)
1. `SCOPE-MVP-PROVISOIRE.md`
2. `DATA-MODEL-MINIMAL.yaml`
3. `TRACEABILITY-SPEC.md`
4. `RULES-CONFORMITE-V0.yaml`
5. `TEST-PLAN-V0.md`

## Définition de “prêt pour matrice”
On est prêt quand:
- les contrats I/O sont stables,
- les règles bloquantes sont explicitement écrites,
- un dry run de bout en bout est réalisable sur 1 dossier test,
- les métriques baseline sont capturées.
