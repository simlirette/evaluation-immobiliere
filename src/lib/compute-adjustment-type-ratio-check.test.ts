import { describe, it, expect } from 'vitest'
import { computeAdjustmentTypeRatioCheck } from './compute-adjustment-type-ratio-check'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentTypeRatioCheck', () => {
  it('returns null for empty adjustments', () => {
    expect(computeAdjustmentTypeRatioCheck([])).toBeNull()
  })

  it('returns null when all adjustments are zero', () => {
    expect(computeAdjustmentTypeRatioCheck([mkAdj('a', 0, 0, 0, 0)])).toBeNull()
  })

  it('entries sum pctOfGross to 100', () => {
    const adjs = [mkAdj('a', 10000, 5000, 2000, 3000)]
    const r = computeAdjustmentTypeRatioCheck(adjs)!
    const total = r.entries.reduce((s, e) => s + e.pctOfGross, 0)
    expect(Math.round(total)).toBe(100)
  })

  it('overReliance true when one type > 50%', () => {
    const adjs = [mkAdj('a', 30000, 1000, 500, 500)]
    const r = computeAdjustmentTypeRatioCheck(adjs)!
    expect(r.hasOverReliance).toBe(true)
    expect(r.entries.find(e => e.type === 'surface')!.overReliance).toBe(true)
  })

  it('overReliance false when balanced', () => {
    const adjs = [mkAdj('a', 5000, 5000, 5000, 5000)]
    const r = computeAdjustmentTypeRatioCheck(adjs)!
    expect(r.hasOverReliance).toBe(false)
    r.entries.forEach(e => expect(e.overReliance).toBe(false))
  })

  it('dominantType is the type with highest pctOfGross', () => {
    const adjs = [mkAdj('a', 1000, 8000, 500, 500)]
    const r = computeAdjustmentTypeRatioCheck(adjs)!
    expect(r.dominantType).toBe('year')
  })

  it('returns 4 entries always', () => {
    const adjs = [mkAdj('a', 5000, 0, 0, 0)]
    expect(computeAdjustmentTypeRatioCheck(adjs)!.entries).toHaveLength(4)
  })
})
