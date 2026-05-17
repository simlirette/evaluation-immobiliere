import { describe, it, expect } from 'vitest'
import { computeSensitivityAnalysis } from './compute-sensitivity-analysis'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number, grossPct = 10): Adjustment {
  const surface_adj = Math.round(adjusted * grossPct / 100)
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: adjusted - surface_adj, surface_adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

const adjs3 = [mkAdj('a', 400000), mkAdj('b', 410000), mkAdj('c', 420000)]

describe('computeSensitivityAnalysis', () => {
  it('returns null for fewer than 3 adjustments', () => {
    expect(computeSensitivityAnalysis([])).toBeNull()
    expect(computeSensitivityAnalysis([mkAdj('a', 400000)])).toBeNull()
    expect(computeSensitivityAnalysis([mkAdj('a', 400000), mkAdj('b', 410000)])).toBeNull()
  })

  it('returns one entry per comparable', () => {
    const result = computeSensitivityAnalysis(adjs3)!
    expect(result.entries).toHaveLength(3)
  })

  it('baseValue matches full-set reconciled value', () => {
    const result = computeSensitivityAnalysis(adjs3)!
    expect(result.baseValue).toBeGreaterThan(0)
    expect(typeof result.baseValue).toBe('number')
  })

  it('each entry has correct comparableLabel', () => {
    const result = computeSensitivityAnalysis(adjs3)!
    expect(result.entries.map(e => e.comparableLabel)).toEqual(['Comp a', 'Comp b', 'Comp c'])
  })

  it('delta = reconciledWithout - baseValue', () => {
    const result = computeSensitivityAnalysis(adjs3)!
    for (const e of result.entries) {
      expect(e.delta).toBe(e.reconciledWithout - result.baseValue)
    }
  })

  it('influential = true when |deltaPct| ≥ 3%', () => {
    // Outlier comp drives value far from others
    const outlierAdjs = [mkAdj('a', 400000, 5), mkAdj('b', 405000, 5), mkAdj('c', 500000, 5)]
    const result = computeSensitivityAnalysis(outlierAdjs)!
    const outlier = result.entries.find(e => e.comparableId === 'c')!
    expect(outlier.influential).toBe(true)
  })

  it('influential = false when all comps are close in value', () => {
    const close = [mkAdj('a', 400000, 5), mkAdj('b', 401000, 5), mkAdj('c', 402000, 5)]
    const result = computeSensitivityAnalysis(close)!
    expect(result.entries.every(e => !e.influential)).toBe(true)
  })

  it('deltaPct is rounded to 1 decimal', () => {
    const result = computeSensitivityAnalysis(adjs3)!
    for (const e of result.entries) {
      expect(e.deltaPct).toBe(Math.round(e.deltaPct * 10) / 10)
    }
  })
})
