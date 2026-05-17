import { describe, it, expect } from 'vitest'
import { computeAdjustmentNetEffect } from './compute-adjustment-net-effect'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: adjusted - salePrice, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustmentNetEffect', () => {
  it('returns empty array for no adjustments', () => {
    expect(computeAdjustmentNetEffect([])).toEqual([])
  })

  it('computes positive direction when adjusted > salePrice', () => {
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 420000)])
    expect(r.totalAdjustment).toBe(20000)
    expect(r.direction).toBe('positif')
  })

  it('computes negative direction when adjusted < salePrice', () => {
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 380000)])
    expect(r.totalAdjustment).toBe(-20000)
    expect(r.direction).toBe('négatif')
  })

  it('computes neutre when adjusted === salePrice', () => {
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 400000)])
    expect(r.direction).toBe('neutre')
    expect(r.netPct).toBe(0)
  })

  it('netPct rounds to 1 decimal', () => {
    // 20000/400000 = 5.0%
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 420000)])
    expect(r.netPct).toBe(5)
  })

  it('magnitude fort when |netPct| >= 10%', () => {
    // 44000/400000 = 11%
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 444000)])
    expect(r.magnitude).toBe('fort')
  })

  it('magnitude modéré when 5% <= |netPct| < 10%', () => {
    // 20000/400000 = 5%
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 420000)])
    expect(r.magnitude).toBe('modéré')
  })

  it('magnitude faible when |netPct| < 5%', () => {
    // 8000/400000 = 2%
    const [r] = computeAdjustmentNetEffect([mkAdj('a', 400000, 408000)])
    expect(r.magnitude).toBe('faible')
  })

  it('returns one entry per adjustment', () => {
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 390000, 395000)]
    const results = computeAdjustmentNetEffect(adjs)
    expect(results).toHaveLength(2)
    expect(results[0].comparableId).toBe('a')
    expect(results[1].comparableId).toBe('b')
  })

  it('handles zero salePrice gracefully', () => {
    const adj: Adjustment = { id: 'x', comparable_id: 'x', comparableLabel: 'X', salePrice: 0, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 5000 }
    const [r] = computeAdjustmentNetEffect([adj])
    expect(r.netPct).toBe(0)
  })
})
