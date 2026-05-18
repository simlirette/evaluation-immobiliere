import { describe, it, expect } from 'vitest'
import { computeGrossAdjustmentOEAQCheck } from './compute-gross-adjustment-oeaq-check'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface_adj: number, year_adj = 0, condition_adj = 0, garage_adj = 0): Adjustment {
  const adjusted = salePrice + surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj, garage_adj, adjusted }
}

describe('computeGrossAdjustmentOEAQCheck', () => {
  it('returns null for empty array', () => {
    expect(computeGrossAdjustmentOEAQCheck([])).toBeNull()
  })

  it('returns entry for single adj', () => {
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, 20000)])!
    expect(r.entries).toHaveLength(1)
  })

  it('grossPct = sum of |all 4 types| / salePrice × 100', () => {
    // |10000| + |5000| + |3000| + |2000| = 20000 / 400000 = 5%
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, 10000, 5000, 3000, 2000)])!
    expect(r.entries[0].grossPct).toBeCloseTo(5, 5)
  })

  it('violation = false when grossPct <= 25', () => {
    // 100000/400000 = 25% → not > 25, so no violation
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, 100000)])!
    expect(r.entries[0].violation).toBe(false)
  })

  it('violation = true when grossPct > 25', () => {
    // 101000/400000 = 25.25% → violation
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, 101000)])!
    expect(r.entries[0].violation).toBe(true)
  })

  it('violationCount counts violations', () => {
    const r = computeGrossAdjustmentOEAQCheck([
      mkAdj('a', 400000, 101000),  // 25.25% → violation
      mkAdj('b', 400000, 20000),   // 5% → ok
      mkAdj('c', 400000, 110000),  // 27.5% → violation
    ])!
    expect(r.violationCount).toBe(2)
  })

  it('compliant = true when no violations', () => {
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, 20000)])!
    expect(r.compliant).toBe(true)
  })

  it('compliant = false when any violation', () => {
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, 101000)])!
    expect(r.compliant).toBe(false)
  })

  it('uses absolute value of negative adj', () => {
    // |-101000| / 400000 = 25.25% → violation
    const r = computeGrossAdjustmentOEAQCheck([mkAdj('a', 400000, -101000)])!
    expect(r.entries[0].violation).toBe(true)
  })
})
