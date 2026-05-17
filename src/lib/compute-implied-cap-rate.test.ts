import { describe, it, expect } from 'vitest'
import { computeImpliedCapRate } from './compute-implied-cap-rate'

describe('computeImpliedCapRate', () => {
  it('returns null for invalid inputs', () => {
    expect(computeImpliedCapRate(0, 2000)).toBeNull()
    expect(computeImpliedCapRate(400000, 0)).toBeNull()
    expect(computeImpliedCapRate(-1, 2000)).toBeNull()
  })

  it('computes annualGrossIncome as monthlyRent × 12', () => {
    const r = computeImpliedCapRate(400000, 2000)!
    expect(r.annualGrossIncome).toBe(24000)
  })

  it('computes annualNetIncome using default expense ratio 0.35', () => {
    // 24000 × (1 - 0.35) = 15600
    const r = computeImpliedCapRate(400000, 2000)!
    expect(r.annualNetIncome).toBe(15600)
  })

  it('computes capRatePct = annualNetIncome / propertyValue × 100', () => {
    // 15600 / 400000 × 100 = 3.9%
    const r = computeImpliedCapRate(400000, 2000)!
    expect(r.capRatePct).toBe(3.9)
  })

  it('interpretation excellent when capRate >= 6%', () => {
    // Need: 6% of 400k = 24000 net → gross = 24000/0.65 = 36923 → monthly ≈ 3077
    const r = computeImpliedCapRate(400000, 3200)!
    expect(r.capRatePct).toBeGreaterThanOrEqual(6)
    expect(r.interpretation).toBe('excellent')
  })

  it('interpretation bon when 4% <= capRate < 6%', () => {
    // capRate ≈ 3.9% → acceptable? need to hit 4%. monthly=2600 → net=2600*12*0.65=20280, 20280/400k=5.07% → bon
    const r = computeImpliedCapRate(400000, 2600)!
    expect(r.capRatePct).toBeGreaterThanOrEqual(4)
    expect(r.interpretation).toBe('bon')
  })

  it('interpretation acceptable when 2% <= capRate < 4%', () => {
    const r = computeImpliedCapRate(400000, 2000)!
    expect(r.interpretation).toBe('acceptable')
  })

  it('interpretation faible when capRate < 2%', () => {
    // 800/month → 9600/yr gross → 6240 net → 6240/400000 = 1.56%
    const r = computeImpliedCapRate(400000, 800)!
    expect(r.interpretation).toBe('faible')
  })

  it('custom expense ratio is respected', () => {
    // No expenses: gross=net=24000, cap=6%
    const r = computeImpliedCapRate(400000, 2000, 0)!
    expect(r.annualNetIncome).toBe(24000)
    expect(r.expenseRatio).toBe(0)
  })
})
