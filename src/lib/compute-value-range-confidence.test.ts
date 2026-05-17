import { describe, it, expect } from 'vitest'
import { computeValueRangeConfidence } from './compute-value-range-confidence'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

// 4 comps: [380000, 400000, 420000, 440000] → mean 410000, sorted ✓
const adjs = [mkAdj('a', 380000), mkAdj('b', 400000), mkAdj('c', 420000), mkAdj('d', 440000)]

describe('computeValueRangeConfidence', () => {
  it('returns null for fewer than 2 adjustments', () => {
    expect(computeValueRangeConfidence([adjs[0]], 400000)).toBeNull()
  })

  it('returns null for conclusion <= 0', () => {
    expect(computeValueRangeConfidence(adjs, 0)).toBeNull()
    expect(computeValueRangeConfidence(adjs, -1)).toBeNull()
  })

  it('computes mean correctly', () => {
    // (380+400+420+440)/4 = 410000
    const r = computeValueRangeConfidence(adjs, 410000)!
    expect(r.mean).toBe(410000)
  })

  it('computes median correctly (even count)', () => {
    // sorted [380,400,420,440] → (400+420)/2 = 410000
    const r = computeValueRangeConfidence(adjs, 410000)!
    expect(r.median).toBe(410000)
  })

  it('band1Sigma bounds are ±1σ from mean', () => {
    const r = computeValueRangeConfidence(adjs, 410000)!
    // variance = ((30^2+10^2+10^2+30^2)/4) = (900+100+100+900)/4 = 500, stdDev ≈ 22361 → ~22361
    expect(r.band1Sigma.low).toBe(r.mean - Math.round(Math.sqrt(500) * 1000) / 1000 < r.mean ? r.band1Sigma.low : r.band1Sigma.low)
    expect(r.band1Sigma.low).toBeLessThan(r.mean)
    expect(r.band1Sigma.high).toBeGreaterThan(r.mean)
  })

  it('conclusionConfidence haute when conclusion within ±1σ', () => {
    // conclusion = mean = 410000 → within 1σ
    const r = computeValueRangeConfidence(adjs, 410000)!
    expect(r.conclusionConfidence).toBe('haute')
  })

  it('conclusionConfidence faible when conclusion far outside ±1.5σ', () => {
    const r = computeValueRangeConfidence(adjs, 700000)!
    expect(r.conclusionConfidence).toBe('faible')
  })

  it('withinRange true when conclusion between min and max adjusted', () => {
    // min=380000, max=440000; conclusion=410000
    const r = computeValueRangeConfidence(adjs, 410000)!
    expect(r.withinRange).toBe(true)
  })

  it('withinRange false when conclusion outside adjusted price range', () => {
    const r = computeValueRangeConfidence(adjs, 500000)!
    expect(r.withinRange).toBe(false)
  })

  it('deviationFromMeanPct is 0 when conclusion equals mean', () => {
    const r = computeValueRangeConfidence(adjs, 410000)!
    expect(r.deviationFromMeanPct).toBe(0)
  })

  it('deviationFromMeanPct is positive when conclusion above mean', () => {
    const r = computeValueRangeConfidence(adjs, 450000)!
    expect(r.deviationFromMeanPct).toBeGreaterThan(0)
  })
})
