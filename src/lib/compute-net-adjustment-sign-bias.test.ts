import { describe, it, expect } from 'vitest'
import { computeNetAdjustmentSignBias } from './compute-net-adjustment-sign-bias'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, totalAdj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: totalAdj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + totalAdj }
}

describe('computeNetAdjustmentSignBias', () => {
  it('returns null for empty array', () => {
    expect(computeNetAdjustmentSignBias([])).toBeNull()
  })

  it('upward when net adj > 1% of salePrice positive', () => {
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, 20000)])!
    expect(r.countUpward).toBe(1)
    expect(r.countDownward).toBe(0)
  })

  it('downward when net adj > 1% negative', () => {
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, -20000)])!
    expect(r.countDownward).toBe(1)
    expect(r.countUpward).toBe(0)
  })

  it('neutral when |net adj| < 1% of salePrice', () => {
    // 1% of 400000 = 4000; adj = 3000 → neutral
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, 3000)])!
    expect(r.countNeutral).toBe(1)
  })

  it('biased true when dominant direction ≥ 70%', () => {
    // 3 upward out of 3 → 100% → biased
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, 20000), mkAdj('b', 400000, 15000), mkAdj('c', 400000, 10000)])!
    expect(r.biased).toBe(true)
    expect(r.dominantDirection).toBe('upward')
  })

  it('biased false when no direction reaches 70%', () => {
    // 2 up, 2 down → 50% each
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, 20000), mkAdj('b', 400000, 15000), mkAdj('c', 400000, -20000), mkAdj('d', 400000, -15000)])!
    expect(r.biased).toBe(false)
  })

  it('dominancePct reflects dominant count / total × 100', () => {
    // 3 upward, 1 downward → 75%
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, 20000), mkAdj('b', 400000, 15000), mkAdj('c', 400000, 10000), mkAdj('d', 400000, -20000)])!
    expect(r.dominancePct).toBeCloseTo(75, 0)
  })

  it('dominantDirection neutral when neutral is most common', () => {
    const r = computeNetAdjustmentSignBias([mkAdj('a', 400000, 1000), mkAdj('b', 400000, 2000), mkAdj('c', 400000, 20000)])!
    expect(r.dominantDirection).toBe('neutral')
  })
})
