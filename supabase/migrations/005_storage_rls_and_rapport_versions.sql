-- Tighten document storage access and add report version history.
-- Storage object names must use: {auth.uid()}/{dossier_uuid}/{filename}

insert into storage.buckets (id, name, public)
values ('dossier-documents', 'dossier-documents', false)
on conflict (id) do update set public = false;

-- Replace broad bucket policies from 001_v3_schema.sql.
drop policy if exists "users upload own docs" on storage.objects;
drop policy if exists "users read own docs" on storage.objects;
drop policy if exists "users update own docs" on storage.objects;
drop policy if exists "users delete own docs" on storage.objects;
drop policy if exists "users upload dossier docs by owner path" on storage.objects;
drop policy if exists "users read dossier docs by owner path" on storage.objects;
drop policy if exists "users update dossier docs by owner path" on storage.objects;
drop policy if exists "users delete dossier docs by owner path" on storage.objects;

create policy "users upload dossier docs by owner path"
  on storage.objects for insert
  with check (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
    and (storage.foldername(name))[1] = auth.uid()::text
    and exists (
      select 1 from public.dossiers d
      where d.id::text = (storage.foldername(name))[2]
        and d.created_by = auth.uid()
    )
  );

create policy "users read dossier docs by owner path"
  on storage.objects for select
  using (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
    and (storage.foldername(name))[1] = auth.uid()::text
    and exists (
      select 1 from public.dossiers d
      where d.id::text = (storage.foldername(name))[2]
        and d.created_by = auth.uid()
    )
  );

create policy "users update dossier docs by owner path"
  on storage.objects for update
  using (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
    and (storage.foldername(name))[1] = auth.uid()::text
    and exists (
      select 1 from public.dossiers d
      where d.id::text = (storage.foldername(name))[2]
        and d.created_by = auth.uid()
    )
  )
  with check (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
    and (storage.foldername(name))[1] = auth.uid()::text
    and exists (
      select 1 from public.dossiers d
      where d.id::text = (storage.foldername(name))[2]
        and d.created_by = auth.uid()
    )
  );

create policy "users delete dossier docs by owner path"
  on storage.objects for delete
  using (
    bucket_id = 'dossier-documents'
    and auth.uid() is not null
    and (storage.foldername(name))[1] = auth.uid()::text
    and exists (
      select 1 from public.dossiers d
      where d.id::text = (storage.foldername(name))[2]
        and d.created_by = auth.uid()
    )
  );

-- Tighten document metadata RLS to match the storage path convention.
alter table documents enable row level security;

drop policy if exists "users manage docs of own dossiers" on documents;
drop policy if exists "users read docs of own dossiers" on documents;
drop policy if exists "users insert docs of own dossiers" on documents;
drop policy if exists "users update docs of own dossiers" on documents;
drop policy if exists "users delete docs of own dossiers" on documents;

create policy "users read docs of own dossiers"
  on documents for select
  using (
    exists (
      select 1 from dossiers d
      where d.id = documents.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users insert docs of own dossiers"
  on documents for insert
  with check (
    uploaded_by = auth.uid()
    and storage_path like auth.uid()::text || '/' || dossier_id::text || '/%'
    and exists (
      select 1 from dossiers d
      where d.id = documents.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users update docs of own dossiers"
  on documents for update
  using (
    exists (
      select 1 from dossiers d
      where d.id = documents.dossier_id
        and d.created_by = auth.uid()
    )
  )
  with check (
    uploaded_by = auth.uid()
    and storage_path like auth.uid()::text || '/' || dossier_id::text || '/%'
    and exists (
      select 1 from dossiers d
      where d.id = documents.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users delete docs of own dossiers"
  on documents for delete
  using (
    exists (
      select 1 from dossiers d
      where d.id = documents.dossier_id
        and d.created_by = auth.uid()
    )
  );

-- Pin rows must also be scoped to the user's own dossiers.
alter table user_dossier_pins
  alter column user_id set default auth.uid();

drop policy if exists "users manage own pins" on user_dossier_pins;
drop policy if exists "users read own dossier pins" on user_dossier_pins;
drop policy if exists "users insert own dossier pins" on user_dossier_pins;
drop policy if exists "users update own dossier pins" on user_dossier_pins;
drop policy if exists "users delete own dossier pins" on user_dossier_pins;

create policy "users read own dossier pins"
  on user_dossier_pins for select
  using (
    user_id = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.id = user_dossier_pins.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users insert own dossier pins"
  on user_dossier_pins for insert
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.id = user_dossier_pins.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users update own dossier pins"
  on user_dossier_pins for update
  using (
    user_id = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.id = user_dossier_pins.dossier_id
        and d.created_by = auth.uid()
    )
  )
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.id = user_dossier_pins.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users delete own dossier pins"
  on user_dossier_pins for delete
  using (
    user_id = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.id = user_dossier_pins.dossier_id
        and d.created_by = auth.uid()
    )
  );

-- Version history for report drafts. The app stores runtime dossier slugs in dossier_id.
create table if not exists rapport_versions (
  id          uuid primary key default gen_random_uuid(),
  session_id  text not null,
  dossier_id  text not null,
  content     text not null,
  format      text not null default 'abrege'
                check (format in ('abrege', 'complet', 'markdown', 'html')),
  label       text not null default '',
  is_initial  boolean not null default false,
  created_by  uuid references auth.users on delete set null default auth.uid(),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

alter table rapport_versions enable row level security;

create index if not exists rapport_versions_session_created_idx
  on rapport_versions (session_id, created_at desc);

create index if not exists rapport_versions_dossier_created_idx
  on rapport_versions (dossier_id, created_at desc);

drop trigger if exists rapport_versions_updated_at on rapport_versions;
create trigger rapport_versions_updated_at
  before update on rapport_versions
  for each row execute function touch_updated_at();

drop policy if exists "users read own rapport versions" on rapport_versions;
drop policy if exists "users insert own rapport versions" on rapport_versions;
drop policy if exists "users update own rapport versions" on rapport_versions;
drop policy if exists "users delete own rapport versions" on rapport_versions;

create policy "users read own rapport versions"
  on rapport_versions for select
  using (
    exists (
      select 1 from dossiers d
      where d.slug = rapport_versions.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users insert own rapport versions"
  on rapport_versions for insert
  with check (
    created_by = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.slug = rapport_versions.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users update own rapport versions"
  on rapport_versions for update
  using (
    created_by = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.slug = rapport_versions.dossier_id
        and d.created_by = auth.uid()
    )
  )
  with check (
    created_by = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.slug = rapport_versions.dossier_id
        and d.created_by = auth.uid()
    )
  );

create policy "users delete own rapport versions"
  on rapport_versions for delete
  using (
    created_by = auth.uid()
    and exists (
      select 1 from dossiers d
      where d.slug = rapport_versions.dossier_id
        and d.created_by = auth.uid()
    )
  );
