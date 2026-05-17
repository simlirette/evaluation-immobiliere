import { describe, it, expect } from 'vitest'
import { computeTimeAdjustedSalePrice } from './compute-time-adjusted-sale-price'

const REF = new Date('2025-01-01')

describe('computeTimeAdjustedSalePrice', () => {
  it('returns null for empty saleDate', () => {
    expect(computeTimeAdjustedSalePrice('', 400000, 0.5, REF)).toBeNull()
  })

  it('returns null for salePrice <= 0', () => {
    expect(computeTimeAdjustedSalePrice('2024-01-01', 0, 0.5, REF)).toBeNull()
    expect(computeTimeAdjustedSalePrice('2024-01-01', -1, 0.5, REF)).toBeNull()
  })

  it('returns null when refDate is before saleDate (monthsElapsed <= 0)', () => {
    // sale in the future relative to refDate
    expect(computeTimeAdjustedSalePrice('2025-06-01', 400000, 0.5, REF)).toBeNull()
  })

  it('zero rate → adjustedPrice equals salePrice, adjustmentPct = 0', () => {
    const result = computeTimeAdjustedSalePrice('2024-01-01', 400000, 0, REF)!
    expect(result.adjustedPrice).toBe(400000)
    expect(result.adjustmentPct).toBe(0)
  })

  it('positive rate → price increases toward refDate', () => {
    // 12 months at 1%/month → +12% → 448000
    const result = computeTimeAdjustedSalePrice('2024-01-01', 400000, 1, REF)!
    expect(result.adjustedPrice).toBeGreaterThan(400000)
    expect(result.adjustmentPct).toBeGreaterThan(0)
    expect(result.monthsElapsed).toBeCloseTo(12, 0)
  })

  it('negative rate → price decreases toward refDate', () => {
    const result = computeTimeAdjustedSalePrice('2024-01-01', 400000, -1, REF)!
    expect(result.adjustedPrice).toBeLessThan(400000)
    expect(result.adjustmentPct).toBeLessThan(0)
  })

  it('12 months at 0.25%/month → +3% annually → ~412000', () => {
    const result = computeTimeAdjustedSalePrice('2024-01-01', 400000, 0.25, REF)!
    // 400000 * (1 + 0.0025 * 12) = 400000 * 1.03 = 412000
    expect(result.adjustedPrice).toBe(412000)
    expect(result.adjustmentPct).toBe(3)
  })

  it('adjustedPrice is a rounded integer', () => {
    const result = computeTimeAdjustedSalePrice('2024-01-01', 123456, 0.333, REF)!
    expect(Number.isInteger(result.adjustedPrice)).toBe(true)
  })

  it('does not use default refDate = today (accepts explicit refDate)', () => {
    const ref1 = new Date('2025-01-01')
    const ref2 = new Date('2026-01-01')
    const r1 = computeTimeAdjustedSalePrice('2024-01-01', 400000, 0.5, ref1)!
    const r2 = computeTimeAdjustedSalePrice('2024-01-01', 400000, 0.5, ref2)!
    expect(r2.adjustedPrice).toBeGreaterThan(r1.adjustedPrice)
    expect(r2.monthsElapsed).toBeGreaterThan(r1.monthsElapsed)
  })
})
