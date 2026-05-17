import type { Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface GrossToNetRatioEntry {
  comparableId: string
  comparableLabel: string
  grossAdj: number
  /** |adjusted − salePrice| */
  absNetAdj: number
  /**
   * grossAdj / absNetAdj.
   * null when absNetAdj = 0 (adjustments fully cancel out or no net movement).
   */
  ratio: number | null
}

export interface GrossToNetRatio {
  entries: GrossToNetRatioEntry[]
  /**
   * Mean ratio across comps where absNetAdj > 0.
   * null when no comps have a non-zero net adjustment.
   */
  avgRatio: number | null
  /** Comparable ids where ratio > 3 — heavy sign cancellation */
  highCancellationIds: string[]
}

/**
 * For each comparable, computes the ratio of gross adjustment to absolute net adjustment.
 * A ratio of 1 means all adjustments are in the same direction (no cancellation).
 * A ratio of 3 means for every $1 of net movement, $3 was applied (high cancellation).
 *
 * Returns null when adjustments is empty.
 */
export function computeGrossToNetRatio(adjs: Adjustment[]): GrossToNetRatio | null {
  if (adjs.length === 0) return null

  const entries: GrossToNetRatioEntry[] = adjs.map(a => {
    const { gross: grossAdj } = computeGrossAdjustment(a)
    const absNetAdj = Math.abs(a.adjusted - a.salePrice)
    const ratio = absNetAdj > 0
      ? Math.round((grossAdj / absNetAdj) * 100) / 100
      : null

    return {
      comparableId: a.comparable_id,
      comparableLabel: a.comparableLabel,
      grossAdj,
      absNetAdj,
      ratio,
    }
  })

  const withRatio = entries.filter(e => e.ratio !== null)
  const avgRatio = withRatio.length > 0
    ? Math.round(withRatio.reduce((s, e) => s + e.ratio!, 0) / withRatio.length * 100) / 100
    : null

  const highCancellationIds = entries
    .filter(e => e.ratio !== null && e.ratio > 3)
    .map(e => e.comparableId)

  return { entries, avgRatio, highCancellationIds }
}
