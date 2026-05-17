import type { Adjustment } from '@/types'

export interface GrossAdjustmentCeilingEntry {
  comparableId: string
  comparableLabel: string
  salePrice: number
  /** Gross adjustment per line (surface) as % of sale price */
  surfacePct: number
  yearPct: number
  conditionPct: number
  garagePct: number
  /** Max single-line gross adj % */
  maxLinePct: number
  /** Sum of all gross adj / salePrice × 100 */
  totalGrossPct: number
  /** True when any single line > 15% */
  exceedsLineCeiling: boolean
  /** True when total gross > 25% */
  exceedsTotalCeiling: boolean
  /** True when either ceiling is exceeded */
  hasViolation: boolean
}

export interface GrossAdjustmentCeilingReport {
  entries: GrossAdjustmentCeilingEntry[]
  /** Number of comparables with at least one violation */
  violationCount: number
  /** True when all comparables comply */
  compliant: boolean
  /** Average total gross adj % across all comparables */
  avgTotalGrossPct: number
}

/**
 * Audits OEAQ gross adjustment ceilings for each comparable:
 * - Line ceiling: any single adjustment type > 15% of sale price
 * - Total ceiling: sum of all gross adjustments > 25% of sale price
 *
 * Returns null when no adjustments provided.
 */
export function computeGrossAdjustmentCeiling(adjs: Adjustment[]): GrossAdjustmentCeilingReport | null {
  if (adjs.length === 0) return null

  const entries: GrossAdjustmentCeilingEntry[] = adjs.map(a => {
    const sp = a.salePrice > 0 ? a.salePrice : 1
    const surfacePct = Math.round(Math.abs(a.surface_adj) / sp * 1000) / 10
    const yearPct = Math.round(Math.abs(a.year_adj) / sp * 1000) / 10
    const conditionPct = Math.round(Math.abs(a.condition_adj) / sp * 1000) / 10
    const garagePct = Math.round(Math.abs(a.garage_adj) / sp * 1000) / 10
    const maxLinePct = Math.max(surfacePct, yearPct, conditionPct, garagePct)
    const totalGrossPct = Math.round((Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)) / sp * 1000) / 10
    const exceedsLineCeiling = maxLinePct > 15
    const exceedsTotalCeiling = totalGrossPct > 25
    return {
      comparableId: a.comparable_id,
      comparableLabel: a.comparableLabel,
      salePrice: a.salePrice,
      surfacePct, yearPct, conditionPct, garagePct,
      maxLinePct, totalGrossPct,
      exceedsLineCeiling, exceedsTotalCeiling,
      hasViolation: exceedsLineCeiling || exceedsTotalCeiling,
    }
  })

  const violationCount = entries.filter(e => e.hasViolation).length
  const avgTotalGrossPct = Math.round(entries.reduce((s, e) => s + e.totalGrossPct, 0) / entries.length * 10) / 10

  return { entries, violationCount, compliant: violationCount === 0, avgTotalGrossPct }
}
