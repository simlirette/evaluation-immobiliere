import type { Adjustment } from '@/types'

export interface AdjustmentNetPerCompEntry {
  id: string
  comparableLabel: string
  netAdj: number
  netPct: number
  direction: 'positive' | 'negative' | 'neutral'
}

export interface AdjustmentNetPerCompSummary {
  entries: AdjustmentNetPerCompEntry[]
}

export function computeAdjustmentNetPerCompSummary(adjs: Adjustment[]): AdjustmentNetPerCompSummary | null {
  if (adjs.length === 0) return null

  const entries: AdjustmentNetPerCompEntry[] = adjs.map(a => {
    const netAdj = a.surface_adj + a.year_adj + a.condition_adj + a.garage_adj
    const netPct = (netAdj / a.salePrice) * 100
    const direction: 'positive' | 'negative' | 'neutral' =
      netAdj > 0 ? 'positive' : netAdj < 0 ? 'negative' : 'neutral'
    return { id: a.id, comparableLabel: a.comparableLabel, netAdj, netPct, direction }
  })

  entries.sort((a, b) => Math.abs(b.netAdj) - Math.abs(a.netAdj))

  return { entries }
}
