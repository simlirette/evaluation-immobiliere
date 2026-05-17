import type { Comparable } from '@/types'
import { computePricePerM2 } from './comparable-utils'

export interface ValuePerM2Conclusion {
  /** Reconciled value / subject hab_m2 */
  pricePerM2: number
  /** Median $/m² of the comparable set (null if <2 comps have hab_m2) */
  medianCompM2: number | null
  /** (pricePerM2 - medianCompM2) / medianCompM2 × 100, null if no median */
  vsMedianPct: number | null
  /** 'haut' >+10%, 'bas' <-10%, 'médian' otherwise; null if no median */
  signal: 'haut' | 'médian' | 'bas' | null
}

/**
 * Translates a reconciled dollar value to a $/m² conclusion and benchmarks it
 * against the comparable set's median $/m².
 *
 * Returns null when reconciledValue or subjectHabM2 are invalid.
 */
export function computeValuePerM2Conclusion(
  reconciledValue: number,
  subjectHabM2: number,
  comparables: Comparable[],
): ValuePerM2Conclusion | null {
  if (!reconciledValue || !subjectHabM2 || subjectHabM2 <= 0) return null

  const pricePerM2 = Math.round(reconciledValue / subjectHabM2)

  const compM2s = comparables
    .map(c => computePricePerM2(c.sale_price, c.hab_m2))
    .filter((v): v is number => v !== null)
    .sort((a, b) => a - b)

  if (compM2s.length < 2) {
    return { pricePerM2, medianCompM2: null, vsMedianPct: null, signal: null }
  }

  const mid = Math.floor(compM2s.length / 2)
  const medianCompM2 = compM2s.length % 2 === 0
    ? Math.round((compM2s[mid - 1] + compM2s[mid]) / 2)
    : compM2s[mid]

  const vsMedianPct = Math.round(((pricePerM2 - medianCompM2) / medianCompM2) * 1000) / 10
  const signal: ValuePerM2Conclusion['signal'] =
    vsMedianPct > 10 ? 'haut' : vsMedianPct < -10 ? 'bas' : 'médian'

  return { pricePerM2, medianCompM2, vsMedianPct, signal }
}
