import { describe, it, expect } from 'vitest'
import { computeAdjustmentProfile } from './compute-adjustment-profile'
import type { Adjustment } from '@/types'

function mkAdj(overrides: Partial<Adjustment> = {}): Adjustment {
  return {
    id: 'a1', comparable_id: 'c1', comparableLabel: 'Comp', salePrice: 400000,
    surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 400000,
    ...overrides,
  }
}

describe('computeAdjustmentProfile', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentProfile([])).toBeNull()
  })

  it('all types present in output', () => {
    const result = computeAdjustmentProfile([mkAdj()])!
    const types = result.types.map(t => t.type)
    expect(types).toContain('surface')
    expect(types).toContain('year')
    expect(types).toContain('condition')
    expect(types).toContain('garage')
  })

  it('dominantType is null when all adjustments are zero', () => {
    expect(computeAdjustmentProfile([mkAdj()])!.dominantType).toBeNull()
  })

  it('identifies dominant type correctly', () => {
    const adjs = [mkAdj({ surface_adj: 10000, year_adj: 2000 })]
    const result = computeAdjustmentProfile(adjs)!
    expect(result.dominantType).toBe('surface')
  })

  it('computes pctOfGrossTotal summing to 100', () => {
    const adjs = [mkAdj({ surface_adj: 10000, year_adj: -5000, condition_adj: 5000, garage_adj: -10000 })]
    const result = computeAdjustmentProfile(adjs)!
    const total = result.types.reduce((s, t) => s + t.pctOfGrossTotal, 0)
    expect(total).toBeCloseTo(100, 0)
  })

  it('direction is positive when net > 0', () => {
    const result = computeAdjustmentProfile([mkAdj({ surface_adj: 5000 })])!
    expect(result.types.find(t => t.type === 'surface')!.direction).toBe('positive')
  })

  it('direction is negative when net < 0', () => {
    const result = computeAdjustmentProfile([mkAdj({ condition_adj: -3000 })])!
    expect(result.types.find(t => t.type === 'condition')!.direction).toBe('negative')
  })

  it('direction is neutral when net = 0', () => {
    const adjs = [mkAdj({ year_adj: 5000 }), mkAdj({ year_adj: -5000 })]
    const result = computeAdjustmentProfile(adjs)!
    expect(result.types.find(t => t.type === 'year')!.direction).toBe('neutral')
  })

  it('avgPerComp is rounded net / count', () => {
    const adjs = [mkAdj({ surface_adj: 3000 }), mkAdj({ surface_adj: 4000 })]
    const surface = computeAdjustmentProfile(adjs)!.types.find(t => t.type === 'surface')!
    expect(surface.avgPerComp).toBe(3500)
  })

  it('does not mutate input', () => {
    const adj = mkAdj({ surface_adj: 5000 })
    const copy = { ...adj }
    computeAdjustmentProfile([adj])
    expect(adj).toEqual(copy)
  })
})
