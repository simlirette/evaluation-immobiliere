export interface HoldingCostEstimate {
  /** Monthly mortgage payment (principal + interest) */
  monthlyMortgage: number
  /** Annual property tax estimate (1% of purchase price / 12) */
  monthlyTax: number
  /** Annual insurance estimate (0.5% of purchase price / 12) */
  monthlyInsurance: number
  /** Annual maintenance estimate (1% of purchase price / 12) */
  monthlyMaintenance: number
  /** Sum of all monthly costs */
  monthlyTotal: number
  /** monthlyTotal × holdingMonths */
  totalHoldingCost: number
  /** Loan amount after down payment */
  loanAmount: number
  /** Number of months used for total calculation */
  holdingMonths: number
}

/**
 * Estimates monthly and total holding costs for a property.
 *
 * Uses standard Canadian approximations:
 * - Property tax: 1% of purchase price per year
 * - Insurance: 0.5% per year
 * - Maintenance: 1% per year
 * - Mortgage: standard Canadian semi-annual compounding, converted to monthly
 *
 * Returns null when purchasePrice ≤ 0, downPaymentPct < 0 or > 100,
 * annualRatePct ≤ 0, or amortizationYears ≤ 0.
 */
export function computeHoldingCostEstimate(
  purchasePrice: number,
  downPaymentPct: number,
  annualRatePct: number,
  amortizationYears: number,
  holdingYears = 5,
): HoldingCostEstimate | null {
  if (purchasePrice <= 0 || downPaymentPct < 0 || downPaymentPct > 100 || annualRatePct <= 0 || amortizationYears <= 0) return null

  const loanAmount = purchasePrice * (1 - downPaymentPct / 100)
  const holdingMonths = Math.round(holdingYears * 12)
  const n = amortizationYears * 12

  // Canadian mortgage: semi-annual compounding → monthly equivalent rate
  const semiAnnualRate = annualRatePct / 100 / 2
  const monthlyRate = (1 + semiAnnualRate) ** (1 / 6) - 1
  const monthlyMortgage = loanAmount > 0
    ? Math.round(loanAmount * monthlyRate / (1 - (1 + monthlyRate) ** -n))
    : 0

  const monthlyTax = Math.round(purchasePrice * 0.01 / 12)
  const monthlyInsurance = Math.round(purchasePrice * 0.005 / 12)
  const monthlyMaintenance = Math.round(purchasePrice * 0.01 / 12)
  const monthlyTotal = monthlyMortgage + monthlyTax + monthlyInsurance + monthlyMaintenance
  const totalHoldingCost = monthlyTotal * holdingMonths

  return {
    monthlyMortgage,
    monthlyTax,
    monthlyInsurance,
    monthlyMaintenance,
    monthlyTotal,
    totalHoldingCost,
    loanAmount: Math.round(loanAmount),
    holdingMonths,
  }
}
