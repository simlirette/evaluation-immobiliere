import { describe, it, expect } from 'vitest'
import { computePanelAdjustmentBalance } from './compute-panel-adjustment-balance'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const total = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + total }
}

describe('computePanelAdjustmentBalance', () => {
  it('returns null for empty array', () => {
    expect(computePanelAdjustmentBalance([])).toBeNull()
  })

  it('totalPositive sums all positive adj values across all types', () => {
    const r = computePanelAdjustmentBalance([mkAdj('a', 10000, 5000, 0, 0)])!
    expect(r.totalPositive).toBe(15000)
  })

  it('totalNegative sums all negative adj values (as negative number)', () => {
    const r = computePanelAdjustmentBalance([mkAdj('a', 0, -5000, -3000, 0)])!
    expect(r.totalNegative).toBe(-8000)
  })

  it('netBalance = totalPositive + totalNegative', () => {
    const r = computePanelAdjustmentBalance([mkAdj('a', 10000, -5000, 0, 0)])!
    expect(r.netBalance).toBe(5000)
    expect(r.netBalance).toBe(r.totalPositive + r.totalNegative)
  })

  it('balancePct = netBalance / gross × 100', () => {
    // totalPos = 10000, totalNeg = -5000, gross = 15000, net = 5000 → 33.33%
    const r = computePanelAdjustmentBalance([mkAdj('a', 10000, -5000, 0, 0)])!
    expect(r.balancePct).toBeCloseTo(33.33, 1)
  })

  it('balancePct = 0 when perfectly balanced', () => {
    const r = computePanelAdjustmentBalance([mkAdj('a', 5000, -5000, 0, 0)])!
    expect(r.netBalance).toBe(0)
    expect(r.balancePct).toBe(0)
  })

  it('aggregates across multiple comps', () => {
    const r = computePanelAdjustmentBalance([
      mkAdj('a', 10000, 0, 0, 0),
      mkAdj('b', 0, -4000, 0, 0),
    ])!
    expect(r.totalPositive).toBe(10000)
    expect(r.totalNegative).toBe(-4000)
    expect(r.netBalance).toBe(6000)
  })
})
