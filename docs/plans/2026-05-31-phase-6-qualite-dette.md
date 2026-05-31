# Phase 6 — Qualité, dette technique & observabilité (transverse)

**Dépend de :** transverse (jalons à la fin de P2 et P3 ; à exécuter en continu)
**Débloque :** maintenabilité, vélocité, fiabilité de toutes les autres phases.
**Effort :** M
**Objectif :** réduire la dette qui ralentit/menace le reste. Couvre **A11 (élagage module), A12 (api.py, dead code, unification), A13 (CI/E2E)**.

## Périmètre
**Inclus :** découpe `api.py`, élagage `data_enrichment`, CI durcie + E2E, dead code, observabilité.
**Exclus :** nouvelles fonctionnalités.

---

## Tâches

### T6.1 — Découper `api.py` (256 Ko) (A12)
- Extraire par domaine : routing/HTTP, auth/RBAC, dossiers, checkpoints, rapport, assistant, mandat.
- Conserver l'API publique (routes inchangées) ; tests de non-régression sur chaque route.
- **Fichiers :** `backend/api.py` → `backend/api/` (package modulaire).
- **DoD :** aucun module > ~30 Ko ; toutes les routes répondent identiquement ; tests verts.

### T6.2 — Élaguer `data_enrichment.py` (5 353 l.) au périmètre OEAQ (A11)
- Garder : zonage→AMU, rôle municipal, SCHL conditionnel locatif, géocodage, Infolot/MAMH/SIRF.
- Sortir/retirer : scores investissement/QdV/risque, climat, criminalité, projection 5 ans, ratio prix-loyer (déjà hors rapport en P0 ; ici on les isole dans un module optionnel ou on les supprime).
- Retirer les stubs WDS morts.
- **Fichiers :** `backend/engine/data_enrichment.py` → cœur + `enrichment_optionnel.py` (ou suppression).
- **DoD :** `data_enrichment` cœur ne contient que les sources du workflow OEAQ ; LOC réduites significativement ; tests verts.

### T6.3 — Unification des calculs TS/Python (A12 calculs) — *jalon avec P2.2*
- Finaliser la source de vérité unique (moteur Python) ; déprécier/retirer les calculs frontend redondants de la **valeur finale** ; documenter ce que le frontend calcule encore (affichage seulement).
- **DoD :** la valeur finale a une seule implémentation ; doc à jour.

### T6.4 — CI durcie + E2E (A13)
- Mocker les appels réseau des tests (`data_enrichment`, SIRF, Infolot) → tests hermétiques.
- Ajouter un E2E « happy path » : runtime + frontend, dossier fixture → 4 checkpoints → rapport.
- Optionnel : gate de déploiement (lint/test/build verts requis avant deploy).
- **Fichiers :** `.github/workflows/ci.yml`, `backend/tests/` (fixtures réseau), `tests/e2e/`.
- **DoD :** CI sans accès réseau ; E2E vert ; flakiness éliminée.

### T6.5 — Dead code & cohérence (A12)
- Supprimer `ThemeToggle.tsx`, `TabBar.tsx` (zéro imports) et tout mort détecté ; standardiser les icônes.
- **DoD :** aucun import mort ; build propre.

### T6.6 — Observabilité runtime
- Métriques pipeline (déjà émises : wall_clock, blocking/warning counts) → exposer ; `total_tokens` réellement renseigné (actuellement 0).
- **DoD :** métriques par run consultables ; coût LLM réel par dossier visible.

---

## Critère de done de la phase
`api.py` modularisé ; `data_enrichment` au périmètre OEAQ ; calculs unifiés ; CI hermétique + E2E ; pas de dead code ; observabilité réelle (tokens/coût).
