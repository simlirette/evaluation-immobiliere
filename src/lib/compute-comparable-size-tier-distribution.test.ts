import { describe, it, expect } from 'vitest'
import { computeComparableSizeTierDistribution } from './compute-comparable-size-tier-distribution'
import type { Comparable } from '@/types'

function mkComp(id: string, hab_m2: number | null, sale_price = 300000): Comparable {
  return { id, rank: id, address: '', hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeComparableSizeTierDistribution', () => {
  it('returns null for empty array', () => {
    expect(computeComparableSizeTierDistribution([])).toBeNull()
  })

  it('returns 4 tiers', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', 100)])!
    expect(r.tiers).toHaveLength(4)
  })

  it('places 75 m² in < 80 tier', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', 75)])!
    expect(r.tiers[0].count).toBe(1)
    expect(r.tiers[1].count).toBe(0)
  })

  it('places 80 m² in 80–120 tier (min inclusive)', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', 80)])!
    expect(r.tiers[0].count).toBe(0)
    expect(r.tiers[1].count).toBe(1)
  })

  it('places 120 m² in 120–160 tier (min inclusive)', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', 120)])!
    expect(r.tiers[1].count).toBe(0)
    expect(r.tiers[2].count).toBe(1)
  })

  it('places 160 m² in > 160 tier (min inclusive)', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', 160)])!
    expect(r.tiers[2].count).toBe(0)
    expect(r.tiers[3].count).toBe(1)
  })

  it('avgPrice = mean sale_price of tier members', () => {
    const r = computeComparableSizeTierDistribution([
      mkComp('a', 90, 300000),
      mkComp('b', 100, 400000),
    ])!
    expect(r.tiers[1].avgPrice).toBeCloseTo(350000, 0)
  })

  it('avgPrice = null for empty tier', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', 90)])!
    expect(r.tiers[0].avgPrice).toBeNull()
  })

  it('missingCount = count of null or zero hab_m2', () => {
    const r = computeComparableSizeTierDistribution([mkComp('a', null), mkComp('b', 0), mkComp('c', 100)])!
    expect(r.missingCount).toBe(2)
  })
})
