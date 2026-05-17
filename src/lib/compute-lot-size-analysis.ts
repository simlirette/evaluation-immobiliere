import type { Comparable } from '@/types'

export interface LotSizeAnalysis {
  count: number
  median: number
  min: number
  max: number
  /** Coefficient of variation % — spread indicator */
  cvPct: number
  /** Comparables with null terrain_m2 */
  missingCount: number
}

/**
 * Computes lot size (terrain_m2) statistics across a set of comparables.
 * Returns null when fewer than 2 comparables have terrain_m2 data.
 */
export function computeLotSizeAnalysis(comps: Comparable[]): LotSizeAnalysis | null {
  const values = comps
    .map(c => c.terrain_m2)
    .filter((v): v is number => v != null && v > 0)

  const missingCount = comps.length - values.length

  if (values.length < 2) return null

  const sorted = [...values].sort((a, b) => a - b)
  const min = sorted[0]
  const max = sorted[sorted.length - 1]
  const mid = Math.floor(sorted.length / 2)
  const median = sorted.length % 2 === 0
    ? Math.round((sorted[mid - 1] + sorted[mid]) / 2)
    : sorted[mid]
  const avg = values.reduce((s, v) => s + v, 0) / values.length
  const variance = values.reduce((s, v) => s + (v - avg) ** 2, 0) / values.length
  const stdDev = Math.sqrt(variance)
  const cvPct = avg > 0 ? Math.round((stdDev / avg) * 1000) / 10 : 0

  return { count: values.length, median, min, max, cvPct, missingCount }
}
