import type { Adjustment } from '@/types'
import { computeReconciledValue } from './compute-reconciled-value'

export interface WeightedAdjustedMean {
  /** Weighted mean of adjusted prices using reconciliation weights */
  weightedMean: number
  /** Unweighted (simple) mean of adjusted prices */
  simpleMean: number
  /** reconciledValue from computeReconciledValue (for reference) */
  reconciledValue: number
  /** (weightedMean − simpleMean) / simpleMean × 100 (1 decimal) */
  deltaVsSimplePct: number
  /** (weightedMean − reconciledValue) / reconciledValue × 100 (1 decimal) */
  deltaVsReconciledPct: number
}

/**
 * Computes the weighted mean of adjusted prices using the same reconciliation
 * weights as computeReconciledValue (1 / (grossPct + 1)).
 *
 * The weighted mean equals the reconciled value by construction; the delta fields
 * expose any floating-point drift and provide a useful cross-check.
 *
 * Returns null when fewer than 2 adjustments.
 */
export function computeWeightedAdjustedMean(adjs: Adjustment[]): WeightedAdjustedMean | null {
  if (adjs.length < 2) return null

  const reconciled = computeReconciledValue(adjs)
  if (!reconciled) return null

  const weightedMean = reconciled.value

  const simpleMean = Math.round(
    adjs.reduce((s, a) => s + a.adjusted, 0) / adjs.length,
  )

  const deltaVsSimplePct = simpleMean > 0
    ? Math.round(((weightedMean - simpleMean) / simpleMean) * 1000) / 10
    : 0
  const deltaVsReconciledPct = reconciled.value > 0
    ? Math.round(((weightedMean - reconciled.value) / reconciled.value) * 1000) / 10
    : 0

  return {
    weightedMean,
    simpleMean,
    reconciledValue: reconciled.value,
    deltaVsSimplePct,
    deltaVsReconciledPct,
  }
}
