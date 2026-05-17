import { describe, it, expect } from 'vitest'
import { computeTimeAdjustedPriceRange } from './compute-time-adjusted-price-range'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, sale_date: string): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date, meta: '', price: String(sale_price), date: sale_date }
}

function monthsAgo(n: number): string {
  const d = new Date()
  d.setMonth(d.getMonth() - n)
  return d.toISOString().slice(0, 10)
}

describe('computeTimeAdjustedPriceRange', () => {
  it('returns null for fewer than 2 comparables', () => {
    expect(computeTimeAdjustedPriceRange([mkComp('a', 400000, '2024-01-01')], 0.5)).toBeNull()
  })

  it('returns null when monthlyRatePct is 0', () => {
    const comps = [mkComp('a', 400000, '2023-01-01'), mkComp('b', 500000, '2022-01-01')]
    expect(computeTimeAdjustedPriceRange(comps, 0)).toBeNull()
  })

  it('indexed min <= indexed max', () => {
    const comps = [
      mkComp('a', 300000, monthsAgo(24)),
      mkComp('b', 400000, monthsAgo(12)),
      mkComp('c', 500000, monthsAgo(6)),
    ]
    const r = computeTimeAdjustedPriceRange(comps, 0.5)!
    expect(r.min).toBeLessThanOrEqual(r.max)
  })

  it('range = max − min', () => {
    const comps = [mkComp('a', 300000, monthsAgo(12)), mkComp('b', 500000, monthsAgo(12))]
    const r = computeTimeAdjustedPriceRange(comps, 0.5)!
    expect(r.range).toBe(r.max - r.min)
  })

  it('count matches number of comparables', () => {
    const comps = [mkComp('a', 300000, monthsAgo(6)), mkComp('b', 400000, monthsAgo(12)), mkComp('c', 500000, monthsAgo(18))]
    expect(computeTimeAdjustedPriceRange(comps, 0.3)!.count).toBe(3)
  })

  it('indexed prices are higher than originals for positive rate (past sales)', () => {
    const comps = [mkComp('a', 300000, monthsAgo(12)), mkComp('b', 400000, monthsAgo(6))]
    const r = computeTimeAdjustedPriceRange(comps, 0.5)!
    expect(r.min).toBeGreaterThan(300000)
  })

  it('median is between min and max', () => {
    const comps = [mkComp('a', 300000, monthsAgo(24)), mkComp('b', 400000, monthsAgo(12)), mkComp('c', 500000, monthsAgo(6))]
    const r = computeTimeAdjustedPriceRange(comps, 0.3)!
    expect(r.median).toBeGreaterThanOrEqual(r.min)
    expect(r.median).toBeLessThanOrEqual(r.max)
  })
})
