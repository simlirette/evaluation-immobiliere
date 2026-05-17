import { describe, it, expect } from 'vitest'
import { computeNeighborhoodComparability } from './compute-neighborhood-comparability'
import type { Comparable, Adjustment } from '@/types'

function mkComp(id: string, saleDate: string, salePrice: number): Comparable {
  return { id, rank: id, address: `addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: 2000, renovated_year: null, garage_type: null, sale_price: salePrice, sale_date: saleDate, meta: '', price: '', date: '' }
}

function mkAdj(id: string, salePrice: number, grossAdj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: grossAdj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + grossAdj }
}

const recentDate = new Date().toISOString().slice(0, 10)

describe('computeNeighborhoodComparability', () => {
  it('returns null for < 2 adjustments', () => {
    const comp = mkComp('a', recentDate, 400000)
    expect(computeNeighborhoodComparability([comp], [mkAdj('a', 400000, 0)])).toBeNull()
  })

  it('returns null for empty comparables', () => {
    expect(computeNeighborhoodComparability([], [mkAdj('a', 400000, 0), mkAdj('b', 410000, 0)])).toBeNull()
  })

  it('recencyScore 100 when all comps are recent', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 0)]
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.recencyScore).toBe(100)
  })

  it('recencyScore 0 when all comps are stale (> 24 months)', () => {
    const staleDate = `${new Date().getFullYear() - 3}-01-01`
    const comps = [mkComp('a', staleDate, 400000), mkComp('b', staleDate, 400000)]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 0)]
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.recencyScore).toBe(0)
  })

  it('concentrationScore 100 when all prices identical (CV=0)', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 0)]
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.concentrationScore).toBe(100)
  })

  it('adjustmentScore 100 when gross adjustments are zero', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 0)]
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.adjustmentScore).toBe(100)
  })

  it('adjustmentScore 0 when gross adj >= 20% of sale price', () => {
    // avgGrossPct=20, 100-20*5=0
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a', 400000, 80000), mkAdj('b', 400000, 80000)] // 20%
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.adjustmentScore).toBe(0)
  })

  it('strength forte when score >= 70', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 0)]
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.strength).toBe('forte')
    expect(r.score).toBeGreaterThanOrEqual(70)
  })

  it('strength faible when score < 40 (stale + dispersed + large adj)', () => {
    const staleDate = `${new Date().getFullYear() - 3}-01-01`
    const comps = [mkComp('a', staleDate, 300000), mkComp('b', staleDate, 600000)]
    // CV = huge, recency 0, large adj
    const adjs = [mkAdj('a', 300000, 60000), mkAdj('b', 600000, 120000)] // 20%
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.strength).toBe('faible')
    expect(r.score).toBeLessThan(40)
  })

  it('score is average of 3 sub-scores', () => {
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400000)]
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 400000, 0)]
    const r = computeNeighborhoodComparability(comps, adjs)!
    expect(r.score).toBe(Math.round((r.recencyScore + r.concentrationScore + r.adjustmentScore) / 3))
  })
})
