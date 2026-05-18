import { describe, it, expect } from 'vitest'
import { computeAdjustmentNetPerCompSummary } from './compute-adjustment-net-per-comp-summary'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface_adj: number, year_adj = 0, condition_adj = 0, garage_adj = 0): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj, garage_adj, adjusted: salePrice + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentNetPerCompSummary', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentNetPerCompSummary([])).toBeNull()
  })

  it('netAdj = sum of all 4 types', () => {
    const r = computeAdjustmentNetPerCompSummary([mkAdj('a', 400000, 10000, 5000, -3000, -2000)])!
    expect(r.entries[0].netAdj).toBe(10000)
  })

  it('netPct = netAdj / salePrice × 100', () => {
    // 20000/400000 = 5%
    const r = computeAdjustmentNetPerCompSummary([mkAdj('a', 400000, 20000)])!
    expect(r.entries[0].netPct).toBeCloseTo(5, 5)
  })

  it('direction = positive when netAdj > 0', () => {
    const r = computeAdjustmentNetPerCompSummary([mkAdj('a', 400000, 10000)])!
    expect(r.entries[0].direction).toBe('positive')
  })

  it('direction = negative when netAdj < 0', () => {
    const r = computeAdjustmentNetPerCompSummary([mkAdj('a', 400000, -10000)])!
    expect(r.entries[0].direction).toBe('negative')
  })

  it('direction = neutral when netAdj = 0', () => {
    const r = computeAdjustmentNetPerCompSummary([mkAdj('a', 400000, 10000, -10000)])!
    expect(r.entries[0].direction).toBe('neutral')
  })

  it('entries sorted by |netAdj| descending', () => {
    const r = computeAdjustmentNetPerCompSummary([
      mkAdj('a', 400000, 5000),
      mkAdj('b', 400000, -30000),
      mkAdj('c', 400000, 15000),
    ])!
    expect(r.entries[0].id).toBe('b')
    expect(r.entries[1].id).toBe('c')
    expect(r.entries[2].id).toBe('a')
  })
})
