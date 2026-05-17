import { describe, it, expect } from 'vitest'
import { computeAdjustedPriceStats } from './compute-adjusted-price-stats'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: id, salePrice: adjusted, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustedPriceStats', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustedPriceStats([])).toBeNull()
  })

  it('returns null for single adjustment', () => {
    expect(computeAdjustedPriceStats([mkAdj('a', 400000)])).toBeNull()
  })

  it('cv = 0 when all prices identical', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 400000), mkAdj('c', 400000)]
    const result = computeAdjustedPriceStats(adjs)!
    expect(result.cv).toBe(0)
    expect(result.cohesion).toBe('excellent')
    expect(result.stdDev).toBe(0)
  })

  it('cohesion excellent when cv < 5%', () => {
    // mean=400000, prices differ by ~4% → cv ≈ 2%
    const adjs = [mkAdj('a', 392000), mkAdj('b', 408000)]
    const result = computeAdjustedPriceStats(adjs)!
    expect(result.cohesion).toBe('excellent')
  })

  it('cohesion bon when 5% ≤ cv < 10%', () => {
    // mean=400000, values spread ±4% each → cv ≈ 5.7%
    const adjs = [mkAdj('a', 377000), mkAdj('b', 423000)]
    const result = computeAdjustedPriceStats(adjs)!
    expect(['bon', 'excellent']).toContain(result.cohesion)
  })

  it('cohesion faible when cv ≥ 15%', () => {
    // large spread
    const adjs = [mkAdj('a', 300000), mkAdj('b', 500000)]
    const result = computeAdjustedPriceStats(adjs)!
    expect(result.cv).toBeGreaterThanOrEqual(15)
    expect(result.cohesion).toBe('faible')
  })

  it('count matches number of adjustments', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 410000), mkAdj('c', 420000)]
    expect(computeAdjustedPriceStats(adjs)!.count).toBe(3)
  })

  it('mean is rounded integer', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 410000)]
    const r = computeAdjustedPriceStats(adjs)!
    expect(Number.isInteger(r.mean)).toBe(true)
    expect(r.mean).toBe(405000)
  })

  it('cv is rounded to 1 decimal', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 420000)]
    const r = computeAdjustedPriceStats(adjs)!
    expect(r.cv).toBe(Math.round(r.cv * 10) / 10)
  })
})
