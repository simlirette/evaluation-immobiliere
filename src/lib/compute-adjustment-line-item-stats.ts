import type { Adjustment } from '@/types'

export interface LineItemStats {
  min: number
  max: number
  mean: number
  median: number
}

export interface AdjustmentLineItemStats {
  surface: LineItemStats
  year: LineItemStats
  condition: LineItemStats
  garage: LineItemStats
}

function stats(values: number[]): LineItemStats {
  const sorted = [...values].sort((a, b) => a - b)
  const n = sorted.length
  const mean = values.reduce((s, v) => s + v, 0) / n
  const median = n % 2 === 1
    ? sorted[Math.floor(n / 2)]
    : (sorted[n / 2 - 1] + sorted[n / 2]) / 2
  return { min: sorted[0], max: sorted[n - 1], mean, median }
}

export function computeAdjustmentLineItemStats(adjs: Adjustment[]): AdjustmentLineItemStats | null {
  if (adjs.length === 0) return null

  return {
    surface: stats(adjs.map(a => a.surface_adj)),
    year: stats(adjs.map(a => a.year_adj)),
    condition: stats(adjs.map(a => a.condition_adj)),
    garage: stats(adjs.map(a => a.garage_adj)),
  }
}
