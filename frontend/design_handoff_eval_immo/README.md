# Handoff: Éval Immo — application web pour évaluateurs agréés

## Dark mode

The app supports light and dark themes, toggled via the **Apparence** control in the firm-menu popover (sidebar bottom).

**How it works:**
- `theme.js` is loaded at the top of every HTML page (before stylesheets render) to avoid FOUC. It reads `localStorage["evalimmo-theme"]` and falls back to `prefers-color-scheme`. It sets `data-theme="dark"` or `"light"` on `<html>`.
- The whole design is token-driven, so dark mode just overrides the CSS custom properties — see `[data-theme="dark"] { … }` at the bottom of `app.css`. Per-page CSS doesn't need changes.
- A small global `window.EvalImmoTheme = { get, set, toggle }` API exposes theme control. The Sidebar component listens for `theme-change` CustomEvents.

**Dark palette** (tokens redefined under `[data-theme="dark"]`):

| Token | Light | Dark |
|---|---|---|
| `--paper` | `#faf9f5` | `#1a1814` |
| `--paper-2` | `#f3f1ea` | `#221f1a` |
| `--paper-3` | `#ebe8dd` | `#2c2922` |
| `--paper-hi` | `#ffffff` | `#26231d` |
| `--ink` | `#1f1e1c` | `#f3eddc` |
| `--ink-2` | `#2c2a26` | `#e6dfca` |
| `--ink-3` | `#4a4640` | `#c4bda5` |
| `--ink-mute` | `#6b6760` | `#948c79` |
| `--ink-faint` | `#a8a299` | `#645e51` |
| `--rule` | `#e6e2d6` | `#393530` |
| `--rule-soft` | `#efece1` | `#2e2b25` |
| `--rule-strong` | `#cdc7b7` | `#4f4a40` |
| `--navy` | `#1c3559` | `#7da4d6` (lighter for AA on dark) |
| `--verdigris` | `#4a6b54` | `#8bb89a` |
| `--ochre` | `#b88a3e` | `#d8a85e` |
| `--oxblood` | `#8a3030` | `#d27878` |

**Implementation in target framework:**
1. Replicate the `theme.js` boot script (or use your framework's color-mode plugin — Next.js `next-themes`, Vue `useDark`, etc.). Persist to `localStorage` and apply the attribute to `<html>` before paint.
2. Mirror both `:root` and `[data-theme="dark"]` token blocks in your design-token system.
3. Hardcoded `rgba(31,30,28,…)` values in `app.css` (sidebar nav hover, active states, focus rings) are flipped to `rgba(243,237,220,…)` under dark — preserve these overrides.
4. The Sidebar firm menu contains the toggle UI (`.theme-pill` with two segmented buttons "Clair" / "Sombre" with Sun/Moon icons).

## Overview

Éval Immo is a web application for Québec real-estate appraisers (évaluateurs agréés / É.A.) — members of the **Ordre des évaluateurs agréés du Québec (OEAQ)**. It supports the full workflow of a property appraisal mandate, from intake to a signed report archived under OEAQ retention rules.

The design covers **10 screens**:

| # | Screen | File | Purpose |
|---|--------|------|---------|
| 0 | **Login / first-run** | `login.html` | Sign in (SSO + email/password) or sign up via firm + OEAQ membership |
| 1 | **Dossiers** | `mes-dossiers.html` | List/grid of active dossiers with search, filter pills, sort, grid/rows view |
| 2 | **Dossier détail** | `dossier.html` | Workspace for a single dossier — 5-stage stepper, side facts, persistent agent chat |
| 3 | **Nouveau dossier** | `nouveau-dossier.html` | 4-step creation wizard (entry path → property → mandate → confirmation) |
| 4 | **Bibliothèque** | `bibliotheque.html` | Reference library — 4 tabs: Ventes (sales), Marchés (markets), Coûts (costs), Taux (cap rates) |
| 5 | **Modèles** | `modeles.html` | 6 report templates, sortable card grid |
| 6 | **Archives** | `archives.html` | Completed dossiers grouped by year, with year-pill filter |
| 7 | **Paramètres** | `parametres.html` | 7-section settings (Profil, Cabinet, Membres, Intégrations, Utilisation, Sécurité, Préférences) |
| 8 | **Aide** | `aide.html` | In-app workflow guide, FAQ, keyboard shortcuts, contact |
| 9 | **Style system** | `style-system.html` | Visual design system reference page (tokens, components, type) |

---

## About the Design Files

The files in this bundle are **design references created in HTML/React (Babel-in-browser)** — prototypes showing intended look and behavior, **not production code to copy directly**.

The task is to **recreate these designs in the target codebase's existing environment** (e.g. a Next.js app with Tailwind, a Vue + Vite setup, a SwiftUI iOS client) using its established patterns and libraries. If no codebase exists yet, choose an appropriate framework (Next.js + Tailwind + Radix recommended for parity).

**What to lift from the prototypes:**
- Exact colors, type, spacing, radii, shadows (see "Design Tokens" below)
- Component anatomy and visual states
- Copy text (in French / Québec French — keep it exact, all dates, accents, terminology)
- Interactions and flows

**What NOT to lift:**
- The Babel-in-browser script tag setup
- The inline `<script type="text/babel">` files (rewrite as proper components)
- The `window.X = …` data globals (use real fetching / state management)
- Mock data — replace with API calls or real database queries

---

## Fidelity

**High-fidelity (hi-fi).** Pixel-perfect mockups with final colors, typography, spacing, and interactions. The developer should recreate the UI pixel-perfectly using the target codebase's libraries — every spacing value, color hex, font size, and border-radius is intentional.

---

## Brand & visual direction

- **Aesthetic:** warm, paper-like, Claude.ai-inspired — bright cream background (`#faf9f5`), rounded corners, soft hairline borders, no harsh shadows, system sans-serif (SF Pro / Segoe UI) as the workhorse with **Source Serif 4** as the accent face for page titles, address blocks, and headlines.
- **Tone:** professional, calm, French/Québec. Respects OEAQ vocabulary (É.A., rôle d'évaluation, mandat, attestation).
- **Density:** comfortable — generous padding inside cards, hairline separators between rows. Not enterprise-dense.
- **Iconography:** custom inline SVGs with 1.4–1.6 stroke-width, rounded line-caps. No emoji.
- **No maps, no charts beyond simple sparklines/bars.** Earlier iterations had abstract neighborhood maps inside dossier cards — those were intentionally removed.

---

## Design Tokens

All tokens are defined as CSS custom properties in `app.css`. Use the same values in your target framework's design-token system.

### Paper / surfaces (warm cream palette)

| Token | Hex | Use |
|---|---|---|
| `--paper` | `#faf9f5` | Page background |
| `--paper-2` | `#f3f1ea` | Hover, subtle row tint |
| `--paper-3` | `#ebe8dd` | Avatar/icon tile background |
| `--paper-hi` | `#ffffff` | Cards, panels, popovers |

### Ink (text)

| Token | Hex | Use |
|---|---|---|
| `--ink` | `#1f1e1c` | Primary text, h1 |
| `--ink-2` | `#2c2a26` | Strong text |
| `--ink-3` | `#4a4640` | Mid text |
| `--ink-mute` | `#6b6760` | Subtitle, meta |
| `--ink-faint` | `#a8a299` | Eyebrows, placeholders, disabled |

### Rules / borders

| Token | Hex | Use |
|---|---|---|
| `--rule` | `#e6e2d6` | Default border |
| `--rule-soft` | `#efece1` | Subtle dividers |
| `--rule-strong` | `#cdc7b7` | Hover border |

### Accents

| Token | Hex | Use |
|---|---|---|
| `--navy` | `#1c3559` | Primary accent (CTA, "value indiquée", "Done" stepper dots) |
| `--navy-hi` | `#284a7a` | Navy hover |
| `--navy-deep` | `#12233d` | Gradient bottom |
| `--navy-tint` | `#eef1f7` | Soft navy bg (pills) |
| `--sienna` | `#8a4a1f` | (reserved) |
| `--verdigris` | `#4a6b54` | Success / complete status |
| `--ochre` | `#b88a3e` | "En cours" status, agent suggestions, attention |
| `--oxblood` | `#8a3030` | Error, deadline, required-field marker |

### Typography

| Token | Value |
|---|---|
| `--sans` | `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif` |
| `--serif` | `"Source Serif 4", "Iowan Old Style", Georgia, serif` (Google Fonts) |

**Type scale:**

| Role | Family | Size | Weight | Letter-spacing | Line-height |
|---|---|---|---|---|---|
| H1 page (default) | serif | 36px | 500 | -.015em | 1.1 |
| H1 with stepper below | serif | 32px | 500 | -.015em | 1.15 |
| H2 panel | serif | 22px | 500 | -.005em | 1.2 |
| H3 card / side-card | serif | 16–18px | 500 | -.005em | 1.25 |
| Subtitle | sans | 14px | 400 | 0 | 1.55 (max-width 64ch) |
| Body | sans | 14px | 400 | 0 | 1.5 |
| Body serif (notes/lead) | serif | 15.5–16px | 400 | 0 | 1.55–1.65 |
| Eyebrow | sans | 11px | 500 | .04em uppercase | 1.2 |
| Numeric (prices, IDs) | sans | inherit | inherit | tabular-nums lining-nums |

### Radii

| Token | Value | Use |
|---|---|---|
| `--r-sm` | 6px | Small inline chips, kbd |
| `--r-md` | 10px | Inputs, buttons, sidebar nav items, small inner cards |
| `--r-lg` | 14px | Top-level cards, panels, large surfaces |
| `--r-xl` | 20px | (reserved) |
| `--r-pill` | 999px | Pills, filter chips, search field, switches |

### Shadows

| Token | Use |
|---|---|
| `--shadow-card` | `none` (default — cards rely on border alone) |
| `--shadow-hover` | `0 2px 8px -4px rgba(31,30,28,.08), 0 8px 24px -16px rgba(31,30,28,.12)` (clickable card hover) |
| `--shadow-float` | `0 12px 32px -16px rgba(31,30,28,.18)` (popovers, menus) |

### Spacing

Use a **4px grid**. Common values: 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32, 40. Page horizontal gutters: **40px**. Vertical body padding: **28px top, 80px bottom**.

---

## Layout system

Every authenticated page uses a 2-column shell:

```
┌─────────────┬───────────────────────────────────────────┐
│  Sidebar    │  Main pane                                │
│  260px      │  flex column, min-width 1280              │
└─────────────┴───────────────────────────────────────────┘
```

**Sidebar (260px, sticky 100vh, paper background, hairline right border):**
- Brand wordmark "Éval Immo" (serif, navy italic on "Immo"), tagline "Évaluateurs agréés — Québec"
- *(Dossier detail only)* "Current dossier" block: gray rounded rectangle showing the open dossier's address (serif) + ID right-aligned (sans, faint)
- **Travail** nav group: Nouveau dossier (Plus icon) · Dossiers · Bibliothèque · Modèles · Archives — each with icon + label + count badge
- **Épinglés** group: pinned dossiers, indented, with status dot + address
- **Récents** group: 3 most recently modified dossiers
- Spacer
- **Firm card** (button, opens popover upward): seal (initials "MT") + name "Maxime Tremblay" + credential "É.A. — OEAQ 4218" + chevron. Popover contains Paramètres / Aide / Se déconnecter.

**Main pane:** column flex. Children in order:
1. `.topbar` — page header area (28px top padding, 40px horizontal)
2. `.X-body` — main scrollable content (28px top, 40px horizontal, 80px bottom)

---

## Components catalogue

### Buttons (`app.css`)

```
.btn                — base: 14px sans 500, padding 9px 18px, border-radius var(--r-md), bg ink #1f1e1c, text paper-hi
.btn.accent         — bg var(--navy), text #fff
.btn.secondary      — bg transparent, border rule, color ink
.btn.ghost          — transparent, no border, hover paper-2
.btn.btn-sm         — 12.5px / 5px 12px
.btn.btn-full       — width 100%, 13px / 8px 12px
.btn:active         — translateY(1px)
.btn[disabled]      — opacity .35, not-allowed
```

### Pills

```
Filter pill         — border rule, padding 7px 14px, border-radius pill
  .pill.active      — bg ink, color paper-hi
Status chip         — dot ::before (6px), color tied to status (ochre/verdigris/ink-faint)
```

### Dropdown (custom, `Dropdown` component in `components.jsx`)

Triggers a popover menu styled to match the page. Used for filters where the native `<select>` menu would look out of place.

```
.dropdown .dd-trigger   — pill button (pill radius, white bg, hairline border)
.dropdown .dd-menu      — popover (white, r-md, shadow-float, drops down)
.dropdown .dd-item      — 8px 12px, r-sm, hover paper-2, active = subtle gray bg + Check icon
.dropdown.open caret    — rotates 180°
Closes on outside click + Escape
```

### Sidebar nav item (`.sidebar .nav a`)

```
padding 8px 10px, border-radius r-md, 14px sans, color ink-2
:hover  — bg rgba(31,30,28,.04), color ink
.active — bg rgba(31,30,28,.06), color ink, weight 500
icon 16px, opacity .7 (active 1)
.count right-aligned, font-size 12px ink-faint
```

### Stepper (shared, `app.css`)

Underlined tabs with rounded gray box on the active step. Used by Dossier detail (5 stages) and Nouveau dossier (4 steps).

```
.stepper                — flex centered, padding 14px 0 24px, full-width hairline below (::after)
.stepper .step          — sans 17px, color ink-mute, gap 10px
.stepper .step .num     — 14px ink-faint (for upcoming/now); replaced by Check icon for done
.stepper .step.done     — color ink-2, Check icon (verdigris)
.stepper .step.now      — color ink, bg rgba(31,30,28,.06), border-radius r-md, padding 8px 18px
```

### Card patterns

**Dossier card** (grid view of `mes-dossiers`):
- White bg, r-lg, 1px rule border, padding 18px 20px 16px
- Header row: status chip + pin button (opacity 0, fades in on hover)
- Address (serif 19px 500), city line (sans 13px, italic on type)
- Hairline divider, then 3-column facts (Année / Superficie / Stade or Valeur)
- Footer with client (truncated) + "Mod. X" stamp
- Hover: border → rule-strong, soft shadow lift

**Dossier row** (list view): full-width grid row, columns Adresse / Type / Année / Superficie / Stade-Valeur / Client / Modifié / Actions, hover paper-2.

**Panel** (used inside Dossier workspace): white, r-lg, 1px border, padding 22px 24px 24px. Has `.panel-head { display: flex; justify-content: space-between }` with serif H2 and optional ghost action.

**Side card** (right column of Dossier workspace): white, r-lg, padding 16px 18px 18px. H3 is uppercase 11px sans 500 ink-faint.

### Tables

Tables are CSS Grid (not `<table>`). Pattern:

```
.X-head — sans 11px 500 .04em uppercase ink-faint, paper bg, border-bottom rule-soft
.X-row  — sans 13.5px ink-2, border-top rule-soft, hover paper-2 (+r-md if hover background)
.X-row .num — text-align right, tabular-nums lining-nums
.X-row .strong — color ink, weight 600
```

Sortable headers (`.sort-head` button): caret 9×6 SVG that fades in (opacity 0 → 1), rotates 180° for ascending.

### Form fields (Nouveau dossier, Login)

```
input, textarea — sans 14px ink, bg paper-hi, border 1px rule, r-md, padding 9px 12px
:focus — bg paper-hi, border ink-mute, box-shadow 0 0 0 3px rgba(31,30,28,.04)
input[type="date"] — native indicator hidden, custom calendar SVG overlay via background-image, click anywhere triggers showPicker()
.af-check input[type="checkbox"] — 16px, accent-color ink
.switch (toggle) — 36×20 pill, bg paper-3 off → verdigris on, knob translates 16px
```

### Status colors by domain

| Status (status of a dossier) | Color | Background |
|---|---|---|
| brouillon | `--ink-faint` | (dot only) |
| encours | `--ochre` | (dot) / `rgba(184,138,62,.12)` (pill) |
| complet | `--verdigris` | (dot) / `rgba(74,107,84,.12)` (pill) |

| Mandate type | Color | Background |
|---|---|---|
| Hypothécaire / Acquisition | `--navy` | `--navy-tint` |
| Pré-vente / Refinancement | `--ochre` | `rgba(184,138,62,.12)` |
| Successoral / Donation | `--verdigris` | `rgba(74,107,84,.12)` |
| Litige | `--oxblood` | `rgba(138,48,48,.10)` |

---

## Per-screen specifications

### 0 — Login (`login.html`)

Two-column split, no sidebar. Left = brand panel (warm cream gradient with radial accents). Right = form.

**Left panel:**
- Top: serif wordmark "Éval Immo" (38px) + tag "Évaluateurs agréés — Québec"
- Middle: rotating quote (3 quotes, auto-cycle every 8s + clickable dot navigator). Quote serif italic 22px, attribution sans (name 13.5px ink, firm 12.5px ink-mute). Large opening `"` glyph at 120px navy 12% opacity behind quote.
- Bottom: OEAQ seal card (frosted white, backdrop-filter blur 4px) — É.A. ring + 2 compliance lines (OEAQ + Loi 25).

**Right panel:**
- Top-right corner link: "Aperçu de l'application →" (pill, navy text)
- Form (max-width 400px, centered):
  - **Sign in** (default): eyebrow "Bon retour" → H1 serif 36px "Se connecter" → SSO button "Continuer avec Microsoft" (Microsoft 4-square colored icon: red `#F35325`, green `#81BC06`, blue `#05A6F0`, yellow `#FFBA08`) → "ou" divider → Email + Password fields → "Mot de passe oublié" (navy link, top-right of password label) → password show/hide toggle → "Garder ma session active 14 jours" checkbox → primary "Se connecter" button → switch link "Pas encore de compte ? S'inscrire via votre firme"
  - **Sign up**: eyebrow "Bienvenue" → H1 "Créer votre cabinet" → fields Prénom/Nom (row) → Courriel → N° de membre OEAQ + Cabinet (row) → terms checkbox with inline links → "Vérifier auprès de l'OEAQ" button (disabled until all required + checkbox)
  - **Sent (post sign-up)**: green check seal → H1 "Vérification en cours" → 3-step checklist (Courriel envoyé ✓ done verdigris / Vérification OEAQ ● active ochre with pulse animation / Activation pending)
- Footer: copyright + Confidentialité / Conditions / Montréal · Québec

### 1 — Dossiers (`mes-dossiers.html`)

Page H1 "Dossiers" (no subtitle). Right-side actions: "Importer un dossier" (secondary) + "Nouveau dossier" (accent, links to wizard).

**Sticky toolbar (3 cols + view toggle):**
- Search field (pill, 360px max) with `Glass` icon, supports `esc` key chip to clear when content
- Filter pills row: Tous (count) · En cours · Complets · Brouillons — active pill = inverse (ink bg, paper-hi text)
- Sort select: small italic native select with custom chevron, font-size 14px, label "Trier par" eyebrow. Options: Modifié récemment / Créé récemment / Adresse (A–Z) / Valeur (décroissant)
- View toggle: grid + rows icons, 13×13px, active = ink bg

**Body:**
- Card grid: `repeat(auto-fill, minmax(320px, 1fr))` with 16px gap (see Dossier card spec)
- List view: single white card (r-lg, overflow hidden) containing header row + rows with sortable columns. Pin button revealed on row hover.

**State views (centered seal + h2 serif + p ink-mute):**
- Loading: shimmer skeleton cards (196px tall, animated linear gradient)
- Empty: navy-ring seal, "Aucun dossier ouvert."
- Error: oxblood-ring seal "!" — "Connexion interrompue"
- Partial: banner inside grid (yellow pulse dot + message + "3 / 12" eyebrow)
- No-results: filter clear button

### 2 — Dossier détail (`dossier.html`)

Workspace for one dossier. URL: `dossier.html?id=2026-0418` (falls back to first dossier).

**Topbar:**
- H1: address (serif 32px) with dossier ID inline right (sans 14px ink-faint) — e.g. `245, av. Wiseman   2026-0418`
- Head meta line: City, Montréal · Type · Year · Area (sans 13.5px ink-mute, dot-sep between)
- Right actions: Imprimer (ghost) / Partager (secondary) / Reprendre (accent)
- Stepper: 5 stages (Dossier / Marché / Analyse / Synthèse / Rapport), padding 14px 0 24px, hairline below the whole topbar

**Body (`.dossier-body` grid: `1fr 340px`, gap 28px, padding 24px 40px 60px):**

*Main column (varies per stage):*

| Stage | Content (see `dossier-stages.jsx`) |
|---|---|
| 1 Dossier | 4 panels: Identification (6 KV), Caractéristiques (9 KV in 3 cols), Mandat (6 KV in 2 cols), Visite (status row with verdigris check + photo/room/lot stats) |
| 2 Marché | "Analyse comparative" panel — comparables table (7 cols: Comparable / Vendu / Superficie / Prix / $/pi² / Ajust. / Distance) + reconciliation block showing Médiane $/pi², Étendue, **Valeur indiquée** (navy serif 18px range) + Notes panel (serif body) |
| 3 Analyse | 3-card grid (Comparaison 70 % / Coût 30 % / Revenus N/A — `na` class is opacity .55), each with title, value (serif 26px), weight pill, notes. Below: reconciliation row with weighted final value (serif 28px navy) + Justification panel |
| 4 Synthèse | `synthese-hero` panel: eyebrow → label → **valeur finale (serif 56px, -.02em letter-spacing)** → range row → 3-col meta (Date / Méthode / Confiance — verdigris for "Élevé"). Then Narratif (serif body). Then Attestation panel with declaration text + signature line (cursive SVG) + actions (Réviser secondary / Signer accent with check icon) + ochre status pill "En attente de signature" |
| 5 Rapport | `rapport-hero`: 2-col grid. Left = mock document cover (aspect-ratio 1:1.294, 56px padding, eyebrow + serif 32px addr + italic city + 3-col cover meta at bottom + navy É.A. seal absolute top-right). Right = stats stack (pages, sections complete) + 3 export buttons. Below: sections checklist with done/pending icons (verdigris check / paper-2 clock) + page counts |

*Aside (sticky, 340px):* `Faits saillants` (11 fact-rows) → `Mandat & client` (org/person/role/contact with navy links + ochre dot mandate-tag) → `Activité` (timeline ul, 80px when col + ink-2 what) → `Documents` (filetype-colored 30×36 tile + name + size · date, "Ajouter un document" ghost btn).

**Persistent agent chat (`.agent-chat-wrap`):** fixed bottom, offset 260px left, gradient fade. Pill capsule 18px r, max-width 760px:
- Suggestions row: ochre Sparkle icon + 3 suggestion chips (paper-2 pill bg, clickable → fills input)
- Input row: 36px circular Paperclip attach button (ink-faint, hover paper-2) + text input + 36px circular send button (paper-2 when empty, ink filled when ready)
- `STAGE_PROMPTS` and `STAGE_SUGGESTIONS` change per active stage

### 3 — Nouveau dossier (`nouveau-dossier.html`)

4-step wizard. No crumbs row, centered narrow content (max 720px / 880px / 760px depending on step).

**Topbar:** H1 "Nouveau dossier" (serif 32px) + subtitle that changes per step. Stepper (4 steps).

**Steps:**
1. **Point de départ** — 4 large path cards (grid `44px 1fr 28px`, 1.5px border, r-lg, padding 18px). Icon tile (44×44 r-md paper-2, ink when selected) + Title with optional badge ("Recommandé" navy / "Bêta" ochre) + Description + Check mark when selected. Selected card: border ink, soft outline shadow.
2. **Propriété** — Large search input (16px sans, 12px 16px padding, 1.5px border, r-md, focus glow). Below: result rows (serif 15.5px addr, sans 12.5px meta) when no property selected. After selection: preview card (r-lg, padding 22px 24px) with eyebrow → H3 serif 24px addr → city → hairline → 6-KV grid (3 cols) → ochre Sparkle note banner about auto-enrichment.
3. **Mandat** — 2-col form. Sections (r-lg, padding 20px 22px): Mandat (type dropdown / modèle dropdown / dates row) + Client (org with `<datalist>` autocomplete / représentant / phone + email) + Notes (full-width textarea, serif 14.5px).
4. **Confirmation** — single `confirm-card` (r-lg, padding 28px 32px) with header (eyebrow + serif 26px addr + sub) + 3 sections (Propriété / Mandat / Notes if present) each with uppercase 11px header + 3-col KV grid + footer "Méthode de démarrage". On submit: verdigris-bg "Dossier créé. Redirection..." banner, then `setTimeout` → dossier.html.

**Sticky footer:** Précédent (ghost, disabled on step 1) / "Étape X sur 4" status / Continuer (accent, disabled until valid) → on step 4: "Créer le dossier"

### 4 — Bibliothèque (`bibliotheque.html`)

H1 "Bibliothèque" + subtitle. Right actions: Exporter / Importer (accent +).

**Tabs (underlined, biblio-tabs):** Ventes (count) · Marchés · Coûts · Taux. Active = ink border-bottom + count pill paper-3. Sit on a hairline that runs across the topbar bottom.

**Ventes tab:**
- Toolbar: search + 2 custom Dropdowns (Quartier / Type) + Réinitialiser (ghost, only when filters applied)
- 4 stat cards row (r-lg, padding 14px 18px): Ventes filtrées / Médiane prix / Médiane $/pi² / Étendue prix
- Sortable table (9 cols, see Tables section). Address shows serif 15px addr + sans 11.5px ink-faint meta (ID + source). `.used-badge` navy pill (rgba 28,53,89,.10) for count of past usage.

**Marchés tab:** card grid (auto-fill 290px). Each card: H3 district + YTD pill (verdigris pos, oxblood neg, ±0.1% precision) → median $/pi² (serif 38px) + unit → **inline 240×44 SVG sparkline** (navy line + filled area at 8% opacity + final dot) → 3-col stats (Étendue / DOM médian / Ventes 12m).

**Coûts tab:** intro paragraph + grouped sections (one per category) each with H3 + 5-col table (Qualité / Taux / Unité / Source / Mis à jour).

**Taux tab:** intro + card grid (auto-fill 280px). Each card: serif segment name + zone → `tc-cap` row with serif 30px navy "X.X – Y.Y" + "% taux global" → hairline → vacancy footer.

### 5 — Modèles (`modeles.html`)

H1 "Modèles" + subtitle. Sort dropdown ("Plus utilisés / Nom A-Z / Modifié récemment") + "Nouveau modèle" (accent).

Card grid (auto-fill 360px, 16px gap). Each card (r-lg, padding 22px 24px 18px, grid layout with 16px gap):
- Head row: category pill (résidentiel = navy / commercial = verdigris / spécialisé = ochre / restreint = ink-mute) + More (⋯) action
- Serif 22px title
- 13.5px desc paragraph
- 3-col stats with hairlines top+bottom: sections / pages env. / documents (serif 24px values)
- Foot: navy norm row with Seal icon + "OEAQ — Rapport narratif" + meta row (Utilisé dans N dossiers · Mod. date)
- Actions row: Aperçu (ghost) / Démarrer un dossier (secondary)
- Hover: rule-strong border + soft shadow

### 6 — Archives (`archives.html`)

H1 "Archives" + subtitle. Right action: "Exporter le registre" (secondary with Print icon).

**Body:**
- Toolbar: search + Mandat custom Dropdown + Réinitialiser (when active)
- Year strip: horizontal pills, "Toutes années" + each year with count. Active pill: ink bg, paper-hi text.
- 4-col summary card (Affichage / Valeur totale évaluée / Plus récent / Plus ancien). Values serif 22px, with dividers between columns.
- Year-grouped sections (sorted DESCENDING by year): big serif 32px year + count.
- Each row (grid `64px 2fr 140px 1.4fr 120px 90px 140px`):
  - Date stack: day (serif 22px) over month (uppercase 10.5px), with right hairline
  - Address (serif 16px) + meta row (city · type · year · area)
  - Mandate pill (`mandate-X` slug class for color)
  - Client (truncated)
  - Value (numeric, right-aligned)
  - ID (faint)
  - Hover-revealed Voir / Cloner ghost buttons

**Notes:** if total archive count (mock = 142) exceeds visible rows: "Affichage de N sur 142 — Charger plus" banner.

### 7 — Paramètres (`parametres.html`)

2-column layout (220px nav + main, 32px gap). Deep-link with `?section=ID`, state syncs to URL via `history.replaceState`.

**Sub-nav (sticky, top 24px):** 7 items (Profil, Cabinet, Membres, Intégrations, Utilisation, Sécurité, Préférences). Each: icon (16px) + label, padding 9px 12px, r-md. Active = `rgba(31,30,28,.06)` bg.

**Main:** column flex, max-width 760px, gap 18px.

Section cards (`param-card`): white, r-lg, padding 22px 24px 20px. Head row: serif 18px H3 + optional ghost action (right). Body uses `pc-row` pattern: 200px label / value with dashed hairline divider.

**Profil:** Hero card (64×64 navy avatar with white initials + name H2 + meta row with É.A.-OEAQ pill) → Identité / Coordonnées / Adhésion professionnelle (with "En règle" status-pill verdigris) / Signature (handwritten cursive SVG + name + OEAQ#).

**Cabinet:** Identification (NEQ, etc) / Adresse / Logo (64×64 r-md tile with serif italic "T·É" mark) / Brand swatches (3 colored 56px tiles with name + hex below).

**Membres:** Table (5 cols: Personne with 32px avatar + name + email / Rôle / OEAQ # / Statut pill (active verdigris / invited ochre) / Gérer btn). Then "Permissions par défaut" toggles.

**Intégrations:** Auto-fill 240px card grid. Each card: 36×36 paper-2 logo + status pill (connected verdigris with dot / available paper-2) → serif 16px name → desc → foot row (Depuis date + Gérer btn, OR Connecter btn).

**Utilisation:** 4-col usage grid (each with k + serif 22px value + optional /max + 4px bar with navy fill) → 5-row breakdown bars (140px label / 8px bar with category color / value) → 6-col history bar chart (140px tall bars with navy gradient + month label). Then info banner (navy-tint bg, navy-ring icon, "La facturation est gérée par votre cabinet").

**Sécurité:** Password card + Authentification toggles (verdigris when on) + Sessions list (device emoji in 36×36 r-md paper-2 tile + name + meta + "Actuel" navy pill OR Déconnecter btn) + Journal d'audit (120px when col + what with bold author).

**Préférences:** Affichage facts + Agent IA toggles + Notifications toggles.

### 8 — Aide (`aide.html`)

2-col layout (220px sticky TOC + main, 48px gap). H1 "Comment Éval Immo fonctionne" with subtitle, plus a 320px search pill at top-right.

**Left TOC:** "Sommaire" uppercase label + 9 anchor buttons. Highlights active section based on scroll position (160px offset). Two extra links to Paramètres + Soutien at bottom.

**Sections (gap 64px, max-width 720px):** Each has eyebrow + serif 28px title + serif 16px lead.

| Section | Content |
|---|---|
| Survol | Flow diagram: 5 connected `flow-step` cards (n° + label + desc) separated by `›` arrows. Then 3 `pillar` cards. |
| Créer un dossier | Numbered serif list with circular step markers (30×30 numbered circles). CTA "Démarrer un dossier →". |
| Les 5 étapes | 2-col card grid, each stage card has num + name + what + details. |
| L'agent IA | 2-col "Ce qu'il fait / Ce qu'il ne fait pas" cards (latter has dashed border, ul items use `—` ochre or oxblood bullets). Then ochre tinted prompt explainer. |
| Bibliothèque & Modèles | 2-col `biblio-aide-card` rows (serif label / sans desc) + H3 + serif paragraph. |
| Conformité OEAQ | Checklist of 6 items (verdigris check + sans 14px). |
| Raccourcis clavier | 2-col groups with `<kbd>` styled keys (paper-hi bg, double bottom border) + desc. |
| FAQ | Single white panel containing accordion items. Click to expand → caret rotates, serif body in fi-a. |
| Nous joindre | 3-col contact cards (serif H4 + desc + navy email links). |

---

## Interactions & Behavior

### Navigation
- All sidebar nav items use plain `<a href>` for full-page navigation between HTML files. Card/row clicks set `window.location.href`.
- Recent / pinned dossier sidebar links → `dossier.html?id={id}`
- "Nouveau dossier" sidebar item → `nouveau-dossier.html`
- Dossier card / row click → `dossier.html?id={id}`
- Archive row "Voir" / "Cloner" → `dossier.html?id={id}` (mock)
- Firm card menu → Paramètres / Aide / Se déconnecter (→ `login.html`)

### Hover states
- **Clickable cards** (dossier card, model card): border → rule-strong + `--shadow-hover` lift, 0.15s transition. Pin button fades in (opacity 0 → 1).
- **List rows** (dossier row, archive row, biblio table row, comp row): bg → paper-2, no transform.
- **Sidebar nav**: bg → `rgba(31,30,28,.04)`, color → ink, 0.12s.
- **All buttons**: transition 0.15s on bg, transform 0.05s on active.
- **Stepper steps**: color → ink.

### Sorting
- List view headers + Bibliothèque table headers: click toggles direction, caret rotates 180° between asc/desc, only the active column shows a caret (others fade in at 55% on hover). Default direction is desc for numeric/date columns, asc for string columns.

### Filtering
- Pills and dropdowns immediately filter the visible list/grid. "Réinitialiser" appears when any filter is non-default.
- Year strip filter on Archives: clicking a year filters; "Toutes années" resets.

### Wizards & multi-step
- Stepper steps in Nouveau dossier: clicking a *previous* step jumps back, clicking forward steps is disabled until the current step's required fields are filled (controlled by `canAdvance`).
- Dossier detail stepper: any step is clickable (no validation).

### Forms
- Custom Dropdown: opens on click, closes on outside click + Escape. Drops downward.
- Date input: clicking anywhere on the field calls `e.currentTarget.showPicker?.()` — picker opens consistently across browsers. Visual: hide native indicator, overlay our own calendar SVG via `background-image`.
- Required fields shown with `*` in oxblood. Submit button disabled until all required + accept checkbox.

### Animations
- Login left panel: rotating quotes (8s `setInterval`), active dot widens to 20px.
- Loading skeleton: shimmer animation `100% 0 → -100% 0` over 1.6s linear infinite.
- Switch toggle: knob `translateX(16px)` over .18s ease, bg fades.
- Stepper "now" step: subtle pulse not used; rather a static rounded bg.
- Login Sent step: `.ss-pulse` keyframe (0/100% box-shadow 0 0 0 0 ochre 36%, 50% expanded 6px transparent), 1.3s ease-in-out infinite.
- Firm menu chevron: rotates 90° when open.

---

## State Management

For each screen, lift these into the target framework's state (React Context, Vuex, etc) or fetch from API:

| Screen | State |
|---|---|
| Dossiers | `query`, `statusFilter`, `sort`, `sortDir`, `view` (grid/rows), `viewState` (success/loading/empty/error/partial), `dossiers[]` (with optimistic pin toggle) |
| Dossier | `stage` (1-5), `d` (resolved from `?id=`), `ext` (extra details) |
| Nouveau dossier | `step`, `path`, `property`, `mandate{type,client,contact,phone,email,dateValeur,dateEcheance,modele,notes}`, `created` |
| Bibliothèque | `tab`, per-tab filters (`query`, `district`, `type`), `sort`, `sortDir` |
| Archives | `query`, `year`, `mandate`, `items[]` |
| Paramètres | `section`, persisted to `?section=` via `history.replaceState` |
| Aide | `query` (TOC filter), `active` (scroll-tracked) |
| Login | `mode` (signin/signup/sent), `email`, `password`, `showPw`, `remember`, sign-up form `data`, `quoteIdx` |

---

## Assets

- **Font: Source Serif 4** from Google Fonts — `https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,400..700&display=swap`. Used for h1/h2, addresses, key headlines, signature.
- **System sans** — `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif`. No web font needed.
- **All icons are inline SVG** in `components.jsx` (`Icon.Folder`, `Library`, `Template`, `Archive`, `Settings`, `Glass`, `Grid`, `Rows`, `Plus`, `Pin`, `Bell`, `Chevron`, `ChevronLeft`, `Check`, `Print`, `Share`, `Edit`, `Clock`, `Send`, `Sparkle`, `More`, `Seal`, `Plug`, `Help`, `Paperclip`). Stroke 1.4–1.6, round line-caps/joins. Lift these as-is.
- **No raster images / logos used** — the "logo" in Paramètres > Cabinet is an inline serif italic glyph "T·É" inside a rounded tile. The DocuSign / QuickBooks / Outlook integration cards use 2-letter monogram tiles. Replace with real logos in production.
- **Signature** is an inline SVG path (`M10,55 C30,20 60,75 …`) intended as a placeholder for an actual stored signature image.

---

## Files in this bundle

### HTML entrypoints (one per screen)
- `login.html`
- `mes-dossiers.html`
- `dossier.html`
- `nouveau-dossier.html`
- `bibliotheque.html`
- `modeles.html`
- `archives.html`
- `parametres.html`
- `aide.html`
- `style-system.html` (visual reference of tokens/components)

### Shared React components & data
- `components.jsx` — `Sidebar`, `DossierCard`, `DossierRow`, `Dropdown`, `Icon` object, `formatMoney`, `formatNum`
- `data.js` — `DOSSIERS[]`, `STATUS_META`, `STAGE_LABELS`
- `dossier-data.js` — extra details (comps, activity, documents) for the example dossier `2026-0418`
- `biblio-data.js` — `VENTES`, `MARCHES`, `COUTS`, `TAUX`, `DISTRICTS`
- `archives-data.js` — `ARCHIVES[]`

### Per-page JSX + CSS
- `mes-dossiers.jsx`
- `dossier.jsx` + `dossier-stages.jsx` (5 stage view components) + `dossier.css`
- `nouveau-dossier.jsx` + `nouveau-dossier.css`
- `bibliotheque.jsx` + `bibliotheque.css`
- `modeles.jsx` + `modeles.css`
- `archives.jsx` + `archives.css`
- `parametres.jsx` + `parametres-sections.jsx` + `parametres.css`
- `aide.jsx` + `aide.css`
- `login.jsx` + `login.css`

### Shared stylesheet
- `app.css` — design tokens (CSS custom properties), shell, sidebar, stepper, buttons, forms, status pills, filter pills, custom Dropdown, dot-sep, eyebrow, default page topbar + toolbar, dossier card grid, skeleton/empty/error states.

---

## Implementation suggestions

1. **Replicate the design tokens** in your framework's token system first. `app.css` `:root` is the single source of truth.
2. **Build the shell** (sidebar + main pane) as a layout component before per-page work — every screen depends on it.
3. **Build the shared primitives** next: Button, Pill, Dropdown, FilterPillGroup, Stepper, Card / Panel / SideCard, ToggleSwitch, StatusChip, MandatePill.
4. **Per-screen**, work top-down: topbar → toolbar → body. Each screen's CSS file mirrors the source mock 1:1.
5. **Replace mock data** with API calls. The current JS files are deliberately structured as flat arrays — easy to swap for `useQuery` / Pinia stores.
6. **French copy is part of the design.** Every label, placeholder, and microcopy line is in Québec French — preserve verbatim including accents.
7. **Verify accessibility**: the prototypes use proper roles (`role="menu"`, `role="listbox"`, `aria-haspopup`, `aria-expanded`) for the firm popover and Dropdown — keep these conventions.

— end of handoff
