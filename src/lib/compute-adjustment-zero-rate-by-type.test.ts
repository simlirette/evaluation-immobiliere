import { describe, it, expect } from 'vitest'
import { computeAdjustmentZeroRateByType } from './compute-adjustment-zero-rate-by-type'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const total = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + total }
}

describe('computeAdjustmentZeroRateByType', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentZeroRateByType([])).toBeNull()
  })

  it('unusedTypes includes types where all comps have adj = 0', () => {
    const r = computeAdjustmentZeroRateByType([mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 3000, 0, 0, 0)])!
    expect(r.unusedTypes).toContain('Année')
    expect(r.unusedTypes).toContain('État')
    expect(r.unusedTypes).toContain('Garage')
    expect(r.unusedTypes).not.toContain('Surface')
  })

  it('universalTypes includes types where no comp has adj = 0', () => {
    const r = computeAdjustmentZeroRateByType([mkAdj('a', 5000, 3000, 0, 0), mkAdj('b', 2000, 1000, 0, 0)])!
    expect(r.universalTypes).toContain('Surface')
    expect(r.universalTypes).toContain('Année')
    expect(r.universalTypes).not.toContain('État')
  })

  it('zeroPct correct: zeroCount/total × 100 rounded', () => {
    // 2 out of 3 comps have year_adj = 0 → 67%
    const r = computeAdjustmentZeroRateByType([
      mkAdj('a', 0, 5000, 0, 0),
      mkAdj('b', 0, 0, 0, 0),
      mkAdj('c', 0, 0, 0, 0),
    ])!
    const year = r.entries.find(e => e.type === 'year')!
    expect(year.zeroPct).toBe(67)
  })

  it('zeroCount correct', () => {
    const r = computeAdjustmentZeroRateByType([mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 0, 0, 0, 0)])!
    const surface = r.entries.find(e => e.type === 'surface')!
    expect(surface.zeroCount).toBe(1)
  })

  it('four entries always returned', () => {
    const r = computeAdjustmentZeroRateByType([mkAdj('a', 1000, 2000, 3000, 4000)])!
    expect(r.entries).toHaveLength(4)
  })

  it('empty unusedTypes and universalTypes when mixed', () => {
    // surface: 1 zero, 1 non-zero → neither unused nor universal
    const r = computeAdjustmentZeroRateByType([mkAdj('a', 5000, 0, 0, 0), mkAdj('b', 0, 0, 0, 0)])!
    expect(r.unusedTypes).not.toContain('Surface')
    expect(r.universalTypes).not.toContain('Surface')
  })
})
