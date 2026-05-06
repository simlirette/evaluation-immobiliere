import { createClient } from '@/lib/supabase/client'
import type { DbAdjustment, DbComparable } from '@/types/db'
import type { Adjustment } from '@/types'

export async function fetchAdjustments(dossierId: string): Promise<Adjustment[]> {
  const supabase = createClient()

  const [{ data: adjs, error: e1 }, { data: comps, error: e2 }] = await Promise.all([
    supabase.from('adjustments').select('*').eq('dossier_id', dossierId),
    supabase.from('comparables').select('*').eq('dossier_id', dossierId).order('sort_order'),
  ])

  if (e1) throw e1
  if (e2) throw e2

  const compMap = new Map<string, DbComparable>(
    (comps ?? []).map(c => [c.id, c as DbComparable])
  )

  return (adjs ?? []).map((adj: DbAdjustment): Adjustment => {
    const comp = compMap.get(adj.comparable_id)
    const total = adj.surface_adj + adj.year_adj + adj.condition_adj + adj.garage_adj
    return {
      id: adj.id,
      comparable_id: adj.comparable_id,
      comparableLabel: comp ? `${comp.rank} — ${comp.address}` : adj.comparable_id,
      salePrice: comp?.sale_price ?? 0,
      surface_adj: adj.surface_adj,
      year_adj: adj.year_adj,
      condition_adj: adj.condition_adj,
      garage_adj: adj.garage_adj,
      adjusted: (comp?.sale_price ?? 0) + total,
    }
  })
}
