import { describe, it, expect } from 'vitest'
import { computeComparableQualityScore } from './compute-comparable-quality-score'
import type { Comparable, Adjustment } from '@/types'

function mkComp(id: string, sale_date: string): Comparable {
  return {
    id, rank: id, address: `Addr ${id}`,
    hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null,
    garage_type: null, sale_price: 400000, sale_date,
    meta: '', price: '', date: '',
  }
}

function mkAdj(comparable_id: string, grossAdj = 0): Adjustment {
  return {
    id: comparable_id,
    comparable_id,
    comparableLabel: `Comp ${comparable_id}`,
    salePrice: 400000,
    surface_adj: grossAdj,
    year_adj: 0, condition_adj: 0, garage_adj: 0,
    adjusted: 400000 + grossAdj,
  }
}

// Recent date = 1 month ago (relative to test run); stale = 40 months ago
const now = new Date()
const recentDate = new Date(now.getFullYear(), now.getMonth() - 1, 1)
const staleDate = new Date(now.getFullYear(), now.getMonth() - 40, 1)
const RECENT = recentDate.toISOString().slice(0, 10)
const STALE = staleDate.toISOString().slice(0, 10)

describe('computeComparableQualityScore', () => {
  it('returns empty array when no comparables', () => {
    expect(computeComparableQualityScore([], [])).toEqual([])
  })

  it('excludes comparables not in adjs', () => {
    const comps = [mkComp('a', RECENT)]
    expect(computeComparableQualityScore(comps, [])).toEqual([])
  })

  it('scores recent comp with no adjustment as 10 (max)', () => {
    const comps = [mkComp('a', RECENT)]
    const adjs = [mkAdj('a', 0)]
    const result = computeComparableQualityScore(comps, adjs)
    expect(result[0].score).toBe(10)
    expect(result[0].label).toBe('excellent')
  })

  it('scores stale comp with heavy adjustment as low', () => {
    const comps = [mkComp('a', STALE)]
    // grossPct = 40%+ → adjustmentScore = 0; stale → recencyScore = 0
    const adjs = [{ ...mkAdj('a', 0), surface_adj: 400000 * 0.5 }] // 50% gross
    const result = computeComparableQualityScore(comps, adjs)
    expect(result[0].score).toBeLessThanOrEqual(2)
  })

  it('sorts results descending by score', () => {
    const comps = [mkComp('a', STALE), mkComp('b', RECENT)]
    const adjs = [mkAdj('a', 0), mkAdj('b', 0)]
    const result = computeComparableQualityScore(comps, adjs)
    expect(result[0].comparableId).toBe('b')
    expect(result[1].comparableId).toBe('a')
  })

  it('recencyScore decreases with age', () => {
    const fresh = computeComparableQualityScore([mkComp('a', RECENT)], [mkAdj('a')])[0]
    const stale = computeComparableQualityScore([mkComp('a', STALE)], [mkAdj('a')])[0]
    expect(fresh.recencyScore).toBeGreaterThan(stale.recencyScore)
  })

  it('adjustmentScore decreases with gross adjustment', () => {
    const noAdj = computeComparableQualityScore([mkComp('a', RECENT)], [mkAdj('a', 0)])[0]
    const heavyAdj = computeComparableQualityScore([mkComp('a', RECENT)], [{ ...mkAdj('a', 0), surface_adj: 400000 * 0.5 }])[0]
    expect(noAdj.adjustmentScore).toBeGreaterThan(heavyAdj.adjustmentScore)
  })

  it('label is faible when score <= 2', () => {
    const comps = [mkComp('a', STALE)]
    const adjs = [{ ...mkAdj('a', 0), surface_adj: 400000 * 0.5 }]
    const result = computeComparableQualityScore(comps, adjs)[0]
    expect(result.label).toBe('faible')
  })

  it('does not mutate inputs', () => {
    const comps = [mkComp('a', RECENT)]
    const adjs = [mkAdj('a', 0)]
    const compsCopy = JSON.parse(JSON.stringify(comps))
    computeComparableQualityScore(comps, adjs)
    expect(comps[0]).toEqual(compsCopy[0])
  })
})
