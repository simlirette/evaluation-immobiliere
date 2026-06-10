# State — eval-immo

_Updated: 2026-06-10 | HEAD: 49e7a8d (master)_

## Current Goal

Refonte frontend pixel-perfect selon `frontend/design_handoff_eval_immo/`. **P1-P4 + P5a faites. Reste P5b (conversion des panels) + P6 (QA pixel).**

## Fait

- **P1 (8df1602)** shell + primitives (globals.css = app.css, Sidebar handoff, Icon/Dropdown/Stepper, boot thème).
- **P2 (57fead6, 2af03f3)** modèles/archives/bibliothèque/aide/paramètres/login.
- **P3 (db74fc7)** Mes-dossiers (cards/rows/toolbar/états ; facts backend manquants → « — »).
- **P4 (169c242)** wizard /dossier/nouveau 4 étapes câblé createRuntimeDossier ; recherche = index mock.
- **P5a (49e7a8d)** workspace dossier : topbar design (h1+ID+méta+actions), grid 1fr/340px, aside réelle (fact_chips→fact-rows, client-block+mandate-tag, documents réels avec doc-icons). Panels existants conservés dans la colonne 1fr. Branche isNew morte supprimée.
- Pattern : `.app` grid, `.main` scroll interne, CSS handoff importé par page. Tests : tsc/vitest 1188/build verts à chaque phase. Lint : 1 erreur PRÉ-EXISTANTE useFetch.ts.

## P5b — conversion des panels (prochaine grosse session)

Cible : panels document-first du handoff (dossier-stages.jsx) + chat **capsule** unique en bas (STAGE_PROMPTS/SUGGESTIONS, .agent-chat-wrap déjà dans dossier.css), en préservant :
1. **StageDossier** : 4 panels KV (Identification/Caractéristiques/Mandat/Visite) ← fact_chips + inspection réelle ; DropZone/upload + correction de faits + CP1 restent (CheckpointReviewPanel s'insère comme panel).
2. **StageMarche** : comp-table 7 col + recon (médiane/étendue/valeur indiquée) ← fetchRuntimeComparables ; CP2 = CheckpointComparablePanel.
3. **StageAnalyse** : approach-grid 3 cards + recon-weighted ← enrichment/valuation ; AdjustmentsTable conservée.
4. **StageSynthese** : synthese-hero (valeur 56px, fourchette, méta 3 col) + narratif + signoff (SignatureForm réel) ← SynthesePanel data.
5. **StageRapport** : rapport-hero (cover + stats + 3 exports) + checklist sections ← RapportPanel/report_check ; éditeur TipTap accessible via Aperçu/Modifier.
6. Chat capsule : un seul useAgentChat au niveau page, conversation en overlay/drawer (à décider) ; retirer les ChatInput internes des panels.
7. Aside : brancher Activité (journal checkpoints `/app/checkpoint/log` ou events) + upload direct depuis « Ajouter un document ».
8. Retirer NewDossierForm mort de DossierPanel.

## P6 — QA pixel

Browse port 3100 (`NEXT_PUBLIC_SUPABASE_URL="" npx next dev -p 3100`) écran par écran vs HTML handoff ; workspace avec backend local (`python backend/api.py` + dossier démo `/app/demo`) ou en prod via /setup-browser-cookies.

## Open (hors refonte)

- Liste dossiers backend à enrichir (année/superficie/valeur/client) pour les facts cards P3 ; endpoint recherche registre (P4) ; endpoints bibliothèque/modèles/archives réels.
- MAMH cache prod · smoke SIRF (payant) · corpus manquants (expropriation, LIR/ARC, CCQ, Loi 141, LPTAA, facteurs-rajustement) · T3.6 vrai dossier · Loi 25 avis · OEAQ §6.5 · Stripe.
