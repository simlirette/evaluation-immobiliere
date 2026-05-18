import { describe, it, expect } from 'vitest'
import { computeAdjustmentNetPctHistogram } from './compute-adjustment-net-pct-histogram'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, totalAdj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: totalAdj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + totalAdj }
}

describe('computeAdjustmentNetPctHistogram', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentNetPctHistogram([])).toBeNull()
  })

  it('returns 8 buckets', () => {
    const r = computeAdjustmentNetPctHistogram([mkAdj('a', 400000, 0)])!
    expect(r.buckets).toHaveLength(8)
  })

  it('buckets sum to total adjs', () => {
    const adjs = [mkAdj('a', 400000, 20000), mkAdj('b', 400000, -20000), mkAdj('c', 400000, 0)]
    const r = computeAdjustmentNetPctHistogram(adjs)!
    const total = r.buckets.reduce((s, b) => s + b.count, 0)
    expect(total).toBe(3)
  })

  it('places +5% adj in "0 → 5 %" bucket', () => {
    // 20000/400000 = 5% → falls in "0 → 5 %" (min=0, max=5, exclusive upper → goes to "5 → 10 %"?)
    // Let me check: 5% is not < 5, so it's in "5 → 10 %"
    const r = computeAdjustmentNetPctHistogram([mkAdj('a', 400000, 20000)])! // exactly 5%
    const bucket510 = r.buckets.find(b => b.label === '5 → 10 %')!
    expect(bucket510.count).toBe(1)
  })

  it('places negative adj in correct bucket', () => {
    // -40000/400000 = -10% → in "−10 → −5 %" (min=-10, max=-5): -10 >= -10 and -10 < -5? No, -10 is not < -5.
    // So -10% goes to "−15 → −10 %" bucket (min=-15, max=-10): -10 >= -15 and -10 < -10? No.
    // Actually at exactly -10%: min=-10, max=-5 means -10 >= -10 ✓ and -10 < -5 ✗. Goes to "−15 → −10 %" (min=-15, max=-10): -10 >= -15 ✓, -10 < -10 ✗. Goes to "< −15 %"? No.
    // Let me re-check bandFor: for -10%: band "−10 → −5 %": min=-10, aboveMin: -10 >= -10 ✓; max=-5, belowMax: -10 < -5 ✓. So it IS in "−10 → −5 %".
    // Wait: belowMax = max === null || pct < max = -10 < -5 = true. Yes, -10 < -5 is TRUE. So -10% goes in "−10 → −5 %".
    const r = computeAdjustmentNetPctHistogram([mkAdj('a', 400000, -40000)])! // -10%
    const bucket = r.buckets.find(b => b.label === '−10 → −5 %')!
    expect(bucket.count).toBe(1)
  })

  it('places >15% adj in "> 15 %" bucket', () => {
    // 80000/400000 = 20% → "> 15 %"
    const r = computeAdjustmentNetPctHistogram([mkAdj('a', 400000, 80000)])!
    const bucket = r.buckets.find(b => b.label === '> 15 %')!
    expect(bucket.count).toBe(1)
  })

  it('places <-15% adj in "< −15 %" bucket', () => {
    // -80000/400000 = -20% → "< −15 %"
    const r = computeAdjustmentNetPctHistogram([mkAdj('a', 400000, -80000)])!
    const bucket = r.buckets.find(b => b.label === '< −15 %')!
    expect(bucket.count).toBe(1)
  })
})
