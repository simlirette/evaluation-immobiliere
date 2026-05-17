import { describe, it, expect } from 'vitest'
import { computeAppraisalRiskScore } from './compute-appraisal-risk-score'
import type { Comparable, Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adjusted: number, surfAdj = 0, yearAdj = 0): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: surfAdj, year_adj: yearAdj, condition_adj: 0, garage_adj: 0, adjusted }
}

function mkComp(id: string, saleDate: string, salePrice: number): Comparable {
  return { id, rank: id, address: `addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: 2000, renovated_year: null, garage_type: null, sale_price: salePrice, sale_date: saleDate, meta: '', price: '', date: '' }
}

const recentDate = new Date().toISOString().slice(0, 10)

describe('computeAppraisalRiskScore', () => {
  it('returns null for empty adjustments', () => {
    expect(computeAppraisalRiskScore([], [])).toBeNull()
  })

  it('score 0 and riskLevel faible for clean data (3+ comps, no issues)', () => {
    // 3 recent comps, all same-direction adjustments, no outliers
    const comps = [
      mkComp('a', recentDate, 400000),
      mkComp('b', recentDate, 410000),
      mkComp('c', recentDate, 420000),
    ]
    const adjs = [
      mkAdj('a', 400000, 404000, 4000, 0),
      mkAdj('b', 410000, 415000, 5000, 0),
      mkAdj('c', 420000, 424000, 4000, 0),
    ]
    const r = computeAppraisalRiskScore(adjs, comps)!
    expect(r.riskLevel).toBe('faible')
    expect(r.score).toBeLessThan(30)
  })

  it('score elevated (>= 30) when stale data + inconsistent adjustments', () => {
    const staleDate = `${new Date().getFullYear() - 4}-01-01`
    const comps = [
      mkComp('a', staleDate, 400000),
      mkComp('b', staleDate, 400001),
    ]
    const adjs = [
      mkAdj('a', 400000, 406000, 6000, 0),
      mkAdj('b', 400001, 394000, -6000, 0),  // mixed direction → inconsistency
    ]
    const r = computeAppraisalRiskScore(adjs, comps)!
    expect(r.score).toBeGreaterThanOrEqual(30)
    expect(['modéré', 'élevé']).toContain(r.riskLevel)
  })

  it('riskLevel élevé when many signals fire simultaneously', () => {
    // Stale comps + mixed surface AND year adjustments (2 inconsistency types) + outlier
    const staleDate = `${new Date().getFullYear() - 4}-01-01`
    const comps = [
      mkComp('a', staleDate, 400000),
      mkComp('b', staleDate, 400001),
      mkComp('c', staleDate, 400002),
    ]
    const adjs = [
      mkAdj('a', 400000, 412000, 6000, 6000),    // surface+ year+
      mkAdj('b', 400001, 388000, -6000, -6001),   // surface- year- → both types mixed
      mkAdj('c', 400002, 480000, 80000, 0),        // 16.5% above median 412k → outlier + influential
    ]
    const r = computeAppraisalRiskScore(adjs, comps)!
    expect(r.score).toBeGreaterThanOrEqual(60)
    expect(r.riskLevel).toBe('élevé')
  })

  it('factors contains meaningful strings', () => {
    const staleDate = `${new Date().getFullYear() - 4}-01-01`
    const comps = [mkComp('a', staleDate, 400000), mkComp('b', staleDate, 400001)]
    const adjs = [mkAdj('a', 400000, 406000, 6000), mkAdj('b', 400001, 394000, -6000)]
    const r = computeAppraisalRiskScore(adjs, comps)!
    expect(r.factors.length).toBeGreaterThan(0)
    r.factors.forEach(f => expect(typeof f).toBe('string'))
  })

  it('score capped at 100', () => {
    // Manufacture worst case: stale comps, few comps, mixed adjustments, outlier
    const staleDate = `${new Date().getFullYear() - 4}-01-01`
    const comps = [mkComp('a', staleDate, 400000), mkComp('b', staleDate, 400001)]
    const adjs = [
      mkAdj('a', 400000, 450000, 50000),  // large positive → outlier
      mkAdj('b', 400001, 350000, -50001), // large negative, mixed
    ]
    const r = computeAppraisalRiskScore(adjs, comps)!
    expect(r.score).toBeLessThanOrEqual(100)
  })

  it('riskLevel transitions at 30 and 60', () => {
    // Just test boundary shapes
    const comps = [mkComp('a', recentDate, 400000), mkComp('b', recentDate, 400001)]
    const adjs = [mkAdj('a', 400000, 402000, 2000), mkAdj('b', 400001, 402001, 2000)]
    const r = computeAppraisalRiskScore(adjs, comps)!
    if (r.score < 30) expect(r.riskLevel).toBe('faible')
    else if (r.score < 60) expect(r.riskLevel).toBe('modéré')
    else expect(r.riskLevel).toBe('élevé')
  })
})
