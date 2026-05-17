import { describe, it, expect } from 'vitest'
import { computePricePerM2Distribution } from './compute-price-per-m2-distribution'
import type { Comparable } from '@/types'

function mkComp(id: string, hab_m2: number | null, sale_price: number): Comparable {
  return { id, rank: id, address: `addr ${id}`, hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

const comps = [
  mkComp('a', 100, 400000),  // 4000 $/m²
  mkComp('b', 100, 500000),  // 5000 $/m²
  mkComp('c', 100, 300000),  // 3000 $/m²
  mkComp('d', 100, 600000),  // 6000 $/m²
]

describe('computePricePerM2Distribution', () => {
  it('returns null for fewer than 2 valid comps', () => {
    expect(computePricePerM2Distribution([])).toBeNull()
    expect(computePricePerM2Distribution([mkComp('a', 100, 400000)])).toBeNull()
  })

  it('returns null when no comp has hab_m2', () => {
    expect(computePricePerM2Distribution([mkComp('a', null, 400000), mkComp('b', null, 500000)])).toBeNull()
  })

  it('excludes comps with null or zero hab_m2', () => {
    const mixed = [mkComp('a', null, 400000), mkComp('b', 100, 500000), mkComp('c', 0, 300000)]
    // only comp b is valid → < 2 → null
    expect(computePricePerM2Distribution(mixed)).toBeNull()
  })

  it('computes min, max correctly', () => {
    const r = computePricePerM2Distribution(comps)!
    expect(r.min).toBe(3000)
    expect(r.max).toBe(6000)
  })

  it('computes median correctly (even count)', () => {
    // sorted: [3000, 4000, 5000, 6000] → median = (4000+5000)/2 = 4500
    const r = computePricePerM2Distribution(comps)!
    expect(r.median).toBe(4500)
  })

  it('computes median correctly (odd count)', () => {
    const r = computePricePerM2Distribution([mkComp('a', 100, 300000), mkComp('b', 100, 400000), mkComp('c', 100, 500000)])!
    // sorted: [3000, 4000, 5000] → median = 4000
    expect(r.median).toBe(4000)
  })

  it('computes mean correctly', () => {
    // (3000+4000+5000+6000)/4 = 4500
    const r = computePricePerM2Distribution(comps)!
    expect(r.mean).toBe(4500)
  })

  it('count matches valid comps only', () => {
    const mixed = [mkComp('a', null, 400000), mkComp('b', 100, 500000), mkComp('c', 100, 300000)]
    const r = computePricePerM2Distribution(mixed)!
    expect(r.count).toBe(2)
  })

  it('cv is stdDev/mean×100 rounded to 1 decimal', () => {
    // 2 comps: 4000 and 6000 → mean 5000, variance ((1000^2+1000^2)/2)=1000000, stdDev=1000, CV=20%
    const r = computePricePerM2Distribution([mkComp('a', 100, 400000), mkComp('b', 100, 600000)])!
    expect(r.cv).toBe(20)
  })
})
