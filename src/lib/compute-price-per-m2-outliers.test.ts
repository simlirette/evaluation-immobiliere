import { describe, it, expect } from 'vitest'
import { computePricePerM2Outliers } from './compute-price-per-m2-outliers'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: String(sale_price), date: '2024-01-01' }
}

describe('computePricePerM2Outliers', () => {
  it('returns null for fewer than 4 comps with hab_m2', () => {
    expect(computePricePerM2Outliers([mkComp('a', 400000, 80), mkComp('b', 500000, 100), mkComp('c', 300000, 90)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computePricePerM2Outliers([])).toBeNull()
  })

  it('iqr = q3 − q1', () => {
    const comps = [mkComp('a', 300000, 100), mkComp('b', 400000, 100), mkComp('c', 500000, 100), mkComp('d', 600000, 100)]
    const r = computePricePerM2Outliers(comps)!
    expect(r.iqr).toBe(r.q3 - r.q1)
  })

  it('q1 <= median <= q3', () => {
    const comps = [mkComp('a', 300000, 100), mkComp('b', 400000, 100), mkComp('c', 500000, 100), mkComp('d', 600000, 100), mkComp('e', 700000, 100)]
    const r = computePricePerM2Outliers(comps)!
    expect(r.q1).toBeLessThanOrEqual(r.median)
    expect(r.median).toBeLessThanOrEqual(r.q3)
  })

  it('outlierIds contains extreme $/m² comp', () => {
    const comps = [
      mkComp('a', 300000, 100), mkComp('b', 310000, 100),
      mkComp('c', 320000, 100), mkComp('d', 330000, 100),
      mkComp('e', 340000, 100),
      mkComp('outlier', 3000000, 100),  // 30000 $/m² vs ~3200 $/m²
    ]
    const r = computePricePerM2Outliers(comps)!
    expect(r.outlierIds).toContain('outlier')
  })

  it('outlierIds empty when no outliers', () => {
    const comps = [mkComp('a', 300000, 100), mkComp('b', 320000, 100), mkComp('c', 340000, 100), mkComp('d', 360000, 100)]
    expect(computePricePerM2Outliers(comps)!.outlierIds).toHaveLength(0)
  })

  it('missingCount counts comps with null hab_m2', () => {
    const comps = [mkComp('a', 300000, 100), mkComp('b', 400000, null), mkComp('c', 500000, 100), mkComp('d', 600000, 100), mkComp('e', 700000, 100)]
    expect(computePricePerM2Outliers(comps)!.missingCount).toBe(1)
  })

  it('lowerFence = q1 − 1.5 × iqr', () => {
    const comps = [mkComp('a', 300000, 100), mkComp('b', 400000, 100), mkComp('c', 500000, 100), mkComp('d', 600000, 100)]
    const r = computePricePerM2Outliers(comps)!
    expect(r.lowerFence).toBe(Math.round(r.q1 - 1.5 * r.iqr))
  })
})
