import { describe, it, expect } from 'vitest'
import { computeWeightedAdjustedMean } from './compute-weighted-adjusted-mean'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface_adj: number, year_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj: 0, garage_adj: 0, adjusted: salePrice + surface_adj + year_adj }
}

describe('computeWeightedAdjustedMean', () => {
  it('returns null for fewer than 2 adjustments', () => {
    expect(computeWeightedAdjustedMean([mkAdj('a', 400000, 0, 0)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeWeightedAdjustedMean([])).toBeNull()
  })

  it('weightedMean equals reconciledValue', () => {
    const adjs = [mkAdj('a', 400000, 5000, 0), mkAdj('b', 380000, -3000, 2000)]
    const r = computeWeightedAdjustedMean(adjs)!
    expect(r.weightedMean).toBe(r.reconciledValue)
  })

  it('deltaVsReconciledPct is 0 (weightedMean = reconciledValue by construction)', () => {
    const adjs = [mkAdj('a', 400000, 5000, 0), mkAdj('b', 420000, -2000, 0), mkAdj('c', 390000, 0, 3000)]
    expect(computeWeightedAdjustedMean(adjs)!.deltaVsReconciledPct).toBe(0)
  })

  it('simpleMean is unweighted mean of adjusted prices', () => {
    const adjs = [mkAdj('a', 400000, 0, 0), mkAdj('b', 500000, 0, 0)]
    expect(computeWeightedAdjustedMean(adjs)!.simpleMean).toBe(450000)
  })

  it('deltaVsSimplePct positive when high-quality comps above average', () => {
    // comp 'a' zero adj (high weight), adjusted = 500000; comp 'b' large adj (low weight), adjusted = 300000
    const adjs = [mkAdj('a', 500000, 0, 0), mkAdj('b', 400000, -100000, 0)]
    const r = computeWeightedAdjustedMean(adjs)!
    // simpleMean = (500000 + 300000) / 2 = 400000
    // weightedMean favors 'a' → above 400000
    expect(r.deltaVsSimplePct).toBeGreaterThan(0)
  })

  it('equal adjustments → weightedMean equals simpleMean', () => {
    // all zero adj → equal weights → same result
    const adjs = [mkAdj('a', 400000, 0, 0), mkAdj('b', 500000, 0, 0), mkAdj('c', 450000, 0, 0)]
    const r = computeWeightedAdjustedMean(adjs)!
    expect(r.deltaVsSimplePct).toBe(0)
  })
})
