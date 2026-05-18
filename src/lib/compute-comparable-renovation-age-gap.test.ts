import { describe, it, expect } from 'vitest'
import { computeComparableRenovationAgeGap } from './compute-comparable-renovation-age-gap'
import type { Comparable } from '@/types'

function mkComp(id: string, year_built: number | null, renovated_year: number | null): Comparable {
  return { id, rank: id, address: '', hab_m2: null, terrain_m2: null, year_built, renovated_year, garage_type: null, sale_price: 300000, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeComparableRenovationAgeGap', () => {
  it('returns null when no comps have both fields', () => {
    expect(computeComparableRenovationAgeGap([])).toBeNull()
    expect(computeComparableRenovationAgeGap([mkComp('a', 1990, null)])).toBeNull()
    expect(computeComparableRenovationAgeGap([mkComp('a', null, 2010)])).toBeNull()
  })

  it('returns null when renovated_year <= year_built', () => {
    expect(computeComparableRenovationAgeGap([mkComp('a', 2010, 2005)])).toBeNull()
  })

  it('gap = renovated_year - year_built', () => {
    const r = computeComparableRenovationAgeGap([mkComp('a', 1980, 2010)])!
    expect(r.avgGap).toBe(30)
    expect(r.minGap).toBe(30)
    expect(r.maxGap).toBe(30)
  })

  it('count equals valid comps only', () => {
    const r = computeComparableRenovationAgeGap([
      mkComp('a', 1980, 2010),
      mkComp('b', 1990, null),
      mkComp('c', 1970, 2000),
    ])!
    expect(r.count).toBe(2)
  })

  it('avgGap is mean of gaps', () => {
    // gaps: 30 and 20 → avg = 25
    const r = computeComparableRenovationAgeGap([mkComp('a', 1980, 2010), mkComp('b', 1990, 2010)])!
    expect(r.avgGap).toBe(25)
  })

  it('recentlyRenovatedCount counts comps renovated ≤ 10 years ago', () => {
    const currentYear = new Date().getFullYear()
    const r = computeComparableRenovationAgeGap([
      mkComp('a', 1980, currentYear - 5),  // recent
      mkComp('b', 1970, currentYear - 15), // not recent
    ])!
    expect(r.recentlyRenovatedCount).toBe(1)
  })

  it('min and max gap correct', () => {
    const r = computeComparableRenovationAgeGap([
      mkComp('a', 1980, 2010), // gap 30
      mkComp('b', 1990, 2015), // gap 25
      mkComp('c', 2000, 2020), // gap 20
    ])!
    expect(r.minGap).toBe(20)
    expect(r.maxGap).toBe(30)
  })
})
