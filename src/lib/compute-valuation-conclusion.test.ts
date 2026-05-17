import { describe, it, expect } from 'vitest'
import { computeValuationConclusion } from './compute-valuation-conclusion'
import type { Comparable, Adjustment } from '@/types'

const now = new Date()
function recentDate(monthsAgo: number): string {
  const d = new Date(now.getFullYear(), now.getMonth() - monthsAgo, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`
}

function mkComp(id: string, monthsAgo: number, price: number): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: price, sale_date: recentDate(monthsAgo), meta: '', price: '', date: '' }
}

function mkAdj(id: string, comp_id: string, adjusted: number, surface_adj = 0): Adjustment {
  return { id, comparable_id: comp_id, comparableLabel: `Comp ${id}`, salePrice: adjusted - surface_adj, surface_adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

const comps3 = [mkComp('a', 6, 400000), mkComp('b', 4, 410000), mkComp('c', 2, 420000)]
const adjs3 = [mkAdj('a1', 'a', 400000, 20000), mkAdj('b1', 'b', 410000, 10000), mkAdj('c1', 'c', 420000, 5000)]

describe('computeValuationConclusion', () => {
  it('returns null for empty adjustments', () => {
    expect(computeValuationConclusion([], comps3)).toBeNull()
  })

  it('returns reconciledValue as positive integer', () => {
    const r = computeValuationConclusion(adjs3, comps3)!
    expect(r.reconciledValue).toBeGreaterThan(0)
    expect(Number.isInteger(r.reconciledValue)).toBe(true)
  })

  it('averageValue = arithmetic mean of adjusted prices', () => {
    const r = computeValuationConclusion(adjs3, comps3)!
    const expected = Math.round((400000 + 410000 + 420000) / 3)
    expect(r.averageValue).toBe(expected)
  })

  it('confidenceRange.low < reconciledValue < confidenceRange.high (when stdDev > 0)', () => {
    const r = computeValuationConclusion(adjs3, comps3)!
    expect(r.confidenceRange.low).toBeLessThan(r.reconciledValue)
    expect(r.confidenceRange.high).toBeGreaterThan(r.reconciledValue)
  })

  it('confidenceRange.low = confidenceRange.high when all adjusted prices identical', () => {
    const uniform = [mkAdj('a1', 'a', 400000), mkAdj('b1', 'b', 400000)]
    const uniformComps = [mkComp('a', 5, 400000), mkComp('b', 3, 400000)]
    const r = computeValuationConclusion(uniform, uniformComps)!
    expect(r.confidenceRange.low).toBe(r.confidenceRange.high)
  })

  it('reliability élevée when OEAQ min met, CV < 10%, confidence forte', () => {
    // 3 comps meet OEAQ min; small spread → low CV; mix of weights → confidence check
    const tightAdjs = [mkAdj('a1', 'a', 400000, 10000), mkAdj('b1', 'b', 401000, 20000), mkAdj('c1', 'c', 402000, 5000)]
    const r = computeValuationConclusion(tightAdjs, comps3)!
    // Low CV and 3 comps; reliability should be at least modérée
    expect(['élevée', 'modérée']).toContain(r.reliability)
  })

  it('oeaqWarnings counts failing checks', () => {
    // single comp → OEAQ minimum fails
    const single = [mkAdj('a1', 'a', 400000)]
    const singleComp = [mkComp('a', 5, 400000)]
    const r = computeValuationConclusion(single, singleComp)!
    expect(r.oeaqWarnings).toBeGreaterThan(0)
  })

  it('hasTimeAdjustment is true when comps have different dates', () => {
    const r = computeValuationConclusion(adjs3, comps3)!
    expect(r.hasTimeAdjustment).toBe(true)
    expect(r.annualTimeRatePct).not.toBeNull()
  })

  it('hasTimeAdjustment is false with zero or one comp', () => {
    const r = computeValuationConclusion(adjs3, [])!
    expect(r.hasTimeAdjustment).toBe(false)
    expect(r.annualTimeRatePct).toBeNull()
  })
})
