import type { Comparable, Adjustment } from '@/types'
import { computeComparableCompleteness } from './compute-comparable-completeness'
import { detectOutlierComparables } from './detect-outlier-comparables'
import { detectDuplicateComparables } from './detect-duplicate-comparables'
import { validateComparableDate } from './validate-comparable-date'

export interface DataQualityReport {
  /** Average completeness across all comparables (0–100) */
  avgCompletenessPct: number
  /** Number of comparables with stale sale dates */
  staleCount: number
  /** Number of comparable pairs flagged as potential duplicates */
  duplicatePairCount: number
  /** Number of comparables flagged as outliers (>15% vs median adjusted) */
  outlierCount: number
  /** Overall grade: 'bon' / 'acceptable' / 'faible' */
  grade: 'bon' | 'acceptable' | 'faible'
  /** Issues list for display */
  issues: string[]
}

/**
 * Aggregates data quality signals across the full comparable set into
 * a single summary report. Combines completeness, staleness, duplicates,
 * and outlier checks.
 *
 * Returns null when no comparables are provided.
 */
export function computeDataQualityReport(
  comps: Comparable[],
  adjs: Adjustment[],
): DataQualityReport | null {
  if (comps.length === 0) return null

  const completeness = computeComparableCompleteness(comps)
  const avgCompletenessPct = Math.round(
    completeness.reduce((s, c) => s + c.completenessPct, 0) / completeness.length,
  )

  const staleCount = comps.filter(c => {
    const v = validateComparableDate(c.sale_date)
    return v.stale
  }).length

  const duplicates = detectDuplicateComparables(comps)
  const duplicatePairCount = duplicates.length

  const outliers = detectOutlierComparables(adjs)
  const outlierCount = outliers.filter(o => o.isOutlier).length

  const issues: string[] = []
  if (avgCompletenessPct < 60) issues.push(`Complétude moyenne faible (${avgCompletenessPct} %)`)
  if (staleCount > 0) issues.push(`${staleCount} comparable${staleCount > 1 ? 's' : ''} avec vente ancienne`)
  if (duplicatePairCount > 0) issues.push(`${duplicatePairCount} doublon${duplicatePairCount > 1 ? 's' : ''} potentiel${duplicatePairCount > 1 ? 's' : ''}`)
  if (outlierCount > 0) issues.push(`${outlierCount} valeur${outlierCount > 1 ? 's' : ''} atypique${outlierCount > 1 ? 's' : ''}`)

  const grade: DataQualityReport['grade'] =
    issues.length === 0 ? 'bon'
      : issues.length <= 1 && avgCompletenessPct >= 60 ? 'acceptable'
        : 'faible'

  return { avgCompletenessPct, staleCount, duplicatePairCount, outlierCount, grade, issues }
}
