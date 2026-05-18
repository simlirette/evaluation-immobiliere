import { describe, it, expect } from 'vitest'
import { computeAdjustmentSurfaceImpact } from './compute-adjustment-surface-impact'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: 400000 + surface_adj }
}

describe('computeAdjustmentSurfaceImpact', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentSurfaceImpact([])).toBeNull()
  })

  it('counts positive, negative, zero correctly', () => {
    const r = computeAdjustmentSurfaceImpact([mkAdj('a', 15000), mkAdj('b', -8000), mkAdj('c', 0)])!
    expect(r.countPositive).toBe(1)
    expect(r.countNegative).toBe(1)
    expect(r.countZero).toBe(1)
  })

  it('avgWhenApplied is mean of non-zero values', () => {
    // (15000 + -8000) / 2 = 3500
    const r = computeAdjustmentSurfaceImpact([mkAdj('a', 15000), mkAdj('b', -8000), mkAdj('c', 0)])!
    expect(r.avgWhenApplied).toBeCloseTo(3500, 5)
  })

  it('avgWhenApplied null when all zero', () => {
    const r = computeAdjustmentSurfaceImpact([mkAdj('a', 0), mkAdj('b', 0)])!
    expect(r.avgWhenApplied).toBeNull()
  })

  it('dominantDirection positive when most are positive', () => {
    const r = computeAdjustmentSurfaceImpact([mkAdj('a', 15000), mkAdj('b', 10000), mkAdj('c', -5000)])!
    expect(r.dominantDirection).toBe('positive')
  })

  it('dominantDirection negative when most are negative', () => {
    const r = computeAdjustmentSurfaceImpact([mkAdj('a', -15000), mkAdj('b', -10000), mkAdj('c', 5000)])!
    expect(r.dominantDirection).toBe('negative')
  })

  it('dominantDirection neutral when zero most common', () => {
    const r = computeAdjustmentSurfaceImpact([mkAdj('a', 0), mkAdj('b', 0), mkAdj('c', 5000)])!
    expect(r.dominantDirection).toBe('neutral')
  })
})
