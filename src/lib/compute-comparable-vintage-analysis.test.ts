import { describe, it, expect } from 'vitest'
import { computeComparableVintageAnalysis } from './compute-comparable-vintage-analysis'
import type { Comparable } from '@/types'

function mkComp(id: string, year_built: number | null): Comparable {
  return {
    id,
    rank: id,
    address: `Addr ${id}`,
    hab_m2: 100,
    terrain_m2: null,
    year_built,
    renovated_year: null,
    garage_type: null,
    sale_price: 400000,
    sale_date: '2024-01-01',
    meta: '',
    price: '400000',
    date: '2024-01-01',
  }
}

describe('computeComparableVintageAnalysis', () => {
  it('returns null for empty array', () => {
    expect(computeComparableVintageAnalysis([])).toBeNull()
  })

  it('groups comps by decade correctly', () => {
    const comps = [
      mkComp('a', 1930),  // pre-1950
      mkComp('b', 1965),  // 1950–1979
      mkComp('c', 1990),  // 1980–1999
      mkComp('d', 2010),  // 2000–2019
      mkComp('e', 2021),  // 2020+
    ]
    const r = computeComparableVintageAnalysis(comps)!
    expect(r.groups.find(g => g.decade === 'pre-1950')!.count).toBe(1)
    expect(r.groups.find(g => g.decade === '1950–1979')!.count).toBe(1)
    expect(r.groups.find(g => g.decade === '1980–1999')!.count).toBe(1)
    expect(r.groups.find(g => g.decade === '2000–2019')!.count).toBe(1)
    expect(r.groups.find(g => g.decade === '2020+')!.count).toBe(1)
  })

  it('boundary year 1950 falls in 1950–1979', () => {
    const r = computeComparableVintageAnalysis([mkComp('a', 1950)])!
    expect(r.groups.find(g => g.decade === '1950–1979')!.count).toBe(1)
  })

  it('boundary year 1980 falls in 1980–1999', () => {
    const r = computeComparableVintageAnalysis([mkComp('a', 1980)])!
    expect(r.groups.find(g => g.decade === '1980–1999')!.count).toBe(1)
  })

  it('boundary year 2020 falls in 2020+', () => {
    const r = computeComparableVintageAnalysis([mkComp('a', 2020)])!
    expect(r.groups.find(g => g.decade === '2020+')!.count).toBe(1)
  })

  it('vintageBias false when subject has comparable within ±20 years', () => {
    const comps = [mkComp('a', 1985), mkComp('b', 1990), mkComp('c', 1995)]
    const r = computeComparableVintageAnalysis(comps, 1988)!
    expect(r.vintageBias).toBe(false)
  })

  it('vintageBias true when no comparable within ±20 years of subject', () => {
    // Subject 1930, all comps 1990+ (>60 years gap)
    const comps = [mkComp('a', 1990), mkComp('b', 2000), mkComp('c', 2010)]
    const r = computeComparableVintageAnalysis(comps, 1930)!
    expect(r.vintageBias).toBe(true)
  })

  it('vintageBias false when subjectYearBuilt not provided', () => {
    const comps = [mkComp('a', 1990), mkComp('b', 2000), mkComp('c', 2010)]
    const r = computeComparableVintageAnalysis(comps)!
    expect(r.vintageBias).toBe(false)
  })

  it('subjectDecade matches correct bucket', () => {
    const comps = [mkComp('a', 1980)]
    const r = computeComparableVintageAnalysis(comps, 1975)!
    expect(r.subjectDecade).toBe('1950–1979')
  })

  it('subjectDecade is null when subjectYearBuilt not provided', () => {
    const r = computeComparableVintageAnalysis([mkComp('a', 1990)])!
    expect(r.subjectDecade).toBeNull()
  })

  it('tracks comps with missing year_built in missingYearIds', () => {
    const comps = [mkComp('a', 1990), mkComp('b', null), mkComp('c', null)]
    const r = computeComparableVintageAnalysis(comps)!
    expect(r.missingYearIds).toEqual(['b', 'c'])
  })

  it('comps with null year_built not assigned to any decade', () => {
    const comps = [mkComp('a', null), mkComp('b', null), mkComp('c', null)]
    const r = computeComparableVintageAnalysis(comps)!
    expect(r.groups.every(g => g.count === 0)).toBe(true)
  })
})
