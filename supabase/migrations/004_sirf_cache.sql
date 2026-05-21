-- supabase/migrations/004_sirf_cache.sql
-- Cache des transactions SIRF (Registre foncier du Québec).
-- Durée de vie : 90 jours. Partagé entre tous les évaluateurs (service-role only).

create table if not exists sirf_cache (
  id           uuid primary key default gen_random_uuid(),
  no_lot       bigint not null,
  prix_vente   numeric not null default 0,
  date_vente   text    not null default '',
  vendeur      text    not null default '',
  acheteur     text    not null default '',
  source_doc   text    not null default '',   -- identifiant acte SIRF (ex: "2024-12345")
  raw_text     text    not null default '',   -- texte OCR brut pour audit
  fetched_at   timestamptz not null default now(),
  expires_at   timestamptz not null default now() + interval '90 days'
);

-- Lookup rapide par lot + validité
create index if not exists sirf_cache_no_lot_expires
  on sirf_cache (no_lot, expires_at desc);

-- Service-role only — les évaluateurs ne lisent/écrivent pas directement
alter table sirf_cache enable row level security;

create policy "service role full access"
  on sirf_cache for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');
