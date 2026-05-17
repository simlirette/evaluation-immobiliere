import { describe, it, expect } from 'vitest'
import { computeAdjustmentConsistency } from './compute-adjustment-consistency'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj = 0, year_adj = 0, condition_adj = 0, garage_adj = 0): Adjustment {
  return {
    id, comparable_id: id, comparableLabel: `Comp ${id}`,
    salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj,
    adjusted: 400000 + surface_adj + year_adj + condition_adj + garage_adj,
  }
}

describe('computeAdjustmentConsistency', () => {
  it('returns empty array for fewer than 2 adjustments', () => {
    expect(computeAdjustmentConsistency([])).toEqual([])
    expect(computeAdjustmentConsistency([mkAdj('a')])).toEqual([])
  })

  it('returns 4 checks for 2+ adjustments', () => {
    const result = computeAdjustmentConsistency([mkAdj('a'), mkAdj('b')])
    expect(result).toHaveLength(4)
    expect(result.map(c => c.type)).toEqual(['surface', 'year', 'condition', 'garage'])
  })

  it('consistent when all same direction (all positive)', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', 3000)]
    const surface = computeAdjustmentConsistency(adjs).find(c => c.type === 'surface')!
    expect(surface.consistent).toBe(true)
    expect(surface.warning).toBeNull()
  })

  it('consistent when all same direction (all negative)', () => {
    const adjs = [mkAdj('a', -5000), mkAdj('b', -3000)]
    const surface = computeAdjustmentConsistency(adjs).find(c => c.type === 'surface')!
    expect(surface.consistent).toBe(true)
  })

  it('consistent when all zero', () => {
    const adjs = [mkAdj('a', 0), mkAdj('b', 0)]
    const surface = computeAdjustmentConsistency(adjs).find(c => c.type === 'surface')!
    expect(surface.consistent).toBe(true)
    expect(surface.warning).toBeNull()
  })

  it('inconsistent when mixed directions', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', -3000)]
    const surface = computeAdjustmentConsistency(adjs).find(c => c.type === 'surface')!
    expect(surface.consistent).toBe(false)
    expect(surface.warning).not.toBeNull()
    expect(surface.warning).toContain('surface')
  })

  it('counts positive, negative, zero correctly', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', -3000), mkAdj('c', 0)]
    const surface = computeAdjustmentConsistency(adjs).find(c => c.type === 'surface')!
    expect(surface.positiveCount).toBe(1)
    expect(surface.negativeCount).toBe(1)
    expect(surface.zeroCount).toBe(1)
  })

  it('does not mutate input', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', -3000)]
    const copy = adjs.map(a => ({ ...a }))
    computeAdjustmentConsistency(adjs)
    expect(adjs[0]).toEqual(copy[0])
  })

  it('warning mentions count when inconsistent', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', -3000), mkAdj('c', 4000)]
    const surface = computeAdjustmentConsistency(adjs).find(c => c.type === 'surface')!
    expect(surface.warning).toContain('2↑')
    expect(surface.warning).toContain('1↓')
  })
})
