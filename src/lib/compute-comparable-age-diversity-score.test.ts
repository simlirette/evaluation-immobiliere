import { describe, it, expect } from 'vitest'
import { computeComparableAgeDiversityScore } from './compute-comparable-age-diversity-score'
import type { Comparable } from '@/types'

function mkComp(id: string, year_built: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built, renovated_year: null, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01' }
}

describe('computeComparableAgeDiversityScore', () => {
  it('returns null for fewer than 2 comps with year_built', () => {
    expect(computeComparableAgeDiversityScore([mkComp('a', 2000), mkComp('b', null)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeComparableAgeDiversityScore([])).toBeNull()
  })

  it('range = maxYear − minYear', () => {
    const comps = [mkComp('a', 1990), mkComp('b', 2010), mkComp('c', 2000)]
    expect(computeComparableAgeDiversityScore(comps)!.range).toBe(20)
  })

  it('decadeCount counts distinct decades', () => {
    const comps = [mkComp('a', 1985), mkComp('b', 1995), mkComp('c', 2005)]
    expect(computeComparableAgeDiversityScore(comps)!.decadeCount).toBe(3)
  })

  it('decadeCount = 1 when all same decade', () => {
    const comps = [mkComp('a', 2001), mkComp('b', 2005), mkComp('c', 2009)]
    expect(computeComparableAgeDiversityScore(comps)!.decadeCount).toBe(1)
  })

  it('diversity élevée for wide spread', () => {
    const comps = [mkComp('a', 1960), mkComp('b', 1980), mkComp('c', 2000), mkComp('d', 2020)]
    expect(computeComparableAgeDiversityScore(comps)!.diversity).toBe('élevée')
  })

  it('diversity faible for narrow spread', () => {
    const comps = [mkComp('a', 2010), mkComp('b', 2012)]
    expect(computeComparableAgeDiversityScore(comps)!.diversity).toBe('faible')
  })

  it('diversityScore capped at 100', () => {
    const comps = [mkComp('a', 1900), mkComp('b', 1950), mkComp('c', 2000), mkComp('d', 2024)]
    expect(computeComparableAgeDiversityScore(comps)!.diversityScore).toBeLessThanOrEqual(100)
  })

  it('count excludes nulls', () => {
    const comps = [mkComp('a', 2000), mkComp('b', null), mkComp('c', 2010)]
    expect(computeComparableAgeDiversityScore(comps)!.count).toBe(2)
  })
})
