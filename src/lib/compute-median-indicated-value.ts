import type { Adjustment } from '@/types'

/**
 * Computes the median of indicated (adjusted) values across a comparable set.
 * Median is preferred over mean for valuation reconciliation — more robust to outliers.
 * Returns null for empty input.
 */
export function computeMedianIndicatedValue(adjs: Adjustment[]): number | null {
  if (adjs.length === 0) return null
  const sorted = [...adjs].map(a => a.adjusted).sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 1
    ? sorted[mid]
    : Math.round((sorted[mid - 1] + sorted[mid]) / 2)
}
