-- Migration 007 — Modèle tenant multi-bureau (T5.1)
-- Ajoute : bureaux, bureau_membres, bureau_id sur dossiers/sessions

-- ── Table bureaux ──────────────────────────────────────────────────────────────

create table if not exists public.bureaux (
    id              uuid primary key default gen_random_uuid(),
    nom             text not null,
    plan            text not null default 'standard',  -- standard | pro | enterprise
    actif           boolean not null default true,
    cree_le         timestamptz not null default now(),
    mis_a_jour_le   timestamptz not null default now()
);

-- ── Table bureau_membres ───────────────────────────────────────────────────────

do $$ begin
    create type public.bureau_role as enum ('bureau_admin', 'evaluateur', 'lecteur');
exception when duplicate_object then null;
end $$;

create table if not exists public.bureau_membres (
    id              uuid primary key default gen_random_uuid(),
    bureau_id       uuid not null references public.bureaux(id) on delete cascade,
    user_id         uuid not null references auth.users(id) on delete cascade,
    role            public.bureau_role not null default 'evaluateur',
    actif           boolean not null default true,
    ajoute_le       timestamptz not null default now(),
    unique(bureau_id, user_id)
);

create index if not exists bureau_membres_user_idx on public.bureau_membres(user_id);
create index if not exists bureau_membres_bureau_idx on public.bureau_membres(bureau_id);

-- ── Colonne bureau_id sur les tables existantes ────────────────────────────────

-- Sur profiles (si table existe)
alter table if exists public.profiles
    add column if not exists bureau_id uuid references public.bureaux(id);

create index if not exists profiles_bureau_idx on public.profiles(bureau_id);

-- ── Helpers RLS ────────────────────────────────────────────────────────────────

-- Retourne le bureau_id de l'utilisateur courant
create or replace function public.my_bureau_id()
returns uuid
language sql stable security definer
as $$
    select bureau_id
    from public.profiles
    where id = auth.uid()
    limit 1;
$$;

-- Retourne true si l'utilisateur est bureau_admin de son bureau
create or replace function public.is_bureau_admin()
returns boolean
language sql stable security definer
as $$
    select exists (
        select 1 from public.bureau_membres
        where user_id = auth.uid()
          and role = 'bureau_admin'
          and actif = true
    );
$$;

-- ── RLS bureaux ─────────────────────────────────────────────────────────────────

alter table public.bureaux enable row level security;

create policy "bureaux_read_own"
    on public.bureaux for select
    using (
        id = public.my_bureau_id()
        or is_bureau_admin()
    );

-- ── RLS bureau_membres ──────────────────────────────────────────────────────────

alter table public.bureau_membres enable row level security;

create policy "bureau_membres_read_own_bureau"
    on public.bureau_membres for select
    using (
        bureau_id = public.my_bureau_id()
    );

create policy "bureau_membres_admin_write"
    on public.bureau_membres for all
    using (public.is_bureau_admin())
    with check (public.is_bureau_admin());
