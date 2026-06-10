# State — eval-immo

_Updated: 2026-06-10 | HEAD: d9fdbd6 (master)_

## Current Goal

Refonte frontend pixel-perfect selon `frontend/design_handoff_eval_immo/`. **P1-P5b faites. Reste P5c (onglet Dossier) + P6 (QA pixel).**

## Fait

- **P1 (8df1602)** shell + primitives (globals.css = app.css, Sidebar handoff, Icon/Dropdown/Stepper, boot thème).
- **P2 (57fead6, 2af03f3)** modèles/archives/bibliothèque/aide/paramètres/login.
- **P3 (db74fc7)** Mes-dossiers (cards/rows/toolbar/états ; facts backend manquants → « — »).
- **P4 (169c242)** wizard /dossier/nouveau 4 étapes câblé createRuntimeDossier ; recherche = index mock.
- **P5a (49e7a8d)** workspace dossier : topbar design (h1+ID+méta+actions), grid 1fr/340px, aside réelle (fact_chips→fact-rows, client-block+mandate-tag, documents réels avec doc-icons). Panels existants conservés dans la colonne 1fr. Branche isNew morte supprimée.
- Pattern : `.app` grid, `.main` scroll interne, CSS handoff importé par page. Tests : tsc/vitest 1188/build verts à chaque phase. Lint : 1 erreur PRÉ-EXISTANTE useFetch.ts.

## P5b ✅ (d9fdbd6)

Marché (comp-table+recon+vérifications), Analyse (approach-grid+recon-weighted+grille/édition/analytics conservées), Synthèse (hero+narratif+alertes+signoff SignatureForm), Rapport (rapport-hero+checklist+conditions, éditeur TipTap/versions conservés). AgentChatCapsule (suggestions par étape, streaming réel, tiroir réponses) active sur marché/analyse/synthèse/rapport.

## P5c — restant workspace

1. **DossierPanel** (onglet Dossier) : convertir en StageDossier design (4 panels KV Identification/Caractéristiques/Mandat/Visite ← fact_chips + inspection) en gardant DropZone/upload, correction de faits, pipeline progress, CP1-CP4 (CheckpointReviewPanel/ComparablePanel comme panels) ; basculer le chat sur la capsule (retirer ChatInput interne) ; supprimer NewDossierForm mort (lignes ~77-160 + branche 876).
2. Aside : brancher Activité (`/app/checkpoint/log` ou events) + upload direct depuis « Ajouter un document ».
3. Décision capsule : conversation streaming en tiroir (actuel) vs zone dédiée.

## P6 — QA pixel

Browse port 3100 (`NEXT_PUBLIC_SUPABASE_URL="" npx next dev -p 3100`) écran par écran vs HTML handoff ; workspace avec backend local (`python backend/api.py` + dossier démo `/app/demo`) ou en prod via /setup-browser-cookies.

## Open (hors refonte)

- Liste dossiers backend à enrichir (année/superficie/valeur/client) pour les facts cards P3 ; endpoint recherche registre (P4) ; endpoints bibliothèque/modèles/archives réels.
- MAMH cache prod · smoke SIRF (payant) · corpus manquants (expropriation, LIR/ARC, CCQ, Loi 141, LPTAA, facteurs-rajustement) · T3.6 vrai dossier · Loi 25 avis · OEAQ §6.5 · Stripe.
