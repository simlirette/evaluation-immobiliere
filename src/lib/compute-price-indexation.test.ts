import { describe, it, expect } from 'vitest'
import { computePriceIndexation } from './compute-price-indexation'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, sale_date: string, year_built: number | null = null): Comparable {
  return {
    id,
    rank: id,
    address: `Addr ${id}`,
    hab_m2: 100,
    terrain_m2: null,
    year_built,
    renovated_year: null,
    garage_type: null,
    sale_price,
    sale_date,
    meta: '',
    price: String(sale_price),
    date: sale_date,
  }
}

describe('computePriceIndexation', () => {
  it('returns empty array for empty input', () => {
    expect(computePriceIndexation([], 0.5)).toEqual([])
  })

  it('indexedPrice equals originalPrice when monthlyRatePct is 0', () => {
    const comp = mkComp('a', 400000, '2023-01-01')
    const result = computePriceIndexation([comp], 0)
    expect(result[0].indexedPrice).toBe(400000)
    expect(result[0].adjustmentPct).toBe(0)
  })

  it('indexedPrice increases for positive monthly rate', () => {
    const comp = mkComp('a', 400000, '2024-01-01')
    const result = computePriceIndexation([comp], 0.5)
    expect(result[0].indexedPrice).toBeGreaterThan(400000)
  })

  it('indexedPrice decreases for negative monthly rate', () => {
    const comp = mkComp('a', 400000, '2024-01-01')
    const result = computePriceIndexation([comp], -0.5)
    expect(result[0].indexedPrice).toBeLessThan(400000)
  })

  it('uses linear adjustment: 12 months × 0.5%/mo = 6% total', () => {
    // Sale exactly 12 months ago relative to a fixed date
    const saleDate = new Date()
    saleDate.setMonth(saleDate.getMonth() - 12)
    const comp = mkComp('a', 100000, saleDate.toISOString().slice(0, 10))
    const result = computePriceIndexation([comp], 0.5)
    // 12 * 0.5% = 6% → indexedPrice = 106000
    expect(result[0].indexedPrice).toBe(106000)
    expect(result[0].adjustmentPct).toBe(6)
    expect(result[0].monthsAdjusted).toBe(12)
  })

  it('comparableLabel is the address', () => {
    const comp = mkComp('x', 300000, '2024-06-01')
    const result = computePriceIndexation([comp], 0.3)
    expect(result[0].comparableLabel).toBe('Addr x')
    expect(result[0].comparableId).toBe('x')
  })

  it('returns one entry per comparable', () => {
    const comps = [
      mkComp('a', 300000, '2023-01-01'),
      mkComp('b', 400000, '2023-06-01'),
      mkComp('c', 500000, '2024-01-01'),
    ]
    const result = computePriceIndexation(comps, 0.4)
    expect(result).toHaveLength(3)
    expect(result.map(r => r.comparableId)).toEqual(['a', 'b', 'c'])
  })

  it('monthsAdjusted is non-negative for past sale dates', () => {
    const comp = mkComp('a', 400000, '2020-01-01')
    const result = computePriceIndexation([comp], 0.5)
    expect(result[0].monthsAdjusted).toBeGreaterThan(0)
  })
})
