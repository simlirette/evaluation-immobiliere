import { describe, it, expect } from 'vitest'
import { computeGrossAdjustmentTrend } from './compute-gross-adjustment-trend'
import type { Comparable, Adjustment } from '@/types'

function mkComp(id: string, sale_date: string): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 400000, sale_date, meta: '', price: '400000', date: sale_date }
}

function mkAdj(id: string, salePrice: number, surface_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + surface_adj }
}

describe('computeGrossAdjustmentTrend', () => {
  it('returns null for fewer than 3 matched pairs', () => {
    const comps = [mkComp('a', '2024-01-01'), mkComp('b', '2023-01-01')]
    const adjs = [mkAdj('a', 400000, 5000), mkAdj('b', 400000, 8000)]
    expect(computeGrossAdjustmentTrend(comps, adjs)).toBeNull()
  })

  it('returns null for empty inputs', () => {
    expect(computeGrossAdjustmentTrend([], [])).toBeNull()
  })

  it('count equals matched pairs', () => {
    const comps = [mkComp('a', '2024-01-01'), mkComp('b', '2023-01-01'), mkComp('c', '2022-01-01'), mkComp('d', '2021-01-01')]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 10000), mkAdj('c', 400000, 20000), mkAdj('d', 400000, 30000)]
    expect(computeGrossAdjustmentTrend(comps, adjs)!.count).toBe(4)
  })

  it('direction increasing when older comps have higher grossPct', () => {
    // Older comps → larger adjustments → positive slope
    const comps = [
      mkComp('a', '2024-06-01'),
      mkComp('b', '2023-06-01'),
      mkComp('c', '2022-06-01'),
      mkComp('d', '2021-06-01'),
    ]
    const adjs = [
      mkAdj('a', 400000, 4000),    // recent, low adj (~1%)
      mkAdj('b', 400000, 20000),   // 12 months, moderate
      mkAdj('c', 400000, 40000),   // 24 months, higher
      mkAdj('d', 400000, 60000),   // 36 months, highest
    ]
    const r = computeGrossAdjustmentTrend(comps, adjs)!
    expect(r.direction).toBe('increasing')
    expect(r.slopePerMonth).toBeGreaterThan(0)
  })

  it('direction stable for flat grossPct', () => {
    const comps = [
      mkComp('a', '2024-01-01'),
      mkComp('b', '2023-07-01'),
      mkComp('c', '2023-01-01'),
    ]
    const adjs = [
      mkAdj('a', 400000, 20000),
      mkAdj('b', 400000, 20000),
      mkAdj('c', 400000, 20000),
    ]
    expect(computeGrossAdjustmentTrend(comps, adjs)!.direction).toBe('stable')
  })

  it('r2 and significant are present', () => {
    const comps = [mkComp('a', '2024-01-01'), mkComp('b', '2023-01-01'), mkComp('c', '2022-01-01')]
    const adjs = [mkAdj('a', 400000, 4000), mkAdj('b', 400000, 20000), mkAdj('c', 400000, 40000)]
    const r = computeGrossAdjustmentTrend(comps, adjs)!
    expect(r.r2).toBeGreaterThanOrEqual(0)
    expect(r.r2).toBeLessThanOrEqual(1)
    expect(typeof r.significant).toBe('boolean')
  })
})
