import { describe, it, expect } from 'vitest'
import { computeAdjustmentNetMagnitudeProfile } from './compute-adjustment-net-magnitude-profile'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, totalAdj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: totalAdj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + totalAdj }
}

describe('computeAdjustmentNetMagnitudeProfile', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentNetMagnitudeProfile([])).toBeNull()
  })

  it('faible when |netAdj| < 5% of salePrice', () => {
    // 10000/400000 = 2.5% → faible
    const r = computeAdjustmentNetMagnitudeProfile([mkAdj('a', 400000, 10000)])!
    expect(r.entries[0].magnitude).toBe('faible')
    expect(r.countFaible).toBe(1)
  })

  it('modéré when 5% ≤ |netAdj| ≤ 15%', () => {
    // 40000/400000 = 10% → modéré
    const r = computeAdjustmentNetMagnitudeProfile([mkAdj('a', 400000, 40000)])!
    expect(r.entries[0].magnitude).toBe('modéré')
    expect(r.countModéré).toBe(1)
  })

  it('fort when |netAdj| > 15%', () => {
    // 80000/400000 = 20% → fort
    const r = computeAdjustmentNetMagnitudeProfile([mkAdj('a', 400000, 80000)])!
    expect(r.entries[0].magnitude).toBe('fort')
    expect(r.countFort).toBe(1)
  })

  it('negative net adj classified by absolute value', () => {
    // -80000/400000 = 20% → fort
    const r = computeAdjustmentNetMagnitudeProfile([mkAdj('a', 400000, -80000)])!
    expect(r.entries[0].magnitude).toBe('fort')
  })

  it('counts sum to total adjs', () => {
    const r = computeAdjustmentNetMagnitudeProfile([
      mkAdj('a', 400000, 10000),  // faible
      mkAdj('b', 400000, 40000),  // modéré
      mkAdj('c', 400000, 80000),  // fort
    ])!
    expect(r.countFaible + r.countModéré + r.countFort).toBe(3)
  })

  it('one entry per adjustment', () => {
    const r = computeAdjustmentNetMagnitudeProfile([mkAdj('a', 400000, 10000), mkAdj('b', 400000, 40000)])!
    expect(r.entries).toHaveLength(2)
  })

  it('boundary: exactly 15% → modéré (not fort)', () => {
    // 60000/400000 = 15% exactly → modéré (≤ 15)
    const r = computeAdjustmentNetMagnitudeProfile([mkAdj('a', 400000, 60000)])!
    expect(r.entries[0].magnitude).toBe('modéré')
  })
})
