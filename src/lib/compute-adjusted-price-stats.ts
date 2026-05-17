import type { Adjustment } from '@/types'

export interface AdjustedPriceStats {
  count: number
  mean: number
  stdDev: number
  /** Coefficient of variation = stdDev / mean × 100 (%), rounded to 1 decimal */
  cv: number
  /** 'excellent' cv < 5%, 'bon' < 10%, 'acceptable' < 15%, 'faible' ≥ 15% */
  cohesion: 'excellent' | 'bon' | 'acceptable' | 'faible'
}

/**
 * Computes dispersion statistics on the adjusted (indicated) prices of a
 * comparable set. The coefficient of variation (CV) measures how tightly
 * the adjusted values cluster — a low CV signals a coherent comp set.
 *
 * Returns null when fewer than 2 adjustments are provided (CV is meaningless
 * with a single data point).
 */
export function computeAdjustedPriceStats(adjs: Adjustment[]): AdjustedPriceStats | null {
  if (adjs.length < 2) return null

  const prices = adjs.map(a => a.adjusted)
  const mean = prices.reduce((s, p) => s + p, 0) / prices.length
  if (mean === 0) return null

  const variance = prices.reduce((s, p) => s + (p - mean) ** 2, 0) / prices.length
  const stdDev = Math.sqrt(variance)
  const cv = Math.round((stdDev / mean) * 1000) / 10

  const cohesion: AdjustedPriceStats['cohesion'] =
    cv < 5 ? 'excellent' : cv < 10 ? 'bon' : cv < 15 ? 'acceptable' : 'faible'

  return {
    count: prices.length,
    mean: Math.round(mean),
    stdDev: Math.round(stdDev),
    cv,
    cohesion,
  }
}
