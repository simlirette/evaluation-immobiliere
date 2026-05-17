import { describe, it, expect } from 'vitest'
import { computeComparablePriceSkew } from './compute-comparable-price-skew'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: String(sale_price), date: '2024-01-01' }
}

describe('computeComparablePriceSkew', () => {
  it('returns null for fewer than 3 comps', () => {
    expect(computeComparablePriceSkew([mkComp('a', 400000), mkComp('b', 500000)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeComparablePriceSkew([])).toBeNull()
  })

  it('skew 0 for symmetric distribution', () => {
    // mean = median for symmetric
    const comps = [mkComp('a', 300000), mkComp('b', 400000), mkComp('c', 500000)]
    const r = computeComparablePriceSkew(comps)!
    expect(r.skew).toBe(0)
    expect(r.interpretation).toBe('symétrique')
  })

  it('positive skew when mean > median (high outlier)', () => {
    const comps = [mkComp('a', 300000), mkComp('b', 310000), mkComp('c', 320000), mkComp('d', 1000000)]
    const r = computeComparablePriceSkew(comps)!
    expect(r.skew).toBeGreaterThan(0)
    expect(r.interpretation).toBe('asymétrie positive')
  })

  it('negative skew when mean < median (low outlier)', () => {
    const comps = [mkComp('a', 100000), mkComp('b', 490000), mkComp('c', 500000), mkComp('d', 510000)]
    const r = computeComparablePriceSkew(comps)!
    expect(r.skew).toBeLessThan(0)
    expect(r.interpretation).toBe('asymétrie négative')
  })

  it('count equals number of comparables', () => {
    const comps = [mkComp('a', 300000), mkComp('b', 400000), mkComp('c', 500000)]
    expect(computeComparablePriceSkew(comps)!.count).toBe(3)
  })

  it('mean >= median for right-skewed set', () => {
    const comps = [mkComp('a', 300000), mkComp('b', 310000), mkComp('c', 320000), mkComp('d', 1000000)]
    const r = computeComparablePriceSkew(comps)!
    expect(r.mean).toBeGreaterThan(r.median)
  })

  it('interpretation symétrique when |skew| < 0.5', () => {
    const comps = [mkComp('a', 390000), mkComp('b', 400000), mkComp('c', 410000)]
    expect(computeComparablePriceSkew(comps)!.interpretation).toBe('symétrique')
  })
})
