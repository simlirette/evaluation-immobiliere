# State — eval-immo

_Updated: 2026-06-10 | HEAD: 8df1602 (master)_

## Current Goal

Refonte frontend pixel-perfect selon `frontend/design_handoff_eval_immo/`. **Phase 1 faite.**

## Phase 1 livrée (8df1602)

- `globals.css` = port 1:1 de `app.css` handoff (sidebar/topbar/toolbar/search/pills/btn/cards/list/badges/états/dropdown/stepper/theme-pill/dark) + section COMPAT pour panels existants (.panel, .side-card, .field, .agent-chat-*, .page-h1).
- `Sidebar.tsx` réécrit anatomie handoff : statique 260px (toggle supprimé), wordmark, bloc dossier courant (props addr/id/city), nav Travail + counts réels (dossiers runtime, mocks biblio/modèles/archives), épinglés/récents (fetchRuntimeDossiers), firm card popover + theme-pill, profil É.A. réel (fetchEvaluateurProfile).
- Nouveaux : `shared/Icon.tsx` (set handoff), `shared/Dropdown.tsx`. `Stepper.tsx` markup handoff.
- `layout.tsx` : boot thème anti-FOUC. Morts supprimés : SidebarNav/Footer/Recent/Toggle/Wordmark, DossierListItem, AgentChat.
- Vérifié : tsc ✅ vitest 1188 ✅ build ✅ + screenshots light/dark/popover (dev sans auth, port 3100).

## Phases restantes (plan refonte)

2. Écrans simples : login complet (2 col, quotes, SSO, sign-up OEAQ), aide, modèles, archives, bibliothèque, paramètres 7 sections.
3. Mes-dossiers : toolbar handoff (search 360px, pills avec counts, sort-select italique, view-toggle), grid/rows, 5 états.
4. Wizard nouveau dossier 4 étapes (+ flux vision 1.2 suggestion agent → confirmation).
5. Workspace dossier panel-first : panels par étape + aside 340px + chat capsule (préserver streaming/checkpoints).
6. QA pixel écran par écran vs HTML handoff.

## Open (hors refonte)

- MAMH cache prod à confirmer · smoke SIRF (payant) · corpus manquants (expropriation, LIR/ARC, CCQ, Loi 141, LPTAA, facteurs-rajustement) · T3.6 vrai dossier · Loi 25 avis · OEAQ §6.5 · Stripe.
- `backend/runtime_sessions_acceptance/` non suivi = evidence acceptance locale (garder hors git).
