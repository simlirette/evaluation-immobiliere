import { describe, it, expect } from 'vitest'
import { detectOutlierComparables } from './detect-outlier-comparables'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return {
    id,
    comparable_id: id,
    comparableLabel: `Comp ${id}`,
    salePrice: adjusted,
    surface_adj: 0,
    year_adj: 0,
    condition_adj: 0,
    garage_adj: 0,
    adjusted,
  }
}

describe('detectOutlierComparables', () => {
  it('returns empty array for empty input', () => {
    expect(detectOutlierComparables([])).toEqual([])
  })

  it('returns empty array for 1 comparable', () => {
    expect(detectOutlierComparables([mkAdj('a', 400000)])).toEqual([])
  })

  it('returns empty array for 2 comparables', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 500000)]
    expect(detectOutlierComparables(adjs)).toEqual([])
  })

  it('returns all non-outliers when values within threshold', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 410000), mkAdj('c', 420000)]
    const result = detectOutlierComparables(adjs)
    expect(result).toHaveLength(3)
    expect(result.every(r => !r.isOutlier)).toBe(true)
  })

  it('flags outlier above threshold', () => {
    // median = 410000; c at 500000 → +21.9% → outlier at default 15%
    const adjs = [mkAdj('a', 400000), mkAdj('b', 420000), mkAdj('c', 500000)]
    const result = detectOutlierComparables(adjs)
    const c = result.find(r => r.id === 'c')!
    expect(c.isOutlier).toBe(true)
    expect(c.deviationFromMedianPct).toBeGreaterThan(15)
  })

  it('flags outlier below threshold', () => {
    // median = 410000; a at 300000 → -26.8% → outlier
    const adjs = [mkAdj('a', 300000), mkAdj('b', 400000), mkAdj('c', 420000)]
    const result = detectOutlierComparables(adjs)
    const a = result.find(r => r.id === 'a')!
    expect(a.isOutlier).toBe(true)
    expect(a.deviationFromMedianPct).toBeLessThan(-15)
  })

  it('respects custom threshold', () => {
    // median = 410000; c at 450000 → +9.8% → not outlier at default 15%, but outlier at 5%
    const adjs = [mkAdj('a', 400000), mkAdj('b', 420000), mkAdj('c', 450000)]
    const def = detectOutlierComparables(adjs, 15)
    const strict = detectOutlierComparables(adjs, 5)
    expect(def.find(r => r.id === 'c')!.isOutlier).toBe(false)
    expect(strict.find(r => r.id === 'c')!.isOutlier).toBe(true)
  })

  it('computes deviation to 1 decimal precision', () => {
    // sorted: [400000, 420000, 450000] → median = 420000; b at 450000 → (450000-420000)/420000 = 7.142...→ 7.1
    const adjs = [mkAdj('a', 400000), mkAdj('b', 450000), mkAdj('c', 420000)]
    const b = detectOutlierComparables(adjs).find(r => r.id === 'b')!
    expect(b.deviationFromMedianPct).toBe(7.1)
  })

  it('does not mutate input array', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 410000), mkAdj('c', 420000)]
    const copy = [...adjs]
    detectOutlierComparables(adjs)
    expect(adjs).toEqual(copy)
  })

  it('returns zero deviation when all values equal median', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 400000), mkAdj('c', 400000)]
    const result = detectOutlierComparables(adjs)
    expect(result.every(r => r.deviationFromMedianPct === 0 && !r.isOutlier)).toBe(true)
  })
})
