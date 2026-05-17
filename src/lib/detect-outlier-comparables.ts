import type { Adjustment } from '@/types'
import { computeMedianIndicatedValue } from './compute-median-indicated-value'

export interface ComparableOutlier {
  id: string
  adjusted: number
  deviationFromMedianPct: number   // positive = above median, negative = below
  isOutlier: boolean
}

/**
 * Detects comparables whose adjusted (indicated) value deviates significantly from the median.
 * Default threshold: 15 % — flags comparables that may need re-examination or exclusion.
 * Returns empty array when fewer than 3 comparables (median not meaningful with 1–2).
 */
export function detectOutlierComparables(
  adjs: Adjustment[],
  thresholdPct = 15,
): ComparableOutlier[] {
  if (adjs.length < 3) return []
  const median = computeMedianIndicatedValue(adjs)
  if (median == null || median === 0) return []

  return adjs.map(a => {
    const deviationFromMedianPct = Math.round(((a.adjusted - median) / median) * 1000) / 10
    return {
      id: a.id,
      adjusted: a.adjusted,
      deviationFromMedianPct,
      isOutlier: Math.abs(deviationFromMedianPct) > thresholdPct,
    }
  })
}
