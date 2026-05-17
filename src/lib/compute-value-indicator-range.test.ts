import { describe, it, expect } from 'vitest'
import { computeValueIndicatorRange } from './compute-value-indicator-range'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 300000, surface_adj: adjusted - 300000, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeValueIndicatorRange', () => {
  it('returns null for < 4 adjs', () => {
    expect(computeValueIndicatorRange([])).toBeNull()
    expect(computeValueIndicatorRange([mkAdj('a', 300000), mkAdj('b', 310000), mkAdj('c', 320000)])).toBeNull()
  })

  it('iqr = q3 - q1', () => {
    const adjs = [mkAdj('a', 280000), mkAdj('b', 290000), mkAdj('c', 310000), mkAdj('d', 320000)]
    const r = computeValueIndicatorRange(adjs)!
    expect(r.iqr).toBeCloseTo(r.q3 - r.q1, 5)
  })

  it('midpoint = (q1 + q3) / 2', () => {
    const adjs = [mkAdj('a', 280000), mkAdj('b', 290000), mkAdj('c', 310000), mkAdj('d', 320000)]
    const r = computeValueIndicatorRange(adjs)!
    expect(r.midpoint).toBeCloseTo((r.q1 + r.q3) / 2, 5)
  })

  it('iqrPct = iqr / midpoint × 100', () => {
    const adjs = [mkAdj('a', 280000), mkAdj('b', 290000), mkAdj('c', 310000), mkAdj('d', 320000)]
    const r = computeValueIndicatorRange(adjs)!
    expect(r.iqrPct).toBeCloseTo((r.iqr / r.midpoint) * 100, 5)
  })

  it('q1 < q3 for spread values', () => {
    const adjs = [mkAdj('a', 280000), mkAdj('b', 290000), mkAdj('c', 310000), mkAdj('d', 320000)]
    const r = computeValueIndicatorRange(adjs)!
    expect(r.q1).toBeLessThan(r.q3)
  })

  it('iqr = 0 when all adjusted prices identical', () => {
    const adjs = [mkAdj('a', 300000), mkAdj('b', 300000), mkAdj('c', 300000), mkAdj('d', 300000)]
    const r = computeValueIndicatorRange(adjs)!
    expect(r.iqr).toBe(0)
    expect(r.iqrPct).toBe(0)
  })

  it('works with 5 values', () => {
    const adjs = [mkAdj('a', 280000), mkAdj('b', 290000), mkAdj('c', 300000), mkAdj('d', 310000), mkAdj('e', 320000)]
    const r = computeValueIndicatorRange(adjs)!
    expect(r.q1).toBeGreaterThan(0)
    expect(r.q3).toBeGreaterThan(r.q1)
  })
})
