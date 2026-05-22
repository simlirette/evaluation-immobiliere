-- ─── S1 : Séparation Dossier / Session ──────────────────────────────────────
-- Dossier = entité métier persistante (évaluateur la crée, elle dure)
-- Session = run technique interne lié à un dossier (le système la crée)

-- ─── Enrichissement table dossiers ──────────────────────────────────────────
alter table dossiers
  add column if not exists mandat_type   text not null default 'residentiel_standard',
  add column if not exists statut_global text not null default 'brouillon'
    check (statut_global in ('brouillon', 'en-cours', 'complet'));

-- ─── Table sessions ──────────────────────────────────────────────────────────
create table if not exists sessions (
  id              uuid    primary key default gen_random_uuid(),
  dossier_id      uuid    not null references dossiers(id) on delete cascade,
  session_uuid    text    not null unique,          -- clé filesystem (hex12)
  statut_pipeline text    not null default 'initialise'
    check (statut_pipeline in ('initialise', 'en-cours', 'pret_revision', 'valide', 'archive')),
  created_at      timestamptz not null default now(),
  validated_at    timestamptz,
  archived_at     timestamptz
);

alter table sessions enable row level security;

drop policy if exists "users see own sessions" on sessions;
create policy "users see own sessions"
  on sessions for select
  using (exists (
    select 1 from dossiers d
    where d.id = sessions.dossier_id
      and d.created_by = auth.uid()
  ));

drop policy if exists "users insert own sessions" on sessions;
create policy "users insert own sessions"
  on sessions for insert
  with check (exists (
    select 1 from dossiers d
    where d.id = sessions.dossier_id
      and d.created_by = auth.uid()
  ));

drop policy if exists "users update own sessions" on sessions;
create policy "users update own sessions"
  on sessions for update
  using (exists (
    select 1 from dossiers d
    where d.id = sessions.dossier_id
      and d.created_by = auth.uid()
  ));

-- Index pour la politique d'archivage (sessions > 30 jours non-validées)
create index if not exists sessions_archive_idx
  on sessions (statut_pipeline, created_at)
  where statut_pipeline not in ('valide', 'archive');

-- ─── Fonction d'archivage automatique ────────────────────────────────────────
-- archive_stale_sessions() → à appeler via pg_cron ou manuellement
-- Retourne le nombre de sessions archivées
create or replace function archive_stale_sessions()
returns int language plpgsql as $$
declare
  archived_count int;
begin
  update sessions
  set
    statut_pipeline = 'archive',
    archived_at     = now()
  where statut_pipeline not in ('valide', 'archive')
    and created_at < now() - interval '30 days';
  get diagnostics archived_count = row_count;
  return archived_count;
end;
$$;
