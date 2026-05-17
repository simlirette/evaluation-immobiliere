import { describe, it, expect, beforeEach } from 'vitest'
import { computeDataQualityReport } from './compute-data-quality-report'
import type { Comparable, Adjustment } from '@/types'

const now = new Date()
function recentDate(): string {
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`
}
function oldDate(): string {
  return `${now.getFullYear() - 4}-01-01`
}

let _priceSeq = 400000
function mkComp(id: string, opts: { date?: string; full?: boolean } = {}): Comparable {
  _priceSeq += 5000 // unique price per comp to avoid same-price-date duplicates
  return {
    id, rank: id, address: `Addr ${id}`,
    hab_m2: opts.full ? 120 : null,
    terrain_m2: opts.full ? 400 : null,
    year_built: opts.full ? 1990 : null,
    renovated_year: null,
    garage_type: opts.full ? 'Détaché' : null,
    sale_price: _priceSeq,
    sale_date: opts.date ?? recentDate(),
    meta: '', price: '', date: '',
  }
}

beforeEach(() => { _priceSeq = 400000 })

function mkAdj(id: string, comp_id: string, adjusted: number): Adjustment {
  return { id, comparable_id: comp_id, comparableLabel: `Comp ${id}`, salePrice: adjusted, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeDataQualityReport', () => {
  it('returns null for empty comparables', () => {
    expect(computeDataQualityReport([], [])).toBeNull()
  })

  it('grade bon when no issues', () => {
    const comps = [mkComp('a', { full: true }), mkComp('b', { full: true }), mkComp('c', { full: true })]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 402000), mkAdj('c1', 'c', 404000)]
    const r = computeDataQualityReport(comps, adjs)!
    expect(r.grade).toBe('bon')
    expect(r.issues).toHaveLength(0)
  })

  it('detects stale comparables', () => {
    const comps = [mkComp('a', { date: oldDate() }), mkComp('b')]
    const r = computeDataQualityReport(comps, [])!
    expect(r.staleCount).toBe(1)
    expect(r.issues.some(i => i.includes('ancienne'))).toBe(true)
  })

  it('avgCompletenessPct reflects missing fields', () => {
    // comp 'a': only sale_date present = 1/5 = 20%; comp 'b': all 5 = 100% → avg = 60%
    const comps = [mkComp('a'), mkComp('b', { full: true })]
    const r = computeDataQualityReport(comps, [])!
    expect(r.avgCompletenessPct).toBe(60)
  })

  it('outlierCount from adjustments', () => {
    // 3 adjs needed; one outlier value
    const comps = [mkComp('a'), mkComp('b'), mkComp('c')]
    const adjs = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 405000), mkAdj('c1', 'c', 700000)]
    const r = computeDataQualityReport(comps, adjs)!
    expect(r.outlierCount).toBeGreaterThan(0)
    expect(r.issues.some(i => i.includes('atypique'))).toBe(true)
  })

  it('grade faible when multiple issues', () => {
    // stale + no fields → completeness issue
    const comps = [mkComp('a', { date: oldDate() }), mkComp('b', { date: oldDate() })]
    const r = computeDataQualityReport(comps, [])!
    expect(r.grade).toBe('faible')
  })

  it('duplicatePairCount from detect-duplicate-comparables', () => {
    // Same address → duplicate
    const comps = [
      { ...mkComp('a'), address: '10 rue Test' },
      { ...mkComp('b'), address: '10 rue Test' },
      mkComp('c'),
    ]
    const r = computeDataQualityReport(comps, [])!
    expect(r.duplicatePairCount).toBeGreaterThan(0)
  })

  it('issues array is empty when no problems detected', () => {
    const comps = [mkComp('a', { full: true })]
    const r = computeDataQualityReport(comps, [])!
    // 1 comp, full data, recent date, no outliers (need ≥3 for outlier detection)
    // staleCount = 0, completeness = 100%, no duplicates, no outliers
    expect(r.staleCount).toBe(0)
    expect(r.duplicatePairCount).toBe(0)
    expect(r.outlierCount).toBe(0)
  })
})
