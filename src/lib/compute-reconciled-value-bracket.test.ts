import { describe, it, expect } from 'vitest'
import { computeReconciledValueBracket } from './compute-reconciled-value-bracket'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeReconciledValueBracket', () => {
  it('returns null for empty adjustments', () => {
    expect(computeReconciledValueBracket([], 400000)).toBeNull()
  })

  it('returns null when reconciledValue is 0', () => {
    expect(computeReconciledValueBracket([mkAdj('a', 400000)], 0)).toBeNull()
  })

  it('bracketed true when value within range', () => {
    const adjs = [mkAdj('a', 350000), mkAdj('b', 450000)]
    const r = computeReconciledValueBracket(adjs, 400000)!
    expect(r.bracketed).toBe(true)
    expect(r.deviationPct).toBe(0)
    expect(r.min).toBe(350000)
    expect(r.max).toBe(450000)
  })

  it('bracketed false when value above range', () => {
    const adjs = [mkAdj('a', 300000), mkAdj('b', 400000)]
    const r = computeReconciledValueBracket(adjs, 500000)!
    expect(r.bracketed).toBe(false)
    expect(r.deviationPct).toBeGreaterThan(0)
  })

  it('bracketed false when value below range', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 500000)]
    const r = computeReconciledValueBracket(adjs, 300000)!
    expect(r.bracketed).toBe(false)
    expect(r.deviationPct).toBeGreaterThan(0)
  })

  it('deviationPct is % from nearest fence', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 500000)]
    const r = computeReconciledValueBracket(adjs, 600000)!
    // (600000 - 500000) / 500000 = 20%
    expect(r.deviationPct).toBe(20)
  })

  it('bracketed true when value equals min', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 500000)]
    expect(computeReconciledValueBracket(adjs, 400000)!.bracketed).toBe(true)
  })

  it('bracketed true when value equals max', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 500000)]
    expect(computeReconciledValueBracket(adjs, 500000)!.bracketed).toBe(true)
  })
})
