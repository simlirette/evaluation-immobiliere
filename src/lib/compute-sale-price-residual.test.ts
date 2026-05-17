import { describe, it, expect } from 'vitest'
import { computeSalePriceResidual } from './compute-sale-price-residual'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + adj }
}

describe('computeSalePriceResidual', () => {
  it('returns null for empty array', () => {
    expect(computeSalePriceResidual([], 300000)).toBeNull()
  })

  it('returns null when reconciledValue <= 0', () => {
    expect(computeSalePriceResidual([mkAdj('a', 300000, 0)], 0)).toBeNull()
    expect(computeSalePriceResidual([mkAdj('a', 300000, 0)], -1)).toBeNull()
  })

  it('residualPct = |adjusted - reconciledValue| / reconciledValue × 100', () => {
    // adjusted = 320000; reconciled = 300000; residual = 20000/300000 = 6.67%
    const r = computeSalePriceResidual([mkAdj('a', 300000, 20000)], 300000)!
    expect(r.entries[0].residualPct).toBeCloseTo(6.67, 1)
  })

  it('large true when residualPct > 5%', () => {
    const r = computeSalePriceResidual([mkAdj('a', 300000, 20000)], 300000)!
    expect(r.entries[0].large).toBe(true)
  })

  it('large false when residualPct ≤ 5%', () => {
    // adjusted = 310000; reconciled = 300000; residual = 10000/300000 = 3.33%
    const r = computeSalePriceResidual([mkAdj('a', 300000, 10000)], 300000)!
    expect(r.entries[0].large).toBe(false)
  })

  it('largeResidualIds contains only large comps', () => {
    const r = computeSalePriceResidual([
      mkAdj('a', 300000, 10000), // 3.33% — not large
      mkAdj('b', 300000, 20000), // 6.67% — large
    ], 300000)!
    expect(r.largeResidualIds).toContain('b')
    expect(r.largeResidualIds).not.toContain('a')
  })

  it('stdDevResidual = 0 when all residuals equal', () => {
    // both adjusted to 300000 → residualPct = 0 for both → stdDev = 0
    const r = computeSalePriceResidual([mkAdj('a', 290000, 10000), mkAdj('b', 310000, -10000)], 300000)!
    expect(r.stdDevResidual).toBeCloseTo(0, 5)
  })

  it('one entry per adjustment', () => {
    const r = computeSalePriceResidual([mkAdj('a', 300000, 0), mkAdj('b', 310000, 0)], 300000)!
    expect(r.entries).toHaveLength(2)
  })
})
