import { describe, it, expect } from 'vitest'
import { computeComparableSimilarityScore } from './compute-comparable-similarity-score'
import type { Comparable } from '@/types'

function mkComp(id: string, hab_m2: number | null, year_built: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2, terrain_m2: null, year_built, renovated_year: null, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01' }
}

describe('computeComparableSimilarityScore', () => {
  it('returns null when subject has neither hab_m2 nor year_built', () => {
    const comps = [mkComp('a', 100, 2000)]
    expect(computeComparableSimilarityScore(comps, {})).toBeNull()
    expect(computeComparableSimilarityScore(comps, { hab_m2: null, year_built: null })).toBeNull()
  })

  it('score 100 when perfect match on both factors', () => {
    const comps = [mkComp('a', 100, 2000)]
    const r = computeComparableSimilarityScore(comps, { hab_m2: 100, year_built: 2000 })!
    expect(r[0].score).toBe(100)
  })

  it('sizeDiffPct 0 when same size', () => {
    const comps = [mkComp('a', 100, null)]
    const r = computeComparableSimilarityScore(comps, { hab_m2: 100 })!
    expect(r[0].sizeDiffPct).toBe(0)
  })

  it('score decreases as size difference grows', () => {
    const exact = computeComparableSimilarityScore([mkComp('a', 100, null)], { hab_m2: 100 })![0].score
    const similar = computeComparableSimilarityScore([mkComp('a', 110, null)], { hab_m2: 100 })![0].score
    const different = computeComparableSimilarityScore([mkComp('a', 130, null)], { hab_m2: 100 })![0].score
    expect(exact).toBeGreaterThan(similar)
    expect(similar).toBeGreaterThan(different)
  })

  it('score 0 when size diff >= 20% and age diff >= 20 years (both factors)', () => {
    // sizeDiff >= 20%, ageDiff >= 20 → sizeScore=0, ageScore=0 → score=0
    const comps = [mkComp('a', 130, 1980)]  // 30% size diff, 24 yr age diff
    const r = computeComparableSimilarityScore(comps, { hab_m2: 100, year_built: 2004 })!
    expect(r[0].score).toBe(0)
  })

  it('ageDiff null when comp has no year_built', () => {
    const comps = [mkComp('a', 100, null)]
    const r = computeComparableSimilarityScore(comps, { year_built: 2000 })!
    expect(r[0].ageDiff).toBeNull()
  })

  it('sizeDiffPct null when comp has no hab_m2', () => {
    const comps = [mkComp('a', null, 2000)]
    const r = computeComparableSimilarityScore(comps, { hab_m2: 100 })!
    expect(r[0].sizeDiffPct).toBeNull()
  })

  it('returns one entry per comparable', () => {
    const comps = [mkComp('a', 100, 2000), mkComp('b', 110, 1995), mkComp('c', 90, 2005)]
    const r = computeComparableSimilarityScore(comps, { hab_m2: 100, year_built: 2000 })!
    expect(r).toHaveLength(3)
    expect(r.map(e => e.comparableId)).toEqual(['a', 'b', 'c'])
  })

  it('when only one factor available score scaled to 0-100', () => {
    // Only hab_m2 in subject, perfect match → score = 100
    const comps = [mkComp('a', 100, null)]
    const r = computeComparableSimilarityScore(comps, { hab_m2: 100 })!
    expect(r[0].score).toBe(100)
  })
})
