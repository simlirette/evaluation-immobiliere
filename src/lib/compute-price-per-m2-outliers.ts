import type { Comparable } from '@/types'
import { computePricePerM2 } from './comparable-utils'

export interface PricePerM2Outliers {
  q1: number
  median: number
  q3: number
  iqr: number
  lowerFence: number
  upperFence: number
  /** IDs of comparables with $/m² outside [lowerFence, upperFence] */
  outlierIds: string[]
  /** Number of comps excluded for missing hab_m2 */
  missingCount: number
}

function quantile(sorted: number[], p: number): number {
  const pos = p * (sorted.length - 1)
  const lo = Math.floor(pos)
  const hi = Math.ceil(pos)
  return lo === hi ? sorted[lo] : Math.round(sorted[lo] + (pos - lo) * (sorted[hi] - sorted[lo]))
}

/**
 * Detects $/m² outliers using IQR Tukey fences.
 * Separate from computeComparablePriceQuartiles which operates on raw prices.
 *
 * Returns null when fewer than 4 comparables have hab_m2 data.
 */
export function computePricePerM2Outliers(comps: Comparable[]): PricePerM2Outliers | null {
  const valid = comps
    .map(c => ({ id: c.id, m2: computePricePerM2(c.sale_price, c.hab_m2) }))
    .filter((v): v is { id: string; m2: number } => v.m2 !== null)

  const missingCount = comps.length - valid.length

  if (valid.length < 4) return null

  const sorted = [...valid].sort((a, b) => a.m2 - b.m2)
  const values = sorted.map(v => v.m2)

  const q1 = quantile(values, 0.25)
  const median = quantile(values, 0.5)
  const q3 = quantile(values, 0.75)
  const iqr = q3 - q1
  const lowerFence = Math.round(q1 - 1.5 * iqr)
  const upperFence = Math.round(q3 + 1.5 * iqr)

  const outlierIds = valid
    .filter(v => v.m2 < lowerFence || v.m2 > upperFence)
    .map(v => v.id)

  return { q1, median, q3, iqr, lowerFence, upperFence, outlierIds, missingCount }
}
