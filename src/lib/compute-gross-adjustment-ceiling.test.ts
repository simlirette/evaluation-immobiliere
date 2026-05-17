import { describe, it, expect } from 'vitest'
import { computeGrossAdjustmentCeiling } from './compute-gross-adjustment-ceiling'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface: number, year = 0, condition = 0, garage = 0): Adjustment {
  return {
    id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice,
    surface_adj: surface, year_adj: year, condition_adj: condition, garage_adj: garage,
    adjusted: salePrice + surface + year + condition + garage,
  }
}

describe('computeGrossAdjustmentCeiling', () => {
  it('returns null for empty adjustments', () => {
    expect(computeGrossAdjustmentCeiling([])).toBeNull()
  })

  it('compliant when all adjustments under ceiling', () => {
    // 10% surface, 5% year — total 15%, both under ceiling
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, 40000, 20000)])!
    expect(r.compliant).toBe(true)
    expect(r.violationCount).toBe(0)
  })

  it('exceedsLineCeiling when surface adj > 15%', () => {
    // 70000/400000 = 17.5% → exceeds 15% line ceiling
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, 70000)])!
    expect(r.entries[0].exceedsLineCeiling).toBe(true)
    expect(r.entries[0].hasViolation).toBe(true)
  })

  it('exceedsTotalCeiling when total gross > 25%', () => {
    // 50000+60000 = 110000/400000 = 27.5% → exceeds total
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, 50000, 60000)])!
    expect(r.entries[0].exceedsTotalCeiling).toBe(true)
    expect(r.entries[0].hasViolation).toBe(true)
  })

  it('no violation at exactly 15% line', () => {
    // 60000/400000 = 15% — exactly at ceiling → not a violation (> not >=)
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, 60000)])!
    expect(r.entries[0].exceedsLineCeiling).toBe(false)
  })

  it('no violation at exactly 25% total', () => {
    // 100000/400000 = 25% → not a violation
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, 60000, 40000)])!
    expect(r.entries[0].exceedsTotalCeiling).toBe(false)
  })

  it('violationCount counts only comps with violations', () => {
    const adjs = [
      mkAdj('a', 400000, 70000),   // 17.5% line — violation
      mkAdj('b', 400000, 20000),   // 5% — no violation
    ]
    const r = computeGrossAdjustmentCeiling(adjs)!
    expect(r.violationCount).toBe(1)
    expect(r.compliant).toBe(false)
  })

  it('avgTotalGrossPct is mean of all totalGrossPct', () => {
    // a: 10%, b: 20% → avg 15%
    const adjs = [mkAdj('a', 400000, 40000), mkAdj('b', 400000, 80000)]
    const r = computeGrossAdjustmentCeiling(adjs)!
    expect(r.avgTotalGrossPct).toBe(15)
  })

  it('surfacePct rounds to 1 decimal', () => {
    // 33000/400000 = 8.25% → 8.3%
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, 33000)])!
    expect(r.entries[0].surfacePct).toBeCloseTo(8.3, 1)
  })

  it('handles negative adjustments (uses abs)', () => {
    const r = computeGrossAdjustmentCeiling([mkAdj('a', 400000, -70000)])!
    expect(r.entries[0].exceedsLineCeiling).toBe(true)
  })
})
