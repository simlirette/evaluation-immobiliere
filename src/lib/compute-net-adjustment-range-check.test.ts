import { describe, it, expect } from 'vitest'
import { computeNetAdjustmentRangeCheck } from './compute-net-adjustment-range-check'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number = 0, condition_adj: number = 0, garage_adj: number = 0): Adjustment {
  const totalAdj = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + totalAdj }
}

describe('computeNetAdjustmentRangeCheck', () => {
  it('returns null for empty array', () => {
    expect(computeNetAdjustmentRangeCheck([])).toBeNull()
  })

  it('no violation when |net adj| < 15% of salePrice', () => {
    // netAdj = 50000; 50000/400000 = 12.5% < 15
    const r = computeNetAdjustmentRangeCheck([mkAdj('a', 50000)])!
    expect(r.entries[0].violation).toBe(false)
    expect(r.violationCount).toBe(0)
    expect(r.compliant).toBe(true)
  })

  it('violation when |net adj| > 15% of salePrice', () => {
    // netAdj = 80000; 80000/400000 = 20% > 15
    const r = computeNetAdjustmentRangeCheck([mkAdj('a', 80000)])!
    expect(r.entries[0].violation).toBe(true)
    expect(r.violationCount).toBe(1)
    expect(r.compliant).toBe(false)
  })

  it('negative net adj also checked by absolute value', () => {
    // netAdj = -80000; |80000|/400000 = 20% → violation
    const r = computeNetAdjustmentRangeCheck([mkAdj('a', -80000)])!
    expect(r.entries[0].violation).toBe(true)
  })

  it('netAdjPct computed correctly', () => {
    // net = 60000; pct = 15% exactly → no violation (> not >=)
    const r = computeNetAdjustmentRangeCheck([mkAdj('a', 60000)])!
    expect(r.entries[0].netAdjPct).toBeCloseTo(15, 5)
    expect(r.entries[0].violation).toBe(false)
  })

  it('violationCount counts only violating comps', () => {
    const r = computeNetAdjustmentRangeCheck([mkAdj('a', 20000), mkAdj('b', 80000), mkAdj('c', 40000)])!
    expect(r.violationCount).toBe(1)
  })

  it('one entry per adjustment', () => {
    const r = computeNetAdjustmentRangeCheck([mkAdj('a', 10000), mkAdj('b', 20000)])!
    expect(r.entries).toHaveLength(2)
  })
})
