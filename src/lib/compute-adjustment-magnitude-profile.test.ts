import { describe, it, expect } from 'vitest'
import { computeAdjustmentMagnitudeProfile } from './compute-adjustment-magnitude-profile'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surfAdj = 0, yearAdj = 0, condAdj = 0, garAdj = 0): Adjustment {
  const sp = 400000
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: sp, surface_adj: surfAdj, year_adj: yearAdj, condition_adj: condAdj, garage_adj: garAdj, adjusted: sp + surfAdj + yearAdj + condAdj + garAdj }
}

describe('computeAdjustmentMagnitudeProfile', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentMagnitudeProfile([])).toBeNull()
  })

  it('nonZeroCount correct for surface type', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', 0), mkAdj('c', 3000)]
    const r = computeAdjustmentMagnitudeProfile(adjs)!
    const surface = r.entries.find(e => e.type === 'surface')!
    expect(surface.nonZeroCount).toBe(2)
    expect(surface.pctOfComps).toBeCloseTo(66.7, 0)
  })

  it('avgAbsolute is mean of non-zero absolute values', () => {
    // surface: |5000| + |3000| / 2 = 4000
    const adjs = [mkAdj('a', 5000), mkAdj('b', 0), mkAdj('c', -3000)]
    const r = computeAdjustmentMagnitudeProfile(adjs)!
    expect(r.entries.find(e => e.type === 'surface')!.avgAbsolute).toBe(4000)
  })

  it('maxAbsolute is largest absolute value', () => {
    const adjs = [mkAdj('a', 1000), mkAdj('b', 8000), mkAdj('c', -3000)]
    const r = computeAdjustmentMagnitudeProfile(adjs)!
    expect(r.entries.find(e => e.type === 'surface')!.maxAbsolute).toBe(8000)
  })

  it('avgAbsolute and maxAbsolute 0 when all zero', () => {
    const adjs = [mkAdj('a', 0), mkAdj('b', 0)]
    const r = computeAdjustmentMagnitudeProfile(adjs)!
    expect(r.entries.find(e => e.type === 'surface')!.avgAbsolute).toBe(0)
    expect(r.entries.find(e => e.type === 'surface')!.maxAbsolute).toBe(0)
  })

  it('dominantType is type with highest avgAbsolute', () => {
    const adjs = [mkAdj('a', 1000, 10000), mkAdj('b', 2000, 9000)]
    // surface avg: 1500, year avg: 9500 → dominant = year
    const r = computeAdjustmentMagnitudeProfile(adjs)!
    expect(r.dominantType).toBe('year')
  })

  it('dominantType null when all adjustments zero', () => {
    const adjs = [mkAdj('a'), mkAdj('b')]
    expect(computeAdjustmentMagnitudeProfile(adjs)!.dominantType).toBeNull()
  })

  it('entries always contain all 4 types', () => {
    const adjs = [mkAdj('a', 5000)]
    expect(computeAdjustmentMagnitudeProfile(adjs)!.entries).toHaveLength(4)
  })
})
