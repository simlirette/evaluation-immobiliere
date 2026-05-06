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
  garage_type    text,
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
