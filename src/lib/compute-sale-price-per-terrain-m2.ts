import type { Comparable } from '@/types'

export interface SalePricePerTerrainM2 {
  count: number
  min: number
  max: number
  mean: number
  median: number
  /** stdDev / mean × 100 (1 decimal) */
  cv: number
  /** Number of comparables excluded due to null terrain_m2 */
  missingCount: number
}

/**
 * Computes $/terrain m² distribution statistics across comparables.
 * Only includes comparables where terrain_m2 > 0 and sale_price > 0.
 *
 * Returns null when fewer than 2 comparables have valid terrain_m2.
 */
export function computeSalePricePerTerrainM2(comps: Comparable[]): SalePricePerTerrainM2 | null {
  const valid = comps.filter(c => c.terrain_m2 != null && c.terrain_m2 > 0 && c.sale_price > 0)
  const missingCount = comps.length - valid.length

  if (valid.length < 2) return null

  const values = valid.map(c => c.sale_price / c.terrain_m2!)
  const sorted = [...values].sort((a, b) => a - b)
  const n = sorted.length

  const min = Math.round(sorted[0])
  const max = Math.round(sorted[n - 1])
  const mean = Math.round(values.reduce((s, v) => s + v, 0) / n)
  const median = n % 2 === 0
    ? Math.round((sorted[n / 2 - 1] + sorted[n / 2]) / 2)
    : Math.round(sorted[Math.floor(n / 2)])
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const stdDev = Math.sqrt(variance)
  const cv = mean > 0 ? Math.round((stdDev / mean) * 1000) / 10 : 0

  return { count: n, min, max, mean, median, cv, missingCount }
}
