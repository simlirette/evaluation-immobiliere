import { describe, it, expect } from 'vitest'
import { computeBuildingAgeStats } from './compute-building-age-stats'
import type { Comparable } from '@/types'

function mkComp(id: string, year_built: number | null, sale_date = '2024-01-01'): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2: null, year_built, renovated_year: null, garage_type: null, sale_price: 400000, sale_date, meta: '', price: '400000', date: sale_date }
}

describe('computeBuildingAgeStats', () => {
  it('returns null for fewer than 2 valid comps', () => {
    expect(computeBuildingAgeStats([mkComp('a', null)])).toBeNull()
    expect(computeBuildingAgeStats([mkComp('a', 1990)])).toBeNull()
  })

  it('age at sale = sale_date year − year_built', () => {
    // 2024 - 1994 = 30; 2024 - 1984 = 40
    const comps = [mkComp('a', 1994, '2024-01-01'), mkComp('b', 1984, '2024-01-01')]
    const r = computeBuildingAgeStats(comps)!
    expect(r.min).toBe(30)
    expect(r.max).toBe(40)
  })

  it('median for odd count', () => {
    const comps = [mkComp('a', 1994), mkComp('b', 1984), mkComp('c', 1974)]
    // ages: 30, 40, 50 → median 40
    const r = computeBuildingAgeStats(comps)!
    expect(r.median).toBe(40)
  })

  it('median for even count', () => {
    const comps = [mkComp('a', 1994), mkComp('b', 1990), mkComp('c', 1984), mkComp('d', 1980)]
    // ages: 30, 34, 40, 44 → median (34+40)/2 = 37
    const r = computeBuildingAgeStats(comps)!
    expect(r.median).toBe(37)
  })

  it('avgAge is rounded mean', () => {
    const comps = [mkComp('a', 1994), mkComp('b', 1984)]
    // ages: 30, 40 → avg 35
    expect(computeBuildingAgeStats(comps)!.avgAge).toBe(35)
  })

  it('missingCount counts null year_built', () => {
    const comps = [mkComp('a', 1990), mkComp('b', null), mkComp('c', 1985)]
    expect(computeBuildingAgeStats(comps)!.missingCount).toBe(1)
    expect(computeBuildingAgeStats(comps)!.count).toBe(2)
  })

  it('excludes negative age (sale before build year)', () => {
    // year_built 2030, sale 2024 → age -6 → excluded
    const comps = [mkComp('a', 1990), mkComp('b', 2030), mkComp('c', 1985)]
    const r = computeBuildingAgeStats(comps)!
    expect(r.count).toBe(2)
  })
})
