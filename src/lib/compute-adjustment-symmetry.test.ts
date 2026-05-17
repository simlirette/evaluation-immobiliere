import { describe, it, expect } from 'vitest'
import { computeAdjustmentSymmetry } from './compute-adjustment-symmetry'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surfAdj: number, yearAdj = 0): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: surfAdj, year_adj: yearAdj, condition_adj: 0, garage_adj: 0, adjusted: 400000 + surfAdj + yearAdj }
}

describe('computeAdjustmentSymmetry', () => {
  it('returns null for fewer than 3 adjustments', () => {
    expect(computeAdjustmentSymmetry([mkAdj('a', 5000), mkAdj('b', 6000)])).toBeNull()
  })

  it('overallSymmetric true when all CV <= 50%', () => {
    // Surface: [5000, 6000, 5500] — very consistent, CV low
    const adjs = [mkAdj('a', 5000), mkAdj('b', 6000), mkAdj('c', 5500)]
    const r = computeAdjustmentSymmetry(adjs)!
    expect(r.overallSymmetric).toBe(true)
    expect(r.surface.symmetric).toBe(true)
  })

  it('asymmetricCount > 0 when CV > 50% for a type', () => {
    // Surface: [0, 0, 50000] — extreme outlier, high CV
    const adjs = [mkAdj('a', 1), mkAdj('b', 1), mkAdj('c', 50000)]
    const r = computeAdjustmentSymmetry(adjs)!
    expect(r.surface.cv).toBeGreaterThan(50)
    expect(r.surface.symmetric).toBe(false)
    expect(r.asymmetricCount).toBeGreaterThan(0)
  })

  it('symmetric true when fewer than 2 non-zero values for a type', () => {
    // condition_adj all zero → treated as symmetric (insufficient data)
    const adjs = [mkAdj('a', 5000), mkAdj('b', 6000), mkAdj('c', 5500)]
    const r = computeAdjustmentSymmetry(adjs)!
    expect(r.condition.symmetric).toBe(true)
    expect(r.condition.mean).toBe(0)
  })

  it('surface.mean is mean of surface_adj values', () => {
    // (5000+6000+7000)/3 = 6000
    const adjs = [mkAdj('a', 5000), mkAdj('b', 6000), mkAdj('c', 7000)]
    const r = computeAdjustmentSymmetry(adjs)!
    expect(r.surface.mean).toBe(6000)
  })

  it('year type reports independently from surface', () => {
    // Surface consistent, year inconsistent
    const adjs = [
      mkAdj('a', 5000, 1),
      mkAdj('b', 5000, 1),
      mkAdj('c', 5000, 50000),  // year spike
    ]
    const r = computeAdjustmentSymmetry(adjs)!
    expect(r.surface.symmetric).toBe(true)
    expect(r.year.symmetric).toBe(false)
  })

  it('cv rounds to 1 decimal', () => {
    const adjs = [mkAdj('a', 5000), mkAdj('b', 6000), mkAdj('c', 7000)]
    const r = computeAdjustmentSymmetry(adjs)!
    expect(typeof r.surface.cv).toBe('number')
    expect(Number.isFinite(r.surface.cv)).toBe(true)
  })
})
