import { describe, it, expect } from 'vitest'
import { computeReconciliationConcentration } from './compute-reconciliation-concentration'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const totalAdj = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + totalAdj }
}

describe('computeReconciliationConcentration', () => {
  it('returns null for fewer than 2 adjustments', () => {
    expect(computeReconciliationConcentration([mkAdj('a', 0, 0, 0, 0)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeReconciliationConcentration([])).toBeNull()
  })

  it('weights sum to ~100', () => {
    const adjs = [mkAdj('a', 0, 0, 0, 0), mkAdj('b', 0, 0, 0, 0)]
    const r = computeReconciliationConcentration(adjs)!
    const total = Object.values(r.weights).reduce((s, w) => s + w, 0)
    expect(Math.round(total)).toBe(100)
  })

  it('equal weights when same gross adj → hhi = 1/n', () => {
    // All zero adj → equal weights
    const adjs = [mkAdj('a', 0, 0, 0, 0), mkAdj('b', 0, 0, 0, 0), mkAdj('c', 0, 0, 0, 0), mkAdj('d', 0, 0, 0, 0)]
    const r = computeReconciliationConcentration(adjs)!
    expect(r.hhi).toBeCloseTo(1 / 4, 1)
    expect(r.concentrated).toBe(false)
  })

  it('concentrated true when one comp carries > 40% weight', () => {
    // One comp has zero adj (high weight), others have large adj (low weight)
    const adjs = [
      mkAdj('a', 0, 0, 0, 0),         // grossPct ≈ 0 → weight ≈ 1/(0+1) = 1 → very high weight
      mkAdj('b', 80000, 0, 0, 0),     // grossPct = 20% → weight = 1/21 ≈ 0.048
      mkAdj('c', 80000, 0, 0, 0),
      mkAdj('d', 80000, 0, 0, 0),
    ]
    const r = computeReconciliationConcentration(adjs)!
    expect(r.concentrated).toBe(true)
    expect(r.maxWeightId).toBe('a')
  })

  it('maxWeightId is the adjustment with highest weight', () => {
    const adjs = [mkAdj('a', 0, 0, 0, 0), mkAdj('b', 50000, 0, 0, 0)]
    const r = computeReconciliationConcentration(adjs)!
    expect(r.maxWeightId).toBe('a')
    expect(r.maxWeightPct).toBeGreaterThan(50)
  })

  it('hhi between 0 and 1', () => {
    const adjs = [mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 10000, 0, 0, 0), mkAdj('c', 15000, 0, 0, 0)]
    const r = computeReconciliationConcentration(adjs)!
    expect(r.hhi).toBeGreaterThan(0)
    expect(r.hhi).toBeLessThanOrEqual(1)
  })
})
