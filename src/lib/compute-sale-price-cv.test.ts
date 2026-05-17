import { describe, it, expect } from 'vitest'
import { computeSalePriceCV } from './compute-sale-price-cv'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number): Comparable {
  return { id, rank: id, address: '', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeSalePriceCV', () => {
  it('returns null for < 2 comps', () => {
    expect(computeSalePriceCV([])).toBeNull()
    expect(computeSalePriceCV([mkComp('a', 300000)])).toBeNull()
  })

  it('cv = 0 when all prices identical', () => {
    const r = computeSalePriceCV([mkComp('a', 300000), mkComp('b', 300000)])!
    expect(r.cv).toBe(0)
    expect(r.cohesion).toBe('homogène')
  })

  it('cohesion homogène when cv < 10%', () => {
    // mean=300000, prices differ by 5% → cv < 10
    const r = computeSalePriceCV([mkComp('a', 285000), mkComp('b', 315000)])!
    expect(r.cohesion).toBe('homogène')
  })

  it('cohesion modérée when 10% ≤ cv ≤ 20%', () => {
    // mean=300000, stdDev≈30000 → cv≈10%
    const r = computeSalePriceCV([mkComp('a', 270000), mkComp('b', 330000)])!
    expect(r.cv).toBeGreaterThanOrEqual(10)
    expect(r.cv).toBeLessThanOrEqual(20)
    expect(r.cohesion).toBe('modérée')
  })

  it('cohesion hétérogène when cv > 20%', () => {
    // large spread: 100k and 500k → mean=300k, stdDev=200k, cv≈66%
    const r = computeSalePriceCV([mkComp('a', 100000), mkComp('b', 500000)])!
    expect(r.cv).toBeGreaterThan(20)
    expect(r.cohesion).toBe('hétérogène')
  })

  it('mean and count correct', () => {
    const r = computeSalePriceCV([mkComp('a', 200000), mkComp('b', 400000)])!
    expect(r.count).toBe(2)
    expect(r.mean).toBe(300000)
  })

  it('stdDev correct for two values', () => {
    // mean=300000; deviations ±100000; variance=10000000000; stdDev=100000
    const r = computeSalePriceCV([mkComp('a', 200000), mkComp('b', 400000)])!
    expect(r.stdDev).toBeCloseTo(100000, 0)
  })
})
