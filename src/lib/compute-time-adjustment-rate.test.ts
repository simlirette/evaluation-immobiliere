import { describe, it, expect } from 'vitest'
import { computeTimeAdjustmentRate } from './compute-time-adjustment-rate'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string, sale_price: number): Comparable {
  return {
    id, rank: id, address: `Addr ${id}`,
    hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null,
    garage_type: null, sale_price, sale_date,
    meta: '', price: '', date: '',
  }
}

describe('computeTimeAdjustmentRate', () => {
  it('returns null for empty array', () => {
    expect(computeTimeAdjustmentRate([])).toBeNull()
  })

  it('returns null for single comparable', () => {
    expect(computeTimeAdjustmentRate([mkComp('a', '2024-01-01', 400000)])).toBeNull()
  })

  it('returns null when all dates are the same', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2024-01-01', 420000)]
    expect(computeTimeAdjustmentRate(comps)).toBeNull()
  })

  it('computes positive rate when prices increase over time', () => {
    // 400000 → 412000 over 12 months → +3%/yr → +0.25%/mo
    const comps = [
      mkComp('a', '2024-01-01', 400000),
      mkComp('b', '2025-01-01', 412000),
    ]
    const result = computeTimeAdjustmentRate(comps)!
    expect(result.annualRatePct).toBeGreaterThan(0)
    expect(result.monthlyRatePct).toBeGreaterThan(0)
  })

  it('computes negative rate when prices decrease', () => {
    const comps = [
      mkComp('a', '2024-01-01', 420000),
      mkComp('b', '2025-01-01', 400000),
    ]
    expect(computeTimeAdjustmentRate(comps)!.annualRatePct).toBeLessThan(0)
  })

  it('confidence is faible for 1 pair', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 412000)]
    expect(computeTimeAdjustmentRate(comps)!.confidence).toBe('faible')
  })

  it('confidence is modérée for 2 pairs', () => {
    const comps = [
      mkComp('a', '2024-01-01', 400000),
      mkComp('b', '2024-07-01', 406000),
      mkComp('c', '2025-01-01', 412000),
    ]
    expect(computeTimeAdjustmentRate(comps)!.confidence).toBe('modérée')
  })

  it('confidence is élevée for 3+ pairs', () => {
    const comps = [
      mkComp('a', '2024-01-01', 400000),
      mkComp('b', '2024-05-01', 404000),
      mkComp('c', '2024-09-01', 408000),
      mkComp('d', '2025-01-01', 412000),
    ]
    expect(computeTimeAdjustmentRate(comps)!.confidence).toBe('élevée')
  })

  it('annualRatePct is rounded to 1 decimal', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 413000)]
    const r = computeTimeAdjustmentRate(comps)!.annualRatePct
    expect(r).toBe(Math.round(r * 10) / 10)
  })

  it('does not mutate input', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 412000)]
    const copy = comps.map(c => ({ ...c }))
    computeTimeAdjustmentRate(comps)
    expect(comps[0]).toEqual(copy[0])
  })
})
