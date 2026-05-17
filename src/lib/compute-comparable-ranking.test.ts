import { describe, it, expect } from 'vitest'
import { computeComparableRanking } from './compute-comparable-ranking'
import type { Comparable, Adjustment } from '@/types'

function mkComp(id: string, sale_date: string, sale_price: number): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date, meta: '', price: '', date: '' }
}

function mkAdj(id: string, comp_id: string, adjusted: number, grossAdj = 0): Adjustment {
  return { id, comparable_id: comp_id, comparableLabel: `Comp ${id}`, salePrice: adjusted - grossAdj, surface_adj: grossAdj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

// Compute recent date so quality scores are stable
const now = new Date()
const recentDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`
const oldDate = `${now.getFullYear() - 3}-01-01`

describe('computeComparableRanking', () => {
  it('returns empty array for empty inputs', () => {
    expect(computeComparableRanking([], [])).toEqual([])
    expect(computeComparableRanking([mkComp('a', recentDate, 400000)], [])).toEqual([])
  })

  it('returns one entry per adjustment', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 410000)]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 410000)]
    expect(computeComparableRanking(comps, adjs)).toHaveLength(2)
  })

  it('ranks are assigned starting from 1', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 410000), mkComp('c', recentDate, 420000)]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 410000), mkAdj('c1', 'c', 420000)]
    const result = computeComparableRanking(comps, adjs)
    const ranks = result.map(r => r.rank).sort((a, b) => a - b)
    expect(ranks).toEqual([1, 2, 3])
  })

  it('recent comp ranks higher than old comp (same price and adj)', () => {
    const comps = [mkComp('a', oldDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 400000)]
    const result = computeComparableRanking(comps, adjs)
    const recent = result.find(r => r.comparableId === 'b')!
    const old = result.find(r => r.comparableId === 'a')!
    expect(recent.rank).toBeLessThan(old.rank)
  })

  it('outlier comp ranks lower than non-outlier', () => {
    // Need ≥3 comps for outlier detection
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 405000), mkComp('c', recentDate, 600000)]
    // c is an outlier (adjusted 700000 >> median ~402500)
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 405000), mkAdj('c1', 'c', 700000)]
    const result = computeComparableRanking(comps, adjs)
    const outlier = result.find(r => r.comparableId === 'c')!
    const normal = result.find(r => r.comparableId === 'a')!
    expect(outlier.isOutlier).toBe(true)
    expect(outlier.rank).toBeGreaterThan(normal.rank)
  })

  it('rankScore is between 0 and 100', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', oldDate, 410000)]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 410000)]
    const result = computeComparableRanking(comps, adjs)
    expect(result.every(r => r.rankScore >= 0 && r.rankScore <= 100)).toBe(true)
  })

  it('sorted by rank (rank 1 first)', () => {
    const comps = [mkComp('a', oldDate, 400000), mkComp('b', recentDate, 400000), mkComp('c', recentDate, 400000)]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 400000), mkAdj('c1', 'c', 400000)]
    const result = computeComparableRanking(comps, adjs)
    expect(result[0].rank).toBe(1)
    expect(result[result.length - 1].rank).toBe(result.length)
  })
})
