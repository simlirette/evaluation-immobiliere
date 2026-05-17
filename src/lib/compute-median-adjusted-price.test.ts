import { describe, it, expect } from 'vitest'
import { computeMedianAdjustedPrice } from './compute-median-adjusted-price'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + adj }
}

describe('computeMedianAdjustedPrice', () => {
  it('returns null for < 2 adjs', () => {
    expect(computeMedianAdjustedPrice([], 300000)).toBeNull()
    expect(computeMedianAdjustedPrice([mkAdj('a', 300000, 0)], 300000)).toBeNull()
  })

  it('returns null when reconciledValue <= 0', () => {
    expect(computeMedianAdjustedPrice([mkAdj('a', 300000, 0), mkAdj('b', 310000, 0)], 0)).toBeNull()
  })

  it('median of two: average of both', () => {
    // adjusted: 290000 and 310000 → median = 300000
    const r = computeMedianAdjustedPrice([mkAdj('a', 300000, -10000), mkAdj('b', 300000, 10000)], 300000)!
    expect(r.median).toBe(300000)
  })

  it('median of three: middle value', () => {
    // adjusted: 280000, 300000, 320000 → median = 300000
    const r = computeMedianAdjustedPrice([
      mkAdj('a', 300000, -20000), mkAdj('b', 300000, 0), mkAdj('c', 300000, 20000),
    ], 300000)!
    expect(r.median).toBe(300000)
  })

  it('delta = reconciledValue - median', () => {
    const r = computeMedianAdjustedPrice([mkAdj('a', 300000, 0), mkAdj('b', 320000, 0)], 315000)!
    expect(r.delta).toBeCloseTo(r.reconciledValue - r.median, 5)
  })

  it('deltaPct = delta / median × 100', () => {
    const r = computeMedianAdjustedPrice([mkAdj('a', 300000, 0), mkAdj('b', 300000, 0)], 315000)!
    expect(r.deltaPct).toBeCloseTo((15000 / 300000) * 100, 5)
  })

  it('delta = 0 when reconciledValue equals median', () => {
    const r = computeMedianAdjustedPrice([mkAdj('a', 300000, 0), mkAdj('b', 300000, 0)], 300000)!
    expect(r.delta).toBe(0)
    expect(r.deltaPct).toBe(0)
  })
})
