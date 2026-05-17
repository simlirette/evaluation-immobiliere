export interface ImpliedCapRate {
  /** Annual gross rental income estimate */
  annualGrossIncome: number
  /** Net operating income (gross × (1 - expenseRatio)) */
  annualNetIncome: number
  /** annualNetIncome / propertyValue × 100 */
  capRatePct: number
  /** 'excellent' ≥ 6%, 'bon' ≥ 4%, 'acceptable' ≥ 2%, 'faible' < 2% */
  interpretation: 'excellent' | 'bon' | 'acceptable' | 'faible'
  /** Expense ratio used (default 0.35 = 35%) */
  expenseRatio: number
}

/**
 * Computes the implied capitalization rate for a property given its value
 * and an estimated monthly rental income.
 *
 * Uses a default expense ratio of 35% (operating expenses / gross income),
 * typical for residential rental in Québec.
 *
 * Returns null when propertyValue ≤ 0 or monthlyRent ≤ 0.
 */
export function computeImpliedCapRate(
  propertyValue: number,
  monthlyRent: number,
  expenseRatio = 0.35,
): ImpliedCapRate | null {
  if (propertyValue <= 0 || monthlyRent <= 0) return null

  const annualGrossIncome = Math.round(monthlyRent * 12)
  const annualNetIncome = Math.round(annualGrossIncome * (1 - expenseRatio))
  const capRatePct = Math.round((annualNetIncome / propertyValue) * 10000) / 100

  const interpretation: ImpliedCapRate['interpretation'] =
    capRatePct >= 6 ? 'excellent' : capRatePct >= 4 ? 'bon' : capRatePct >= 2 ? 'acceptable' : 'faible'

  return { annualGrossIncome, annualNetIncome, capRatePct, interpretation, expenseRatio }
}
