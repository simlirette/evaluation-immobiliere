import type { Adjustment } from '@/types'

export interface PanelAdjustmentBalance {
  totalPositive: number
  totalNegative: number
  netBalance: number
  balancePct: number
}

export function computePanelAdjustmentBalance(adjs: Adjustment[]): PanelAdjustmentBalance | null {
  if (adjs.length === 0) return null

  let totalPositive = 0
  let totalNegative = 0

  for (const a of adjs) {
    for (const v of [a.surface_adj, a.year_adj, a.condition_adj, a.garage_adj]) {
      if (v > 0) totalPositive += v
      else if (v < 0) totalNegative += v
    }
  }

  const netBalance = totalPositive + totalNegative
  const gross = totalPositive - totalNegative
  const balancePct = gross > 0 ? (netBalance / gross) * 100 : 0

  return { totalPositive, totalNegative, netBalance, balancePct }
}
