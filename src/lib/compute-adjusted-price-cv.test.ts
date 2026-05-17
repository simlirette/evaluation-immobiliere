import { describe, it, expect } from 'vitest'
import { computeAdjustedPriceCV } from './compute-adjusted-price-cv'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + adj }
}

describe('computeAdjustedPriceCV', () => {
  it('returns null for < 2 adjs', () => {
    expect(computeAdjustedPriceCV([])).toBeNull()
    expect(computeAdjustedPriceCV([mkAdj('a', 300000, 10000)])).toBeNull()
  })

  it('homogenized true when adjustedCV < rawCV', () => {
    // raw: 200k and 400k → high spread; adj brings to 290k and 310k → tight
    const r = computeAdjustedPriceCV([mkAdj('a', 200000, 90000), mkAdj('b', 400000, -90000)])!
    expect(r.homogenized).toBe(true)
    expect(r.adjustedCV).toBeLessThan(r.rawCV)
  })

  it('homogenized false when adjustedCV >= rawCV', () => {
    // adj pushes prices further apart
    const r = computeAdjustedPriceCV([mkAdj('a', 200000, -50000), mkAdj('b', 400000, 50000)])!
    expect(r.homogenized).toBe(false)
  })

  it('delta = adjustedCV - rawCV', () => {
    const r = computeAdjustedPriceCV([mkAdj('a', 200000, 90000), mkAdj('b', 400000, -90000)])!
    expect(r.delta).toBeCloseTo(r.adjustedCV - r.rawCV, 5)
  })

  it('rawCV = 0 when all sale prices identical', () => {
    const r = computeAdjustedPriceCV([mkAdj('a', 300000, 10000), mkAdj('b', 300000, -10000)])!
    expect(r.rawCV).toBe(0)
  })

  it('adjustedCV = 0 when all adjusted prices identical', () => {
    // salePrice 200k adj +100k and 400k adj -100k → both adjusted to 300k
    const r = computeAdjustedPriceCV([mkAdj('a', 200000, 100000), mkAdj('b', 400000, -100000)])!
    expect(r.adjustedCV).toBeCloseTo(0, 5)
  })

  it('rawCV > 0 for different prices', () => {
    const r = computeAdjustedPriceCV([mkAdj('a', 200000, 0), mkAdj('b', 400000, 0)])!
    expect(r.rawCV).toBeGreaterThan(0)
  })
})
