import type { Adjustment } from '@/types'
import { computeReconciledValue } from './compute-reconciled-value'

export interface SensitivityEntry {
  comparableId: string
  comparableLabel: string
  /** Reconciled value when this comparable is excluded */
  reconciledWithout: number
  /** Absolute change vs full-set reconciled value */
  delta: number
  /** Percentage change vs full-set reconciled value, rounded to 1 decimal */
  deltaPct: number
  /** Whether excluding this comp changes the value by more than 3% */
  influential: boolean
}

export interface SensitivityAnalysis {
  baseValue: number
  entries: SensitivityEntry[]
}

/**
 * Leave-one-out sensitivity analysis on the weighted reconciled value.
 * For each comparable, computes the reconciled value of the remaining set
 * to reveal how much each comp drives the conclusion.
 *
 * Returns null when fewer than 3 adjustments (need at least 2 remaining after exclusion).
 */
export function computeSensitivityAnalysis(adjs: Adjustment[]): SensitivityAnalysis | null {
  if (adjs.length < 3) return null

  const base = computeReconciledValue(adjs)
  if (!base) return null

  const entries: SensitivityEntry[] = adjs.map(excluded => {
    const remaining = adjs.filter(a => a.id !== excluded.id)
    const without = computeReconciledValue(remaining)!
    const delta = without.value - base.value
    const deltaPct = Math.round((delta / base.value) * 1000) / 10
    return {
      comparableId: excluded.comparable_id,
      comparableLabel: excluded.comparableLabel,
      reconciledWithout: without.value,
      delta,
      deltaPct,
      influential: Math.abs(deltaPct) >= 3,
    }
  })

  return { baseValue: base.value, entries }
}
