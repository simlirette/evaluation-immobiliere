import { describe, it, expect } from 'vitest'
import { computeRenovationProfile } from './compute-renovation-profile'
import type { Comparable } from '@/types'

const currentYear = new Date().getFullYear()

function mkComp(id: string, renovated_year: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: null, renovated_year, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01' }
}

describe('computeRenovationProfile', () => {
  it('returns null for empty array', () => {
    expect(computeRenovationProfile([])).toBeNull()
  })

  it('renovatedCount and renovatedPct correct', () => {
    const comps = [mkComp('a', 2015), mkComp('b', null), mkComp('c', null), mkComp('d', 2018)]
    const r = computeRenovationProfile(comps)!
    expect(r.renovatedCount).toBe(2)
    expect(r.renovatedPct).toBe(50)
  })

  it('avgRenovationAge is null when no renovations', () => {
    const comps = [mkComp('a', null), mkComp('b', null)]
    expect(computeRenovationProfile(comps)!.avgRenovationAge).toBeNull()
  })

  it('avgRenovationAge computed relative to current year', () => {
    const yr = currentYear - 5
    const comps = [mkComp('a', yr), mkComp('b', yr)]
    expect(computeRenovationProfile(comps)!.avgRenovationAge).toBe(5)
  })

  it('recentlyRenovatedIds includes only renovations within 10 years', () => {
    const recent = currentYear - 5
    const old = currentYear - 15
    const comps = [mkComp('a', recent), mkComp('b', old), mkComp('c', recent)]
    const r = computeRenovationProfile(comps)!
    expect(r.recentlyRenovatedIds).toContain('a')
    expect(r.recentlyRenovatedIds).toContain('c')
    expect(r.recentlyRenovatedIds).not.toContain('b')
  })

  it('recentlyRenovatedIds empty when all old', () => {
    const comps = [mkComp('a', currentYear - 20), mkComp('b', currentYear - 30)]
    expect(computeRenovationProfile(comps)!.recentlyRenovatedIds).toHaveLength(0)
  })

  it('renovatedPct is 0 when none renovated', () => {
    const comps = [mkComp('a', null), mkComp('b', null), mkComp('c', null)]
    expect(computeRenovationProfile(comps)!.renovatedPct).toBe(0)
  })

  it('renovatedPct is 100 when all renovated', () => {
    const comps = [mkComp('a', 2010), mkComp('b', 2015)]
    expect(computeRenovationProfile(comps)!.renovatedPct).toBe(100)
  })
})
