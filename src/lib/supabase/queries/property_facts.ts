import { createClient } from '@/lib/supabase/client'
import type { FactChip } from '@/types'

export async function fetchPropertyFacts(dossierId: string): Promise<FactChip[]> {
  const supabase = createClient()
  const { data, error } = await supabase
    .from('property_facts')
    .select('label, highlight')
    .eq('dossier_id', dossierId)
    .order('sort_order', { ascending: true })

  if (error) throw error
  return data ?? []
}
