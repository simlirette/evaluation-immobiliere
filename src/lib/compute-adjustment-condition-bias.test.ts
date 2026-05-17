import { describe, it, expect } from 'vitest'
import { computeAdjustmentConditionBias } from './compute-adjustment-condition-bias'
import type { Adjustment } from '@/types'

function mkAdj(id: string, condition_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: 0, year_adj: 0, condition_adj, garage_adj: 0, adjusted: 400000 + condition_adj }
}

describe('computeAdjustmentConditionBias', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentConditionBias([])).toBeNull()
  })

  it('counts positive, negative, zero correctly', () => {
    const r = computeAdjustmentConditionBias([
      mkAdj('a', 10000), mkAdj('b', -5000), mkAdj('c', 0),
    ])!
    expect(r.countPositive).toBe(1)
    expect(r.countNegative).toBe(1)
    expect(r.countZero).toBe(1)
  })

  it('avgWhenApplied is mean of non-zero condition_adj values', () => {
    // (10000 + -5000) / 2 = 2500
    const r = computeAdjustmentConditionBias([mkAdj('a', 10000), mkAdj('b', -5000), mkAdj('c', 0)])!
    expect(r.avgWhenApplied).toBeCloseTo(2500, 5)
  })

  it('avgWhenApplied null when all zero', () => {
    const r = computeAdjustmentConditionBias([mkAdj('a', 0), mkAdj('b', 0)])!
    expect(r.avgWhenApplied).toBeNull()
  })

  it('dominantDirection positive when most are positive', () => {
    const r = computeAdjustmentConditionBias([mkAdj('a', 10000), mkAdj('b', 8000), mkAdj('c', -3000)])!
    expect(r.dominantDirection).toBe('positive')
  })

  it('dominantDirection negative when most are negative', () => {
    const r = computeAdjustmentConditionBias([mkAdj('a', -10000), mkAdj('b', -8000), mkAdj('c', 3000)])!
    expect(r.dominantDirection).toBe('negative')
  })

  it('dominantDirection neutral when zero is most common', () => {
    const r = computeAdjustmentConditionBias([mkAdj('a', 0), mkAdj('b', 0), mkAdj('c', 5000)])!
    expect(r.dominantDirection).toBe('neutral')
  })
})
