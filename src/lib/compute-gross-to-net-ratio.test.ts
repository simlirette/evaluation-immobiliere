import { describe, it, expect } from 'vitest'
import { computeGrossToNetRatio } from './compute-gross-to-net-ratio'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const totalAdj = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + totalAdj }
}

describe('computeGrossToNetRatio', () => {
  it('returns null for empty array', () => {
    expect(computeGrossToNetRatio([])).toBeNull()
  })

  it('ratio 1 when all adjustments same direction', () => {
    // gross = 10000, net = 10000 → ratio = 1
    const r = computeGrossToNetRatio([mkAdj('a', 10000, 0, 0, 0)])!
    expect(r.entries[0].ratio).toBe(1)
  })

  it('ratio > 1 when adjustments partially cancel', () => {
    // gross = |5000| + |-3000| = 8000; net = |5000 - 3000| = 2000; ratio = 4
    const r = computeGrossToNetRatio([mkAdj('a', 5000, -3000, 0, 0)])!
    expect(r.entries[0].ratio).toBe(4)
  })

  it('ratio null when net = 0 (full cancellation)', () => {
    // gross = 5000 + 5000 = 10000; net = 0 → ratio null
    const r = computeGrossToNetRatio([mkAdj('a', 5000, -5000, 0, 0)])!
    expect(r.entries[0].ratio).toBeNull()
  })

  it('highCancellationIds contains comps with ratio > 3', () => {
    // ratio = 4 > 3
    const r = computeGrossToNetRatio([mkAdj('a', 5000, -3000, 0, 0)])!
    expect(r.highCancellationIds).toContain('a')
  })

  it('highCancellationIds empty when no high cancellation', () => {
    const r = computeGrossToNetRatio([mkAdj('a', 10000, 0, 0, 0)])!
    expect(r.highCancellationIds).toHaveLength(0)
  })

  it('avgRatio is mean ratio across comps with non-zero net', () => {
    // comp a: gross=10000, net=10000, ratio=1; comp b: gross=8000, net=2000, ratio=4 → avg=2.5
    const r = computeGrossToNetRatio([mkAdj('a', 10000, 0, 0, 0), mkAdj('b', 5000, -3000, 0, 0)])!
    expect(r.avgRatio).toBe(2.5)
  })

  it('avgRatio null when all comps have zero net', () => {
    const r = computeGrossToNetRatio([mkAdj('a', 5000, -5000, 0, 0)])!
    expect(r.avgRatio).toBeNull()
  })

  it('returns one entry per adjustment', () => {
    const adjs = [mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 3000, 0, 0, 0)]
    expect(computeGrossToNetRatio(adjs)!.entries).toHaveLength(2)
  })
})
