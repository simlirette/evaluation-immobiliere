import { describe, it, expect } from 'vitest'
import { computeAdjustmentSummaryByComp } from './compute-adjustment-summary-by-comp'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj, garage_adj, adjusted: salePrice + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentSummaryByComp', () => {
  it('returns empty array for empty input', () => {
    expect(computeAdjustmentSummaryByComp([])).toEqual([])
  })

  it('returns one entry per adjustment', () => {
    const adjs = [mkAdj('a', 400000, 5000, 0, 0, 0), mkAdj('b', 500000, -3000, 2000, 0, 0)]
    expect(computeAdjustmentSummaryByComp(adjs)).toHaveLength(2)
  })

  it('direction upward when netAmount > 0', () => {
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 10000, 0, 0, 0)])[0]
    expect(r.direction).toBe('upward')
    expect(r.netAmount).toBe(10000)
  })

  it('direction downward when netAmount < 0', () => {
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, -10000, 0, 0, 0)])[0]
    expect(r.direction).toBe('downward')
  })

  it('direction neutral when netAmount = 0', () => {
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 10000, -10000, 0, 0)])[0]
    expect(r.direction).toBe('neutral')
  })

  it('grossPct uses absolute values', () => {
    // |10000| + |5000| = 15000; 15000/400000 = 3.75%
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 10000, -5000, 0, 0)])[0]
    expect(r.grossPct).toBe(3.8)
  })

  it('netPct is signed', () => {
    // net = 10000 - 5000 = 5000; 5000/400000 = 1.25%
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 10000, -5000, 0, 0)])[0]
    expect(r.netPct).toBe(1.3)
  })

  it('magnitude fort when |netPct| >= 10', () => {
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 50000, 0, 0, 0)])[0]
    expect(r.magnitude).toBe('fort')
  })

  it('magnitude modéré when |netPct| >= 5', () => {
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 25000, 0, 0, 0)])[0]
    expect(r.magnitude).toBe('modéré')
  })

  it('magnitude faible when |netPct| < 5', () => {
    const r = computeAdjustmentSummaryByComp([mkAdj('a', 400000, 5000, 0, 0, 0)])[0]
    expect(r.magnitude).toBe('faible')
  })
})
