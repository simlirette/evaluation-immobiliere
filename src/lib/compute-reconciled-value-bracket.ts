import type { Adjustment } from '@/types'

export interface ReconciledValueBracket {
  /** Minimum adjusted price across all comparables */
  min: number
  /** Maximum adjusted price across all comparables */
  max: number
  reconciledValue: number
  /** True when reconciledValue is within [min, max] */
  bracketed: boolean
  /**
   * When not bracketed: % distance from the nearest fence (positive value).
   * When bracketed: 0.
   */
  deviationPct: number
}

/**
 * Checks whether the reconciled value falls within the adjusted price range of the comp set.
 * A value outside [min adjusted, max adjusted] violates OEAQ's range-bracketing expectation.
 *
 * Returns null when adjustments is empty or reconciledValue ≤ 0.
 */
export function computeReconciledValueBracket(
  adjs: Adjustment[],
  reconciledValue: number,
): ReconciledValueBracket | null {
  if (adjs.length === 0 || reconciledValue <= 0) return null

  const prices = adjs.map(a => a.adjusted)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const bracketed = reconciledValue >= min && reconciledValue <= max

  let deviationPct = 0
  if (!bracketed) {
    if (reconciledValue < min) {
      deviationPct = Math.round(((min - reconciledValue) / min) * 1000) / 10
    } else {
      deviationPct = Math.round(((reconciledValue - max) / max) * 1000) / 10
    }
  }

  return { min, max, reconciledValue, bracketed, deviationPct }
}
