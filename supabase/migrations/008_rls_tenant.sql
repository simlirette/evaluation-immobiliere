-- Migration 008 — RLS par bureau (tenant-aware) (T5.2)
-- Remplace/complète les policies created_by=auth.uid() par logique bureau.
-- Dépend de migration 007.

-- ── dossiers ───────────────────────────────────────────────────────────────────

-- Ajouter bureau_id si la table dossiers existe
alter table if exists public.dossiers
    add column if not exists bureau_id uuid references public.bureaux(id);

create index if not exists dossiers_bureau_idx on public.dossiers(bureau_id)
    where bureau_id is not null;

-- Supprimer les anciennes policies et recréer avec bureau isolation
drop policy if exists "dossiers_read_own" on public.dossiers;
drop policy if exists "dossiers_write_own" on public.dossiers;

create policy "dossiers_read_bureau"
    on public.dossiers for select
    using (
        -- Évaluateur : ses propres dossiers
        created_by = auth.uid()
        -- Bureau admin : tous les dossiers du bureau
        or (bureau_id = public.my_bureau_id() and public.is_bureau_admin())
        -- Membre du même bureau : dossiers du bureau (lecture)
        or bureau_id = public.my_bureau_id()
    );

create policy "dossiers_write_own"
    on public.dossiers for insert
    with check (
        created_by = auth.uid()
        and (bureau_id = public.my_bureau_id() or bureau_id is null)
    );

create policy "dossiers_update_bureau"
    on public.dossiers for update
    using (
        created_by = auth.uid()
        or (bureau_id = public.my_bureau_id() and public.is_bureau_admin())
    );

-- ── sessions ────────────────────────────────────────────────────────────────────

alter table if exists public.sessions
    add column if not exists bureau_id uuid references public.bureaux(id);

create index if not exists sessions_bureau_idx on public.sessions(bureau_id)
    where bureau_id is not null;

drop policy if exists "sessions_read_own" on public.sessions;

-- sessions n'a pas de created_by — isolation par bureau_id seulement
create policy "sessions_read_bureau"
    on public.sessions for select
    using (
        (bureau_id = public.my_bureau_id() and public.is_bureau_admin())
        or bureau_id = public.my_bureau_id()
        or bureau_id is null  -- sessions sans bureau = accès libre (transition)
    );

create policy "sessions_write_all"
    on public.sessions for insert
    with check (
        bureau_id = public.my_bureau_id() or bureau_id is null
    );

-- ── rapport_versions ────────────────────────────────────────────────────────────

drop policy if exists "rapport_versions_read_own" on public.rapport_versions;

create policy "rapport_versions_read_bureau"
    on public.rapport_versions for select
    using (
        created_by = auth.uid()
        or exists (
            select 1 from public.sessions s
            where s.id::text = rapport_versions.session_id
              and (s.bureau_id = public.my_bureau_id() and public.is_bureau_admin())
        )
    );

-- ── Commentaires d'audit ────────────────────────────────────────────────────────

comment on policy "dossiers_read_bureau" on public.dossiers is
    'T5.2 : isolation tenant bureau. Évaluateur voit ses dossiers; admin voit tout le bureau.';

comment on policy "sessions_read_bureau" on public.sessions is
    'T5.2 : isolation tenant bureau.';
