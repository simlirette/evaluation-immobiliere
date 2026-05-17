import type { Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'

export interface AdjustmentSummaryEntry {
  comparableId: string
  comparableLabel: string
  salePrice: number
  adjustedPrice: number
  /** Sum of absolute values of all adj fields / salePrice × 100 */
  grossPct: number
  /** adjusted − salePrice */
  netAmount: number
  /** netAmount / salePrice × 100 (1 decimal, signed) */
  netPct: number
  /** 'upward' when netAmount > 0, 'downward' < 0, 'neutral' = 0 */
  direction: 'upward' | 'downward' | 'neutral'
  /** 'fort' |netPct| ≥ 10%, 'modéré' ≥ 5%, 'faible' < 5% */
  magnitude: 'fort' | 'modéré' | 'faible'
}

/**
 * Produces a per-comparable summary combining gross and net adjustment metrics.
 * Convenience aggregation that brings together computeGrossAdjustment and
 * computeAdjustmentNetEffect into a single record per comparable.
 *
 * Returns [] when adjustments is empty.
 */
export function computeAdjustmentSummaryByComp(adjs: Adjustment[]): AdjustmentSummaryEntry[] {
  return adjs.map(a => {
    const { grossPct } = computeGrossAdjustment(a)
    const netAmount = a.adjusted - a.salePrice
    const netPct = a.salePrice > 0
      ? Math.round((netAmount / a.salePrice) * 1000) / 10
      : 0
    const absNetPct = Math.abs(netPct)
    const direction: AdjustmentSummaryEntry['direction'] =
      netAmount > 0 ? 'upward' : netAmount < 0 ? 'downward' : 'neutral'
    const magnitude: AdjustmentSummaryEntry['magnitude'] =
      absNetPct >= 10 ? 'fort' : absNetPct >= 5 ? 'modéré' : 'faible'

    return {
      comparableId: a.comparable_id,
      comparableLabel: a.comparableLabel,
      salePrice: a.salePrice,
      adjustedPrice: a.adjusted,
      grossPct: Math.round(grossPct * 10) / 10,
      netAmount,
      netPct,
      direction,
      magnitude,
    }
  })
}
