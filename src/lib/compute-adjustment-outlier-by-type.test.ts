import { describe, it, expect } from 'vitest'
import { computeAdjustmentOutlierByType } from './compute-adjustment-outlier-by-type'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + surface_adj + year_adj + condition_adj + garage_adj }
}

describe('computeAdjustmentOutlierByType', () => {
  it('returns null for fewer than 3 adjustments', () => {
    expect(computeAdjustmentOutlierByType([mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 6000, 0, 0, 0)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeAdjustmentOutlierByType([])).toBeNull()
  })

  it('hasOutliers false when all values are similar', () => {
    const adjs = [mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 5100, 0, 0, 0), mkAdj('c', 4900, 0, 0, 0), mkAdj('d', 5050, 0, 0, 0)]
    expect(computeAdjustmentOutlierByType(adjs)!.hasOutliers).toBe(false)
  })

  it('detects outlier in surface type', () => {
    const adjs = [
      mkAdj('a', 5000, 0, 0, 0),
      mkAdj('b', 5100, 0, 0, 0),
      mkAdj('c', 4900, 0, 0, 0),
      mkAdj('d', 5050, 0, 0, 0),
      mkAdj('e', 4950, 0, 0, 0),
      mkAdj('f', 5020, 0, 0, 0),
      mkAdj('outlier', 500000, 0, 0, 0),  // extreme outlier — >2σ even after mean shift
    ]
    const r = computeAdjustmentOutlierByType(adjs)!
    expect(r.surface.outlierIds).toContain('outlier')
    expect(r.hasOutliers).toBe(true)
  })

  it('outlierIds empty when type has zero stdDev', () => {
    // All year_adj = 0 → stdDev = 0 → no outliers possible
    const adjs = [mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 6000, 0, 0, 0), mkAdj('c', 4000, 0, 0, 0)]
    expect(computeAdjustmentOutlierByType(adjs)!.year.outlierIds).toHaveLength(0)
  })

  it('returns all 4 types', () => {
    const adjs = [mkAdj('a', 0, 0, 0, 0), mkAdj('b', 0, 0, 0, 0), mkAdj('c', 0, 0, 0, 0)]
    const r = computeAdjustmentOutlierByType(adjs)!
    expect(r).toHaveProperty('surface')
    expect(r).toHaveProperty('year')
    expect(r).toHaveProperty('condition')
    expect(r).toHaveProperty('garage')
  })

  it('mean is correct for type', () => {
    const adjs = [mkAdj('a', 3000, 0, 0, 0), mkAdj('b', 6000, 0, 0, 0), mkAdj('c', 9000, 0, 0, 0)]
    expect(computeAdjustmentOutlierByType(adjs)!.surface.mean).toBe(6000)
  })
})
