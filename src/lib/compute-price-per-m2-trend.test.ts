import { describe, it, expect } from 'vitest'
import { computePricePerM2Trend } from './compute-price-per-m2-trend'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null, sale_date: string): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date, meta: '', price: String(sale_price), date: sale_date }
}

describe('computePricePerM2Trend', () => {
  it('returns null for fewer than 3 comps with hab_m2', () => {
    expect(computePricePerM2Trend([mkComp('a', 400000, 100, '2024-01-01'), mkComp('b', 500000, 100, '2024-06-01')])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computePricePerM2Trend([])).toBeNull()
  })

  it('count equals number of valid comps', () => {
    const comps = [
      mkComp('a', 400000, 100, '2023-01-01'),
      mkComp('b', 420000, 100, '2023-07-01'),
      mkComp('c', 440000, 100, '2024-01-01'),
      mkComp('d', 500000, null, '2024-01-01'),  // excluded
    ]
    expect(computePricePerM2Trend(comps)!.count).toBe(3)
  })

  it('direction rising when slope > 50', () => {
    // prices sharply rising: 3000, 4000, 5000 $/m² over 12 months each
    const comps = [
      mkComp('a', 300000, 100, '2022-01-01'),
      mkComp('b', 400000, 100, '2023-01-01'),
      mkComp('c', 500000, 100, '2024-01-01'),
    ]
    expect(computePricePerM2Trend(comps)!.direction).toBe('rising')
  })

  it('direction falling when slope < -50', () => {
    const comps = [
      mkComp('a', 500000, 100, '2022-01-01'),
      mkComp('b', 400000, 100, '2023-01-01'),
      mkComp('c', 300000, 100, '2024-01-01'),
    ]
    expect(computePricePerM2Trend(comps)!.direction).toBe('falling')
  })

  it('direction stable for flat prices', () => {
    const comps = [
      mkComp('a', 400000, 100, '2023-01-01'),
      mkComp('b', 400000, 100, '2023-07-01'),
      mkComp('c', 400000, 100, '2024-01-01'),
    ]
    expect(computePricePerM2Trend(comps)!.direction).toBe('stable')
  })

  it('r2 = 1 for perfect linear trend', () => {
    const comps = [
      mkComp('a', 300000, 100, '2022-01-01'),
      mkComp('b', 400000, 100, '2023-01-01'),
      mkComp('c', 500000, 100, '2024-01-01'),
    ]
    const r = computePricePerM2Trend(comps)!
    expect(r.r2).toBeCloseTo(1, 1)
    expect(r.significant).toBe(true)
  })

  it('significant false when r2 < 0.5', () => {
    // Random-looking prices → low r2
    const comps = [
      mkComp('a', 300000, 100, '2023-01-01'),
      mkComp('b', 500000, 100, '2023-07-01'),
      mkComp('c', 320000, 100, '2024-01-01'),
    ]
    const r = computePricePerM2Trend(comps)!
    expect(r.significant).toBe(false)
  })
})
