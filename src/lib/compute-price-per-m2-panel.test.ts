import { describe, it, expect } from 'vitest'
import { computePricePerM2Panel } from './compute-price-per-m2-panel'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null): Comparable {
  return { id, rank: id, address: '', hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computePricePerM2Panel', () => {
  it('returns null for empty array', () => {
    expect(computePricePerM2Panel([])).toBeNull()
  })

  it('returns null when < 2 valid comps', () => {
    expect(computePricePerM2Panel([mkComp('a', 300000, null)])).toBeNull()
    expect(computePricePerM2Panel([mkComp('a', 300000, 100)])).toBeNull()
  })

  it('skips comps with null or zero hab_m2', () => {
    const r = computePricePerM2Panel([
      mkComp('a', 300000, 0),
      mkComp('b', 300000, null),
      mkComp('c', 300000, 100),
      mkComp('d', 400000, 100),
    ])!
    expect(r.count).toBe(2)
  })

  it('mean = avg of ppm2 values', () => {
    // 300000/100=3000, 400000/100=4000 → mean=3500
    const r = computePricePerM2Panel([mkComp('a', 300000, 100), mkComp('b', 400000, 100)])!
    expect(r.mean).toBeCloseTo(3500, 5)
  })

  it('median of even count = avg of middle two', () => {
    const r = computePricePerM2Panel([mkComp('a', 300000, 100), mkComp('b', 400000, 100)])!
    expect(r.median).toBeCloseTo(3500, 5)
  })

  it('median of odd count = middle value', () => {
    const r = computePricePerM2Panel([
      mkComp('a', 300000, 100),
      mkComp('b', 400000, 100),
      mkComp('c', 350000, 100),
    ])!
    expect(r.median).toBeCloseTo(3500, 5)
  })

  it('min and max are correct', () => {
    const r = computePricePerM2Panel([mkComp('a', 300000, 100), mkComp('b', 500000, 100)])!
    expect(r.min).toBeCloseTo(3000, 5)
    expect(r.max).toBeCloseTo(5000, 5)
  })

  it('stdDev uses population variance (÷n)', () => {
    // ppm2: [3000, 4000], mean=3500, variance=(250000+250000)/2=250000, stdDev=500
    const r = computePricePerM2Panel([mkComp('a', 300000, 100), mkComp('b', 400000, 100)])!
    expect(r.stdDev).toBeCloseTo(500, 5)
  })

  it('cv = stdDev/mean × 100', () => {
    const r = computePricePerM2Panel([mkComp('a', 300000, 100), mkComp('b', 400000, 100)])!
    expect(r.cv).toBeCloseTo(500 / 3500 * 100, 3)
  })
})
