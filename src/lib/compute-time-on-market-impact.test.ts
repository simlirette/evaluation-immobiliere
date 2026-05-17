import { describe, it, expect } from 'vitest'
import { computeTimeOnMarketImpact } from './compute-time-on-market-impact'

describe('computeTimeOnMarketImpact', () => {
  it('returns null for negative daysOnMarket', () => {
    expect(computeTimeOnMarketImpact(-1)).toBeNull()
  })

  it('category rapide for 0-30 days', () => {
    expect(computeTimeOnMarketImpact(0)!.category).toBe('rapide')
    expect(computeTimeOnMarketImpact(30)!.category).toBe('rapide')
  })

  it('category normal for 31-90 days', () => {
    expect(computeTimeOnMarketImpact(31)!.category).toBe('normal')
    expect(computeTimeOnMarketImpact(90)!.category).toBe('normal')
  })

  it('category prolongé for 91-180 days', () => {
    expect(computeTimeOnMarketImpact(91)!.category).toBe('prolongé')
    expect(computeTimeOnMarketImpact(180)!.category).toBe('prolongé')
  })

  it('category très prolongé for > 180 days', () => {
    expect(computeTimeOnMarketImpact(181)!.category).toBe('très prolongé')
  })

  it('estimatedDiscountPct is 0 for rapide', () => {
    expect(computeTimeOnMarketImpact(15)!.estimatedDiscountPct).toBe(0)
  })

  it('estimatedDiscountPct is -1 for normal', () => {
    expect(computeTimeOnMarketImpact(60)!.estimatedDiscountPct).toBe(-1)
  })

  it('estimatedDiscountPct is -3 for prolongé', () => {
    expect(computeTimeOnMarketImpact(120)!.estimatedDiscountPct).toBe(-3)
  })

  it('estimatedDiscountPct is -5 for très prolongé', () => {
    expect(computeTimeOnMarketImpact(200)!.estimatedDiscountPct).toBe(-5)
  })

  it('estimatedDiscountAmount is null when no propertyValue', () => {
    expect(computeTimeOnMarketImpact(120)!.estimatedDiscountAmount).toBeNull()
  })

  it('estimatedDiscountAmount computed when propertyValue provided', () => {
    // 120 days → -3% of 400000 = -12000
    const r = computeTimeOnMarketImpact(120, 400000)!
    expect(r.estimatedDiscountAmount).toBe(-12000)
  })

  it('estimatedDiscountAmount is 0 for rapide category', () => {
    expect(computeTimeOnMarketImpact(10, 400000)!.estimatedDiscountAmount).toBe(0)
  })
})
