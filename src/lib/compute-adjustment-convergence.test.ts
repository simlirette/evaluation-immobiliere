import { describe, it, expect } from 'vitest'
import { computeAdjustmentConvergence } from './compute-adjustment-convergence'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustmentConvergence', () => {
  it('returns null for fewer than 3 adjustments', () => {
    expect(computeAdjustmentConvergence([mkAdj('a', 400000, 410000), mkAdj('b', 420000, 415000)])).toBeNull()
  })

  it('converged true when adjustedCv < rawCv', () => {
    // Raw: 300k, 500k, 700k — high spread; adjusted all near 500k — low spread
    const adjs = [mkAdj('a', 300000, 490000), mkAdj('b', 500000, 500000), mkAdj('c', 700000, 510000)]
    const r = computeAdjustmentConvergence(adjs)!
    expect(r.converged).toBe(true)
    expect(r.adjustedCv).toBeLessThan(r.rawCv)
  })

  it('converged false when adjustments widen spread', () => {
    // Raw: 490k, 500k, 510k — tight; adjusted: 300k, 500k, 700k — wide
    const adjs = [mkAdj('a', 490000, 300000), mkAdj('b', 500000, 500000), mkAdj('c', 510000, 700000)]
    const r = computeAdjustmentConvergence(adjs)!
    expect(r.converged).toBe(false)
    expect(r.adjustedCv).toBeGreaterThan(r.rawCv)
  })

  it('convergencePct positive when converged', () => {
    const adjs = [mkAdj('a', 300000, 490000), mkAdj('b', 500000, 500000), mkAdj('c', 700000, 510000)]
    expect(computeAdjustmentConvergence(adjs)!.convergencePct).toBeGreaterThan(0)
  })

  it('convergencePct negative when diverged', () => {
    const adjs = [mkAdj('a', 490000, 300000), mkAdj('b', 500000, 500000), mkAdj('c', 510000, 700000)]
    expect(computeAdjustmentConvergence(adjs)!.convergencePct).toBeLessThan(0)
  })

  it('rawCv and adjustedCv are non-negative', () => {
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 420000, 415000), mkAdj('c', 380000, 405000)]
    const r = computeAdjustmentConvergence(adjs)!
    expect(r.rawCv).toBeGreaterThanOrEqual(0)
    expect(r.adjustedCv).toBeGreaterThanOrEqual(0)
  })

  it('convergencePct 0 when rawCv is 0', () => {
    // All same price — rawCv = 0
    const adjs = [mkAdj('a', 400000, 410000), mkAdj('b', 400000, 420000), mkAdj('c', 400000, 430000)]
    expect(computeAdjustmentConvergence(adjs)!.convergencePct).toBe(0)
  })
})
