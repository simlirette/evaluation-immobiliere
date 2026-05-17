import type { Comparable } from '@/types'

export interface ComparableRepresentativeness {
  subjectValue: number
  /** Minimum sale price among comparables */
  compMin: number
  /** Maximum sale price among comparables */
  compMax: number
  /** True when subjectValue is within [compMin, compMax] of raw sale prices */
  withinRange: boolean
  /**
   * When not withinRange: % distance from the nearest fence (positive value).
   * When withinRange: 0.
   */
  deviationPct: number
}

/**
 * Checks whether a subject's estimated value falls within the raw (unadjusted)
 * sale price range of the comparable set.
 *
 * Unlike computeReconciledValueBracket (which uses adjusted prices), this uses
 * unadjusted sale prices — a broader sanity check on market-level representativeness.
 *
 * Returns null when fewer than 2 comparables or subjectValue ≤ 0.
 */
export function computeComparableRepresentativeness(
  comps: Comparable[],
  subjectValue: number,
): ComparableRepresentativeness | null {
  if (comps.length < 2 || subjectValue <= 0) return null

  const prices = comps.map(c => c.sale_price)
  const compMin = Math.min(...prices)
  const compMax = Math.max(...prices)
  const withinRange = subjectValue >= compMin && subjectValue <= compMax

  let deviationPct = 0
  if (!withinRange) {
    if (subjectValue < compMin) {
      deviationPct = Math.round(((compMin - subjectValue) / compMin) * 1000) / 10
    } else {
      deviationPct = Math.round(((subjectValue - compMax) / compMax) * 1000) / 10
    }
  }

  return { subjectValue, compMin, compMax, withinRange, deviationPct }
}
