import type { PriceIndexationEntry } from './compute-price-indexation'

export interface PriceIndexationSummary {
  count: number
  /** Sum of (indexedPrice − originalPrice) across all comparables */
  totalAdded: number
  /** Mean adjustmentPct across all comparables (1 decimal) */
  avgAdjPct: number
  /** Id of the comparable with the largest |adjustmentPct| */
  mostAdjustedId: string
  /** |adjustmentPct| of the most-adjusted comparable */
  mostAdjustedPct: number
  /** Id of the comparable with the smallest |adjustmentPct| */
  leastAdjustedId: string
  /** |adjustmentPct| of the least-adjusted comparable */
  leastAdjustedPct: number
}

/**
 * Aggregates a set of PriceIndexationEntry records into summary statistics.
 * Useful for conveying the overall magnitude of time-indexation in the comp set.
 *
 * Returns null when entries is empty.
 */
export function computePriceIndexationSummary(
  entries: PriceIndexationEntry[],
): PriceIndexationSummary | null {
  if (entries.length === 0) return null

  const totalAdded = entries.reduce((s, e) => s + (e.indexedPrice - e.originalPrice), 0)
  const avgAdjPct = Math.round(
    (entries.reduce((s, e) => s + e.adjustmentPct, 0) / entries.length) * 10,
  ) / 10

  const byAbsPct = [...entries].sort((a, b) => Math.abs(b.adjustmentPct) - Math.abs(a.adjustmentPct))
  const most = byAbsPct[0]
  const least = byAbsPct[byAbsPct.length - 1]

  return {
    count: entries.length,
    totalAdded: Math.round(totalAdded),
    avgAdjPct,
    mostAdjustedId: most.comparableId,
    mostAdjustedPct: Math.abs(most.adjustmentPct),
    leastAdjustedId: least.comparableId,
    leastAdjustedPct: Math.abs(least.adjustmentPct),
  }
}
