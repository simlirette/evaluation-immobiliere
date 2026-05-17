import type { Adjustment } from '@/types'

export interface AdjustmentConvergence {
  /** CV of raw sale prices */
  rawCv: number
  /** CV of adjusted indicated values */
  adjustedCv: number
  /**
   * (rawCv - adjustedCv) / rawCv × 100
   * Positive = adjustments tightened the spread (good)
   * Negative = adjustments widened the spread (flag)
   */
  convergencePct: number
  /** True when adjustedCv < rawCv */
  converged: boolean
}

function cv(values: number[]): number {
  if (values.length < 2) return 0
  const mean = values.reduce((s, v) => s + v, 0) / values.length
  if (mean === 0) return 0
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length
  return Math.round(Math.sqrt(variance) / mean * 1000) / 10
}

/**
 * Measures whether adjustments tightened (converged) or widened the price spread.
 * A positive convergencePct means adjusted prices are more homogeneous than raw,
 * which validates the adjustment methodology.
 *
 * Returns null when fewer than 3 adjustments.
 */
export function computeAdjustmentConvergence(adjs: Adjustment[]): AdjustmentConvergence | null {
  if (adjs.length < 3) return null

  const rawCv = cv(adjs.map(a => a.salePrice))
  const adjustedCv = cv(adjs.map(a => a.adjusted))
  const convergencePct = rawCv > 0
    ? Math.round((rawCv - adjustedCv) / rawCv * 1000) / 10
    : 0

  return { rawCv, adjustedCv, convergencePct, converged: adjustedCv < rawCv }
}
