import type { Adjustment, Comparable } from '@/types'
import { computeComparableQualityScore } from './compute-comparable-quality-score'
import { computeReconciledValue } from './compute-reconciled-value'
import { detectOutlierComparables } from './detect-outlier-comparables'

export interface ComparableRanking {
  comparableId: string
  comparableLabel: string
  /** Quality score 0–10 from recency + inverse gross adj */
  qualityScore: number
  /** Weight % in weighted reconciliation (0–100) */
  weightPct: number
  /** Whether this comp is an outlier (>15% from median adjusted price) */
  isOutlier: boolean
  /** Composite rank score 0–100: quality×50% + weight×30% + non-outlier×20% */
  rankScore: number
  /** Rank position (1 = best) */
  rank: number
}

/**
 * Ranks comparables by composite score combining quality, reconciliation weight,
 * and outlier status. Provides a single recommended ordering for the appraiser.
 *
 * Returns [] when adjustments is empty or quality scores cannot be computed.
 */
export function computeComparableRanking(
  comps: Comparable[],
  adjs: Adjustment[],
): ComparableRanking[] {
  if (comps.length === 0 || adjs.length === 0) return []

  const qualityScores = computeComparableQualityScore(comps, adjs)
  const qualityMap = new Map(qualityScores.map(q => [q.comparableId, q.score]))

  const reconciled = computeReconciledValue(adjs)
  const weightMap = reconciled ? new Map(Object.entries(reconciled.weights)) : new Map<string, number>()

  const outliers = detectOutlierComparables(adjs)
  const outlierSet = new Set(outliers.filter(o => o.isOutlier).map(o => o.id))

  const entries = adjs.map(a => {
    const qualityScore = qualityMap.get(a.comparable_id) ?? 0
    const weightPct = weightMap.get(a.id) ?? 0
    const isOutlier = outlierSet.has(a.id)
    // Non-outlier bonus: 10 (not outlier) or 0 (outlier)
    const outlierBonus = isOutlier ? 0 : 10
    const rankScore = Math.round(
      (qualityScore / 10) * 50 + (weightPct / 100) * 30 + outlierBonus * 2,
    )
    return {
      comparableId: a.comparable_id,
      comparableLabel: a.comparableLabel,
      qualityScore,
      weightPct,
      isOutlier,
      rankScore,
      rank: 0,
    }
  })

  entries.sort((a, b) => b.rankScore - a.rankScore)
  entries.forEach((e, i) => { e.rank = i + 1 })

  return entries
}
