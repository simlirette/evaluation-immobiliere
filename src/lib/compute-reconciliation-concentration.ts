import type { Adjustment } from '@/types'
import { computeReconciledValue } from './compute-reconciled-value'

export interface ReconciliationConcentration {
  /** Weight pct per adjustment id (0–100, sums to 100) */
  weights: Record<string, number>
  /**
   * Herfindahl-Hirschman Index: sum of squared weight fractions (0–1).
   * 1/n for equal weights; approaches 1 when one comp dominates.
   */
  hhi: number
  /** True when any single comparable carries > 40% of reconciliation weight */
  concentrated: boolean
  /** Id of the adjustment with the highest weight */
  maxWeightId: string
  /** Highest weight pct */
  maxWeightPct: number
}

/**
 * Measures how concentrated the reconciliation weights are across comparables.
 * A high HHI (or any weight > 40%) signals over-reliance on a single comparable.
 *
 * Returns null when fewer than 2 adjustments or computeReconciledValue returns null.
 */
export function computeReconciliationConcentration(
  adjs: Adjustment[],
): ReconciliationConcentration | null {
  if (adjs.length < 2) return null

  const reconciled = computeReconciledValue(adjs)
  if (!reconciled) return null

  const weights = reconciled.weights

  // HHI: sum of (wi/100)²
  const hhi = Math.round(
    Object.values(weights).reduce((s, w) => s + (w / 100) ** 2, 0) * 1000,
  ) / 1000

  const maxEntry = Object.entries(weights).reduce(
    (best, [id, pct]) => pct > best.pct ? { id, pct } : best,
    { id: adjs[0].id, pct: 0 },
  )

  return {
    weights,
    hhi,
    concentrated: maxEntry.pct > 40,
    maxWeightId: maxEntry.id,
    maxWeightPct: maxEntry.pct,
  }
}
