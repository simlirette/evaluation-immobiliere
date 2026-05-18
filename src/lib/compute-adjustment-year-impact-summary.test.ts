import { describe, it, expect } from 'vitest'
import { computeAdjustmentYearImpactSummary } from './compute-adjustment-year-impact-summary'
import type { Adjustment } from '@/types'

function mkAdj(id: string, year_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: 0, year_adj, condition_adj: 0, garage_adj: 0, adjusted: 400000 + year_adj }
}

describe('computeAdjustmentYearImpactSummary', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentYearImpactSummary([])).toBeNull()
  })

  it('totalImpact is sum of all year_adj', () => {
    const r = computeAdjustmentYearImpactSummary([mkAdj('a', 10000), mkAdj('b', 5000)])!
    expect(r.totalImpact).toBe(15000)
  })

  it('totalImpact negative when adjustments are negative', () => {
    const r = computeAdjustmentYearImpactSummary([mkAdj('a', -10000), mkAdj('b', -5000)])!
    expect(r.totalImpact).toBe(-15000)
  })

  it('avgPerComp = totalImpact / count', () => {
    const r = computeAdjustmentYearImpactSummary([mkAdj('a', 10000), mkAdj('b', 5000)])!
    expect(r.avgPerComp).toBe(7500)
  })

  it('maxAbsId is the comp with largest |year_adj|', () => {
    const r = computeAdjustmentYearImpactSummary([mkAdj('a', 5000), mkAdj('b', -12000), mkAdj('c', 8000)])!
    expect(r.maxAbsId).toBe('b')
    expect(r.maxAbsValue).toBe(-12000)
  })

  it('dominantDirection positive when most comps have positive year_adj', () => {
    const r = computeAdjustmentYearImpactSummary([mkAdj('a', 10000), mkAdj('b', 5000), mkAdj('c', -3000)])!
    expect(r.dominantDirection).toBe('positive')
  })

  it('dominantDirection neutral when zero most common', () => {
    const r = computeAdjustmentYearImpactSummary([mkAdj('a', 0), mkAdj('b', 0), mkAdj('c', 5000)])!
    expect(r.dominantDirection).toBe('neutral')
  })
})
