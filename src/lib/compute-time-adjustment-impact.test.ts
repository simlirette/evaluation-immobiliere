import { describe, it, expect } from 'vitest'
import { computeTimeAdjustmentImpact } from './compute-time-adjustment-impact'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const totalAdj = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + totalAdj }
}

describe('computeTimeAdjustmentImpact', () => {
  it('returns null for empty array', () => {
    expect(computeTimeAdjustmentImpact([])).toBeNull()
  })

  it('returns one entry per adjustment', () => {
    const r = computeTimeAdjustmentImpact([mkAdj('a', 5000, 3000, 0, 0)])!
    expect(r.entries).toHaveLength(1)
  })

  it('yearAdjPctOfGross is |year_adj| / grossAdj × 100', () => {
    // gross = |5000| + |10000| = 15000; yearAdj = 10000; pct = 10000/15000 = 66.7%
    const r = computeTimeAdjustmentImpact([mkAdj('a', 5000, 10000, 0, 0)])!
    expect(r.entries[0].yearAdjPctOfGross).toBeCloseTo(66.7, 0)
  })

  it('yearAdjPctOfGross null when grossAdj = 0', () => {
    const r = computeTimeAdjustmentImpact([mkAdj('a', 0, 0, 0, 0)])!
    expect(r.entries[0].yearAdjPctOfGross).toBeNull()
  })

  it('avgYearAdjPctOfGross null when all comps have grossAdj = 0', () => {
    expect(computeTimeAdjustmentImpact([mkAdj('a', 0, 0, 0, 0)])!.avgYearAdjPctOfGross).toBeNull()
  })

  it('timeAdjustmentDominant true when avg >= 40%', () => {
    // year_adj dominates: 10000 out of 11000 gross = 90.9%
    const r = computeTimeAdjustmentImpact([mkAdj('a', 1000, 10000, 0, 0), mkAdj('b', 1000, 10000, 0, 0)])!
    expect(r.timeAdjustmentDominant).toBe(true)
  })

  it('timeAdjustmentDominant false when avg < 40%', () => {
    // year_adj minor: 1000 out of 11000 gross = 9%
    const r = computeTimeAdjustmentImpact([mkAdj('a', 10000, 1000, 0, 0)])!
    expect(r.timeAdjustmentDominant).toBe(false)
  })

  it('avgYearAdjPctOfGross is mean across comps with grossAdj > 0', () => {
    // comp a: yearAdj 10000/10000 = 100%; comp b: yearAdj 0/5000 = 0%; avg = 50%
    const r = computeTimeAdjustmentImpact([mkAdj('a', 0, 10000, 0, 0), mkAdj('b', 5000, 0, 0, 0)])!
    expect(r.avgYearAdjPctOfGross).toBe(50)
  })
})
