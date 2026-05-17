import { describe, it, expect } from 'vitest'
import { computeComparablePriceQuartiles } from './compute-comparable-price-quartiles'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: String(sale_price), date: '2024-01-01' }
}

describe('computeComparablePriceQuartiles', () => {
  it('returns null for fewer than 4 comparables', () => {
    expect(computeComparablePriceQuartiles([mkComp('a', 100), mkComp('b', 200), mkComp('c', 300)])).toBeNull()
    expect(computeComparablePriceQuartiles([])).toBeNull()
  })

  it('iqr = q3 − q1', () => {
    const comps = [mkComp('a', 100000), mkComp('b', 200000), mkComp('c', 300000), mkComp('d', 400000)]
    const r = computeComparablePriceQuartiles(comps)!
    expect(r.iqr).toBe(r.q3 - r.q1)
  })

  it('lowerFence = q1 − 1.5 × iqr', () => {
    const comps = [mkComp('a', 100000), mkComp('b', 200000), mkComp('c', 300000), mkComp('d', 400000)]
    const r = computeComparablePriceQuartiles(comps)!
    expect(r.lowerFence).toBe(Math.round(r.q1 - 1.5 * r.iqr))
  })

  it('upperFence = q3 + 1.5 × iqr', () => {
    const comps = [mkComp('a', 100000), mkComp('b', 200000), mkComp('c', 300000), mkComp('d', 400000)]
    const r = computeComparablePriceQuartiles(comps)!
    expect(r.upperFence).toBe(Math.round(r.q3 + 1.5 * r.iqr))
  })

  it('q1 <= q2 <= q3', () => {
    const comps = [mkComp('a', 150000), mkComp('b', 250000), mkComp('c', 350000), mkComp('d', 450000), mkComp('e', 550000)]
    const r = computeComparablePriceQuartiles(comps)!
    expect(r.q1).toBeLessThanOrEqual(r.q2)
    expect(r.q2).toBeLessThanOrEqual(r.q3)
  })

  it('outlierIds contains extreme price comps', () => {
    // 5 normal comps + 1 extreme outlier
    const comps = [
      mkComp('a', 300000), mkComp('b', 310000), mkComp('c', 320000),
      mkComp('d', 330000), mkComp('e', 340000),
      mkComp('outlier', 2000000),
    ]
    const r = computeComparablePriceQuartiles(comps)!
    expect(r.outlierIds).toContain('outlier')
  })

  it('outlierIds empty when no outliers', () => {
    const comps = [mkComp('a', 300000), mkComp('b', 320000), mkComp('c', 340000), mkComp('d', 360000)]
    const r = computeComparablePriceQuartiles(comps)!
    expect(r.outlierIds).toHaveLength(0)
  })

  it('q2 is the median', () => {
    // 5 values: 100, 200, 300, 400, 500 → median = 300
    const comps = [mkComp('a', 100000), mkComp('b', 200000), mkComp('c', 300000), mkComp('d', 400000), mkComp('e', 500000)]
    expect(computeComparablePriceQuartiles(comps)!.q2).toBe(300000)
  })
})
