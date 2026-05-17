import { describe, it, expect } from 'vitest'
import { computePricePerM2Stats } from './compute-price-per-m2-stats'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null): Comparable {
  return {
    id, rank: id, address: `Addr ${id}`,
    hab_m2, terrain_m2: null, year_built: null, renovated_year: null,
    garage_type: null, sale_price, sale_date: '2024-01-01',
    meta: '', price: '', date: '',
  }
}

describe('computePricePerM2Stats', () => {
  it('returns null for empty array', () => {
    expect(computePricePerM2Stats([])).toBeNull()
  })

  it('returns null when only one valid comp', () => {
    expect(computePricePerM2Stats([mkComp('a', 400000, 100)])).toBeNull()
  })

  it('excludes comps without hab_m2', () => {
    const comps = [mkComp('a', 400000, 100), mkComp('b', 500000, null)]
    expect(computePricePerM2Stats(comps)).toBeNull()
  })

  it('computes min, max, avg correctly', () => {
    const comps = [
      mkComp('a', 400000, 100),  // 4000/m²
      mkComp('b', 500000, 100),  // 5000/m²
    ]
    const result = computePricePerM2Stats(comps)!
    expect(result.min).toBe(4000)
    expect(result.max).toBe(5000)
    expect(result.avg).toBe(4500)
    expect(result.spread).toBe(1000)
  })

  it('computes median for odd count', () => {
    const comps = [
      mkComp('a', 400000, 100),  // 4000
      mkComp('b', 500000, 100),  // 5000
      mkComp('c', 600000, 100),  // 6000
    ]
    expect(computePricePerM2Stats(comps)!.median).toBe(5000)
  })

  it('computes median for even count (average of middle two)', () => {
    const comps = [
      mkComp('a', 400000, 100),  // 4000
      mkComp('b', 500000, 100),  // 5000
      mkComp('c', 600000, 100),  // 6000
      mkComp('d', 700000, 100),  // 7000
    ]
    expect(computePricePerM2Stats(comps)!.median).toBe(5500)
  })

  it('count reflects only comps with hab_m2', () => {
    const comps = [
      mkComp('a', 400000, 100),
      mkComp('b', 500000, 100),
      mkComp('c', 600000, null),
    ]
    expect(computePricePerM2Stats(comps)!.count).toBe(2)
  })

  it('does not mutate input', () => {
    const comps = [mkComp('a', 400000, 100), mkComp('b', 500000, 100)]
    const copy = comps.map(c => ({ ...c }))
    computePricePerM2Stats(comps)
    expect(comps[0]).toEqual(copy[0])
  })
})
