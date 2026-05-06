import { createClient } from '@/lib/supabase/client'
import type { Dossier } from '@/types'

function formatUpdatedAt(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return "Modifié aujourd'hui"
  if (days === 1) return 'Il y a 1 jour'
  if (days < 7) return `Il y a ${days} jours`
  if (days < 14) return 'Il y a 1 semaine'
  return `Il y a ${Math.floor(days / 7)} semaines`
}

function toUiDossier(row: Record<string, unknown>, userId: string): Dossier {
  const pins = row.user_dossier_pins as Array<{ user_id: string }> | null
  return {
    id: row.id as string,
    slug: row.slug as string,
    address: row.address as string,
    property_type: row.property_type as string,
    neighborhood: row.neighborhood as string,
    status: row.status as Dossier['status'],
    updatedAt: formatUpdatedAt(row.updated_at as string),
    pinned: Array.isArray(pins) && pins.some(p => p.user_id === userId),
  }
}

export async function fetchDossiers(): Promise<Dossier[]> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return []

  const { data, error } = await supabase
    .from('dossiers')
    .select('*, user_dossier_pins!left(user_id)')
    .order('updated_at', { ascending: false })

  if (error) throw error
  return (data ?? []).map(row => toUiDossier(row, user.id))
}

export async function fetchDossier(slug: string): Promise<Dossier | null> {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return null

  const { data, error } = await supabase
    .from('dossiers')
    .select('*, user_dossier_pins!left(user_id)')
    .eq('slug', slug)
    .single()

  if (error) return null
  return toUiDossier(data, user.id)
}
