import type { Adjustment, Comparable } from '@/types'
import { computeReconciledValue } from './compute-reconciled-value'
import { computeAdjustedPriceStats } from './compute-adjusted-price-stats'
import { computeTimeAdjustmentRate } from './compute-time-adjustment-rate'
import { checkComparableMinimum } from './check-comparable-minimum'
import { buildOEAQChecklist } from './build-oeaq-checklist'

export interface ValuationConclusion {
  /** Weighted reconciled value */
  reconciledValue: number
  /** Simple average of adjusted prices */
  averageValue: number
  /** ±1 stdDev confidence interval around reconciledValue */
  confidenceRange: { low: number; high: number }
  /** CV of adjusted prices */
  cv: number
  /** Overall reliability: 'élevée' | 'modérée' | 'faible' */
  reliability: 'élevée' | 'modérée' | 'faible'
  /** Number of OEAQ checks failing */
  oeaqWarnings: number
  /** Whether a time adjustment rate was detected */
  hasTimeAdjustment: boolean
  /** Annualized time adjustment rate (% per year), null if not detected */
  annualTimeRatePct: number | null
}

/**
 * Synthesizes key analytics into a structured valuation conclusion.
 * Combines weighted reconciliation, dispersion stats, OEAQ compliance,
 * and time adjustment rate into a single summary object.
 *
 * Returns null when no adjustments are provided.
 */
export function computeValuationConclusion(
  adjs: Adjustment[],
  comps: Comparable[],
): ValuationConclusion | null {
  if (adjs.length === 0) return null

  const reconciled = computeReconciledValue(adjs)
  if (!reconciled) return null

  const prices = adjs.map(a => a.adjusted)
  const averageValue = Math.round(prices.reduce((s, p) => s + p, 0) / prices.length)

  const stats = computeAdjustedPriceStats(adjs)
  const cv = stats?.cv ?? 0
  const stdDev = stats?.stdDev ?? 0
  const confidenceRange = {
    low: Math.round(reconciled.value - stdDev),
    high: Math.round(reconciled.value + stdDev),
  }

  const timeRate = comps.length >= 2 ? computeTimeAdjustmentRate(comps) : null
  const oeaqChecks = buildOEAQChecklist(comps, adjs)
  const oeaqWarnings = oeaqChecks.filter(c => !c.pass).length
  const minCheck = checkComparableMinimum(comps)

  // Reliability: high when OEAQ min met + low CV + reconciliation confidence forte
  const reliability: ValuationConclusion['reliability'] =
    (minCheck.pass && cv < 10 && reconciled.confidence === 'forte') ? 'élevée'
      : (cv < 20 && oeaqWarnings <= 2) ? 'modérée'
        : 'faible'

  return {
    reconciledValue: reconciled.value,
    averageValue,
    confidenceRange,
    cv,
    reliability,
    oeaqWarnings,
    hasTimeAdjustment: timeRate !== null,
    annualTimeRatePct: timeRate?.annualRatePct ?? null,
  }
}
