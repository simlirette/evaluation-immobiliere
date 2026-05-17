import { describe, it, expect } from 'vitest'
import { computeAdjustmentDirectionBalance } from './compute-adjustment-direction-balance'
import type { Adjustment } from '@/types'

function mkAdj(id: string, salePrice: number, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustmentDirectionBalance', () => {
  it('returns null for empty array', () => {
    expect(computeAdjustmentDirectionBalance([])).toBeNull()
  })

  it('upCount counts comps where adjusted > salePrice', () => {
    const adjs = [mkAdj('a', 400000, 420000), mkAdj('b', 400000, 380000), mkAdj('c', 400000, 410000)]
    const r = computeAdjustmentDirectionBalance(adjs)!
    expect(r.upCount).toBe(2)
    expect(r.downCount).toBe(1)
  })

  it('neutralCount counts zero-net adjustments', () => {
    const adjs = [mkAdj('a', 400000, 400000), mkAdj('b', 400000, 410000)]
    const r = computeAdjustmentDirectionBalance(adjs)!
    expect(r.neutralCount).toBe(1)
  })

  it('direction is upward when >70% positive', () => {
    const adjs = [
      mkAdj('a', 400000, 420000),
      mkAdj('b', 400000, 415000),
      mkAdj('c', 400000, 410000),
      mkAdj('d', 400000, 380000),
    ]
    // 3/4 = 75% upward
    expect(computeAdjustmentDirectionBalance(adjs)!.direction).toBe('upward')
  })

  it('direction is downward when >70% negative', () => {
    const adjs = [
      mkAdj('a', 400000, 380000),
      mkAdj('b', 400000, 375000),
      mkAdj('c', 400000, 370000),
      mkAdj('d', 400000, 420000),
    ]
    // 3/4 = 75% downward
    expect(computeAdjustmentDirectionBalance(adjs)!.direction).toBe('downward')
  })

  it('direction is balanced when neither exceeds 70%', () => {
    const adjs = [mkAdj('a', 400000, 420000), mkAdj('b', 400000, 380000), mkAdj('c', 400000, 410000), mkAdj('d', 400000, 390000)]
    // 50/50
    expect(computeAdjustmentDirectionBalance(adjs)!.direction).toBe('balanced')
  })

  it('balanced is true only when direction === balanced', () => {
    const adjs = [mkAdj('a', 400000, 420000), mkAdj('b', 400000, 410000), mkAdj('c', 400000, 415000)]
    const r = computeAdjustmentDirectionBalance(adjs)!
    expect(r.balanced).toBe(false)
    expect(r.direction).toBe('upward')
  })

  it('upPct rounds to 1 decimal', () => {
    const adjs = [mkAdj('a', 400000, 420000), mkAdj('b', 400000, 410000), mkAdj('c', 400000, 380000)]
    const r = computeAdjustmentDirectionBalance(adjs)!
    // 2/3 up = 66.7%
    expect(r.upPct).toBeCloseTo(66.7, 0)
  })
})
