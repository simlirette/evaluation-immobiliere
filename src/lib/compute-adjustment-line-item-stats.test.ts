import { describe, it, expect } from 'vitest'
import { computeAdjustmentLineItemStats } from './compute-adjustment-line-item-stats'
import type { Adjustment } from '@/types'

function mkAdj(id: string, surface_adj: number, year_adj: number, condition_adj: number, garage_adj: number): Adjustment {
  const totalAdj = surface_adj + year_adj + condition_adj + garage_adj
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj, year_adj, condition_adj, garage_adj, adjusted: 400000 + totalAdj }
}

describe('computeAdjustmentLineItemStats', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentLineItemStats([])).toBeNull()
  })

  it('single adj: min=max=mean=median', () => {
    const r = computeAdjustmentLineItemStats([mkAdj('a', 5000, -3000, 1000, 0)])!
    expect(r.surface.min).toBe(5000)
    expect(r.surface.max).toBe(5000)
    expect(r.surface.mean).toBe(5000)
    expect(r.surface.median).toBe(5000)
  })

  it('min and max across comps', () => {
    const r = computeAdjustmentLineItemStats([mkAdj('a', 2000, 0, 0, 0), mkAdj('b', 8000, 0, 0, 0)])!
    expect(r.surface.min).toBe(2000)
    expect(r.surface.max).toBe(8000)
  })

  it('mean correct', () => {
    const r = computeAdjustmentLineItemStats([mkAdj('a', 2000, 0, 0, 0), mkAdj('b', 8000, 0, 0, 0)])!
    expect(r.surface.mean).toBe(5000)
  })

  it('median even count: average of two middle values', () => {
    // [2000, 4000, 6000, 8000] → median = (4000+6000)/2 = 5000
    const r = computeAdjustmentLineItemStats([
      mkAdj('a', 2000, 0, 0, 0), mkAdj('b', 4000, 0, 0, 0),
      mkAdj('c', 6000, 0, 0, 0), mkAdj('d', 8000, 0, 0, 0),
    ])!
    expect(r.surface.median).toBe(5000)
  })

  it('median odd count: middle value', () => {
    // [1000, 3000, 5000] → median = 3000
    const r = computeAdjustmentLineItemStats([mkAdj('a', 1000, 0, 0, 0), mkAdj('b', 5000, 0, 0, 0), mkAdj('c', 3000, 0, 0, 0)])!
    expect(r.surface.median).toBe(3000)
  })

  it('all four types present', () => {
    const r = computeAdjustmentLineItemStats([mkAdj('a', 1000, -2000, 500, 1500)])!
    expect(r.year.mean).toBe(-2000)
    expect(r.condition.mean).toBe(500)
    expect(r.garage.mean).toBe(1500)
  })
})
