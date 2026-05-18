import { describe, it, expect } from 'vitest'
import { computeAdjustmentEfficiencyRatio } from './compute-adjustment-efficiency-ratio'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj = 0, condition_adj = 0, garage_adj = 0): Adjustment {
  const salePrice = 400000
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj, garage_adj, adjusted: salePrice + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentEfficiencyRatio', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentEfficiencyRatio([])).toBeNull()
  })

  it('efficiency = 1 when all adjs same direction', () => {
    // net=30000, gross=30000 → efficiency=1
    const r = computeAdjustmentEfficiencyRatio([mkAdj('a', 10000, 10000, 5000, 5000)])!
    expect(r.entries[0].efficiency).toBeCloseTo(1, 5)
  })

  it('efficiency = 0 when adjs fully cancel (net=0)', () => {
    // surface 10000 + year -10000 → net=0, gross=20000 → efficiency=0
    const r = computeAdjustmentEfficiencyRatio([mkAdj('a', 10000, -10000)])!
    expect(r.entries[0].efficiency).toBeCloseTo(0, 5)
  })

  it('efficiency = 0 when all adjs are zero', () => {
    const r = computeAdjustmentEfficiencyRatio([mkAdj('a', 0)])!
    expect(r.entries[0].efficiency).toBe(0)
  })

  it('efficiency = |net| / gross for partial cancellation', () => {
    // surface 20000 + year -10000 → net=10000, gross=30000 → eff=1/3
    const r = computeAdjustmentEfficiencyRatio([mkAdj('a', 20000, -10000)])!
    expect(r.entries[0].efficiency).toBeCloseTo(1 / 3, 5)
  })

  it('mean = avg of efficiencies', () => {
    // a: eff=1, b: eff=0 → mean=0.5
    const r = computeAdjustmentEfficiencyRatio([
      mkAdj('a', 10000),
      mkAdj('b', 10000, -10000),
    ])!
    expect(r.mean).toBeCloseTo(0.5, 5)
  })

  it('min and max are correct', () => {
    const r = computeAdjustmentEfficiencyRatio([
      mkAdj('a', 10000),          // eff=1
      mkAdj('b', 10000, -10000),  // eff=0
    ])!
    expect(r.min).toBeCloseTo(0, 5)
    expect(r.max).toBeCloseTo(1, 5)
  })
})
