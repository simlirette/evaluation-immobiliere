import { describe, it, expect } from 'vitest'
import { computeHoldingCostEstimate } from './compute-holding-cost-estimate'

describe('computeHoldingCostEstimate', () => {
  it('returns null for invalid inputs', () => {
    expect(computeHoldingCostEstimate(0, 20, 5, 25)).toBeNull()
    expect(computeHoldingCostEstimate(400000, -1, 5, 25)).toBeNull()
    expect(computeHoldingCostEstimate(400000, 101, 5, 25)).toBeNull()
    expect(computeHoldingCostEstimate(400000, 20, 0, 25)).toBeNull()
    expect(computeHoldingCostEstimate(400000, 20, 5, 0)).toBeNull()
  })

  it('computes loanAmount correctly', () => {
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.loanAmount).toBe(320000)
  })

  it('monthlyMortgage is positive for valid loan', () => {
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.monthlyMortgage).toBeGreaterThan(0)
  })

  it('monthlyMortgage is 0 when 100% down', () => {
    const r = computeHoldingCostEstimate(400000, 100, 5, 25)!
    expect(r.monthlyMortgage).toBe(0)
    expect(r.loanAmount).toBe(0)
  })

  it('monthlyTax is ~1%/yr of purchasePrice', () => {
    // 400000 * 0.01 / 12 = 333
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.monthlyTax).toBe(333)
  })

  it('monthlyInsurance is ~0.5%/yr of purchasePrice', () => {
    // 400000 * 0.005 / 12 = 167
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.monthlyInsurance).toBe(167)
  })

  it('monthlyMaintenance is ~1%/yr of purchasePrice', () => {
    // 400000 * 0.01 / 12 = 333
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.monthlyMaintenance).toBe(333)
  })

  it('monthlyTotal = sum of all monthly components', () => {
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.monthlyTotal).toBe(r.monthlyMortgage + r.monthlyTax + r.monthlyInsurance + r.monthlyMaintenance)
  })

  it('totalHoldingCost = monthlyTotal × holdingMonths', () => {
    const r = computeHoldingCostEstimate(400000, 20, 5, 25, 3)!
    expect(r.totalHoldingCost).toBe(r.monthlyTotal * r.holdingMonths)
    expect(r.holdingMonths).toBe(36)
  })

  it('default holdingYears is 5 (60 months)', () => {
    const r = computeHoldingCostEstimate(400000, 20, 5, 25)!
    expect(r.holdingMonths).toBe(60)
  })

  it('higher rate → higher monthly mortgage', () => {
    const low = computeHoldingCostEstimate(400000, 20, 3, 25)!
    const high = computeHoldingCostEstimate(400000, 20, 7, 25)!
    expect(high.monthlyMortgage).toBeGreaterThan(low.monthlyMortgage)
  })
})
