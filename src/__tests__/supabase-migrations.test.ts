import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const migration = readFileSync(
  join(process.cwd(), 'supabase/migrations/005_storage_rls_and_rapport_versions.sql'),
  'utf8',
)

describe('Supabase security migration', () => {
  it('replaces broad document storage policies with owner-path checks', () => {
    expect(migration).toContain('drop policy if exists "users read own docs" on storage.objects')
    expect(migration).toContain("(storage.foldername(name))[1] = auth.uid()::text")
    expect(migration).toContain("d.id::text = (storage.foldername(name))[2]")
    expect(migration).toContain("d.created_by = auth.uid()")
  })

  it('creates rapport_versions with RLS through dossier ownership', () => {
    expect(migration).toContain('create table if not exists rapport_versions')
    expect(migration).toContain('alter table rapport_versions enable row level security')
    expect(migration).toContain('where d.slug = rapport_versions.dossier_id')
    expect(migration).toContain('created_by = auth.uid()')
  })

  it('tightens pin policies to owned dossiers', () => {
    expect(migration).toContain('drop policy if exists "users manage own pins" on user_dossier_pins')
    expect(migration).toContain('create policy "users insert own dossier pins"')
    expect(migration).toContain('where d.id = user_dossier_pins.dossier_id')
  })
})
