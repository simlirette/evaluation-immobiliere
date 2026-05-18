import { describe, it, expect } from 'vitest'
import { computeAdjustedPriceRangeNarrowing } from './compute-adjusted-price-range-narrowing'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + adj }
}

describe('computeAdjustedPriceRangeNarrowing', () => {
  it('returns null for < 2 adjs', () => {
    expect(computeAdjustedPriceRangeNarrowing([])).toBeNull()
    expect(computeAdjustedPriceRangeNarrowing([mkAdj('a', 300000, 0)])).toBeNull()
  })

  it('returns null when rawRange = 0', () => {
    expect(computeAdjustedPriceRangeNarrowing([mkAdj('a', 300000, 10000), mkAdj('b', 300000, -10000)])).toBeNull()
  })

  it('rawRange = max(salePrice) - min(salePrice)', () => {
    const r = computeAdjustedPriceRangeNarrowing([mkAdj('a', 200000, 0), mkAdj('b', 400000, 0)])!
    expect(r.rawRange).toBe(200000)
  })

  it('adjustedRange = max(adjusted) - min(adjusted)', () => {
    // adj: 200000+100000=300000 and 400000-100000=300000 → adjustedRange = 0
    const r = computeAdjustedPriceRangeNarrowing([mkAdj('a', 200000, 100000), mkAdj('b', 400000, -100000)])!
    expect(r.adjustedRange).toBe(0)
  })

  it('narrowed true when adjustedRange < rawRange', () => {
    const r = computeAdjustedPriceRangeNarrowing([mkAdj('a', 200000, 100000), mkAdj('b', 400000, -100000)])!
    expect(r.narrowed).toBe(true)
  })

  it('narrowed false when adjustedRange >= rawRange', () => {
    // adj spreads prices further: 200k-50k=150k and 400k+50k=450k → range widens
    const r = computeAdjustedPriceRangeNarrowing([mkAdj('a', 200000, -50000), mkAdj('b', 400000, 50000)])!
    expect(r.narrowed).toBe(false)
  })

  it('narrowingPct = (rawRange - adjustedRange) / rawRange × 100', () => {
    // raw: 200k range; adj: 0 range → 100%
    const r = computeAdjustedPriceRangeNarrowing([mkAdj('a', 200000, 100000), mkAdj('b', 400000, -100000)])!
    expect(r.narrowingPct).toBeCloseTo(100, 5)
  })
})
