# Phase 3 — Rapport d'expert (livrable identique à un É.A.)

**Dépend de :** Phase 2
**Débloque :** la démo bureau É.A. ; livrable digne d'une signature.
**Effort :** M–L
**Objectif :** que le rapport exporté contienne mécaniquement les 16 éléments, la vraie grille d'ajustements, et que l'attestation soit véridique (inspection). Couvre **A9, A8**.

## Périmètre
**Inclus :** garantie des 16 éléments, grille au rapport, capture d'inspection, repli déterministe complet, export certifiable, mode dégradé honnête.
**Exclus :** mandats spéciaux (P4), multi-bureau (P5).

---

## Tâches

### T3.1 — Validation post-génération des 16 éléments (A9)
Aujourd'hui les 16 éléments sont une consigne au LLM, jamais vérifiée.
- `engine/report_check.py` : valider la présence des 16 éléments CUSPAP/NPP + 7 déclarations d'attestation + UMPP + valeur en chiffres ET lettres dans le rapport généré.
- Si un élément manque → marquer le rapport `INCOMPLET` (avertissement à l'É.A.), jamais livrer un rapport présenté comme complet alors qu'il ne l'est pas.
- **Fichiers :** `backend/engine/report_check.py`, `runtime.py` (post `generate_brouillon_rapport`).
- **DoD :** un rapport amputé d'un élément est détecté et signalé ; test par élément.

### T3.2 — La grille d'ajustements arrive dans le rapport (A9 + A2 au livrable)
`_build_rapport_prompt_v2` ne passe pas les ajustements.
- Passer la grille calculée (T2.1) au prompt **et** au gabarit ; remplir la table « Grille d'ajustements » (plus de `[ADJ]` vides, aucune invention).
- Pour le repli déterministe : injecter la grille réelle.
- **Fichiers :** `backend/engine/runtime.py` (`_build_rapport_prompt_v2`, `_generate_rapport_deterministic`), `templates/*`.
- **DoD :** le rapport (LLM et déterministe) contient la grille remplie avec données réelles.

### T3.3 — Capture d'inspection structurée (A8)
- Modèle d'inspection : date de visite, étendue (intérieur/extérieur), observations par composante (toiture, fondation, mécanique…), photos liées.
- UI de saisie (panneau Dossier ou checkpoint 1) ; alimente l'élément 14 (information sur l'inspection) et l'attestation.
- **Fichiers :** `src/components/panels/DossierPanel.tsx` (ou nouveau), `backend/api.py` (`/app/inspection`), schéma artefact `inspection.json`.
- **DoD :** une inspection saisie apparaît dans le rapport (élément 14) ; l'attestation reflète l'inspection réelle ; sans inspection, le rapport le signale.

### T3.4 — Repli déterministe complet (A9 mode dégradé)
Le repli actuel = stub 6 sections (« aucune inspection »).
- Réécrire `_generate_rapport_deterministic` pour produire les 16 éléments à partir des artefacts (sans LLM), en marquant clairement les sections nécessitant la prose de l'É.A.
- Bandeau explicite « mode dégradé — OpenAI indisponible » distinct du filigrane brouillon.
- **Fichiers :** `backend/engine/runtime.py`.
- **DoD :** LLM coupé → rapport structurellement complet (16 éléments) avec mentions « à rédiger par l'É.A. » ; jamais un faux rapport complet.

### T3.5 — Export certifiable (A9 export)
- Bloc signature complet : nom É.A., **n° de permis OEAQ**, date, espace signature/sceau ; pré-rempli depuis le compte authentifié.
- Au moment où l'É.A. valide (CHECKPOINT 4) et signe : retirer le filigrane « BROUILLON NON CERTIFIÉ » de façon contrôlée (action explicite, horodatée).
- **Fichiers :** `backend/engine/report_export.py`, `package.py`, `api.py` (validation/signature), `templates/*`.
- **DoD :** un rapport validé+signé produit un PDF sans filigrane brouillon, avec bloc signature complet ; l'action est tracée.

### T3.6 — Démo bureau (jalon)
- Passer un dossier résidentiel réel anonymisé de bout en bout ; mesurer le temps réel (remplacer les estimations de `DEMO-CHRONOMETRAGE.md`).
- **DoD :** dossier démo traverse 4 checkpoints → rapport conforme exporté ; chrono réel mesuré.

---

## Critère de done de la phase
Le rapport exporté contient les 16 éléments garantis, la grille d'ajustements réelle, l'inspection ; le mode dégradé est honnête ; un export signé sans filigrane existe ; la démo est chronométrée sur un vrai dossier.
