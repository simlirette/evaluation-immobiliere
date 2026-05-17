import { describe, it, expect } from 'vitest'
import { computeAdjustmentDominantTypeByComp } from './compute-adjustment-dominant-type-by-comp'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const total = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + total }
}

describe('computeAdjustmentDominantTypeByComp', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentDominantTypeByComp([])).toBeNull()
  })

  it('dominantType is the type with largest |value|', () => {
    const r = computeAdjustmentDominantTypeByComp([mkAdj('a', 5000, 10000, 2000, 1000)])!
    expect(r.entries[0].dominantType).toBe('year')
  })

  it('dominantType none when all adjustments are zero', () => {
    const r = computeAdjustmentDominantTypeByComp([mkAdj('a', 0, 0, 0, 0)])!
    expect(r.entries[0].dominantType).toBe('none')
  })

  it('negative values compared by absolute value', () => {
    // |-15000| > |5000|
    const r = computeAdjustmentDominantTypeByComp([mkAdj('a', 5000, -15000, 0, 0)])!
    expect(r.entries[0].dominantType).toBe('year')
  })

  it('mostCommonDominantType is the type appearing most across comps', () => {
    const r = computeAdjustmentDominantTypeByComp([
      mkAdj('a', 10000, 1000, 0, 0),
      mkAdj('b', 8000, 2000, 0, 0),
      mkAdj('c', 1000, 9000, 0, 0),
    ])!
    expect(r.mostCommonDominantType).toBe('surface')
  })

  it('one entry per adjustment', () => {
    const r = computeAdjustmentDominantTypeByComp([mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 3000, 0, 0, 0)])!
    expect(r.entries).toHaveLength(2)
  })

  it('dominantValue is absolute value of dominant adj', () => {
    const r = computeAdjustmentDominantTypeByComp([mkAdj('a', -12000, 5000, 0, 0)])!
    expect(r.entries[0].dominantValue).toBe(12000)
  })
})
