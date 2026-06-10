# State — eval-immo

_Updated: 2026-06-10 | HEAD: fix(infolot) après 84fe160 (master)_

## Current Goal

Audit vision + vérifications faits. Prochain chantier : refonte frontend pixel-perfect selon `frontend/design_handoff_eval_immo/`.

## Cette session (2026-06-10)

- Audit complet : `docs/AUDIT-VISION-2026-06-10.md` (vision ~85-90 % backend, frontend divergent du handoff).
- Acceptance É.A. locale : PASS 6/6 gates (paquet V1).
- **Fix Infolot** : WFS Atlas retiré (404) → ArcGIS REST `Cadastre_allege/MapServer/0/query`, NO_LOT avec espaces parsé, erreurs ArcGIS HTTP 200 détectées. Smoke live PASS + tests verts. Commité.
- Tests : pytest 1037 ✅, vitest 1188 ✅, tsc ✅.

## Open

- **Refonte frontend 100 % identique au handoff** (plan 6 phases dans le message d'audit) — pas commencée.
- MAMH cache prod à confirmer (`provision_mamh_cache.py --all` sur volume Railway).
- Smoke SIRF (payant — approbation facturation requise).
- Corpus manquants : Loi expropriation 2023, LIR/ARC, CCQ, Loi 141, LPTAA, `facteurs-de-rajustement/` (dans `C:\Users\simon\knowledge`) + réindex RAG.
- T3.6 vrai dossier É.A. · avis Loi 25 · OEAQ §6.5 · Stripe.
