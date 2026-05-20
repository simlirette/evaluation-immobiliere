-- ─── S2 : Comptes bureau / É.A. + rôles ─────────────────────────────────────
-- Rôles : bureau_admin (gère les comptes É.A.) / evaluateur (traite les dossiers)

-- ─── Table profiles ──────────────────────────────────────────────────────────
create table profiles (
  id           uuid primary key references auth.users on delete cascade,
  role         text not null default 'evaluateur'
                 check (role in ('bureau_admin', 'evaluateur')),
  display_name text,
  created_at   timestamptz not null default now()
);

alter table profiles enable row level security;

-- Chaque utilisateur lit uniquement son profil
create policy "users read own profile"
  on profiles for select
  using (id = auth.uid());

-- bureau_admin lit tous les profils (pour la gestion des comptes)
create policy "bureau_admin reads all profiles"
  on profiles for select
  using (
    exists (
      select 1 from profiles p
      where p.id = auth.uid()
        and p.role = 'bureau_admin'
    )
  );

create policy "users update own profile"
  on profiles for update
  using (id = auth.uid());

-- ─── Trigger : créer automatiquement le profil à l'inscription ───────────────
create or replace function handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- ─── Colonne confirmed_by sur sessions ───────────────────────────────────────
-- Permet de lier chaque checkpoint à un vrai user Supabase
alter table sessions
  add column if not exists confirmed_by uuid references auth.users;
