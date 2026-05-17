import type { Comparable } from '@/types'

export interface ComparablePriceQuartiles {
  q1: number
  q2: number
  q3: number
  iqr: number
  /** Lower fence: q1 − 1.5 × IQR */
  lowerFence: number
  /** Upper fence: q3 + 1.5 × IQR */
  upperFence: number
  /** IDs of comparables with sale_price outside [lowerFence, upperFence] */
  outlierIds: string[]
}

function quantile(sorted: number[], p: number): number {
  const pos = p * (sorted.length - 1)
  const lo = Math.floor(pos)
  const hi = Math.ceil(pos)
  return lo === hi ? sorted[lo] : Math.round(sorted[lo] + (pos - lo) * (sorted[hi] - sorted[lo]))
}

/**
 * Computes IQR-based price quartiles and Tukey fence outlier detection.
 * Complements detectOutlierComparables (which uses median deviation) with
 * a distribution-based approach.
 *
 * Returns null when fewer than 4 comparables (need enough data for meaningful quartiles).
 */
export function computeComparablePriceQuartiles(comps: Comparable[]): ComparablePriceQuartiles | null {
  if (comps.length < 4) return null

  const sorted = [...comps].sort((a, b) => a.sale_price - b.sale_price).map(c => c.sale_price)

  const q1 = quantile(sorted, 0.25)
  const q2 = quantile(sorted, 0.5)
  const q3 = quantile(sorted, 0.75)
  const iqr = q3 - q1
  const lowerFence = Math.round(q1 - 1.5 * iqr)
  const upperFence = Math.round(q3 + 1.5 * iqr)

  const outlierIds = comps
    .filter(c => c.sale_price < lowerFence || c.sale_price > upperFence)
    .map(c => c.id)

  return { q1, q2, q3, iqr, lowerFence, upperFence, outlierIds }
}
