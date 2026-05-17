import { describe, it, expect } from 'vitest'
import { computeNetAdjustmentDistribution } from './compute-net-adjustment-distribution'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeNetAdjustmentDistribution', () => {
  it('returns null for fewer than 2 adjustments', () => {
    expect(computeNetAdjustmentDistribution([mkAdj('a', 400000, 410000)])).toBeNull()
  })

  it('mean = mean of (adjusted − salePrice)', () => {
    // nets: +10000, +20000 → mean 15000
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 400000, 420000)]
    expect(computeNetAdjustmentDistribution(adjs)!.mean).toBe(15000)
  })

  it('min and max are the extremes', () => {
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 400000, 430000), mkAdj('c', 400000, 390000)]
    const r = computeNetAdjustmentDistribution(adjs)!
    expect(r.min).toBe(-10000)
    expect(r.max).toBe(30000)
  })

  it('range = max − min', () => {
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 400000, 430000), mkAdj('c', 400000, 390000)]
    const r = computeNetAdjustmentDistribution(adjs)!
    expect(r.range).toBe(r.max - r.min)
  })

  it('stdDev is 0 when all net adjustments equal', () => {
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 400000, 410000), mkAdj('c', 400000, 410000)]
    expect(computeNetAdjustmentDistribution(adjs)!.stdDev).toBe(0)
  })

  it('mean is negative when adjustments predominantly downward', () => {
    const adjs = [mkAdj('a', 400000, 380000), mkAdj('b', 400000, 370000), mkAdj('c', 400000, 390000)]
    expect(computeNetAdjustmentDistribution(adjs)!.mean).toBeLessThan(0)
  })

  it('cv is non-negative', () => {
    const adjs = [mkAdj('a', 400000, 415000), mkAdj('b', 400000, 420000), mkAdj('c', 400000, 410000)]
    expect(computeNetAdjustmentDistribution(adjs)!.cv).toBeGreaterThanOrEqual(0)
  })
})
