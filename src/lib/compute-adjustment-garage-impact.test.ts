import { describe, it, expect } from 'vitest'
import { computeAdjustmentGarageImpact } from './compute-adjustment-garage-impact'
import type { Adjustment } from '@/types'

function mkAdj(id: string, garage_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj, adjusted: 400000 + garage_adj }
}

describe('computeAdjustmentGarageImpact', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentGarageImpact([])).toBeNull()
  })

  it('counts positive, negative, zero correctly', () => {
    const r = computeAdjustmentGarageImpact([mkAdj('a', 5000), mkAdj('b', -3000), mkAdj('c', 0)])!
    expect(r.countPositive).toBe(1)
    expect(r.countNegative).toBe(1)
    expect(r.countZero).toBe(1)
  })

  it('avgWhenApplied is mean of non-zero values', () => {
    const r = computeAdjustmentGarageImpact([mkAdj('a', 5000), mkAdj('b', -3000), mkAdj('c', 0)])!
    expect(r.avgWhenApplied).toBeCloseTo(1000, 5)
  })

  it('avgWhenApplied null when all zero', () => {
    const r = computeAdjustmentGarageImpact([mkAdj('a', 0), mkAdj('b', 0)])!
    expect(r.avgWhenApplied).toBeNull()
  })

  it('dominantDirection positive when most are positive', () => {
    const r = computeAdjustmentGarageImpact([mkAdj('a', 5000), mkAdj('b', 4000), mkAdj('c', -1000)])!
    expect(r.dominantDirection).toBe('positive')
  })

  it('dominantDirection negative when most are negative', () => {
    const r = computeAdjustmentGarageImpact([mkAdj('a', -5000), mkAdj('b', -4000), mkAdj('c', 1000)])!
    expect(r.dominantDirection).toBe('negative')
  })

  it('dominantDirection neutral when zero is most common', () => {
    const r = computeAdjustmentGarageImpact([mkAdj('a', 0), mkAdj('b', 0), mkAdj('c', 5000)])!
    expect(r.dominantDirection).toBe('neutral')
  })
})
