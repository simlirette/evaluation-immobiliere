import type { Adjustment } from '@/types'

export interface GrossAdjustmentDistribution {
  min: number
  max: number
  mean: number
  median: number
  stdDev: number
  cv: number
}

function grossPct(a: Adjustment): number {
  const gross = Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)
  return (gross / a.salePrice) * 100
}

export function computeGrossAdjustmentDistribution(adjs: Adjustment[]): GrossAdjustmentDistribution | null {
  if (adjs.length < 2) return null

  const pcts = adjs.map(grossPct)
  const sorted = [...pcts].sort((a, b) => a - b)
  const n = sorted.length
  const mean = pcts.reduce((s, v) => s + v, 0) / n
  const median = n % 2 === 1
    ? sorted[Math.floor(n / 2)]
    : (sorted[n / 2 - 1] + sorted[n / 2]) / 2
  const variance = pcts.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const stdDev = Math.sqrt(variance)
  const cv = mean > 0 ? (stdDev / mean) * 100 : 0

  return { min: sorted[0], max: sorted[n - 1], mean, median, stdDev, cv }
}
