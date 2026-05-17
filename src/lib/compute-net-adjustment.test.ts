import { describe, it, expect } from 'vitest'
import { computeNetAdjustment } from './compute-net-adjustment'
import type { Adjustment } from '@/types'

function mkAdj(overrides: Partial<Adjustment>): Adjustment {
  return {
    id: '1', comparable_id: 'c1', comparableLabel: 'Test',
    salePrice: 400000,
    surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0,
    adjusted: 400000,
    ...overrides,
  }
}

describe('computeNetAdjustment', () => {
  it('all zero adjustments → net 0, pct 0', () => {
    const result = computeNetAdjustment(mkAdj({}))
    expect(result.net).toBe(0)
    expect(result.netPct).toBe(0)
    expect(result.absPct).toBe(0)
  })

  it('positive net adjustment', () => {
    const result = computeNetAdjustment(mkAdj({ surface_adj: 20000, year_adj: 10000 }))
    expect(result.net).toBe(30000)
    expect(result.netPct).toBeCloseTo(7.5, 1)
    expect(result.absPct).toBeCloseTo(7.5, 1)
  })

  it('negative net adjustment', () => {
    const result = computeNetAdjustment(mkAdj({ surface_adj: -40000 }))
    expect(result.net).toBe(-40000)
    expect(result.netPct).toBeCloseTo(-10, 1)
    expect(result.absPct).toBeCloseTo(10, 1)
  })

  it('large adjustment > 25%', () => {
    const result = computeNetAdjustment(mkAdj({ surface_adj: -120000, salePrice: 400000 }))
    expect(result.absPct).toBeCloseTo(30, 1)
  })

  it('salePrice 0 → no division error', () => {
    const result = computeNetAdjustment(mkAdj({ salePrice: 0, surface_adj: 5000 }))
    expect(result.netPct).toBe(0)
    expect(result.absPct).toBe(0)
    expect(result.net).toBe(5000)
  })

  it('sums all four adjustment fields', () => {
    const result = computeNetAdjustment(mkAdj({
      surface_adj: 10000, year_adj: -5000, condition_adj: 3000, garage_adj: -2000,
    }))
    expect(result.net).toBe(6000)
  })

  it('absPct is always non-negative', () => {
    const result = computeNetAdjustment(mkAdj({ surface_adj: -80000 }))
    expect(result.absPct).toBeGreaterThanOrEqual(0)
  })
})
