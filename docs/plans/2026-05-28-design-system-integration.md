# Design System Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current liquid-glass aesthetic with the warm paper design from `design_handoff_eval_immo`, covering all existing pages and 6 new pages.

**Architecture:** CSS custom properties drive the entire token system via `:root` / `[data-theme="dark"]`; Tailwind `@theme` maps tokens to utility classes. The sidebar is rewritten from a callback-driven component to a route-based fixed-position nav. The TabBar (animated glass pill) is replaced by a flat underlined Stepper.

**Tech Stack:** Next.js (App Router), Tailwind v4 (`@theme`), `next/font/google` (Source Serif 4), `next/navigation` (`usePathname`, `useParams`, `useRouter`), CSS custom properties.

**Assumptions:**
- Tailwind v4 is installed (config via CSS `@theme`, no `tailwind.config.ts`). Will NOT work with v3.
- `[data-theme="dark"]` on `<html>` is the dark-mode mechanism — unchanged.
- Backend (Supabase, runtime-api, lib/, hooks/, types/) is NOT touched.
- Design source of truth: `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\README.md` and per-page `.jsx` / `.css` files. Where the spec doc (`2026-05-28-design-system-rework.md`) conflicts with README, the README wins (radii use the token values; interactive components are NOT forced to `border-radius: 0`).

---

## File Map

### Modified
| File | Change |
|------|--------|
| `src/app/globals.css` | Full token replacement — drop glass vars, add paper/ink/navy tokens |
| `src/app/layout.tsx` | Source Serif 4 replaces Cormorant + Inter |
| `src/components/layout/Sidebar.tsx` | Full rewrite — route-based, fixed 260px, slide transform |
| `src/components/layout/SidebarNav.tsx` | Route links for 7 nav items (Travail group + bottom) |
| `src/components/layout/SidebarFooter.tsx` | Firm card + popover (Paramètres/Aide/Déconnecter) + theme toggle |
| `src/components/layout/SidebarWordmark.tsx` | Update to new wordmark style |
| `src/components/layout/TabBar.tsx` | Replaced by Stepper (keep file, gutted and re-exported as alias) |
| `src/components/dossiers/DossierCard.tsx` | Full visual rework — paper tokens, status chip, stage bar, pin |
| `src/components/shared/EmptyState.tsx` | Serif heading, navy ring icon |
| `src/components/shared/Toast.tsx` | Flat, no glass |
| `src/app/dossiers/page.tsx` | Grid/list toggle, toolbar, DossierRow, new Sidebar props |
| `src/app/dossier/[id]/page.tsx` | Topbar, Stepper, body grid, SideCards, AgentChat, new Sidebar props |
| `src/components/panels/DossierPanel.tsx` | Visual rework (kv-grid, visit row) |
| `src/components/panels/MarchePanel.tsx` | Visual rework (comp-table, recon box) |
| `src/components/panels/AnalysePanel.tsx` | Visual rework (approach-grid, weighted recon) |
| `src/components/panels/SynthesePanel.tsx` | Visual rework (hero, attestation) |
| `src/components/panels/RapportPanel.tsx` | Visual rework (cover preview, sections) |
| `src/app/login/page.tsx` | Full two-column rework |

### Created
| File | Purpose |
|------|---------|
| `src/components/layout/SidebarToggle.tsx` | Chevron toggle button pinned to sidebar edge |
| `src/components/layout/Stepper.tsx` | Underlined step tabs (replaces TabBar pill) |
| `src/components/dossiers/DossierRow.tsx` | List-view row (grid columns) |
| `src/components/dossiers/StageBar.tsx` | 5-segment progress bar for DossierCard |
| `src/components/dossier/SideCard.tsx` | Right-column aside cards |
| `src/components/dossier/AgentChat.tsx` | Fixed bottom agent chat strip |
| `src/app/bibliotheque/page.tsx` | 4-tab reference library |
| `src/app/modeles/page.tsx` | Template card grid |
| `src/app/archives/page.tsx` | Grouped completed dossiers |
| `src/app/parametres/page.tsx` | 7-section settings |
| `src/app/aide/page.tsx` | FAQ + accordion |
| `src/app/dossier/nouveau/page.tsx` | Smart entry form |
| `src/data/bibliotheque-mock.ts` | Ventes, Marchés, Coûts, Taux mock data |
| `src/data/archives-mock.ts` | Archive rows mock data |
| `src/data/modeles-mock.ts` | Template cards mock data |

---

## Task 1: Replace CSS design tokens (globals.css)

**Files:**
- Modify: `src/app/globals.css`

**Security flag:** `none`

- [ ] **Step 1: Replace entire globals.css**

Replace `src/app/globals.css` with:

```css
@import "tailwindcss";

/* ── DARK MODE ── */
@custom-variant dark (&:where([data-theme="dark"], [data-theme="dark"] *));

/* ── TAILWIND THEME MAPPING ── */
@theme {
  --font-serif: var(--font-source-serif), "Iowan Old Style", Georgia, serif;
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif;

  --color-paper:     var(--paper);
  --color-paper-2:   var(--paper-2);
  --color-paper-3:   var(--paper-3);
  --color-paper-hi:  var(--paper-hi);
  --color-ink:       var(--ink);
  --color-ink-2:     var(--ink-2);
  --color-ink-3:     var(--ink-3);
  --color-ink-mute:  var(--ink-mute);
  --color-ink-faint: var(--ink-faint);
  --color-rule:      var(--rule);
  --color-rule-soft: var(--rule-soft);
  --color-navy:      var(--navy);
  --color-navy-hi:   var(--navy-hi);
  --color-navy-deep: var(--navy-deep);
  --color-navy-tint: var(--navy-tint);
  --color-verdigris: var(--verdigris);
  --color-ochre:     var(--ochre);
  --color-oxblood:   var(--oxblood);

  --radius-sm:   6px;
  --radius-md:   10px;
  --radius-lg:   14px;
  --radius-pill: 999px;
}

/* ── LIGHT TOKENS ── */
:root {
  --paper:       #faf9f5;
  --paper-2:     #f3f1ea;
  --paper-3:     #ebe8dd;
  --paper-hi:    #ffffff;
  --ink:         #1f1e1c;
  --ink-2:       #2c2a26;
  --ink-3:       #4a4640;
  --ink-mute:    #6b6760;
  --ink-faint:   #a8a299;
  --rule:        #e6e2d6;
  --rule-soft:   #efece1;
  --rule-strong: #cdc7b7;
  --navy:        #1c3559;
  --navy-hi:     #284a7a;
  --navy-deep:   #12233d;
  --navy-tint:   #eef1f7;
  --sienna:      #8a4a1f;
  --verdigris:   #4a6b54;
  --ochre:       #b88a3e;
  --oxblood:     #8a3030;

  --shadow-card:  none;
  --shadow-hover: 0 2px 8px -4px rgba(31,30,28,.08), 0 8px 24px -16px rgba(31,30,28,.12);
  --shadow-float: 0 12px 32px -16px rgba(31,30,28,.18);

  --r-sm:   6px;
  --r-md:   10px;
  --r-lg:   14px;
  --r-pill: 999px;
}

/* ── DARK TOKENS ── */
[data-theme="dark"] {
  --paper:       #1a1814;
  --paper-2:     #221f1a;
  --paper-3:     #2c2922;
  --paper-hi:    #26231d;
  --ink:         #f3eddc;
  --ink-2:       #e6dfca;
  --ink-3:       #c4bda5;
  --ink-mute:    #948c79;
  --ink-faint:   #645e51;
  --rule:        #393530;
  --rule-soft:   #2e2b25;
  --rule-strong: #4f4a40;
  --navy:        #7da4d6;
  --navy-hi:     #9bbce5;
  --navy-deep:   #5d83b8;
  --navy-tint:   rgba(125,164,214,.14);
  --verdigris:   #8bb89a;
  --ochre:       #d8a85e;
  --oxblood:     #d27878;

  --shadow-hover: 0 2px 8px -4px rgba(0,0,0,.20), 0 8px 24px -16px rgba(0,0,0,.28);
  --shadow-float: 0 12px 32px -16px rgba(0,0,0,.40);
}

/* ── BASE ── */
@layer base {
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { height: 100%; }
  body {
    font-family: var(--font-sans);
    font-size: 14px;
    color: var(--ink);
    background: var(--paper);
    transition: background .3s, color .3s;
    overflow: hidden;
  }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(31,30,28,.14); border-radius: 999px; }
  [data-theme="dark"] ::-webkit-scrollbar-thumb { background: rgba(255,255,255,.12); }
}

/* ── SIDEBAR ── */
.sidebar {
  position: fixed;
  top: 0; bottom: 0; left: 0;
  width: 260px;
  background: var(--paper);
  border-right: 1px solid var(--rule-soft);
  transform: translateX(-260px);
  transition: transform .22s cubic-bezier(.4,0,.2,1);
  z-index: 40;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar.open { transform: translateX(0); }
.sidebar-toggle {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  left: 0;
  transition: left .22s cubic-bezier(.4,0,.2,1);
  z-index: 41;
}
.sidebar.open ~ .sidebar-toggle { left: 260px; }

/* ── MAIN ── */
.main-content { width: 100%; height: 100%; overflow: hidden; display: flex; flex-direction: column; }

/* ── DOSSIER GRID ── */
.dossier-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

/* ── CARD HOVER ── */
.card-hover {
  transition: border-color .15s, box-shadow .15s;
}
.card-hover:hover {
  border-color: var(--rule-strong) !important;
  box-shadow: var(--shadow-hover) !important;
}

/* ── CARD ENTRANCE ── */
@keyframes cardIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card-enter { animation: cardIn 260ms cubic-bezier(.22,.68,0,1.2) both; }

/* ── SKELETON SHIMMER ── */
@keyframes shimmer {
  from { background-position: 100% 0; }
  to   { background-position: -100% 0; }
}
.skeleton-shimmer {
  background: linear-gradient(90deg, var(--paper-2) 25%, var(--paper-3) 50%, var(--paper-2) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.6s linear infinite;
}

/* ── PINNED CARD ── */
.card-pinned { border-left: 2.5px solid var(--navy) !important; }

/* ── STEPPER ── */
.stepper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 14px 0 0;
  position: relative;
}
.stepper::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 0; right: 0;
  height: 1px;
  background: var(--rule-soft);
}
.stepper .step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--ink-mute);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color .15s, border-color .15s;
  background: none;
  border-top: none; border-left: none; border-right: none;
  margin-bottom: -1px;
  position: relative;
  z-index: 1;
  white-space: nowrap;
}
.stepper .step:hover { color: var(--ink); }
.stepper .step.done { color: var(--ink-2); }
.stepper .step.done .step-num { color: var(--verdigris); }
.stepper .step.now {
  color: var(--ink);
  font-weight: 500;
  background: rgba(31,30,28,.06);
  border-radius: var(--r-md);
  border-bottom-color: var(--navy);
}
[data-theme="dark"] .stepper .step.now { background: rgba(255,255,255,.07); }
.step-num {
  font-size: 13px;
  color: var(--ink-faint);
  min-width: 18px;
  text-align: center;
}

/* ── BUTTONS ── */
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  font-family: var(--font-sans);
  font-size: 14px; font-weight: 500;
  padding: 9px 18px;
  border-radius: var(--r-md);
  border: none;
  background: var(--ink);
  color: var(--paper-hi);
  cursor: pointer;
  transition: background .15s, transform .05s;
  text-decoration: none;
  white-space: nowrap;
}
.btn:active { transform: translateY(1px); }
.btn:disabled { opacity: .35; cursor: not-allowed; }
.btn.accent { background: var(--navy); color: #fff; }
.btn.accent:hover { background: var(--navy-hi); }
.btn.secondary { background: transparent; border: 1px solid var(--rule); color: var(--ink); }
.btn.secondary:hover { background: var(--paper-2); border-color: var(--rule-strong); }
.btn.ghost { background: transparent; border: none; color: var(--ink-mute); }
.btn.ghost:hover { background: var(--paper-2); color: var(--ink); }
.btn.btn-sm { font-size: 12.5px; padding: 5px 12px; }
.btn.btn-full { width: 100%; font-size: 13px; padding: 8px 12px; }

/* ── PILLS ── */
.pill {
  display: inline-flex; align-items: center;
  padding: 7px 14px;
  border-radius: var(--r-pill);
  border: 1px solid var(--rule);
  font-size: 13px; font-family: var(--font-sans);
  color: var(--ink-3);
  background: transparent;
  cursor: pointer;
  transition: background .12s, color .12s;
  white-space: nowrap;
}
.pill:hover { background: var(--paper-2); }
.pill.active { background: var(--ink); color: var(--paper-hi); border-color: var(--ink); }
[data-theme="dark"] .pill.active { background: var(--ink); border-color: var(--ink); }

/* ── STATUS CHIP ── */
.status-chip {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-family: var(--font-sans);
  color: var(--ink-mute);
}
.status-chip::before {
  content: '';
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.status-chip.encours  { color: var(--ochre); }
.status-chip.complet  { color: var(--verdigris); }
.status-chip.brouillon{ color: var(--ink-faint); }

/* ── FORM FIELDS ── */
.field {
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--ink);
  background: var(--paper-hi);
  border: 1px solid var(--rule);
  border-radius: var(--r-md);
  padding: 9px 12px;
  width: 100%;
  transition: border-color .15s, box-shadow .15s;
}
.field:focus {
  outline: none;
  border-color: var(--ink-mute);
  box-shadow: 0 0 0 3px rgba(31,30,28,.04);
}
[data-theme="dark"] .field:focus { box-shadow: 0 0 0 3px rgba(255,255,255,.04); }

/* ── PANELS ── */
.panel {
  background: var(--paper-hi);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  padding: 22px 24px 24px;
}
.panel-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 18px;
}
.panel-title {
  font-family: var(--font-serif);
  font-size: 22px; font-weight: 500;
  letter-spacing: -.005em;
  color: var(--ink);
}

/* ── SIDE CARDS ── */
.side-card {
  background: var(--paper-hi);
  border: 1px solid var(--rule);
  border-radius: var(--r-lg);
  padding: 16px 18px 18px;
}
.side-card-head {
  font-family: var(--font-sans);
  font-size: 11px; font-weight: 500;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin-bottom: 12px;
}

/* ── EYEBROW ── */
.eyebrow {
  font-family: var(--font-sans);
  font-size: 11px; font-weight: 500;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

/* ── TOPBAR ── */
.topbar {
  padding: 28px 40px 0;
  flex-shrink: 0;
}
.page-h1 {
  font-family: var(--font-serif);
  font-size: 36px; font-weight: 500;
  letter-spacing: -.015em;
  line-height: 1.1;
  color: var(--ink);
}
.dossier-h1 {
  font-family: var(--font-serif);
  font-size: 32px; font-weight: 500;
  letter-spacing: -.015em;
  line-height: 1.15;
  color: var(--ink);
}

/* ── SCROLL FADE MASK ── */
.scroll-fade {
  -webkit-mask-image: linear-gradient(to bottom, transparent 0, black 24px, black calc(100% - 48px), transparent 100%);
  mask-image: linear-gradient(to bottom, transparent 0, black 24px, black calc(100% - 48px), transparent 100%);
}

/* ── AGENT CHAT WRAP ── */
.agent-chat-wrap {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 30;
  transition: left .22s cubic-bezier(.4,0,.2,1);
}
.agent-chat-wrap.sidebar-open { left: 260px; }
.agent-chat-inner {
  pointer-events: auto;
  max-width: 760px;
  margin: 0 auto;
  padding: 0 40px 24px;
}
.agent-chat-gradient {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 120px;
  background: linear-gradient(180deg, transparent 0%, var(--paper) 60%);
  pointer-events: none;
}
.agent-chat-box {
  position: relative;
  background: var(--paper-hi);
  border: 1px solid var(--rule);
  border-radius: 18px;
  overflow: hidden;
}

/* ── SIDEBAR NAV ITEM ── */
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px;
  border-radius: var(--r-md);
  font-size: 14px;
  font-family: var(--font-sans);
  color: var(--ink-2);
  text-decoration: none;
  transition: background .12s, color .12s;
  cursor: pointer;
}
.nav-item:hover { background: rgba(31,30,28,.04); color: var(--ink); }
.nav-item.active { background: rgba(31,30,28,.06); color: var(--ink); font-weight: 500; }
[data-theme="dark"] .nav-item:hover { background: rgba(255,255,255,.05); }
[data-theme="dark"] .nav-item.active { background: rgba(255,255,255,.07); }
.nav-item .nav-icon { opacity: .7; }
.nav-item.active .nav-icon { opacity: 1; }
.nav-count { margin-left: auto; font-size: 12px; color: var(--ink-faint); }
```

- [ ] **Step 2: Verify build**

Run: `cd C:/Users/simon/eval-immo && npm run build 2>&1 | tail -20`
Expected: Build succeeds (CSS warnings OK, no errors)

- [ ] **Step 3: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/globals.css && git commit -m "design: replace glass tokens with warm paper design system"
```

---

## Task 2: Update fonts (layout.tsx)

**Files:**
- Modify: `src/app/layout.tsx`

**Security flag:** `none`

- [ ] **Step 1: Update layout.tsx**

```tsx
import type { Metadata } from 'next'
import { Source_Serif_4 } from 'next/font/google'
import Providers from '@/providers/Providers'
import './globals.css'

const sourceSerif = Source_Serif_4({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  style: ['normal', 'italic'],
  axes: ['opsz'],
  variable: '--font-source-serif',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Éval Immo',
  description: 'Espace de travail pour évaluateurs agréés — pipeline d\u2019évaluation immobilière assisté par IA.',
  robots: { index: false, follow: false },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" data-theme="light">
      <body className={sourceSerif.variable}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

- [ ] **Step 2: Verify build**

Run: `cd C:/Users/simon/eval-immo && npm run build 2>&1 | tail -20`
Expected: Build succeeds

- [ ] **Step 3: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/layout.tsx && git commit -m "design: Source Serif 4 replaces Cormorant Garamond + Inter"
```

---

## Task 3: Rewrite Sidebar component

**Files:**
- Modify: `src/components/layout/Sidebar.tsx`
- Modify: `src/components/layout/SidebarNav.tsx`
- Modify: `src/components/layout/SidebarWordmark.tsx`
- Modify: `src/components/layout/SidebarFooter.tsx`
- Create: `src/components/layout/SidebarToggle.tsx`

**Security flag:** `none`

**Does NOT cover:** Pinned/recent dossier list wiring (those blocks remain empty/stubbed for now; real data comes from existing runtime-api calls that can be re-added in a later pass).

- [ ] **Step 1: Create SidebarToggle.tsx**

```tsx
'use client'

interface Props {
  open: boolean
  onToggle: () => void
}

export default function SidebarToggle({ open, onToggle }: Props) {
  return (
    <button
      onClick={onToggle}
      aria-label={open ? 'Fermer la navigation' : 'Ouvrir la navigation'}
      className="sidebar-toggle w-7 h-14 flex items-center justify-center bg-[var(--paper)] border border-[var(--rule-soft)] border-l-0 rounded-r-[var(--r-md)] text-[var(--ink-mute)] hover:text-[var(--ink)] hover:bg-[var(--paper-2)] transition-colors cursor-pointer"
      style={{ marginTop: '-28px' }}
    >
      <svg width="10" height="16" viewBox="0 0 10 16" fill="none" aria-hidden="true"
        style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .22s' }}>
        <path d="M3 3l4 5-4 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </button>
  )
}
```

- [ ] **Step 2: Rewrite SidebarWordmark.tsx**

```tsx
import Link from 'next/link'
import { APP_WORDMARK } from '@/constants/app'

export default function SidebarWordmark() {
  return (
    <div className="px-5 py-5 border-b border-[var(--rule-soft)]">
      <Link href="/dossiers" className="block no-underline">
        <div
          className="text-[22px] font-medium leading-tight"
          style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.015em', color: 'var(--ink)' }}
        >
          Éval{' '}
          <span style={{ color: 'var(--navy)', fontStyle: 'italic' }}>Immo</span>
        </div>
        <div className="text-[11px] mt-0.5" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)', letterSpacing: '.01em' }}>
          Évaluateurs agréés — Québec
        </div>
      </Link>
    </div>
  )
}
```

- [ ] **Step 3: Rewrite SidebarNav.tsx**

```tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV_ITEMS = [
  { href: '/dossiers',     label: 'Dossiers',     icon: FolderIcon,  count: null },
  { href: '/bibliotheque', label: 'Bibliothèque', icon: LibraryIcon, count: 348 },
  { href: '/modeles',      label: 'Modèles',      icon: TemplateIcon,count: 6 },
  { href: '/archives',     label: 'Archives',     icon: ArchiveIcon, count: 142 },
]

export default function SidebarNav() {
  const pathname = usePathname()
  return (
    <div className="px-3 py-3 flex flex-col gap-px">
      <Link
        href="/dossier/nouveau"
        className="nav-item mb-1"
        style={{ color: 'var(--navy)', fontWeight: 500 }}
      >
        <PlusIcon />
        <span>Nouveau dossier</span>
      </Link>
      {NAV_ITEMS.map(item => (
        <Link
          key={item.href}
          href={item.href}
          className={`nav-item ${pathname === item.href || pathname.startsWith(item.href + '/') ? 'active' : ''}`}
        >
          <span className="nav-icon"><item.icon /></span>
          <span>{item.label}</span>
          {item.count != null && <span className="nav-count">{item.count}</span>}
        </Link>
      ))}
    </div>
  )
}

function PlusIcon() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
}
function FolderIcon() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2 5a1 1 0 011-1h3l1.5 2H13a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1V5z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/></svg>
}
function LibraryIcon() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="2" y="3" width="3" height="10" rx="1" stroke="currentColor" strokeWidth="1.4"/><rect x="6.5" y="3" width="3" height="10" rx="1" stroke="currentColor" strokeWidth="1.4"/><path d="M11 4l2.5 8.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
}
function TemplateIcon() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.4"/><path d="M2 6h12M6 6v8" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
}
function ArchiveIcon() {
  return <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="2" y="4" width="12" height="9" rx="1" stroke="currentColor" strokeWidth="1.4"/><path d="M1 4h14M6 8h4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
}
```

- [ ] **Step 4: Rewrite SidebarFooter.tsx**

```tsx
'use client'

import { useState } from 'react'
import Link from 'next/link'

interface Props {
  onSignOut?: () => void
}

export default function SidebarFooter({ onSignOut }: Props) {
  const [popoverOpen, setPopoverOpen] = useState(false)

  function handleThemeToggle() {
    const html = document.documentElement
    const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
    html.setAttribute('data-theme', next)
    localStorage.setItem('evalimmo-theme', next)
  }

  return (
    <div className="mt-auto border-t border-[var(--rule-soft)]">
      {/* Theme toggle */}
      <div className="px-4 py-3 flex items-center justify-between">
        <span className="text-[12px]" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>Apparence</span>
        <button
          onClick={handleThemeToggle}
          className="text-[12px] px-3 py-1 rounded-[var(--r-pill)] border border-[var(--rule)] hover:bg-[var(--paper-2)] transition-colors cursor-pointer"
          style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}
        >
          Changer
        </button>
      </div>

      {/* Firm card */}
      <div className="relative px-3 pb-3">
        <button
          onClick={() => setPopoverOpen(v => !v)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-[var(--r-md)] hover:bg-[var(--paper-2)] transition-colors text-left cursor-pointer border-none bg-transparent"
          aria-expanded={popoverOpen}
          aria-haspopup="menu"
        >
          <div
            className="w-8 h-8 rounded-[var(--r-md)] flex items-center justify-center flex-shrink-0 text-[13px] font-semibold text-white"
            style={{ background: 'var(--navy)', fontFamily: 'var(--font-sans)' }}
          >
            MT
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[13px] font-medium truncate" style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)' }}>Maxime Tremblay</div>
            <div className="text-[11px] truncate" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>É.A. — OEAQ 4218</div>
          </div>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"
            style={{ color: 'var(--ink-faint)', flexShrink: 0, transform: popoverOpen ? 'rotate(180deg)' : '', transition: 'transform .15s' }}>
            <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        {popoverOpen && (
          <div
            className="absolute bottom-full left-3 right-3 mb-1 rounded-[var(--r-lg)] border border-[var(--rule)] overflow-hidden"
            style={{ background: 'var(--paper-hi)', boxShadow: 'var(--shadow-float)' }}
            role="menu"
          >
            <Link href="/parametres" className="flex items-center gap-2.5 px-3 py-2.5 text-[13px] hover:bg-[var(--paper-2)] transition-colors no-underline" style={{ color: 'var(--ink-2)', fontFamily: 'var(--font-sans)' }} role="menuitem" onClick={() => setPopoverOpen(false)}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="2" stroke="currentColor" strokeWidth="1.4"/><path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
              Paramètres
            </Link>
            <Link href="/aide" className="flex items-center gap-2.5 px-3 py-2.5 text-[13px] hover:bg-[var(--paper-2)] transition-colors no-underline" style={{ color: 'var(--ink-2)', fontFamily: 'var(--font-sans)' }} role="menuitem" onClick={() => setPopoverOpen(false)}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="1.4"/><path d="M7 10v-1M7 4.5c0-1 1.5-1 1.5 0 0 .8-.5 1.2-1 1.5-.5.3-.5.6-.5 1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
              Aide
            </Link>
            <div className="border-t border-[var(--rule-soft)]" />
            <button onClick={() => { setPopoverOpen(false); onSignOut?.() }} className="w-full flex items-center gap-2.5 px-3 py-2.5 text-[13px] text-left hover:bg-[var(--paper-2)] transition-colors cursor-pointer border-none bg-transparent" style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }} role="menuitem">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M5 2H3a1 1 0 00-1 1v8a1 1 0 001 1h2M9 10l3-3-3-3M12 7H5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
              Déconnexion
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 5: Rewrite Sidebar.tsx**

```tsx
'use client'

import { useState, useEffect } from 'react'
import SidebarWordmark from './SidebarWordmark'
import SidebarNav from './SidebarNav'
import SidebarFooter from './SidebarFooter'
import SidebarToggle from './SidebarToggle'

interface Props {
  onSignOut?: () => void
  currentDossierSlug?: string | null
  currentDossierAddress?: string | null
}

export default function Sidebar({ onSignOut, currentDossierSlug, currentDossierAddress }: Props) {
  const [open, setOpen] = useState(true)

  // Restore preference
  useEffect(() => {
    const saved = localStorage.getItem('sidebar-open')
    if (saved !== null) setOpen(saved === 'true')
  }, [])

  function toggle() {
    setOpen(v => {
      localStorage.setItem('sidebar-open', String(!v))
      return !v
    })
  }

  return (
    <>
      <nav className={`sidebar ${open ? 'open' : ''}`} aria-label="Navigation principale">
        <SidebarWordmark />

        {/* Current dossier block (dossier detail only) */}
        {currentDossierSlug && currentDossierAddress && (
          <div className="mx-3 my-2 px-3 py-2 rounded-[var(--r-md)] bg-[var(--paper-2)] border border-[var(--rule-soft)]">
            <div className="eyebrow mb-1">Dossier ouvert</div>
            <div className="text-[14px] font-medium truncate" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
              {currentDossierAddress}
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto scroll-fade">
          <div className="px-3 pt-2 pb-1">
            <span className="eyebrow">Travail</span>
          </div>
          <SidebarNav />
        </div>

        <SidebarFooter onSignOut={onSignOut} />
      </nav>

      <SidebarToggle open={open} onToggle={toggle} />
    </>
  )
}
```

- [ ] **Step 6: Verify build**

Run: `cd C:/Users/simon/eval-immo && npm run build 2>&1 | grep -E "(Error|error)" | head -20`
Expected: No errors

- [ ] **Step 7: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/components/layout/ && git commit -m "design: new route-based Sidebar with paper aesthetic and SidebarToggle"
```

---

## Task 4: Create Stepper component

**Files:**
- Create: `src/components/layout/Stepper.tsx`

**Security flag:** `none`

- [ ] **Step 1: Create Stepper.tsx**

```tsx
'use client'

import { TABS } from '@/constants/app'
import type { TabId } from '@/types'

interface Props {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  completedTabs?: TabId[]
}

const STEP_ORDER: TabId[] = ['dossier', 'marche', 'analyse', 'synthese', 'rapport']

export default function Stepper({ activeTab, onTabChange, completedTabs = [] }: Props) {
  const activeIdx = STEP_ORDER.indexOf(activeTab)

  return (
    <div className="stepper px-10" role="tablist" aria-label="Étapes du dossier">
      {TABS.map((tab, i) => {
        const isDone = completedTabs.includes(tab.id) || i < activeIdx
        const isNow  = tab.id === activeTab
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isNow}
            className={`step ${isDone ? 'done' : ''} ${isNow ? 'now' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span className="step-num">
              {isDone ? (
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M2.5 7l3 3 6-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              ) : (
                i + 1
              )}
            </span>
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/components/layout/Stepper.tsx && git commit -m "design: add Stepper component (underlined tabs, replaces glass TabBar)"
```

---

## Task 5: Update /dossiers page

**Files:**
- Modify: `src/app/dossiers/page.tsx`
- Modify: `src/components/dossiers/DossierCard.tsx`
- Create: `src/components/dossiers/DossierRow.tsx`
- Create: `src/components/dossiers/StageBar.tsx`

**Security flag:** `none`

**Does NOT cover:** Actual filtering/sorting logic changes — existing `filterDossiers` and `sortDossiers` lib functions are reused as-is.

- [ ] **Step 1: Create StageBar.tsx**

```tsx
interface Props {
  stage: number // 1–5
}

const STAGE_LABELS = ['Dossier', 'Marché', 'Analyse', 'Synthèse', 'Rapport']

export default function StageBar({ stage }: Props) {
  return (
    <div className="flex gap-0.5" role="progressbar" aria-valuenow={stage} aria-valuemin={1} aria-valuemax={5} aria-label={`Étape ${stage} sur 5`}>
      {STAGE_LABELS.map((label, i) => (
        <div
          key={label}
          title={label}
          className="h-[3px] flex-1 rounded-[2px] transition-colors"
          style={{
            background: i + 1 < stage
              ? 'var(--navy)'
              : i + 1 === stage
              ? 'var(--ochre)'
              : 'var(--rule)',
          }}
        />
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Rewrite DossierCard.tsx**

```tsx
'use client'

import type { Dossier, DossierStatus } from '@/types'
import { formatRelativeDate } from '@/lib/format-date'
import StageBar from './StageBar'

const STATUS_META: Record<DossierStatus, { label: string; cls: string }> = {
  'en-cours':  { label: 'En cours',  cls: 'encours' },
  complet:     { label: 'Complet',   cls: 'complet' },
  brouillon:   { label: 'Brouillon', cls: 'brouillon' },
}

interface Props {
  dossier: Dossier
  onClick: () => void
  onContextMenu?: (e: React.MouseEvent) => void
  index?: number
}

export default function DossierCard({ dossier, onClick, onContextMenu, index = 0 }: Props) {
  const meta = STATUS_META[dossier.status]
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      aria-label={`Ouvrir le dossier ${dossier.address}`}
      className={`card-enter card-hover group relative rounded-[var(--r-lg)] cursor-pointer border border-[var(--rule)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--navy)] ${dossier.pinned ? 'card-pinned' : ''}`}
      style={{ background: 'var(--paper-hi)', animationDelay: `${index * 45}ms` }}
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-start justify-between gap-2 mb-1">
          <span className={`status-chip text-[12px] ${meta.cls}`}>{meta.label}</span>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {dossier.pinned && (
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-[var(--r-pill)]" style={{ background: 'rgba(184,138,62,.12)', color: 'var(--ochre)' }}>Épinglé</span>
            )}
            {onContextMenu && (
              <button
                className="w-6 h-6 flex items-center justify-center rounded-[var(--r-sm)] hover:bg-[var(--paper-2)] transition-colors cursor-pointer bg-transparent border-none"
                onClick={e => { e.stopPropagation(); onContextMenu(e) }}
                aria-label="Options"
                style={{ color: 'var(--ink-mute)' }}
              >
                <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
                </svg>
              </button>
            )}
          </div>
        </div>

        <div className="text-[19px] font-medium leading-[1.2] pr-2 mb-0.5"
          style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.005em', color: 'var(--ink)' }}>
          {dossier.address}
        </div>
        <div className="text-[13px]" style={{ color: 'var(--ink-mute)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
          {dossier.property_type}
          {dossier.neighborhood && <span style={{ color: 'var(--ink-faint)' }}> · {dossier.neighborhood}</span>}
        </div>
      </div>

      {/* Stage bar */}
      <div className="px-5 pb-3">
        <StageBar stage={1} />
      </div>

      {/* Footer */}
      <div className="px-5 pb-4 flex items-center justify-between border-t border-[var(--rule-soft)] pt-3">
        <span className="text-[12px] truncate mr-2" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>
          {dossier.clientName || '—'}
        </span>
        <span className="text-[11.5px] flex-shrink-0" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>
          Mod. {formatRelativeDate(dossier.updatedAt)}
        </span>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create DossierRow.tsx**

```tsx
'use client'

import type { Dossier, DossierStatus } from '@/types'
import { formatRelativeDate } from '@/lib/format-date'

const STATUS_META: Record<DossierStatus, { label: string; cls: string }> = {
  'en-cours':  { label: 'En cours',  cls: 'encours' },
  complet:     { label: 'Complet',   cls: 'complet' },
  brouillon:   { label: 'Brouillon', cls: 'brouillon' },
}

interface Props {
  dossier: Dossier
  onClick: () => void
}

export default function DossierRow({ dossier, onClick }: Props) {
  const meta = STATUS_META[dossier.status]
  return (
    <div
      role="row"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && onClick()}
      className="grid items-center gap-4 px-5 py-3.5 border-t border-[var(--rule-soft)] hover:bg-[var(--paper-2)] cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[var(--navy)]"
      style={{ gridTemplateColumns: '2fr 140px 100px 80px 1fr 140px' }}
    >
      {/* Address */}
      <div>
        <div className="text-[15px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
          {dossier.address}
        </div>
        {dossier.neighborhood && (
          <div className="text-[12px]" style={{ color: 'var(--ink-faint)' }}>{dossier.neighborhood}</div>
        )}
      </div>
      {/* Type */}
      <div className="text-[13px]" style={{ color: 'var(--ink-3)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
        {dossier.property_type}
      </div>
      {/* Status */}
      <div><span className={`status-chip ${meta.cls}`}>{meta.label}</span></div>
      {/* Stage */}
      <div className="text-[13px] font-variant-numeric tabular-nums" style={{ color: 'var(--ink-mute)' }}>1/5</div>
      {/* Client */}
      <div className="text-[13px] truncate" style={{ color: 'var(--ink-3)' }}>{dossier.clientName || '—'}</div>
      {/* Modified */}
      <div className="text-[12px] text-right" style={{ color: 'var(--ink-faint)' }}>
        {formatRelativeDate(dossier.updatedAt)}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Update /dossiers page — replace Sidebar usage and add grid/list toggle + toolbar**

In `src/app/dossiers/page.tsx`:

1. Remove the `ThemeToggle` import and its JSX.
2. Replace the Sidebar `<Sidebar ... />` call — the new Sidebar takes only `onSignOut`:
   ```tsx
   <Sidebar onSignOut={handleSignOut} />
   ```
3. Add state: `const [view, setView] = useState<'grid' | 'list'>('grid')`
4. Add the toolbar above the card grid:
   ```tsx
   {/* Toolbar */}
   <div className="flex items-center gap-3 px-10 py-4 flex-shrink-0">
     {/* Search */}
     <div className="relative flex-1 max-w-[360px]">
       <svg className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true" style={{ color: 'var(--ink-faint)' }}>
         <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.4"/>
         <path d="M9.5 9.5l3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
       </svg>
       <input
         type="search"
         value={query}
         onChange={e => setQuery(e.target.value)}
         placeholder="Rechercher par adresse…"
         className="w-full pl-9 pr-4 py-2 text-[13.5px] rounded-[var(--r-pill)] border border-[var(--rule)] bg-[var(--paper-hi)] focus:outline-none focus:border-[var(--ink-mute)] transition-colors"
         style={{ fontFamily: 'var(--font-sans)', color: 'var(--ink)' }}
       />
     </div>

     {/* Filter pills */}
     <div className="flex gap-1.5">
       {(Object.keys(STATUS_FILTER_LABELS) as StatusFilter[]).map(f => (
         <button key={f} onClick={() => setStatusFilter(f)}
           className={`pill ${statusFilter === f ? 'active' : ''} text-[12.5px] py-1.5 px-3`}>
           {STATUS_FILTER_LABELS[f]}
         </button>
       ))}
     </div>

     <div className="ml-auto flex items-center gap-2">
       {/* Sort */}
       <select value={sort} onChange={e => setSort(e.target.value as SortKey)}
         className="text-[13px] px-3 py-1.5 rounded-[var(--r-md)] border border-[var(--rule)] bg-[var(--paper-hi)] cursor-pointer focus:outline-none"
         style={{ color: 'var(--ink-3)', fontFamily: 'var(--font-sans)' }}>
         {(Object.keys(SORT_LABELS) as SortKey[]).map(k => (
           <option key={k} value={k}>{SORT_LABELS[k]}</option>
         ))}
       </select>

       {/* View toggle */}
       <div className="flex rounded-[var(--r-md)] border border-[var(--rule)] overflow-hidden">
         <button onClick={() => setView('grid')} aria-pressed={view === 'grid'}
           className={`px-3 py-1.5 transition-colors cursor-pointer border-none ${view === 'grid' ? 'bg-[var(--ink)] text-[var(--paper-hi)]' : 'bg-[var(--paper-hi)] text-[var(--ink-mute)] hover:bg-[var(--paper-2)]'}`}>
           <svg width="13" height="13" viewBox="0 0 13 13" fill="currentColor" aria-hidden="true"><rect x="0" y="0" width="5.5" height="5.5"/><rect x="7.5" y="0" width="5.5" height="5.5"/><rect x="0" y="7.5" width="5.5" height="5.5"/><rect x="7.5" y="7.5" width="5.5" height="5.5"/></svg>
         </button>
         <button onClick={() => setView('list')} aria-pressed={view === 'list'}
           className={`px-3 py-1.5 transition-colors cursor-pointer border-none border-l border-[var(--rule)] ${view === 'list' ? 'bg-[var(--ink)] text-[var(--paper-hi)]' : 'bg-[var(--paper-hi)] text-[var(--ink-mute)] hover:bg-[var(--paper-2)]'}`}>
           <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true"><path d="M0 2h13M0 6.5h13M0 11h13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
         </button>
       </div>
     </div>
   </div>
   ```
5. Wrap existing card grid with conditional: grid view = `dossier-card-grid`, list view = single container with `<DossierRow>` items.
6. Update topbar `h1` to use `page-h1` class, add "Importer" secondary button.

- [ ] **Step 5: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/dossiers/page.tsx src/components/dossiers/ && git commit -m "design: /dossiers page rework — toolbar, grid/list toggle, DossierCard/DossierRow paper style"
```

---

## Task 6: Update /dossier/[id] shell

**Files:**
- Modify: `src/app/dossier/[id]/page.tsx`
- Create: `src/components/dossier/SideCard.tsx`
- Create: `src/components/dossier/AgentChat.tsx`

**Security flag:** `none`

**Does NOT cover:** Panel content (Tasks 8–12). This task covers the shell only: topbar, stepper, body grid, right-column SideCards, AgentChat strip.

- [ ] **Step 1: Create SideCard.tsx**

```tsx
interface FactRow { label: string; value: string }

interface Props {
  title: string
  facts?: FactRow[]
  children?: React.ReactNode
}

export default function SideCard({ title, facts, children }: Props) {
  return (
    <div className="side-card">
      <div className="side-card-head">{title}</div>
      {facts && (
        <div className="flex flex-col">
          {facts.map((f, i) => (
            <div key={i} className="flex items-baseline justify-between py-2.5"
              style={{ borderBottom: '1px dashed var(--rule-soft)' }}>
              <span className="text-[13px]" style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}>{f.label}</span>
              <span className="text-[13px] font-semibold ml-3 text-right" style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)', fontVariantNumeric: 'tabular-nums lining-nums' }}>{f.value}</span>
            </div>
          ))}
        </div>
      )}
      {children}
    </div>
  )
}
```

- [ ] **Step 2: Create AgentChat.tsx**

```tsx
'use client'

import { useState } from 'react'
import type { TabId } from '@/types'

const STAGE_SUGGESTIONS: Record<TabId, string[]> = {
  dossier:  ['Enrichir les données', 'Vérifier les infos', 'Résumer le mandat'],
  marche:   ['Trouver des comparables', 'Analyser les ajustements', 'Valider la grille'],
  analyse:  ['Peser les approches', 'Justifier la pondération', 'Vérifier la cohérence'],
  synthese: ['Rédiger la conclusion', 'Vérifier la conformité', 'Préparer la signature'],
  rapport:  ['Générer le rapport', 'Vérifier les sections', 'Exporter en PDF'],
}

const STAGE_PLACEHOLDERS: Record<TabId, string> = {
  dossier:  'Demandez à l\'agent d\'enrichir le dossier…',
  marche:   'Demandez des comparables ou des ajustements…',
  analyse:  'Demandez une analyse des approches…',
  synthese: 'Demandez de rédiger la conclusion…',
  rapport:  'Demandez de générer ou vérifier le rapport…',
}

interface Props {
  activeTab: TabId
  sidebarOpen: boolean
}

export default function AgentChat({ activeTab, sidebarOpen }: Props) {
  const [input, setInput] = useState('')
  const suggestions = STAGE_SUGGESTIONS[activeTab] ?? []
  const placeholder = STAGE_PLACEHOLDERS[activeTab] ?? 'Demandez à l\'agent…'

  function handleSend() {
    if (!input.trim()) return
    setInput('')
    // TODO: wire to agent API
  }

  return (
    <div className={`agent-chat-wrap ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="agent-chat-gradient" />
      <div className="agent-chat-inner">
        <div className="agent-chat-box">
          {/* Suggestions */}
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[var(--rule-soft)] overflow-x-auto">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true" style={{ color: 'var(--ochre)', flexShrink: 0 }}>
              <path d="M7 1l1.5 4h4l-3.2 2.3 1.2 4L7 9l-3.5 2.3 1.2-4L1.5 5h4z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
            </svg>
            {suggestions.map(s => (
              <button key={s} onClick={() => setInput(s)}
                className="flex-shrink-0 text-[12.5px] px-3 py-1 rounded-[var(--r-pill)] bg-[var(--paper-2)] hover:bg-[var(--paper-3)] border-none cursor-pointer transition-colors"
                style={{ color: 'var(--ink-3)', fontFamily: 'var(--font-sans)' }}>
                {s}
              </button>
            ))}
          </div>
          {/* Input */}
          <div className="flex items-center gap-2 px-3 py-2.5">
            <button className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full hover:bg-[var(--paper-2)] border-none bg-transparent cursor-pointer transition-colors" aria-label="Joindre un fichier" style={{ color: 'var(--ink-faint)' }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M13 7l-5.5 5.5a3.5 3.5 0 01-5-5l6-6a2 2 0 013 3L5 11a.5.5 0 01-.7-.7l5.5-5.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>
            </button>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder={placeholder}
              className="flex-1 text-[14px] bg-transparent border-none focus:outline-none"
              style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)' }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              aria-label="Envoyer"
              className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full border-none cursor-pointer transition-colors"
              style={{ background: input.trim() ? 'var(--ink)' : 'var(--paper-2)', color: input.trim() ? 'var(--paper-hi)' : 'var(--ink-faint)' }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Update /dossier/[id]/page.tsx**

Make these changes (preserve all existing state/data-fetch logic):

a) Remove `TabBar` import, add `Stepper` import.
b) Remove `ThemeToggle` import.
c) Update `<Sidebar>` call to: `<Sidebar onSignOut={handleSignOut} currentDossierSlug={activeDossierId} currentDossierAddress={currentDossierName} />`
d) Replace `<TabBar ... />` with `<Stepper activeTab={activeTab} onTabChange={handleTabChange} />`.
e) Replace the topbar h1/meta area with:
   ```tsx
   <div className="topbar">
     <div className="flex items-start justify-between gap-4 mb-1">
       <div>
         <h1 className="dossier-h1">{currentDossierName || params.id}</h1>
         <div className="text-[13.5px] mt-0.5" style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-sans)' }}>
           Montréal · Résidentiel · 2024
         </div>
       </div>
       <div className="flex items-center gap-2 flex-shrink-0 pt-1">
         <button className="btn ghost btn-sm">Imprimer</button>
         <button className="btn secondary btn-sm">Partager</button>
         <button className="btn accent btn-sm">Reprendre</button>
       </div>
     </div>
     <Stepper activeTab={activeTab} onTabChange={handleTabChange} />
   </div>
   ```
f) Wrap the existing panel + sidebar content in a grid:
   ```tsx
   <div className="flex-1 overflow-y-auto">
     <div className="grid gap-7 px-10 pt-6 pb-36"
       style={{ gridTemplateColumns: 'minmax(0,1fr) 340px' }}>
       {/* panel column */}
       <div>{/* existing panel switch */}</div>
       {/* aside column */}
       <div className="flex flex-col gap-4">
         <SideCard title="Faits saillants" facts={[
           { label: 'Adresse', value: currentDossierName || '—' },
           { label: 'Type', value: 'Résidentiel' },
           { label: 'Année', value: '2024' },
         ]} />
         <SideCard title="Mandat & client">
           <div className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</div>
         </SideCard>
         <SideCard title="Activité">
           <div className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</div>
         </SideCard>
         <SideCard title="Documents">
           <div className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>—</div>
         </SideCard>
       </div>
     </div>
   </div>
   ```
g) Add `<AgentChat activeTab={activeTab} sidebarOpen={true} />` before closing wrapper.

- [ ] **Step 4: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/dossier/ src/components/dossier/ && git commit -m "design: /dossier/[id] shell — topbar, Stepper, body grid, SideCards, AgentChat"
```

---

## Task 7: Rework /login page

**Files:**
- Modify: `src/app/login/page.tsx`

**Security flag:** `security` — auth form; no input validation changes, but review before implementing.

**Does NOT cover:** Actual sign-in/sign-up API wiring — keep existing auth calls.

- [ ] **Step 1: Rewrite login page layout**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\login.jsx` and `login.css` for exact copy text and interaction details, then rewrite `src/app/login/page.tsx` as a two-column layout:

Left panel (50vw, `background: var(--ink)`, flex column):
- Top: wordmark "Éval Immo" serif 38px white + tagline
- Middle: rotating quotes (3 quotes, auto-cycle 8s `setInterval`, active index state)
- Bottom: OEAQ compliance card (white bg, 12% opacity, frosted-look via `background: rgba(255,255,255,.12)`, border `rgba(255,255,255,.2)`)

Right panel (50vw, `background: var(--paper-hi)`, flex column justify-center):
- Sign-in form (max-width 400px, centered): eyebrow "Bon retour" → h1 serif "Se connecter" → Microsoft SSO button → "ou" divider → email field → password field with show/hide → remember checkbox → "Se connecter" accent btn → switch to sign-up link
- Sign-up form (same structure, different fields)
- Sent state (verification steps)
- Footer: copyright

Keep existing `signIn` / `signUp` calls; only change visual structure.

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/login/ && git commit -m "design: /login two-column brand/form layout"
```

---

## Task 8: Rework panel visual markup

**Files:**
- Modify: `src/components/panels/DossierPanel.tsx`
- Modify: `src/components/panels/MarchePanel.tsx`
- Modify: `src/components/panels/AnalysePanel.tsx`
- Modify: `src/components/panels/SynthesePanel.tsx`
- Modify: `src/components/panels/RapportPanel.tsx`

**Security flag:** `none`

**Does NOT cover:** Data-fetch logic, props interfaces, or Supabase calls — only JSX/CSS markup is changed.

- [ ] **Step 1: Read design stage files**

Before editing each panel, read the corresponding stage in:
`C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\dossier-stages.jsx`

This file contains the 5 stage components. Replicate their visual structure using the CSS classes from globals.css (`.panel`, `.panel-head`, `.panel-title`, `.side-card`, `.eyebrow`, `.btn`, tokens).

- [ ] **Step 2: DossierPanel.tsx — kv-grid layout**

Wrap each property group in `<div className="panel mb-5">`. Inside each panel, use a 2 or 3-column grid for KV pairs:
```tsx
<div className="grid grid-cols-3 gap-x-6 gap-y-4 mt-4">
  {/* each field */}
  <div>
    <div className="eyebrow mb-1">Adresse</div>
    <div className="text-[14px]" style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}>{value}</div>
  </div>
</div>
```
Visite row: flex row with verdigris check icon + stats (photos, pièces, lot).

- [ ] **Step 3: MarchePanel.tsx — comp table**

The comparables table uses a CSS grid (not `<table>`):
```tsx
<div className="panel">
  <div className="panel-head"><h2 className="panel-title">Analyse comparative</h2></div>
  {/* table header */}
  <div className="grid text-[11px] font-medium uppercase tracking-[.04em] pb-2 border-b border-[var(--rule-soft)]"
    style={{ color: 'var(--ink-faint)', gridTemplateColumns: '2fr 80px 80px 90px 70px 70px 60px' }}>
    <span>Comparable</span><span className="text-right">Vendu</span>
    <span className="text-right">Superf.</span><span className="text-right">Prix</span>
    <span className="text-right">$/pi²</span><span className="text-right">Ajust.</span>
    <span className="text-right">Dist.</span>
  </div>
  {/* rows */}
  {comps.map((c, i) => (
    <div key={i} className="grid py-3 border-b border-[var(--rule-soft)] hover:bg-[var(--paper-2)] transition-colors"
      style={{ gridTemplateColumns: '2fr 80px 80px 90px 70px 70px 60px' }}>
      <div className="text-[14.5px]" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{c.address}</div>
      <div className="text-right text-[13px]" style={{ color: 'var(--ink-3)', fontVariantNumeric: 'tabular-nums' }}>{c.date}</div>
      {/* ... */}
    </div>
  ))}
  {/* reconciliation */}
  <div className="mt-4 p-4 rounded-[var(--r-md)] bg-[var(--navy-tint)] border border-[rgba(28,53,89,.12)]">
    <div className="flex justify-between items-baseline">
      <span className="text-[13px]" style={{ color: 'var(--ink-mute)' }}>Valeur indiquée</span>
      <span className="text-[18px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--navy)' }}>
        {reconValue}
      </span>
    </div>
  </div>
</div>
```

- [ ] **Step 4: AnalysePanel.tsx — approach grid**

3-column grid for Comparaison / Coût / Revenus approaches:
```tsx
<div className="grid grid-cols-3 gap-4 mb-6">
  {approaches.map(a => (
    <div key={a.id} className={`panel ${a.applicable ? '' : 'opacity-55'}`}>
      <div className="eyebrow mb-2">{a.label}</div>
      <div className="text-[26px] font-medium mb-2" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
        {a.value}
      </div>
      <div className="pill text-[11px] py-0.5 px-2">{a.weight}</div>
    </div>
  ))}
</div>
{/* weighted recon */}
<div className="panel">
  <div className="text-[28px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--navy)', letterSpacing: '-.015em' }}>
    {finalValue}
  </div>
</div>
```

- [ ] **Step 5: SynthesePanel.tsx — hero + attestation**

```tsx
<div className="panel mb-5">
  <div className="eyebrow mb-2">Valeur finale</div>
  <div className="text-[56px] font-medium leading-none mb-3"
    style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)', letterSpacing: '-.02em', fontVariantNumeric: 'tabular-nums lining-nums' }}>
    {finalValue}
  </div>
  <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-[var(--rule-soft)]">
    <div><div className="eyebrow mb-1">Date</div><div className="text-[14px]" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{date}</div></div>
    <div><div className="eyebrow mb-1">Méthode</div><div className="text-[14px]" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{method}</div></div>
    <div><div className="eyebrow mb-1">Confiance</div><div className="text-[14px]" style={{ color: 'var(--verdigris)', fontWeight: 500 }}>Élevée</div></div>
  </div>
</div>
{/* Attestation */}
<div className="panel">
  <div className="panel-head"><h2 className="panel-title">Attestation</h2></div>
  <p className="text-[14px] leading-relaxed mb-6" style={{ color: 'var(--ink-3)', fontFamily: 'var(--font-serif)' }}>{declarationText}</p>
  <div className="border-t border-[var(--rule)] pt-4 flex items-center justify-between">
    <div className="text-[12px]" style={{ color: 'var(--ink-faint)' }}>Signature de l'évaluateur</div>
    <div className="flex items-center gap-2">
      <span className="text-[12px] px-3 py-1 rounded-[var(--r-pill)]" style={{ background: 'rgba(184,138,62,.12)', color: 'var(--ochre)' }}>En attente</span>
      <button className="btn secondary btn-sm">Réviser</button>
      <button className="btn accent btn-sm">Signer</button>
    </div>
  </div>
</div>
```

- [ ] **Step 6: RapportPanel.tsx — cover preview + sections**

```tsx
{/* rapport-hero: 2-col */}
<div className="grid gap-6 mb-6" style={{ gridTemplateColumns: '1fr 280px' }}>
  {/* Cover preview */}
  <div className="panel flex flex-col justify-between min-h-[360px]" style={{ aspectRatio: '1/1.294' }}>
    <div>
      <div className="eyebrow mb-4">Rapport d'évaluation</div>
      <h2 className="text-[32px] font-medium" style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.015em', color: 'var(--ink)' }}>
        {address}
      </h2>
      <div className="text-[15px] mt-1" style={{ color: 'var(--ink-mute)', fontStyle: 'italic', fontFamily: 'var(--font-serif)' }}>
        {city}
      </div>
    </div>
    <div className="grid grid-cols-3 gap-3 pt-4 border-t border-[var(--rule-soft)]">
      {/* cover meta */}
    </div>
  </div>
  {/* Stats + exports */}
  <div className="flex flex-col gap-3">
    <div className="panel"><div className="eyebrow mb-1">Pages</div><div className="text-[22px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{pageCount}</div></div>
    <button className="btn secondary btn-full">Exporter PDF</button>
    <button className="btn secondary btn-full">Exporter Word</button>
    <button className="btn ghost btn-full">Exporter JSON</button>
  </div>
</div>
{/* sections checklist */}
<div className="panel">
  <div className="panel-head"><h2 className="panel-title">Sections</h2></div>
  {sections.map(s => (
    <div key={s.id} className="flex items-center gap-3 py-3 border-b border-[var(--rule-soft)]">
      {s.complete
        ? <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" fill="var(--verdigris)" /><path d="M5 8l2.5 2.5 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
        : <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="var(--rule-strong)" strokeWidth="1.4"/></svg>
      }
      <span className="text-[13.5px] flex-1" style={{ color: s.complete ? 'var(--ink)' : 'var(--ink-mute)' }}>{s.label}</span>
      <span className="text-[12px]" style={{ color: 'var(--ink-faint)' }}>{s.pages} p.</span>
    </div>
  ))}
</div>
```

- [ ] **Step 7: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/components/panels/ && git commit -m "design: rework all 5 panels with paper tokens and structured layout"
```

---

## Task 9: Create mock data files

**Files:**
- Create: `src/data/bibliotheque-mock.ts`
- Create: `src/data/archives-mock.ts`
- Create: `src/data/modeles-mock.ts`

**Security flag:** `none`

- [ ] **Step 1: Read design data files**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\biblio-data.js` and `archives-data.js` to get the exact mock data arrays, then transcribe them to TypeScript in the `src/data/` files.

- [ ] **Step 2: Create bibliotheque-mock.ts**

Export `VENTES`, `MARCHES`, `COUTS`, `TAUX`, `DISTRICTS` arrays typed as needed. Pull exact data from `biblio-data.js`.

- [ ] **Step 3: Create archives-mock.ts**

Export `ARCHIVES` array from `archives-data.js`. Type: `{ id: string; date: string; address: string; city: string; type: string; mandate: string; client: string; value: number; completedAt: string }[]`.

- [ ] **Step 4: Create modeles-mock.ts**

Export `MODELES` array (6 items): `{ id: string; category: 'residentiel'|'commercial'|'specialise'|'restreint'; title: string; description: string; sections: number; pagesEnv: number; documents: number; usedCount: number; lastUsed: string; norm: string }[]`.

- [ ] **Step 5: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/data/ && git commit -m "data: add bibliotheque, archives, modeles mock fixtures"
```

---

## Task 10: Create /dossier/nouveau page

**Files:**
- Create: `src/app/dossier/nouveau/page.tsx`

**Security flag:** `none`

**Does NOT cover:** The existing `/dossier/[id]` catch with `params.id === 'nouveau'` — that code path is replaced by this dedicated route. Remove the `isNew` branch from `/dossier/[id]/page.tsx` in a follow-up.

- [ ] **Step 1: Create nouveau/page.tsx**

```tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { createRuntimeDossier } from '@/lib/runtime-api'

const MANDATE_TYPES = [
  'Hypothécaire', 'Pré-vente', 'Successoral', 'Litige',
  'Acquisition', 'Donation', 'Refinancement', 'Avis restreint',
]

export default function NouveauDossierPage() {
  const router = useRouter()
  const [address, setAddress] = useState('')
  const [mandateType, setMandateType] = useState(MANDATE_TYPES[0])
  const [clientName, setClientName] = useState('')
  const [clientOrg, setClientOrg] = useState('')
  const [clientOpen, setClientOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!address.trim()) return
    setLoading(true)
    setError(null)
    try {
      const d = await createRuntimeDossier({
        address: address.trim(),
        property_type: mandateType,
        neighborhood: '',
      })
      router.push(`/dossier/${d.slug}?tab=dossier`)
    } catch {
      setError('Erreur lors de la création du dossier.')
      setLoading(false)
    }
  }

  return (
    <div className="relative w-full h-screen overflow-hidden flex" style={{ background: 'var(--paper)' }}>
      <Sidebar />
      <main className="main-content overflow-y-auto">
        <div className="topbar mb-8">
          <h1 className="page-h1">Nouveau dossier</h1>
        </div>
        <div className="px-10 max-w-[600px]">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            {/* Adresse */}
            <div>
              <label className="eyebrow block mb-2" htmlFor="address">
                Adresse civique <span style={{ color: 'var(--oxblood)' }}>*</span>
              </label>
              <input
                id="address"
                type="text"
                required
                className="field"
                placeholder="245, av. Wiseman, Montréal"
                value={address}
                onChange={e => setAddress(e.target.value)}
              />
            </div>

            {/* Type de mandat */}
            <div>
              <label className="eyebrow block mb-2" htmlFor="mandate">
                Type de mandat <span style={{ color: 'var(--oxblood)' }}>*</span>
              </label>
              <select
                id="mandate"
                className="field"
                value={mandateType}
                onChange={e => setMandateType(e.target.value)}
              >
                {MANDATE_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>

            {/* Client (collapsible) */}
            <div>
              <button type="button" onClick={() => setClientOpen(v => !v)}
                className="eyebrow flex items-center gap-1.5 mb-2 cursor-pointer bg-transparent border-none p-0"
                style={{ color: 'var(--ink-faint)' }}>
                Client (optionnel)
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true"
                  style={{ transform: clientOpen ? 'rotate(180deg)' : '', transition: 'transform .15s' }}>
                  <path d="M2 3.5l3 3 3-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
                </svg>
              </button>
              {clientOpen && (
                <div className="flex flex-col gap-3">
                  <input className="field" placeholder="Nom" value={clientName} onChange={e => setClientName(e.target.value)} />
                  <input className="field" placeholder="Organisation" value={clientOrg} onChange={e => setClientOrg(e.target.value)} />
                </div>
              )}
            </div>

            {error && <p className="text-[13px]" style={{ color: 'var(--oxblood)' }}>{error}</p>}

            <div>
              <button type="submit" disabled={!address.trim() || loading} className="btn accent">
                {loading ? 'Création…' : 'Créer le dossier →'}
              </button>
            </div>
          </form>

          <p className="mt-5 text-[13px]" style={{ color: 'var(--ink-faint)', fontFamily: 'var(--font-sans)' }}>
            L'agent analysera automatiquement la propriété et prépare les comparables.
          </p>
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/dossier/nouveau/ && git commit -m "feat: /dossier/nouveau smart entry form"
```

---

## Task 11: Create /bibliotheque page

**Files:**
- Create: `src/app/bibliotheque/page.tsx`

**Security flag:** `none`

- [ ] **Step 1: Read design reference**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\bibliotheque.jsx` and `bibliotheque.css` for exact tab structure, table columns, and stat card layout.

- [ ] **Step 2: Create bibliotheque/page.tsx**

4-tab page (`'use client'`). Tabs: Ventes | Marchés | Coûts | Taux. Active tab via `useState<'ventes'|'marches'|'couts'|'taux'>('ventes')`.

Shell:
```tsx
<div className="relative w-full h-screen overflow-hidden flex" style={{ background: 'var(--paper)' }}>
  <Sidebar />
  <main className="main-content overflow-y-auto">
    <div className="topbar">
      <div className="flex items-end justify-between mb-0">
        <h1 className="page-h1">Bibliothèque</h1>
        <div className="flex gap-2 pb-1">
          <button className="btn secondary btn-sm">Exporter</button>
          <button className="btn accent btn-sm">+ Importer</button>
        </div>
      </div>
      {/* underlined tabs */}
      <div className="flex gap-0 border-b border-[var(--rule-soft)] mt-4">
        {(['ventes','marches','couts','taux'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className="px-5 py-3 text-[14px] border-b-2 -mb-px transition-colors cursor-pointer bg-transparent border-t-0 border-l-0 border-r-0"
            style={{
              fontFamily: 'var(--font-sans)',
              borderBottomColor: tab === t ? 'var(--navy)' : 'transparent',
              color: tab === t ? 'var(--ink)' : 'var(--ink-mute)',
              fontWeight: tab === t ? 500 : 400,
            }}>
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>
    </div>
    <div className="px-10 pt-6 pb-16">
      {tab === 'ventes'  && <VentesTab />}
      {tab === 'marches' && <MarchesTab />}
      {tab === 'couts'   && <CoutsTab />}
      {tab === 'taux'    && <TauxTab />}
    </div>
  </main>
</div>
```

Each sub-tab component is a function in the same file importing from `@/data/bibliotheque-mock`. Ventes: searchable sortable table. Marchés: card grid with median $/pi² + SVG sparkline stub. Coûts: grouped table. Taux: card grid.

- [ ] **Step 3: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/bibliotheque/ && git commit -m "feat: /bibliotheque page — 4 tabs, mock data"
```

---

## Task 12: Create /modeles page

**Files:**
- Create: `src/app/modeles/page.tsx`

**Security flag:** `none`

- [ ] **Step 1: Create modeles/page.tsx**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\modeles.jsx` for card structure.

Card grid (`auto-fill minmax(360px,1fr)`, 16px gap). Each card from `MODELES` mock:

```tsx
const CATEGORY_STYLES = {
  residentiel: { bg: 'var(--navy-tint)', color: 'var(--navy)' },
  commercial:  { bg: 'rgba(74,107,84,.12)', color: 'var(--verdigris)' },
  specialise:  { bg: 'rgba(184,138,62,.12)', color: 'var(--ochre)' },
  restreint:   { bg: 'rgba(31,30,28,.06)', color: 'var(--ink-mute)' },
}

function ModeleCard({ m }: { m: typeof MODELES[0] }) {
  const cs = CATEGORY_STYLES[m.category]
  return (
    <div className="card-hover rounded-[var(--r-lg)] border border-[var(--rule)] p-6 flex flex-col gap-4" style={{ background: 'var(--paper-hi)' }}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium px-2.5 py-1 rounded-[var(--r-pill)]" style={{ background: cs.bg, color: cs.color }}>
          {m.category}
        </span>
      </div>
      <h2 className="text-[22px] font-medium" style={{ fontFamily: 'var(--font-serif)', letterSpacing: '-.005em', color: 'var(--ink)' }}>
        {m.title}
      </h2>
      <p className="text-[13.5px] leading-relaxed" style={{ color: 'var(--ink-mute)' }}>{m.description}</p>
      <div className="grid grid-cols-3 gap-2 py-3 border-y border-[var(--rule-soft)]">
        <div className="text-center"><div className="text-[24px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{m.sections}</div><div className="eyebrow">Sections</div></div>
        <div className="text-center"><div className="text-[24px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{m.pagesEnv}</div><div className="eyebrow">Pages env.</div></div>
        <div className="text-center"><div className="text-[24px] font-medium" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>{m.documents}</div><div className="eyebrow">Documents</div></div>
      </div>
      <div className="flex items-center gap-2 pt-1">
        <button className="btn ghost btn-sm">Aperçu</button>
        <button className="btn secondary btn-sm">Démarrer un dossier</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/modeles/ && git commit -m "feat: /modeles page — template card grid"
```

---

## Task 13: Create /archives page

**Files:**
- Create: `src/app/archives/page.tsx`

**Security flag:** `none`

- [ ] **Step 1: Create archives/page.tsx**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\archives.jsx` for row grid and year-group structure.

State: `query`, `year: string | null`, `mandate: string | null`. Import `ARCHIVES` from mock.

Year-strip: horizontal pill row, "Toutes années" + each unique year from data. Active pill = `pill active` class.

Year-grouped sections: group archives by year (descending), render serif year heading + count, then grid rows:
```
gridTemplateColumns: '64px 2fr 140px 1.4fr 120px 90px 140px'
```
Row: date stack (serif 22px day + uppercase month) | address serif | mandate pill | client | value numeric | ID faint | hover ghost buttons.

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/archives/ && git commit -m "feat: /archives page — year-grouped completed dossiers"
```

---

## Task 14: Create /parametres page

**Files:**
- Create: `src/app/parametres/page.tsx`

**Security flag:** `none`

- [ ] **Step 1: Create parametres/page.tsx**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\parametres.jsx` and `parametres-sections.jsx`.

2-column layout: 220px sticky sub-nav + main (max-width 760px). Section state via `useState` + `useEffect` syncing to `?section=` URL param via `history.replaceState`.

7 sections: Profil | Cabinet | Membres | Intégrations | Utilisation | Sécurité | Préférences.

Each section card uses `.panel` class. Rows use `pc-row` pattern:
```tsx
<div className="flex items-baseline py-3 border-b border-[var(--rule-soft)]">
  <span className="text-[13px] min-w-[200px]" style={{ color: 'var(--ink-mute)' }}>{label}</span>
  <span className="text-[13px]" style={{ color: 'var(--ink)' }}>{value}</span>
</div>
```

Static form content only; no API wiring. Préférences section includes theme toggle: "Clair / Sombre / Système" segmented control that calls `document.documentElement.setAttribute('data-theme', ...)`.

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/parametres/ && git commit -m "feat: /parametres page — 7 sections, static content"
```

---

## Task 15: Create /aide page

**Files:**
- Create: `src/app/aide/page.tsx`

**Security flag:** `none`

- [ ] **Step 1: Create aide/page.tsx**

Read `C:\Users\simon\Downloads\eval-immo-design\design_handoff_eval_immo\aide.jsx`.

2-column layout: 220px sticky TOC + main (max-width 720px, gap 64px between sections). Sections: Survol | Créer un dossier | Les 5 étapes | L'agent IA | Bibliothèque & Modèles | Conformité OEAQ | Raccourcis clavier | FAQ | Nous joindre.

FAQ section: accordion items. Each item: `useState<string|null>` tracks open ID. Click toggles; caret SVG rotates 180° when open.

```tsx
function AccordionItem({ q, a, open, onToggle }: { q: string; a: string; open: boolean; onToggle: () => void }) {
  return (
    <div className="border-b border-[var(--rule-soft)]">
      <button onClick={onToggle} className="w-full flex items-center justify-between py-4 text-left bg-transparent border-none cursor-pointer" style={{ color: 'var(--ink)', fontFamily: 'var(--font-sans)', fontSize: 14 }}>
        {q}
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true" style={{ transform: open ? 'rotate(180deg)' : '', transition: 'transform .2s', flexShrink: 0, color: 'var(--ink-mute)' }}>
          <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </button>
      {open && <p className="pb-4 text-[14px] leading-relaxed" style={{ color: 'var(--ink-mute)', fontFamily: 'var(--font-serif)' }}>{a}</p>}
    </div>
  )
}
```

- [ ] **Step 2: Commit**
```bash
cd C:/Users/simon/eval-immo && git add src/app/aide/ && git commit -m "feat: /aide page — TOC, accordion FAQ, static content"
```

---

## Task 16: Final build verification

**Files:** (none modified)

**Security flag:** `none`

- [ ] **Step 1: Full build**

Run: `cd C:/Users/simon/eval-immo && npm run build 2>&1 | tail -30`
Expected: `✓ Compiled successfully` with no type errors.

- [ ] **Step 2: Check new routes registered**

Run: `cd C:/Users/simon/eval-immo && npm run build 2>&1 | grep "Route\|○\|●" | head -30`
Expected: Routes for `/bibliotheque`, `/modeles`, `/archives`, `/parametres`, `/aide`, `/dossier/nouveau` appear in the output.

- [ ] **Step 3: Remove dead code**

After confirming build:
- Remove `ThemeToggle` import from any page that no longer uses it.
- Remove the `isNew` / `nouveau` branch from `/dossier/[id]/page.tsx` (now handled by `/dossier/nouveau/page.tsx`).
- Remove `--glass-*` CSS custom properties if any remain in component files (grep: `glass-bg|glass-blur|glass-border`).

Run: `cd C:/Users/simon/eval-immo && grep -r "glass-bg\|glass-blur\|glass-border\|backdrop-filter" src/ --include="*.tsx" --include="*.css" -l`
Expected: No files found (or only ThemeToggle which gets removed).

- [ ] **Step 4: Final commit**
```bash
cd C:/Users/simon/eval-immo && git add -A && git commit -m "design: cleanup — remove glass dead code after full rework"
```

---

## Self-Review

### Spec coverage
| Requirement | Task |
|-------------|------|
| Design tokens (colors, fonts, shadows, radii) | Task 1, 2 |
| Login page rework | Task 7 |
| /dossiers grid/list toggle, toolbar | Task 5 |
| /dossier/[id] topbar, stepper, body grid | Task 6 |
| All 5 panels | Task 8 |
| SideCards, AgentChat | Task 6 |
| Sidebar route-based, all nav items | Task 3 |
| SidebarToggle | Task 3 |
| ThemeToggle moved to sidebar footer | Task 3 |
| /dossier/nouveau | Task 10 |
| /bibliotheque | Task 11 |
| /modeles | Task 12 |
| /archives | Task 13 |
| /parametres | Task 14 |
| /aide | Task 15 |
| Mock data files | Task 9 |
| Stepper replaces TabBar | Task 4 |

### Gaps
- `DossierListItem.tsx` (existing file in `components/layout/`) — verify it becomes `DossierRow.tsx` or is removed.
- `CheckpointComparablePanel.tsx` and `CheckpointReviewPanel.tsx` — not in design scope, leave as-is.
- `src/app/admin/` route — untouched, out of scope.

### Type consistency
- `StatusFilter` used in Task 5 comes from `@/lib/filter-dossiers` — unchanged.
- `TabId` type used in Stepper and AgentChat — defined in `@/types`.
- `Dossier.clientName` — verify this field exists on the type; if not, use `dossier.address` as fallback.
