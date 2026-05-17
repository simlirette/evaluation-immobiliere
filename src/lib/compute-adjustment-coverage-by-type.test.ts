import { describe, it, expect } from 'vitest'
import { computeAdjustmentCoverageByType } from './compute-adjustment-coverage-by-type'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentCoverageByType', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentCoverageByType([])).toBeNull()
  })

  it('returns 4 entries', () => {
    expect(computeAdjustmentCoverageByType([mkAdj('a', 0, 0, 0, 0)])!.entries).toHaveLength(4)
  })

  it('coveragePct 100 when all comps have non-zero for a type', () => {
    const adjs = [mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 3000, 0, 0, 0)]
    const r = computeAdjustmentCoverageByType(adjs)!
    expect(r.entries.find(e => e.type === 'surface')!.coveragePct).toBe(100)
  })

  it('coveragePct 0 when no comps have non-zero for a type', () => {
    const adjs = [mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 3000, 0, 0, 0)]
    expect(computeAdjustmentCoverageByType(adjs)!.entries.find(e => e.type === 'year')!.coveragePct).toBe(0)
  })

  it('unusedTypes lists types never applied', () => {
    const adjs = [mkAdj('a', 5000, 2000, 0, 0), mkAdj('b', 3000, 1000, 0, 0)]
    const r = computeAdjustmentCoverageByType(adjs)!
    expect(r.unusedTypes).toContain('condition')
    expect(r.unusedTypes).toContain('garage')
  })

  it('universalTypes lists types at >= 80% coverage', () => {
    const adjs = [mkAdj('a', 5000, 2000, 0, 0), mkAdj('b', 3000, 1000, 0, 0), mkAdj('c', 4000, 1500, 0, 0)]
    const r = computeAdjustmentCoverageByType(adjs)!
    expect(r.universalTypes).toContain('surface')
    expect(r.universalTypes).toContain('year')
  })

  it('avgAbsWhenApplied is 0 when coveragePct = 0', () => {
    const adjs = [mkAdj('a', 0, 0, 0, 0)]
    expect(computeAdjustmentCoverageByType(adjs)!.entries.find(e => e.type === 'surface')!.avgAbsWhenApplied).toBe(0)
  })

  it('avgAbsWhenApplied uses absolute value', () => {
    const adjs = [mkAdj('a', -5000, 0, 0, 0), mkAdj('b', 3000, 0, 0, 0)]
    const r = computeAdjustmentCoverageByType(adjs)!
    expect(r.entries.find(e => e.type === 'surface')!.avgAbsWhenApplied).toBe(4000)
  })
})
