import { describe, it, expect } from 'vitest'
import { computeGrossAdjustmentDistribution } from './compute-gross-adjustment-distribution'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number = 0): Adjustment {
  const salePrice = 400000
  const totalAdj = surface_adj + year_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj: 0, garage_adj: 0, adjusted: salePrice + totalAdj }
}

describe('computeGrossAdjustmentDistribution', () => {
  it('returns null for < 2 adjs', () => {
    expect(computeGrossAdjustmentDistribution([])).toBeNull()
    expect(computeGrossAdjustmentDistribution([mkAdj('a', 10000)])).toBeNull()
  })

  it('grossPct = (sum of |adj types|) / salePrice × 100', () => {
    // |20000| + |0| = 20000; 20000/400000 = 5%
    const r = computeGrossAdjustmentDistribution([mkAdj('a', 20000), mkAdj('b', 40000)])!
    expect(r.min).toBeCloseTo(5, 5)
    expect(r.max).toBeCloseTo(10, 5)
  })

  it('mean correct', () => {
    // 5% and 10% → mean 7.5%
    const r = computeGrossAdjustmentDistribution([mkAdj('a', 20000), mkAdj('b', 40000)])!
    expect(r.mean).toBeCloseTo(7.5, 5)
  })

  it('median for even count is avg of two middle', () => {
    // [5, 7.5, 10, 15] → median = (7.5+10)/2 = 8.75
    const r = computeGrossAdjustmentDistribution([mkAdj('a', 20000), mkAdj('b', 30000), mkAdj('c', 40000), mkAdj('d', 60000)])!
    expect(r.median).toBeCloseTo(8.75, 5)
  })

  it('stdDev > 0 when grossPcts differ', () => {
    const r = computeGrossAdjustmentDistribution([mkAdj('a', 20000), mkAdj('b', 40000)])!
    expect(r.stdDev).toBeGreaterThan(0)
  })

  it('cv = stdDev/mean × 100', () => {
    const r = computeGrossAdjustmentDistribution([mkAdj('a', 20000), mkAdj('b', 40000)])!
    expect(r.cv).toBeCloseTo((r.stdDev / r.mean) * 100, 5)
  })

  it('negative adjustments count by absolute value', () => {
    // |-20000| = 20000 → same grossPct as +20000
    const r = computeGrossAdjustmentDistribution([mkAdj('a', -20000), mkAdj('b', 20000)])!
    expect(r.min).toBeCloseTo(5, 5)
    expect(r.max).toBeCloseTo(5, 5)
  })
})
