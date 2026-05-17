import { describe, it, expect } from 'vitest'
import { computeAdjustmentExplainedVariance } from './compute-adjustment-explained-variance'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface_adj: number, year_adj: number = 0): Adjustment {
  const totalAdj = surface_adj + year_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj, condition_adj: 0, garage_adj: 0, adjusted: salePrice + totalAdj }
}

describe('computeAdjustmentExplainedVariance', () => {
  it('returns null for < 2 adjs', () => {
    expect(computeAdjustmentExplainedVariance([])).toBeNull()
    expect(computeAdjustmentExplainedVariance([mkAdj('a', 300000, 10000)])).toBeNull()
  })

  it('returns null when all sale prices identical (saleVariance = 0)', () => {
    expect(computeAdjustmentExplainedVariance([mkAdj('a', 300000, 10000), mkAdj('b', 300000, -5000)])).toBeNull()
  })

  it('varianceReductionPct = 0 when adjustments do not reduce variance', () => {
    // sale prices differ by same amount as adjustments → no reduction
    const r = computeAdjustmentExplainedVariance([mkAdj('a', 200000, 0), mkAdj('b', 400000, 0)])!
    expect(r.varianceReductionPct).toBe(0)
    expect(r.interpretation).toBe('aucune')
  })

  it('varianceReductionPct > 0 when adjustments reduce spread', () => {
    // comps 200k and 400k, adjusted to 300k and 300k → full reduction
    const r = computeAdjustmentExplainedVariance([mkAdj('a', 200000, 100000), mkAdj('b', 400000, -100000)])!
    expect(r.varianceReductionPct).toBeCloseTo(100, 1)
    expect(r.interpretation).toBe('forte')
  })

  it('interpretation forte when varianceReductionPct >= 50', () => {
    // prices: 100k, 300k → var = 10^10; adjust: +75k, -75k → adj: 175k, 225k → var = 6.25×10^8 → reduction ≈ 93.75%
    const r = computeAdjustmentExplainedVariance([mkAdj('a', 100000, 75000), mkAdj('b', 300000, -75000)])!
    expect(r.interpretation).toBe('forte')
  })

  it('interpretation modérée when 20 ≤ reduction < 50', () => {
    // manual: prices 100k, 300k (var=10^10), adjust: +25k, -25k → adj 125k, 275k → var=5.625×10^9 → reduction≈43.75%... need smaller adj
    // prices 100k,300k: mean=200k, var=10^10
    // adj: 100k+10k=110k, 300k-10k=290k: mean=200k, var=(90k^2+90k^2)/2 = 8.1×10^9; reduction = (10^10-8.1×10^9)/10^10 = 19%
    // Use adj 20k: 120k,280k: mean=200k, var=(80k^2+80k^2)/2 = 6.4×10^9; reduction = 36% → modérée
    const r = computeAdjustmentExplainedVariance([mkAdj('a', 100000, 20000), mkAdj('b', 300000, -20000)])!
    expect(r.varianceReductionPct).toBeGreaterThanOrEqual(20)
    expect(r.varianceReductionPct).toBeLessThan(50)
    expect(r.interpretation).toBe('modérée')
  })

  it('saleVariance and adjustedVariance returned', () => {
    const r = computeAdjustmentExplainedVariance([mkAdj('a', 200000, 0), mkAdj('b', 400000, 0)])!
    expect(r.saleVariance).toBeGreaterThan(0)
    expect(r.adjustedVariance).toBeGreaterThanOrEqual(0)
  })
})
