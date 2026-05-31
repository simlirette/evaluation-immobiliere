# Éval Immo — Design System Rework
**Date:** 2026-05-28  
**Source of truth:** `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\`  
**Status:** Approved

---

## Scope

Full visual rework of the eval-immo Next.js frontend to match the design_handoff_eval_immo design system. Three phases delivered as one cohesive plan.

### In scope
- Design tokens (colors, fonts, shadows, radii, dark mode)
- All existing pages: login, /dossiers, /dossier/[id]
- All 5 dossier panels: DossierPanel, MarchePanel, AnalysePanel, SynthesePanel, RapportPanel
- New pages: /bibliotheque, /modeles, /archives, /parametres, /aide
- Sidebar nav wiring for all routes
- Nouveau dossier smart entry form
- Agent chat strip (dossier detail only)
- Grid/list view toggle on /dossiers

### Non-goals
- Backend changes (Supabase, runtime-api, lib/, hooks/, types/)
- OEAQ registry search / PDF import (nouveau dossier Step 1 path options — future)
- Real data wiring for bibliotheque/modeles/archives (mock data, same as panels)
- Mobile responsive beyond what the design covers

---

## Design System

### Typography
- **Serif (editorial):** `Source Serif 4` — headlines, addresses, body text, values. Loaded from Google Fonts. Replaces Cormorant Garamond.
- **Sans (UI chrome):** `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif`. Replaces Inter. No Google Fonts dependency.
- **Font features:** `font-variant: small-caps` for eyebrows/labels; `font-variant-numeric: tabular-nums lining-nums` for all numbers; `font-style: italic` for secondary meta.

### Color tokens (light / dark)

| Token | Light | Dark |
|-------|-------|------|
| `--paper` | `#fbf8ef` | `#1a1814` |
| `--paper-2` | `#f5f0e0` | `#221f1a` |
| `--paper-3` | `#ece5d0` | `#2c2922` |
| `--paper-hi` | `#ffffff` | `#26231d` |
| `--ink` | `#1a140d` | `#f3eddc` |
| `--ink-2` | `#2c2418` | `#e6dfca` |
| `--ink-3` | `#4a4031` | `#c4bda5` |
| `--ink-mute` | `#6b6151` | `#948c79` |
| `--ink-faint` | `#9a907c` | `#645e51` |
| `--rule` | `#d8cdb2` | `#393530` |
| `--rule-soft` | `#e4dcc4` | `#2e2b25` |
| `--rule-strong` | `#a89c80` | `#4f4a40` |
| `--navy` | `#1c3559` | `#7da4d6` |
| `--navy-hi` | `#284a7a` | `#9bbce5` |
| `--navy-deep` | `#12233d` | `#5d83b8` |
| `--navy-tint` | `#eef1f7` | `rgba(125,164,214,.14)` |
| `--sienna` | `#8a4a1f` | `#c98a5a` |
| `--verdigris` | `#3f5a47` | `#8bb89a` |
| `--ochre` | `#b08a3e` | `#d8a85e` |
| `--oxblood` | `#7a2a2a` | `#d27878` |

### Shadows
```css
--shadow-card:   0 1px 0 rgba(26,20,13,.04), 0 8px 24px -16px rgba(26,20,13,.16);
--shadow-hover:  0 2px 8px -4px rgba(26,20,13,.08), 0 8px 24px -16px rgba(26,20,13,.12);
--shadow-float:  0 12px 32px -16px rgba(26,20,13,.18);
```
**No `backdrop-filter` / glass effects anywhere.**

### Radii
All interactive components: `border-radius: 0` (square). Exception: only pills (`border-radius: 999px`) for status badges and the agent chat floating strip. No `r-lg`, `r-md` etc.

### Tailwind v4 integration
Two-layer approach to avoid naming conflicts:
- `@theme` block: maps `--color-paper`, `--color-ink`, etc. → Tailwind utility classes
- `:root` / `[data-theme="dark"]`: raw CSS vars for direct usage in components

---

## Layout

### App shell
Keep `relative w-full h-screen overflow-hidden` pattern. No structural change.

### Sidebar
- `position: fixed; top: 0; bottom: 0; left: 0; width: 260px`
- Slide via `transform: translateX(-260px)` (closed) → `translateX(0)` (open)
- Toggle button: chevron icon pinned to `top: 50%; right: -14px` on the sidebar edge
- When closed: content uses full viewport width (no `padding-left` offset — same as today)
- When open: content uses full viewport but sidebar overlays on top
- No backdrop blur — flat `background: var(--paper)`, `border-right: 1px solid var(--rule-soft)`

### Sidebar nav items (all routes)
```
Travail
  + Nouveau dossier        → /dossier/nouveau
  📁 Dossiers      [count] → /dossiers
  📚 Bibliothèque  [348]   → /bibliotheque
  □  Modèles       [6]     → /modeles
  🗄 Archives      [142]   → /archives

[pinned dossiers section]
[recent dossiers section]

[bottom]
  ⚙ Paramètres             → /parametres
  ? Aide                   → /aide
  [firm footer + theme toggle]
```

---

## Pages

### P0 — globals.css
Replace entire `@theme` / `:root` / `[data-theme="dark"]` block. Drop glass variables. Add design tokens. Keep `@custom-variant dark` targeting `[data-theme="dark"]`.

### P1 — layout.tsx
Replace `Cormorant_Garamond` + `Inter` imports with `Source_Serif_4`. System sans needs no import (CSS stack only). Remove unused font variables.

### P2 — Login (`/login`)
Two-panel layout, `min-height: 100vh; display: grid; grid-template-columns: 1fr 1fr`:
- **Left panel (brand):** Dark `--ink` background. Wordmark large. Rotating testimonial quotes. OEAQ compliance badge + Loi 25 mention at bottom.
- **Right panel (form):** White background. Sign-in form: email + password fields (square, flat border). Microsoft SSO button. "Mot de passe oublié?" link. Sign-up toggle. Sign-in button uses `btn accent` (navy).
- Sign-up: 4-field form (prénom, nom, email, OEAQ member #, cabinet). Checkbox accept terms.
- Sent state: verification steps with animated pulse dot.
- Footer: copyright line.

### P3 — /dossiers
**Topbar:**
- Crumbs row: today's date (fr-CA locale), right-aligned
- Page head: `h1` "Dossiers" (serif 36px), action buttons (Importer + Nouveau dossier accent)

**Toolbar:**
- Search bar: pill-shaped with glass icon, placeholder "Rechercher par adresse…", ESC clear
- Filter pills: Tous [N] | En cours [N] | Complets [N] | Brouillons [N] — active pill = ink bg
- Sort select: "Trier par" label + native select (Modifié / Créé / Adresse / Valeur)
- Grid/list toggle: 2-button group (grid icon | rows icon) — active = ink bg

**Body:**
- Grid view: `card-grid` — `repeat(auto-fill, minmax(320px, 1fr))`, 16px gap
- List view: `card-list` — full-width table with sortable column headers
- States: loading (skeleton cards), error, empty, no-results, partial (banner with pulse dot)

**DossierCard (grid view):**
- `background: var(--paper-hi); border: 1px solid var(--rule); box-shadow: var(--shadow-card)`
- Top: map SVG thumbnail (abstract grid lines + building shapes) with status ribbon
- Body: address (serif 19px bold), city + type (italic muted), stage bar (5 segments, navy=done, ochre=now), facts grid (3 cols: Année / Superficie / Stade or Valeur), foot (client name left, "Mod. [date]" right)
- Pin button: appears on hover, ochre when pinned
- Status chip: colored dot + text (Brouillon/En cours N/5/Complet)

**DossierRow (list view):**
- Columns: Adresse | Type | Année | Superficie | Stade/Valeur | Client | Modifié | [pin]
- Sortable column headers with caret indicator
- Row hover: `background: var(--paper-2)`

### P4 — /dossier/[id]
**Topbar:**
- Page head: `h1` = address (serif 32px) + dossier ID (sans faint small), meta line (city · type · year · area)
- Actions: Imprimer (ghost) | Partager (secondary) | Reprendre (accent)

**Stepper (replaces TabBar pill):**
- 5 steps: Dossier | Marché | Analyse | Synthèse | Rapport
- States: done (checkmark icon), now (filled box, ink bg, rounded), upcoming (number, muted)
- `border-bottom: 2px solid transparent` on container, navy underline on active
- URL mechanism unchanged: `?tab=` search param

**Dossier body:**
- Grid: `minmax(0, 1fr) 340px`, gap 28px, padding 24px 40px 140px (140px for agent chat)
- Main column: stage panel (rendered by active tab)
- Aside (340px): SideCards — Faits saillants, Mandat & client, Activité, Documents

**SideCard:**
- `background: var(--paper-hi); border: 1px solid var(--rule); padding: 16px 18px`
- Header: uppercase eyebrow (sans, 11px, faint)
- Fact rows: key (muted left) | value (bold right), dashed bottom border
- Client block: org (serif 16px), person, role, phone·email
- Activity list: when (12px faint) | who+what (13px)
- Documents list: colored type badge (PDF/ZIP/CSV) + name + size·date

**Panel reworks (maintain existing props/data contracts):**
- Stage 1 (DossierPanel): kv-grid-2/3 for property details, visit status row with stats
- Stage 2 (MarchePanel): comp-table with 7 columns + reconciliation box
- Stage 3 (AnalysePanel): approach-grid (3 cols: Comparaison/Coût/Revenus) + weighted recon
- Stage 4 (SynthesePanel): synthese-hero with large serif value, meta grid, signoff section
- Stage 5 (RapportPanel): rapport-hero (cover preview + side stats), rapport-sections list

**Agent chat strip:**
- `position: fixed; left: 260px; right: 0; bottom: 0`
- Gradient fade: `linear-gradient(180deg, transparent 0%, var(--paper) 60%)`
- Chat box: `max-width: 760px; background: var(--paper-hi); border: 1px solid var(--rule); border-radius: 18px`
- Suggestions row: sparkle icon + pill buttons (stage-specific)
- Input row: paperclip button | text input | send button (ink bg when ready)
- Stage-specific placeholder text and suggestion chips

### P5 — /dossier/nouveau (smart entry)
Single focused form, **no wizard steps**:
- Page head: "Nouveau dossier"
- Field 1: Adresse civique (text, required) — will be address search in future
- Field 2: Type de mandat (select: Hypothécaire / Pré-vente / Successoral / Litige / Acquisition / Donation / Refinancement / Avis restreint)
- Field 3 (optional, collapsible): Client — Nom / Organisation
- Submit: "Créer le dossier →" (accent) → POST to runtime-api → redirect to `/dossier/[slug]?tab=dossier`
- Note below form: "L'agent analysera automatiquement la propriété et prépare les comparables."

### P6 — /bibliotheque
4 tabs: Ventes | Marchés | Coûts | Taux

**Ventes tab:** Filterable/sortable table of comparable sales. Columns: Adresse | Quartier | Type | Date | Superficie | Prix | $/pi². Filter row: search + district dropdown + type dropdown + date range.

**Marchés tab:** Market stats cards by neighbourhood — median price, volume, days on market, trend indicator.

**Coûts tab:** Construction cost table — type × quality grid with $/pi² values. Reference: BNQ/OEAQ coûts de construction.

**Taux tab:** Capitalization rates by property type. Date-stamped. Source indicator.

All data: mock fixtures in `src/data/bibliotheque-mock.ts`.

### P7 — /modeles
Grid of template cards (3 cols). Each card:
- Category badge (résidentiel / spécialisé / commercial / restreint)
- Title (serif)
- Description
- Stats row: N sections · N pages · N documents
- Footer: Utilisé N fois · Dernière fois [date] · Norme OEAQ
- "Utiliser ce modèle" button → future hook

### P8 — /archives
Searchable list of completed dossiers, grouped by year (accordion or sections).
Filter row: search + year dropdown + mandate type dropdown.
Each row: ID | Adresse | Type | Mandat | Client | Valeur | Date complétion | [PDF link].
Data: mock fixtures in `src/data/archives-mock.ts`.

### P9 — /parametres
Left section nav (Profil / Cabinet / Membres / Intégrations / Utilisation / Sécurité / Préférences).
Each section as a panel with form fields.
Préférences section includes theme toggle (Clair / Sombre / Système).
Data: static form, no API wiring.

### P10 — /aide
Accordion FAQ sections: Prise en main / Dossiers / Rapports / Bibliothèque / Facturation / Contact.
Each section: question + answer paragraph. Static content.

---

## Shared Components (updated)

| Component | Change |
|-----------|--------|
| Badge | Square (no pill), small-caps, dot prefix, 4 variants |
| Button (btn) | Square, 4 variants (primary/secondary/accent/ghost) |
| Toast | Flat, bottom-center, no glass |
| EmptyState | Serif heading, navy italic em, É.A. seal icon |
| SkeletonCard | Updated background shimmer to paper tokens |
| ContextMenu | Flat, border `var(--rule)`, no blur |

---

## Migration notes

- All `rgba(31,30,28,…)` hardcoded values → replace with CSS var equivalents
- All `rounded-[Npx]` Tailwind classes → `rounded-none` or removed
- All `backdrop-filter`, `backdropFilter`, `WebkitBackdropFilter` → removed
- All `var(--glass-*)` references → removed
- `ThemeToggle` component: move from top-right overlay into sidebar footer / parametres
- `data-theme` attribute mechanism: unchanged (already `[data-theme="dark"]` on `<html>`)

---

## File structure additions

```
src/
  app/
    bibliotheque/page.tsx
    modeles/page.tsx
    archives/page.tsx
    parametres/page.tsx
    aide/page.tsx
  components/
    layout/
      SidebarToggle.tsx       (chevron toggle button)
    dossiers/
      DossierRow.tsx          (list view row)
      MapThumbnail.tsx        (abstract SVG map per neighbourhood)
      StageBar.tsx            (5-segment progress bar)
    panels/
      AgentChat.tsx           (extracted from dossier shell)
      SideCard.tsx            (aside cards)
  data/
    bibliotheque-mock.ts
    archives-mock.ts
    modeles-mock.ts
```
