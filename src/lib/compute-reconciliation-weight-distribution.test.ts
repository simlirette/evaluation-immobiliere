import { describe, it, expect } from 'vitest'
import { computeReconciliationWeightDistribution } from './compute-reconciliation-weight-distribution'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, surface_adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + surface_adj }
}

describe('computeReconciliationWeightDistribution', () => {
  it('returns null for empty array', () => {
    expect(computeReconciliationWeightDistribution([])).toBeNull()
  })

  it('returns one entry per adj', () => {
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 0), mkAdj('b', 400000, 20000)])!
    expect(r.entries).toHaveLength(2)
  })

  it('weight = 1 / (grossPct + 1)', () => {
    // grossPct = 20000/400000*100 = 5% → weight = 1/(5+1) = 1/6
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 20000), mkAdj('b', 400000, 20000)])!
    const entry = r.entries[0]
    expect(entry.weight).toBeCloseTo(1 / 6, 5)
  })

  it('weightPct sums to 100', () => {
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 0), mkAdj('b', 400000, 20000)])!
    const total = r.entries.reduce((s, e) => s + e.weightPct, 0)
    expect(total).toBeCloseTo(100, 5)
  })

  it('lower grossPct gets higher weightPct', () => {
    // a: 0% gross → weight=1; b: 5% gross → weight=1/6
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 0), mkAdj('b', 400000, 20000)])!
    const a = r.entries.find(e => e.id === 'a')!
    const b = r.entries.find(e => e.id === 'b')!
    expect(a.weightPct).toBeGreaterThan(b.weightPct)
  })

  it('equal gross → equal weightPct (50/50 split)', () => {
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 20000), mkAdj('b', 400000, 20000)])!
    expect(r.entries[0].weightPct).toBeCloseTo(50, 5)
    expect(r.entries[1].weightPct).toBeCloseTo(50, 5)
  })

  it('herfindahl = sum of (weightPct/100)²', () => {
    // equal weights: 2 comps each 50% → H = 0.25+0.25 = 0.5
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 20000), mkAdj('b', 400000, 20000)])!
    expect(r.herfindahl).toBeCloseTo(0.5, 5)
  })

  it('herfindahl = 1 for single comp (max concentration)', () => {
    const r = computeReconciliationWeightDistribution([mkAdj('a', 400000, 0)])!
    expect(r.herfindahl).toBeCloseTo(1, 5)
  })
})
