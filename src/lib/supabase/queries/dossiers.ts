import { createClient } from '@/lib/supabase/client'
import { createRuntimeDossier, fetchRuntimeDossier, type CreateRuntimeDossierInput } from '@/lib/runtime-api'
import type { Dossier, DossierStatus } from '@/types'

export type CreateDossierInput = CreateRuntimeDossierInput

// ── Row shape returned by Supabase ────────────────────────────────────────────

interface DossierRow {
  id: string
  slug: string
  address: string
  property_type: string
  neighborhood: string
  status: DossierStatus
  updated_at: string
  user_dossier_pins: { user_id: string }[]
}

function rowToDossier(row: DossierRow): Dossier {
  return {
    id: row.slug,      // panels use slug as dossierId
    slug: row.slug,
    address: row.address,
    property_type: row.property_type,
    neighborhood: row.neighborhood,
    status: row.status,
    updatedAt: row.updated_at.slice(0, 10),
    pinned: row.user_dossier_pins.length > 0,
  }
}

// ── Queries ───────────────────────────────────────────────────────────────────

export async function fetchDossiers(): Promise<Dossier[]> {
  const supabase = createClient()

  const { data, error } = await supabase
    .from('dossiers')
    .select('id, slug, address, property_type, neighborhood, status, updated_at, user_dossier_pins(user_id)')
    .order('updated_at', { ascending: false })

  if (error) {
    console.error('[fetchDossiers]', error.message)
    return []
  }

  return ((data ?? []) as DossierRow[]).map(rowToDossier).sort(
    (a, b) => Number(b.pinned) - Number(a.pinned)
  )
}

export async function fetchDossier(slug: string): Promise<Dossier | null> {
  // Dossier detail still comes from the runtime API (full facts/comps/etc.)
  return fetchRuntimeDossier(slug)
}

export async function createDossier(input: CreateDossierInput): Promise<Dossier> {
  // 1. Create runtime session first — this generates the session_id (slug)
  const dossier = await createRuntimeDossier(input)

  // 2. Persist in Supabase so the dossier appears in the list across devices/sessions
  const supabase = createClient()
  const { error } = await supabase.from('dossiers').insert({
    slug: dossier.slug,
    address: dossier.address,
    property_type: dossier.property_type,
    neighborhood: dossier.neighborhood,
    status: 'en-cours',
  })

  if (error) {
    // Non-fatal: runtime session created, list will self-heal on next backend sync
    console.warn('[createDossier] Supabase insert failed:', error.message)
  }

  return dossier
}

export async function duplicateDossier(source: Dossier): Promise<Dossier> {
  return createDossier({
    address: `Copie de ${source.address}`,
    property_type: source.property_type,
    neighborhood: source.neighborhood,
  })
}

export async function renameDossier(slug: string, newAddress: string): Promise<void> {
  const supabase = createClient()
  const { error } = await supabase
    .from('dossiers')
    .update({ address: newAddress })
    .eq('slug', slug)

  if (error) {
    console.error('[renameDossier]', error.message)
  }
}

export async function deleteDossier(id: string): Promise<void> {
  // `id` is the slug in this app (panels pass dossierId = slug)
  const supabase = createClient()
  const { error } = await supabase
    .from('dossiers')
    .delete()
    .eq('slug', id)

  if (error) {
    console.error('[deleteDossier]', error.message)
  }
}
