import { describe, it, expect } from 'vitest'
import { computePricePerM2ByDecade } from './compute-price-per-m2-by-decade'
import type { Comparable } from '@/types'

function mkComp(id: string, year_built: number | null, sale_price: number, hab_m2: number | null): Comparable {
  return { id, rank: id, address: '', hab_m2, terrain_m2: null, year_built, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computePricePerM2ByDecade', () => {
  it('returns null for empty array', () => {
    expect(computePricePerM2ByDecade([])).toBeNull()
  })

  it('returns null when no valid comps (need year_built and hab_m2)', () => {
    expect(computePricePerM2ByDecade([mkComp('a', null, 300000, 100)])).toBeNull()
    expect(computePricePerM2ByDecade([mkComp('a', 1990, 300000, null)])).toBeNull()
  })

  it('groups by decade correctly', () => {
    const r = computePricePerM2ByDecade([
      mkComp('a', 1985, 300000, 100), // decade 1980
      mkComp('b', 1992, 300000, 100), // decade 1990
    ])!
    expect(r.entries.map(e => e.decade)).toEqual([1980, 1990])
  })

  it('avgPpm2 = sale_price / hab_m2', () => {
    const r = computePricePerM2ByDecade([mkComp('a', 1990, 300000, 100)])!
    expect(r.entries[0].avgPpm2).toBe(3000)
  })

  it('avgPpm2 averages across comps in same decade', () => {
    // both 1990s: 300000/100=3000 and 400000/100=4000 → avg=3500
    const r = computePricePerM2ByDecade([
      mkComp('a', 1991, 300000, 100),
      mkComp('b', 1998, 400000, 100),
    ])!
    expect(r.entries[0].avgPpm2).toBe(3500)
    expect(r.entries[0].count).toBe(2)
  })

  it('entries sorted by decade ascending', () => {
    const r = computePricePerM2ByDecade([
      mkComp('a', 2005, 300000, 100),
      mkComp('b', 1985, 300000, 100),
    ])!
    expect(r.entries[0].decade).toBeLessThan(r.entries[1].decade)
  })

  it('skips comps with zero hab_m2', () => {
    const r = computePricePerM2ByDecade([
      mkComp('a', 1990, 300000, 0),
      mkComp('b', 1990, 300000, 100),
    ])!
    expect(r.entries[0].count).toBe(1)
  })
})
