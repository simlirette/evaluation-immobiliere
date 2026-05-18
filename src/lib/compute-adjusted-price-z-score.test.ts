import { describe, it, expect } from 'vitest'
import { computeAdjustedPriceZScore } from './compute-adjusted-price-z-score'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 300000, surface_adj: adjusted - 300000, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustedPriceZScore', () => {
  it('returns null for < 3 adjs', () => {
    expect(computeAdjustedPriceZScore([])).toBeNull()
    expect(computeAdjustedPriceZScore([mkAdj('a', 300000), mkAdj('b', 310000)])).toBeNull()
  })

  it('zScore = 0 for mean-valued comp', () => {
    // mean = 300000; comp at 300000 → z = 0
    const r = computeAdjustedPriceZScore([mkAdj('a', 290000), mkAdj('b', 300000), mkAdj('c', 310000)])!
    const mid = r.entries.find(e => e.id === 'b')!
    expect(mid.zScore).toBeCloseTo(0, 5)
  })

  it('positive zScore above mean, negative below', () => {
    const r = computeAdjustedPriceZScore([mkAdj('a', 290000), mkAdj('b', 300000), mkAdj('c', 310000)])!
    const above = r.entries.find(e => e.id === 'c')!
    const below = r.entries.find(e => e.id === 'a')!
    expect(above.zScore).toBeGreaterThan(0)
    expect(below.zScore).toBeLessThan(0)
  })

  it('outlierIds contains comp with |z| > 2', () => {
    // extreme outlier far from others → |z| > 2
    const r = computeAdjustedPriceZScore([
      mkAdj('a', 300000), mkAdj('b', 300000), mkAdj('c', 300000),
      mkAdj('d', 300000), mkAdj('e', 300000), mkAdj('outlier', 900000),
    ])!
    expect(r.outlierIds).toContain('outlier')
  })

  it('outlierIds empty when no outliers', () => {
    const r = computeAdjustedPriceZScore([mkAdj('a', 290000), mkAdj('b', 300000), mkAdj('c', 310000)])!
    expect(r.outlierIds).toHaveLength(0)
  })

  it('all zScores = 0 when all prices identical', () => {
    const r = computeAdjustedPriceZScore([mkAdj('a', 300000), mkAdj('b', 300000), mkAdj('c', 300000)])!
    expect(r.entries.every(e => e.zScore === 0)).toBe(true)
    expect(r.stdDev).toBe(0)
  })

  it('mean correct', () => {
    const r = computeAdjustedPriceZScore([mkAdj('a', 290000), mkAdj('b', 300000), mkAdj('c', 310000)])!
    expect(r.mean).toBe(300000)
  })
})
