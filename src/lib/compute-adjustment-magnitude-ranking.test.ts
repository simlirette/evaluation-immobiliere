import { describe, it, expect } from 'vitest'
import { computeAdjustmentMagnitudeRanking } from './compute-adjustment-magnitude-ranking'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const salePrice = 400000
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj, garage_adj, adjusted: salePrice + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentMagnitudeRanking', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentMagnitudeRanking([])).toBeNull()
  })

  it('returns 4 entries', () => {
    const r = computeAdjustmentMagnitudeRanking([mkAdj('a', 10000, 5000, 3000, 1000)])!
    expect(r.entries).toHaveLength(4)
  })

  it('ranks by totalAbsolute descending', () => {
    // surface=10k, year=5k, condition=3k, garage=1k
    const r = computeAdjustmentMagnitudeRanking([mkAdj('a', 10000, 5000, 3000, 1000)])!
    expect(r.entries[0].type).toBe('surface')
    expect(r.entries[1].type).toBe('year')
    expect(r.entries[2].type).toBe('condition')
    expect(r.entries[3].type).toBe('garage')
  })

  it('rank field is 1-based', () => {
    const r = computeAdjustmentMagnitudeRanking([mkAdj('a', 10000, 5000, 3000, 1000)])!
    expect(r.entries.map(e => e.rank)).toEqual([1, 2, 3, 4])
  })

  it('totalAbsolute sums |adj| across all comps', () => {
    // two comps: surface 10000+(-8000)=18000 total abs
    const r = computeAdjustmentMagnitudeRanking([
      mkAdj('a', 10000, 0, 0, 0),
      mkAdj('b', -8000, 0, 0, 0),
    ])!
    const surfaceEntry = r.entries.find(e => e.type === 'surface')!
    expect(surfaceEntry.totalAbsolute).toBe(18000)
  })

  it('avgAbsolute = totalAbsolute / count', () => {
    const r = computeAdjustmentMagnitudeRanking([
      mkAdj('a', 10000, 0, 0, 0),
      mkAdj('b', -8000, 0, 0, 0),
    ])!
    const surfaceEntry = r.entries.find(e => e.type === 'surface')!
    expect(surfaceEntry.avgAbsolute).toBe(9000)
  })

  it('handles all-zero adjs', () => {
    const r = computeAdjustmentMagnitudeRanking([mkAdj('a', 0, 0, 0, 0)])!
    expect(r.entries.every(e => e.totalAbsolute === 0)).toBe(true)
    expect(r.entries[0].rank).toBe(1)
  })
})
