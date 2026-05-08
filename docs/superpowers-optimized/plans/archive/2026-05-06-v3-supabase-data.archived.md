# Archived - V3 Real Supabase Data

> Archived on 2026-05-08 during the full project audit. This plan no longer matches the current code path: `src/lib/supabase/queries/*` now delegates to `src/lib/runtime-api.ts`, and the active product direction is a runtime-backed agent workbench. Keep this file as a record of the older Supabase-direct direction only.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all `MOCK_*` data with real Supabase queries. No new UI — data wiring only.

**Architecture:** Client components fetch via `createClient()` (browser). URL param stays slug. Internal FK is UUID. Panels receive `dossierId: string` (UUID) as prop from `DossierShellInner`.

**Tech Stack:** Next.js 16 App Router, TypeScript, `@supabase/ssr` (already installed), Supabase Storage.

**Assumptions:**
- Supabase project already configured (`.env.local` filled, V2 auth complete).
- Migrations run manually in Supabase SQL Editor — no CLI migration runner needed.
- Each user sees only their own dossiers (`created_by = auth.uid()` RLS).
- Document upload: bucket `dossier-documents`, private, per-user RLS.

---

## Mock usage map (what to replace)

| File | Mock import | Replace with |
|---|---|---|
| `src/components/layout/Sidebar.tsx` | `MOCK_DOSSIERS` | `fetchDossiers()` in useEffect |
| `src/app/dossiers/page.tsx` | `MOCK_DOSSIERS` | `fetchDossiers()` in useEffect |
| `src/app/dossier/[id]/page.tsx` | `MOCK_DOSSIERS` (name lookup) | `fetchDossier(slug)` → uuid + address |
| `src/components/panels/DossierPanel.tsx` | `MOCK_CHIPS`, `MOCK_DOCUMENTS` | `fetchPropertyFacts(id)`, `fetchDocuments(id)` |
| `src/components/panels/MarchePanel.tsx` | `MOCK_COMPARABLES` | `fetchComparables(id)` |
| `src/components/panels/AnalysePanel.tsx` | `MOCK_ADJUSTMENTS` | `fetchAdjustments(id)` |

---

## File structure

| File | Action |
|---|---|
| `supabase/migrations/001_v3_schema.sql` | Create — full DDL + RLS |
| `src/types/db.ts` | Create — raw DB row types |
| `src/types/index.ts` | Modify — update UI types (structured fields) |
| `src/lib/supabase/queries/dossiers.ts` | Create |
| `src/lib/supabase/queries/documents.ts` | Create |
| `src/lib/supabase/queries/comparables.ts` | Create |
| `src/lib/supabase/queries/adjustments.ts` | Create |
| `src/lib/supabase/queries/pins.ts` | Create |
| `src/app/dossiers/page.tsx` | Modify |
| `src/components/layout/Sidebar.tsx` | Modify |
| `src/app/dossier/[id]/page.tsx` | Modify |
| `src/components/panels/DossierPanel.tsx` | Modify |
| `src/components/panels/MarchePanel.tsx` | Modify |
| `src/components/panels/AnalysePanel.tsx` | Modify |

---

### Task 1: SQL migration

**Files:**
- Create: `supabase/migrations/001_v3_schema.sql`

**Does NOT cover:** Seeding data, storage bucket policies beyond basics.

- [ ] **Step 1: Create migration file**

```sql
-- supabase/migrations/001_v3_schema.sql

-- ─── dossiers ────────────────────────────────────────────────────────────────
create table dossiers (
  id             uuid primary key default gen_random_uuid(),
  slug           text unique not null,
  address        text not null,
  property_type  text not null default '',
  neighborhood   text not null default '',
  status         text not null default 'brouillon'
                   check (status in ('brouillon','en-cours','complet')),
  hab_m2         numeric,
  terrain_m2     numeric,
  year_built     int,
  zoning         text,
  garage_type    text,      -- 'simple' | 'double' | null
  created_by     uuid references auth.users not null,
  created_at     timestamptz default now(),
  updated_at     timestamptz default now()
);

alter table dossiers enable row level security;

create policy "users see own dossiers"
  on dossiers for select
  using (created_by = auth.uid());

create policy "users insert own dossiers"
  on dossiers for insert
  with check (created_by = auth.uid());

create policy "users update own dossiers"
  on dossiers for update
  using (created_by = auth.uid());

create policy "users delete own dossiers"
  on dossiers for delete
  using (created_by = auth.uid());

-- auto-update updated_at
create or replace function touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;

create trigger dossiers_updated_at
  before update on dossiers
  for each row execute function touch_updated_at();

-- ─── user_dossier_pins ───────────────────────────────────────────────────────
create table user_dossier_pins (
  user_id    uuid references auth.users on delete cascade,
  dossier_id uuid references dossiers(id) on delete cascade,
  primary key (user_id, dossier_id)
);

alter table user_dossier_pins enable row level security;

create policy "users manage own pins"
  on user_dossier_pins for all
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- ─── property_facts ──────────────────────────────────────────────────────────
create table property_facts (
  id          uuid primary key default gen_random_uuid(),
  dossier_id  uuid references dossiers(id) on delete cascade not null,
  label       text not null,
  highlight   boolean not null default false,
  sort_order  int not null default 0
);

alter table property_facts enable row level security;

create policy "users see facts of own dossiers"
  on property_facts for all
  using (exists (
    select 1 from dossiers d
    where d.id = property_facts.dossier_id
      and d.created_by = auth.uid()
  ));

-- ─── documents ───────────────────────────────────────────────────────────────
create table documents (
  id           uuid primary key default gen_random_uuid(),
  dossier_id   uuid references dossiers(id) on delete cascade not null,
  display_name text not null,
  storage_path text not null,
  size_bytes   bigint,
  uploaded_by  uuid references auth.users,
  uploaded_at  timestamptz default now()
);

alter table documents enable row level security;

create policy "users manage docs of own dossiers"
  on documents for all
  using (exists (
    select 1 from dossiers d
    where d.id = documents.dossier_id
      and d.created_by = auth.uid()
  ));

-- ─── comparables ─────────────────────────────────────────────────────────────
create table comparables (
  id             uuid primary key default gen_random_uuid(),
  dossier_id     uuid references dossiers(id) on delete cascade not null,
  rank           text not null,
  address        text not null,
  hab_m2         numeric,
  terrain_m2     numeric,
  year_built     int,
  renovated_year int,
  garage_type    text,
  sale_price     numeric not null,
  sale_date      date not null,
  sort_order     int not null default 0
);

alter table comparables enable row level security;

create policy "users manage comps of own dossiers"
  on comparables for all
  using (exists (
    select 1 from dossiers d
    where d.id = comparables.dossier_id
      and d.created_by = auth.uid()
  ));

-- ─── adjustments ─────────────────────────────────────────────────────────────
create table adjustments (
  id             uuid primary key default gen_random_uuid(),
  dossier_id     uuid references dossiers(id) on delete cascade not null,
  comparable_id  uuid references comparables(id) on delete cascade not null,
  surface_adj    numeric not null default 0,
  year_adj       numeric not null default 0,
  condition_adj  numeric not null default 0,
  garage_adj     numeric not null default 0
);

alter table adjustments enable row level security;

create policy "users manage adjustments of own dossiers"
  on adjustments for all
  using (exists (
    select 1 from dossiers d
    where d.id = adjustments.dossier_id
      and d.created_by = auth.uid()
  ));

-- ─── Storage bucket ──────────────────────────────────────────────────────────
insert into storage.buckets (id, name, public)
values ('dossier-documents', 'dossier-documents', false);

create policy "users upload own docs"
  on storage.objects for insert
  with check (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
  );

create policy "users read own docs"
  on storage.objects for select
  using (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
  );
```

- [ ] **Step 2: Run in Supabase SQL Editor**

Paste the full file into Supabase dashboard → SQL Editor → Run.
Expected: no errors, all tables visible in Table Editor.

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/001_v3_schema.sql
git commit -m "feat(db): add V3 schema — dossiers, documents, comparables, adjustments, pins"
```

---

### Task 2: TypeScript DB types

**Files:**
- Create: `src/types/db.ts`
- Modify: `src/types/index.ts`

**Does NOT cover:** Auto-generated Supabase types — we write minimal manual types for now.

- [ ] **Step 1: Create `src/types/db.ts`**

```typescript
// src/types/db.ts
// Raw DB row shapes — match table columns exactly.

export interface DbDossier {
  id: string
  slug: string
  address: string
  property_type: string
  neighborhood: string
  status: 'brouillon' | 'en-cours' | 'complet'
  hab_m2: number | null
  terrain_m2: number | null
  year_built: number | null
  zoning: string | null
  garage_type: string | null
  created_by: string
  created_at: string
  updated_at: string
  pinned?: boolean  // joined from user_dossier_pins
}

export interface DbPropertyFact {
  id: string
  dossier_id: string
  label: string
  highlight: boolean
  sort_order: number
}

export interface DbDocument {
  id: string
  dossier_id: string
  display_name: string
  storage_path: string
  size_bytes: number | null
  uploaded_at: string
}

export interface DbComparable {
  id: string
  dossier_id: string
  rank: string
  address: string
  hab_m2: number | null
  terrain_m2: number | null
  year_built: number | null
  renovated_year: number | null
  garage_type: string | null
  sale_price: number
  sale_date: string
  sort_order: number
}

export interface DbAdjustment {
  id: string
  dossier_id: string
  comparable_id: string
  surface_adj: number
  year_adj: number
  condition_adj: number
  garage_adj: number
}
```

- [ ] **Step 2: Update `src/types/index.ts`**

Update `Dossier` and `Comparable` to structured fields. `Document` gets `size_bytes`. `FactChip` stays (UI shape). Add helpers.

Replace entire file content:

```typescript
// src/types/index.ts

export type Theme = 'light' | 'dark'

export type TabId = 'dossier' | 'marche' | 'analyse' | 'rapport'

export interface Tab {
  id: TabId
  label: string
}

export type DossierStatus = 'brouillon' | 'en-cours' | 'complet'

export interface Dossier {
  id: string           // UUID
  slug: string         // URL param
  address: string
  property_type: string
  neighborhood: string
  status: DossierStatus
  updatedAt: string    // formatted for display
  pinned: boolean
}

export interface Document {
  id: string
  name: string         // display_name
  filename: string     // last segment of storage_path
  sizeLabel: string    // formatted from size_bytes
}

export interface FactChip {
  label: string
  highlight: boolean
}

export interface Comparable {
  id: string
  rank: string
  address: string
  hab_m2: number | null
  terrain_m2: number | null
  year_built: number | null
  renovated_year: number | null
  garage_type: string | null
  sale_price: number
  sale_date: string    // ISO date
  // display helpers
  meta: string         // built from structured fields
  price: string        // formatted
  date: string         // formatted
}

export interface Adjustment {
  id: string
  comparable_id: string
  comparableLabel: string  // e.g. 'C1 — 1624 Sherbrooke'
  salePrice: number
  surface_adj: number
  year_adj: number
  condition_adj: number
  garage_adj: number
  adjusted: number     // computed: salePrice + all adjustments
}

export interface ContextMenuTarget {
  name: string
  pinned: boolean
  x: number
  y: number
}
```

- [ ] **Step 3: Verify build (types only)**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -40
```

Expected: only errors from files still importing MOCK_* — those are fixed in later tasks.

- [ ] **Step 4: Commit**

```bash
git add src/types/db.ts src/types/index.ts
git commit -m "feat(types): add DB row types, update UI types to structured fields"
```

---

### Task 3: Query layer

**Files:**
- Create: `src/lib/supabase/queries/dossiers.ts`
- Create: `src/lib/supabase/queries/documents.ts`
- Create: `src/lib/supabase/queries/comparables.ts`
- Create: `src/lib/supabase/queries/adjustments.ts`
- Create: `src/lib/supabase/queries/pins.ts`

**Does NOT cover:** Mutations beyond pin toggle. Error handling is minimal (throws on error).

- [ ] **Step 1: Create `src/lib/supabase/queries/dossiers.ts`**

```typescript
// src/lib/supabase/queries/dossiers.ts
import { createClient } from '@/lib/supabase/client'
import type { DbDossier } from '@/types/db'
import type { Dossier } from '@/types'

function formatUpdatedAt(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return "Modifié aujourd'hui"
  if (days === 1) return 'Il y a 1 jour'
  if (days < 7) return `Il y a ${days} jours`
  if (days < 14) return 'Il y a 1 semaine'
  return `Il y a ${Math.floor(days / 7)} semaines`
}

function toUiDossier(row: DbDossier): Dossier {
  return {
    id: row.id,
    slug: row.slug,
    address: row.address,
    property_type: row.property_type,
    neighborhood: row.neighborhood,
    status: row.status,
    updatedAt: formatUpdatedAt(row.updated_at),
    pinned: row.pinned ?? false,
  }
}

export async function fetchDossiers(): Promise<Dossier[]> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return []

  const { data, error } = await supabase
    .from('dossiers')
    .select('*, user_dossier_pins!left(user_id)')
    .order('updated_at', { ascending: false })

  if (error) throw error

  return (data ?? []).map(row => ({
    ...toUiDossier(row),
    pinned: Array.isArray(row.user_dossier_pins) && row.user_dossier_pins.some(
      (p: { user_id: string }) => p.user_id === user.id
    ),
  }))
}

export async function fetchDossier(slug: string): Promise<Dossier | null> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return null

  const { data, error } = await supabase
    .from('dossiers')
    .select('*, user_dossier_pins!left(user_id)')
    .eq('slug', slug)
    .single()

  if (error) return null

  return {
    ...toUiDossier(data),
    pinned: Array.isArray(data.user_dossier_pins) && data.user_dossier_pins.some(
      (p: { user_id: string }) => p.user_id === user.id
    ),
  }
}
```

- [ ] **Step 2: Create `src/lib/supabase/queries/documents.ts`**

```typescript
// src/lib/supabase/queries/documents.ts
import { createClient } from '@/lib/supabase/client'
import type { DbDocument } from '@/types/db'
import type { Document } from '@/types'

function formatSize(bytes: number | null): string {
  if (!bytes) return ''
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function toUiDocument(row: DbDocument): Document {
  const filename = row.storage_path.split('/').pop() ?? row.storage_path
  return {
    id: row.id,
    name: row.display_name,
    filename,
    sizeLabel: formatSize(row.size_bytes),
  }
}

export async function fetchDocuments(dossierId: string): Promise<Document[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('documents')
    .select('*')
    .eq('dossier_id', dossierId)
    .order('uploaded_at', { ascending: true })

  if (error) throw error
  return (data ?? []).map(toUiDocument)
}

export async function uploadDocument(
  dossierId: string,
  file: File
): Promise<Document> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Not authenticated')

  const path = `${user.id}/${dossierId}/${Date.now()}-${file.name}`

  const { error: uploadError } = await supabase.storage
    .from('dossier-documents')
    .upload(path, file)

  if (uploadError) throw uploadError

  const { data, error } = await supabase
    .from('documents')
    .insert({
      dossier_id: dossierId,
      display_name: file.name,
      storage_path: path,
      size_bytes: file.size,
      uploaded_by: user.id,
    })
    .select()
    .single()

  if (error) throw error
  return {
    id: data.id,
    name: data.display_name,
    filename: file.name,
    sizeLabel: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
  }
}
```

- [ ] **Step 3: Create `src/lib/supabase/queries/comparables.ts`**

```typescript
// src/lib/supabase/queries/comparables.ts
import { createClient } from '@/lib/supabase/client'
import type { DbComparable } from '@/types/db'
import type { Comparable } from '@/types'

function buildMeta(row: DbComparable): string {
  const parts: string[] = []
  if (row.hab_m2) parts.push(`${row.hab_m2} m² hab.`)
  if (row.terrain_m2) parts.push(`${row.terrain_m2} m² terrain`)
  if (row.year_built) parts.push(String(row.year_built))
  if (row.renovated_year) parts.push(`Rénové ${row.renovated_year}`)
  if (row.garage_type) parts.push(`Garage ${row.garage_type}`)
  return parts.join(' · ')
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 })
    .format(n)
    .replace('CA', '')
    .trim()
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('fr-CA', { month: 'short', year: 'numeric' })
}

function toUiComparable(row: DbComparable): Comparable {
  return {
    id: row.id,
    rank: row.rank,
    address: row.address,
    hab_m2: row.hab_m2,
    terrain_m2: row.terrain_m2,
    year_built: row.year_built,
    renovated_year: row.renovated_year,
    garage_type: row.garage_type,
    sale_price: row.sale_price,
    sale_date: row.sale_date,
    meta: buildMeta(row),
    price: formatPrice(row.sale_price),
    date: formatDate(row.sale_date),
  }
}

export async function fetchComparables(dossierId: string): Promise<Comparable[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('comparables')
    .select('*')
    .eq('dossier_id', dossierId)
    .order('sort_order', { ascending: true })

  if (error) throw error
  return (data ?? []).map(toUiComparable)
}
```

- [ ] **Step 4: Create `src/lib/supabase/queries/adjustments.ts`**

```typescript
// src/lib/supabase/queries/adjustments.ts
import { createClient } from '@/lib/supabase/client'
import type { DbAdjustment, DbComparable } from '@/types/db'
import type { Adjustment } from '@/types'

export async function fetchAdjustments(dossierId: string): Promise<Adjustment[]> {
  const supabase = createClient()

  const [{ data: adjs, error: e1 }, { data: comps, error: e2 }] = await Promise.all([
    supabase.from('adjustments').select('*').eq('dossier_id', dossierId),
    supabase.from('comparables').select('*').eq('dossier_id', dossierId).order('sort_order'),
  ])

  if (e1) throw e1
  if (e2) throw e2

  const compMap = new Map<string, DbComparable>(
    (comps ?? []).map(c => [c.id, c])
  )

  return (adjs ?? []).map((adj: DbAdjustment): Adjustment => {
    const comp = compMap.get(adj.comparable_id)
    const total = adj.surface_adj + adj.year_adj + adj.condition_adj + adj.garage_adj
    return {
      id: adj.id,
      comparable_id: adj.comparable_id,
      comparableLabel: comp ? `${comp.rank} — ${comp.address}` : adj.comparable_id,
      salePrice: comp?.sale_price ?? 0,
      surface_adj: adj.surface_adj,
      year_adj: adj.year_adj,
      condition_adj: adj.condition_adj,
      garage_adj: adj.garage_adj,
      adjusted: (comp?.sale_price ?? 0) + total,
    }
  })
}
```

- [ ] **Step 5: Create `src/lib/supabase/queries/pins.ts`**

```typescript
// src/lib/supabase/queries/pins.ts
import { createClient } from '@/lib/supabase/client'

export async function togglePin(dossierId: string, currentlyPinned: boolean): Promise<void> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return

  if (currentlyPinned) {
    await supabase
      .from('user_dossier_pins')
      .delete()
      .match({ user_id: user.id, dossier_id: dossierId })
  } else {
    await supabase
      .from('user_dossier_pins')
      .insert({ user_id: user.id, dossier_id: dossierId })
  }
}
```

- [ ] **Step 6: Verify no TypeScript errors in new files**

```bash
cd C:\Users\simon\eval-immo && npx tsc --noEmit 2>&1 | head -40
```

- [ ] **Step 7: Commit**

```bash
git add src/lib/supabase/queries/
git commit -m "feat(queries): add Supabase query layer for dossiers, documents, comparables, adjustments, pins"
```

---

### Task 4: Wire `/dossiers` page

**Files:**
- Modify: `src/app/dossiers/page.tsx`

**Does NOT cover:** Pagination, empty state beyond loading.

- [ ] **Step 1: Replace MOCK_DOSSIERS with real fetch**

Old imports block:
```typescript
import { MOCK_DOSSIERS } from '@/data/mock'
```

New imports (add after existing imports):
```typescript
import { fetchDossiers } from '@/lib/supabase/queries/dossiers'
import type { Dossier } from '@/types'
```

Replace `MOCK_DOSSIERS` usage: add state + useEffect at the top of the component.

Old:
```typescript
export default function MesDossiersPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')

  const filtered = MOCK_DOSSIERS.filter(d =>
```

New:
```typescript
export default function MesDossiersPage() {
  const router = useRouter()
  const [search, setSearch] = useState('')
  const [dossiers, setDossiers] = useState<Dossier[]>([])

  useEffect(() => {
    fetchDossiers().then(setDossiers)
  }, [])

  const filtered = dossiers.filter(d =>
```

Update the map key — old uses `d.id` (slug), new also uses `d.id` (UUID — still unique). Update the onClick:

Old:
```typescript
onClick={() => router.push(`/dossier/${d.id}?tab=dossier`)}
```

New:
```typescript
onClick={() => router.push(`/dossier/${d.slug}?tab=dossier`)}
```

Add `useEffect` to the imports line:
```typescript
import { useState, useEffect } from 'react'
```

- [ ] **Step 2: Verify build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20
```

- [ ] **Step 3: Commit**

```bash
git add src/app/dossiers/page.tsx
git commit -m "feat(dossiers): replace mock data with real Supabase fetch"
```

---

### Task 5: Wire Sidebar

**Files:**
- Modify: `src/components/layout/Sidebar.tsx`

**Does NOT cover:** Real-time updates. Pin toggle calls Supabase + updates local state optimistically.

- [ ] **Step 1: Replace MOCK_DOSSIERS + wire pin toggle**

Old imports:
```typescript
import { MOCK_DOSSIERS } from '@/data/mock'
```

New imports (add/replace):
```typescript
import { fetchDossiers } from '@/lib/supabase/queries/dossiers'
import { togglePin } from '@/lib/supabase/queries/pins'
import type { Dossier } from '@/types'
```

Old state init:
```typescript
const [dossiers, setDossiers] = useState(MOCK_DOSSIERS)
```

New:
```typescript
const [dossiers, setDossiers] = useState<Dossier[]>([])

useEffect(() => {
  fetchDossiers().then(setDossiers)
}, [])
```

Add `useEffect` to React import: `import { useState, useEffect } from 'react'`

Update `handlePin` to call Supabase:
```typescript
function handlePin(name: string, pinned: boolean) {
  const dossier = dossiers.find(d => d.address === name)
  if (!dossier) return
  // optimistic update
  setDossiers(prev => prev.map(d =>
    d.address === name ? { ...d, pinned: !pinned } : d
  ))
  togglePin(dossier.id, pinned)
}
```

Update `handleDelete` — remove from local state only (no DB delete from sidebar for now):
```typescript
function handleDelete(name: string) {
  setDossiers(prev => prev.filter(d => d.address !== name))
}
```

- [ ] **Step 2: Verify build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -20
```

- [ ] **Step 3: Commit**

```bash
git add src/components/layout/Sidebar.tsx
git commit -m "feat(sidebar): replace mock dossiers with real Supabase fetch + pin toggle"
```

---

### Task 6: Wire DossierShellInner

**Files:**
- Modify: `src/app/dossier/[id]/page.tsx`

**Does NOT cover:** Error state if dossier not found (just shows slug as name).

- [ ] **Step 1: Replace MOCK_DOSSIERS lookup + pass dossierId to panels**

Add import:
```typescript
import { fetchDossier } from '@/lib/supabase/queries/dossiers'
```

Remove:
```typescript
import { MOCK_DOSSIERS } from '@/data/mock'
```

Add `dossierId` state after existing state declarations:
```typescript
const [dossierId, setDossierId] = useState<string | null>(null)
```

Replace the `currentDossierName` initialization block and add a fetch effect. Old:
```typescript
const [currentDossierName, setCurrentDossierName] = useState(() => {
  const found = MOCK_DOSSIERS.find(d => d.id === params.id)
  return found?.address ?? params.id
})
```

New:
```typescript
const [currentDossierName, setCurrentDossierName] = useState(params.id)
```

Add after all useState declarations:
```typescript
useEffect(() => {
  fetchDossier(params.id).then(d => {
    if (d) {
      setCurrentDossierName(d.address)
      setDossierId(d.id)
    }
  })
}, [params.id])
```

Update panel rendering to pass `dossierId`:
```tsx
{activeTab === 'dossier'  && <DossierPanel isNew={isNew} dossierId={dossierId} />}
{activeTab === 'marche'   && <MarchePanel dossierId={dossierId} />}
{activeTab === 'analyse'  && <AnalysePanel dossierId={dossierId} />}
{activeTab === 'rapport'  && <RapportPanel />}
```

- [ ] **Step 2: Verify build** (will error on panels until Task 7-9 done — OK)

- [ ] **Step 3: Commit after tasks 7-9**

---

### Task 7: Wire DossierPanel

**Files:**
- Modify: `src/components/panels/DossierPanel.tsx`

- [ ] **Step 1: Replace mock chips + documents**

New file content:

```typescript
'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import Chip from '@/components/shared/Chip'
import DocItem from '@/components/shared/DocItem'
import ChatInput from '@/components/shared/ChatInput'
import DropZone from '@/components/shared/DropZone'
import { fetchDocuments, uploadDocument } from '@/lib/supabase/queries/documents'
import { fetchPropertyFacts } from '@/lib/supabase/queries/property_facts'
import type { Document, FactChip } from '@/types'

interface Props {
  isNew: boolean
  dossierId: string | null
}

export default function DossierPanel({ isNew: initialIsNew, dossierId }: Props) {
  const [isNew, setIsNew] = useState(initialIsNew)
  const [chips, setChips] = useState<FactChip[]>([])
  const [documents, setDocuments] = useState<Document[]>([])

  useEffect(() => {
    if (!dossierId) return
    fetchDocuments(dossierId).then(setDocuments)
    fetchPropertyFacts(dossierId).then(setChips)
  }, [dossierId])

  async function handleDrop(files: FileList) {
    if (!dossierId) return
    const uploads = Array.from(files).map(f => uploadDocument(dossierId, f))
    const newDocs = await Promise.all(uploads)
    setDocuments(prev => [...prev, ...newDocs])
    setTimeout(() => setIsNew(false), 300)
  }

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      {isNew ? (
        <DropZone onDrop={handleDrop} />
      ) : (
        <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
          <AgentMessage agentName="Agent Dossier">
            J'ai analysé les <strong>{documents.length} documents</strong> soumis pour ce dossier. Voici les faits extraits :
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {chips.map((c, i) => <Chip key={i} label={c.label} highlight={c.highlight} />)}
            </div>
          </AgentMessage>
          <UserMessage>Voici les documents du dossier</UserMessage>
          <AgentMessage agentName="Agent Dossier" last>
            Joignez les documents du dossier pour commencer l'extraction des faits.
            <div className="flex flex-col gap-1.5 mt-2.5">
              {documents.map(doc => <DocItem key={doc.id} doc={doc} />)}
            </div>
          </AgentMessage>
        </div>
      )}
      <ChatInput placeholder="Écrivez ou collez vos notes ici..." />
    </div>
  )
}
```

Also create `src/lib/supabase/queries/property_facts.ts`:

```typescript
// src/lib/supabase/queries/property_facts.ts
import { createClient } from '@/lib/supabase/client'
import type { FactChip } from '@/types'

export async function fetchPropertyFacts(dossierId: string): Promise<FactChip[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('property_facts')
    .select('label, highlight')
    .eq('dossier_id', dossierId)
    .order('sort_order', { ascending: true })

  if (error) throw error
  return data ?? []
}
```

- [ ] **Step 2: Verify build**

---

### Task 8: Wire MarchePanel

**Files:**
- Modify: `src/components/panels/MarchePanel.tsx`

- [ ] **Step 1: Replace mock comparables**

```typescript
'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import ComparableItem from '@/components/shared/ComparableItem'
import ChatInput from '@/components/shared/ChatInput'
import { fetchComparables } from '@/lib/supabase/queries/comparables'
import type { Comparable } from '@/types'

interface Props {
  dossierId: string | null
}

export default function MarchePanel({ dossierId }: Props) {
  const [comparables, setComparables] = useState<Comparable[]>([])

  useEffect(() => {
    if (!dossierId) return
    fetchComparables(dossierId).then(setComparables)
  }, [dossierId])

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Unifamiliales R-2, rayon 1 km, vendues dans les 18 derniers mois</UserMessage>
        <AgentMessage agentName="Agent Marché">
          J'ai identifié <strong>{comparables.length} comparables</strong> correspondant aux critères.
          <div className="flex flex-col gap-2 mt-2.5">
            {comparables.map(c => <ComparableItem key={c.id} comp={c} />)}
          </div>
        </AgentMessage>
        {comparables.length > 0 && (
          <AgentMessage agentName="Agent Marché" last>
            Prix médian des comparables : <strong>{comparables[Math.floor(comparables.length / 2)]?.price}</strong>.
          </AgentMessage>
        )}
      </div>
      <ChatInput placeholder="Affiner les critères de recherche..." />
    </div>
  )
}
```

---

### Task 9: Wire AnalysePanel

**Files:**
- Modify: `src/components/panels/AnalysePanel.tsx`

- [ ] **Step 1: Replace mock adjustments**

Note: `AdjustmentsTable` currently receives `Adjustment[]` with string fields. Need to check its interface and update it to accept numeric fields, or adapt the query output to match. Check `src/components/shared/AdjustmentsTable.tsx` first and update its props if needed.

```typescript
'use client'

import { useState, useEffect } from 'react'
import AgentMessage from '@/components/shared/AgentMessage'
import UserMessage from '@/components/shared/UserMessage'
import AdjustmentsTable from '@/components/shared/AdjustmentsTable'
import ValeurCard from '@/components/shared/ValeurCard'
import ChatInput from '@/components/shared/ChatInput'
import { fetchAdjustments } from '@/lib/supabase/queries/adjustments'
import type { Adjustment } from '@/types'

interface Props {
  dossierId: string | null
}

export default function AnalysePanel({ dossierId }: Props) {
  const [adjustments, setAdjustments] = useState<Adjustment[]>([])

  useEffect(() => {
    if (!dossierId) return
    fetchAdjustments(dossierId).then(setAdjustments)
  }, [dossierId])

  const adjustedValues = adjustments.map(a => a.adjusted).filter(v => v > 0)
  const median = adjustedValues.length
    ? adjustedValues.sort((a, b) => a - b)[Math.floor(adjustedValues.length / 2)]
    : null

  return (
    <div className="flex flex-col items-center justify-end flex-1 px-6 pb-9">
      <div className="w-full max-w-[640px] flex flex-col gap-0 mb-5 flex-1 overflow-y-auto pt-5 scroll-fade">
        <UserMessage>Applique un ajustement +5% pour la rénovation 2019 et tiens compte du garage double</UserMessage>
        <AgentMessage agentName="Agent Analyse">
          Voici le tableau d'ajustements :
          <AdjustmentsTable rows={adjustments} />
          {median && (
            <ValeurCard
              range=""
              median={`Médiane ajustée : ${new Intl.NumberFormat('fr-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(median).replace('CA', '').trim()}`}
            />
          )}
        </AgentMessage>
      </div>
      <ChatInput placeholder="Modifier les ajustements..." />
    </div>
  )
}
```

**Important:** Before completing this task, read `src/components/shared/AdjustmentsTable.tsx` and update its `rows` prop type to accept `Adjustment[]` with numeric fields instead of string fields. Format numbers inside the component.

---

### Task 10: Final build + commit

- [ ] **Step 1: Full build**

```bash
cd C:\Users\simon\eval-immo && npx next build 2>&1 | tail -30
```

Expected: `✓ Compiled successfully` — zero TypeScript errors.

- [ ] **Step 2: Commit remaining files**

```bash
git add src/app/dossier src/components/panels src/lib/supabase/queries
git commit -m "feat(v3): wire all panels to real Supabase data, remove all MOCK_* usage"
```

---

## Post-execution checklist

1. Run SQL migration in Supabase SQL Editor.
2. Seed at least one dossier manually (Supabase Table Editor) with a `slug` matching an existing URL (e.g. `1842-sherbrooke`).
3. Add property_facts rows for that dossier to verify DossierPanel renders chips.
4. Add comparables rows to verify MarchePanel.
5. `npm run dev` → log in → navigate to `/dossiers` → verify cards load from DB.
6. Navigate to `/dossier/1842-sherbrooke` → verify name in sidebar header.
