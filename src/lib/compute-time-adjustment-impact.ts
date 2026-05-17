import type { Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface TimeAdjustmentImpactEntry {
  comparableId: string
  comparableLabel: string
  yearAdj: number
  grossAdj: number
  /**
   * |year_adj| / grossAdj × 100.
   * null when grossAdj = 0 (no adjustments applied to this comp).
   */
  yearAdjPctOfGross: number | null
}

export interface TimeAdjustmentImpact {
  entries: TimeAdjustmentImpactEntry[]
  /**
   * Mean of yearAdjPctOfGross across comps where grossAdj > 0.
   * null when no comps have any adjustments.
   */
  avgYearAdjPctOfGross: number | null
  /** True when avgYearAdjPctOfGross ≥ 40% — time adjustments dominate the methodology */
  timeAdjustmentDominant: boolean
}

/**
 * Measures what fraction of each comparable's gross adjustment is attributable
 * to the time (year) adjustment component.
 * A high avgYearAdjPctOfGross suggests the appraisal relies heavily on time corrections.
 *
 * Returns null when adjustments is empty.
 */
export function computeTimeAdjustmentImpact(adjs: Adjustment[]): TimeAdjustmentImpact | null {
  if (adjs.length === 0) return null

  const entries: TimeAdjustmentImpactEntry[] = adjs.map(a => {
    const { gross: grossAdj } = computeGrossAdjustment(a)
    const yearAdjPctOfGross = grossAdj > 0
      ? Math.round((Math.abs(a.year_adj) / grossAdj) * 1000) / 10
      : null

    return {
      comparableId: a.comparable_id,
      comparableLabel: a.comparableLabel,
      yearAdj: a.year_adj,
      grossAdj,
      yearAdjPctOfGross,
    }
  })

  const withData = entries.filter(e => e.yearAdjPctOfGross !== null)
  const avgYearAdjPctOfGross = withData.length > 0
    ? Math.round(
        withData.reduce((s, e) => s + e.yearAdjPctOfGross!, 0) / withData.length * 10,
      ) / 10
    : null

  return {
    entries,
    avgYearAdjPctOfGross,
    timeAdjustmentDominant: avgYearAdjPctOfGross != null && avgYearAdjPctOfGross >= 40,
  }
}
