import type { Comparable } from '@/types'

export interface PricePerM2Distribution {
  /** Comparables with valid hab_m2 and sale_price */
  count: number
  min: number
  max: number
  median: number
  mean: number
  stdDev: number
  /** stdDev / mean × 100, rounded to 1 decimal */
  cv: number
}

/**
 * Computes distribution statistics for price-per-m² across comparables.
 * Only includes comparables with hab_m2 > 0 and sale_price > 0.
 * Returns null when fewer than 2 valid comparables.
 */
export function computePricePerM2Distribution(comps: Comparable[]): PricePerM2Distribution | null {
  const ppm2 = comps
    .filter(c => c.hab_m2 != null && c.hab_m2 > 0 && c.sale_price > 0)
    .map(c => Math.round(c.sale_price / c.hab_m2!))

  if (ppm2.length < 2) return null

  const sorted = [...ppm2].sort((a, b) => a - b)
  const n = sorted.length
  const min = sorted[0]
  const max = sorted[n - 1]
  const mean = Math.round(sorted.reduce((s, v) => s + v, 0) / n)
  const median = n % 2 === 0
    ? Math.round((sorted[n / 2 - 1] + sorted[n / 2]) / 2)
    : sorted[Math.floor(n / 2)]
  const variance = sorted.reduce((s, v) => s + (v - mean) ** 2, 0) / n
  const stdDev = Math.round(Math.sqrt(variance))
  const cv = mean > 0 ? Math.round((stdDev / mean) * 1000) / 10 : 0

  return { count: n, min, max, median, mean, stdDev, cv }
}
