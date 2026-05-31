-- Migration 009 — Champs É.A. dans profiles (B2 — profil É.A.)
-- no_permis_oeaq + nom_ea pour pré-remplir SignatureForm

alter table public.profiles
    add column if not exists no_permis_oeaq text not null default '',
    add column if not exists nom_ea          text not null default '';

comment on column public.profiles.no_permis_oeaq is 'Numéro de permis OEAQ de l''évaluateur agréé';
comment on column public.profiles.nom_ea is 'Nom complet de l''évaluateur agréé';
