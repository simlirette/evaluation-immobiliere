import { describe, it, expect } from 'vitest'
import { computeAdjustmentWeightedMedian } from './compute-adjustment-weighted-median'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adjusted: number, surfAdj = 0): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: surfAdj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustmentWeightedMedian', () => {
  it('returns null for fewer than 2 adjustments', () => {
    expect(computeAdjustmentWeightedMedian([mkAdj('a', 400000, 400000)])).toBeNull()
  })

  it('simpleMedian matches unweighted median (odd count)', () => {
    // [380000, 400000, 420000] → median 400000
    const adjs = [mkAdj('a', 400000, 380000), mkAdj('b', 400000, 400000), mkAdj('c', 400000, 420000)]
    const r = computeAdjustmentWeightedMedian(adjs)!
    expect(r.simpleMedian).toBe(400000)
  })

  it('simpleMedian matches unweighted median (even count)', () => {
    // [380000, 400000, 420000, 440000] → (400000+420000)/2 = 410000
    const adjs = [mkAdj('a', 400000, 380000), mkAdj('b', 400000, 400000), mkAdj('c', 400000, 420000), mkAdj('d', 400000, 440000)]
    const r = computeAdjustmentWeightedMedian(adjs)!
    expect(r.simpleMedian).toBe(410000)
  })

  it('weightedMedian equals simpleMedian when all weights equal (no adjustments)', () => {
    // All zero adjustments → all weights 1.0 → uniform → weighted median = simple median
    const adjs = [mkAdj('a', 400000, 380000), mkAdj('b', 400000, 400000), mkAdj('c', 400000, 420000)]
    const r = computeAdjustmentWeightedMedian(adjs)!
    expect(r.weightedMedian).toBe(r.simpleMedian)
    expect(r.delta).toBe(0)
  })

  it('weightedMedian shifts toward comps with lower gross adjustments', () => {
    // a: 380000, surfAdj=0 → high weight; b: 400000, no adj → high weight; c: 420000, surfAdj=80000 (20%) → low weight
    // Low weight on c means weighted median should stay at or below 400000 (vs simple 400000)
    const adjs = [
      mkAdj('a', 400000, 380000, 0),
      mkAdj('b', 400000, 400000, 0),
      mkAdj('c', 400000, 420000, 80000), // 20% gross → low weight
    ]
    const r = computeAdjustmentWeightedMedian(adjs)!
    // Weighted median ≤ simple median (high-adj comp drags down)
    expect(r.weightedMedian).toBeLessThanOrEqual(r.simpleMedian)
  })

  it('delta = weightedMedian - simpleMedian', () => {
    const adjs = [mkAdj('a', 400000, 380000, 0), mkAdj('b', 400000, 400000, 0), mkAdj('c', 400000, 420000, 80000)]
    const r = computeAdjustmentWeightedMedian(adjs)!
    expect(r.delta).toBe(r.weightedMedian - r.simpleMedian)
  })

  it('deltaPct is 0 when weighted equals simple (odd count, equal weights)', () => {
    // 3 comps, all no adjustment → equal weights → weighted median = middle value = simple median
    const adjs = [mkAdj('a', 400000, 380000), mkAdj('b', 400000, 400000), mkAdj('c', 400000, 420000)]
    const r = computeAdjustmentWeightedMedian(adjs)!
    expect(r.weightedMedian).toBe(r.simpleMedian)
    expect(r.deltaPct).toBe(0)
  })

  it('handles 2 adjustments (minimum)', () => {
    const adjs = [mkAdj('a', 400000, 380000), mkAdj('b', 400000, 420000)]
    const r = computeAdjustmentWeightedMedian(adjs)!
    expect(r.simpleMedian).toBe(400000)
    expect(r).not.toBeNull()
  })
})
