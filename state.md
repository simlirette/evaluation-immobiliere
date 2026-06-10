# State — eval-immo

_Updated: 2026-06-10 | HEAD: 169c242 (master)_

## Current Goal

Refonte frontend pixel-perfect selon `frontend/design_handoff_eval_immo/`. **Phases 1 à 4 faites — reste le workspace dossier (P5) + QA finale (P6).**

## Fait

- **P1 (8df1602)** : shell + primitives — globals.css = app.css handoff, Sidebar anatomie handoff (statique 260px, firm menu + theme pill, épinglés/récents réels, profil É.A.), Icon.tsx, Dropdown.tsx, Stepper handoff, boot thème anti-FOUC.
- **P2a (57fead6)** : modèles, archives, bibliothèque (4 onglets), aide — mocks alignés verbatim design, CSS handoff par page. Fix bug handoff yearBuilt archives.
- **P2b (2af03f3)** : paramètres (7 sections, profil branché É.A. réel) + login (quotes, SSO visuel, sign-in Supabase câblé, sign-up OEAQ → sent).
- Pattern pages : `.app` grid 260/1fr, `.main` scroll interne (body overflow:hidden conservé), CSS importé par page (noms scopés par préfixe).
- Santé : tsc ✅ vitest 1188 ✅ build ✅. Lint : 1 erreur PRÉ-EXISTANTE `src/hooks/useFetch.ts:27` (react-hooks/use-memo, fichier non touché).

## Phases restantes

3. ✅ **Mes-dossiers (db74fc7)** : DossierCard/Row + page DOM handoff, pin bouton + context menu conservés, états design. Champs année/superficie/valeur/client absents de la liste backend → « — » muted (endpoint à enrichir plus tard pour les facts réels).
4. ✅ **Wizard nouveau dossier (169c242)** : route statique /dossier/nouveau, 4 étapes, création câblée (createRuntimeDossier + mapping FR→backend), chemin manuel fonctionnel, fix double bordure nd-search. Recherche = index mock (endpoint registre réel à faire). Le flux vision 1.2 (suggestion agent → confirmation) se branchera quand l'intake backend l'exposera. NOTE : l'ancienne branche isNew/NewDossierForm dans dossier/[id] est morte (route shadowée) — à nettoyer en P5.
5. **Workspace dossier panel-first** (dossier.jsx + dossier-stages.jsx + dossier.css) : panels par étape + aside 340px (Faits saillants/Mandat/Activité/Documents) + chat capsule — préserver streaming/checkpoints/pipeline existants.
6. QA pixel par écran vs HTML handoff (browse, port 3100 sans auth : `NEXT_PUBLIC_SUPABASE_URL="" npx next dev -p 3100`).

## Open (hors refonte)

- MAMH cache prod · smoke SIRF (payant) · corpus manquants (expropriation, LIR/ARC, CCQ, Loi 141, LPTAA, facteurs-rajustement) · T3.6 vrai dossier · Loi 25 avis · OEAQ §6.5 · Stripe.
