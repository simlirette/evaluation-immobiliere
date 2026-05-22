import { describe, it, expect } from 'vitest'
import { computeReconciledValue } from './compute-reconciled-value'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number, grossAdj = 0): Adjustment {
  // grossAdj distributed as surface_adj for simplicity (single positive adj)
  return {
    id,
    comparable_id: id,
    comparableLabel: `Comp ${id}`,
    salePrice: adjusted,
    surface_adj: grossAdj,
    year_adj: 0,
    condition_adj: 0,
    garage_adj: 0,
    adjusted,
  }
}

describe('computeReconciledValue', () => {
  it('returns null for empty array', () => {
    expect(computeReconciledValue([])).toBeNull()
  })

  it('returns adjusted value directly for single comparable', () => {
    const result = computeReconciledValue([mkAdj('a', 400000)])
    expect(result).not.toBeNull()
    expect(result!.value).toBe(400000)
  })

  it('returns equal-weight average when all gross adjustments are zero', () => {
    // all gross = 0 → weight = 1/(0+1) = 1 each → simple average
    const adjs = [mkAdj('a', 400000), mkAdj('b', 420000)]
    const result = computeReconciledValue(adjs)!
    expect(result.value).toBe(410000)
  })

  it('weights comp with lower gross adjustment higher', () => {
    // a: grossPct = 0 → weight = 1; b: grossPct = 100% → weight = 1/2
    // a gets 2/3, b gets 1/3 → (400000*2 + 500000*1)/3 = 433333
    const a = mkAdj('a', 400000, 0)    // no gross adj
    const b = { ...mkAdj('b', 500000, 0), surface_adj: 500000 }  // 100% gross
    const result = computeReconciledValue([a, b])!
    expect(result.value).toBeLessThan(460000) // closer to 400k than 500k
    expect(result.weights['a']).toBeGreaterThan(result.weights['b'])
  })

  it('weights sum to 100', () => {
    const adjs = [mkAdj('a', 400000, 0), mkAdj('b', 420000, 10000), mkAdj('c', 440000, 20000)]
    const result = computeReconciledValue(adjs)!
    const total = Object.values(result.weights).reduce((s, w) => s + w, 0)
    expect(total).toBeCloseTo(100, 0)
  })

  it('confidence is forte when weight spread >= 2x', () => {
    // a: weight=1 (grossPct=0), b: weight=0.5 (grossPct=100%) → ratio 2x
    const a = mkAdj('a', 400000, 0)
    const b = { ...mkAdj('b', 500000, 0), surface_adj: 500000 }
    const result = computeReconciledValue([a, b])!
    expect(result.confidence).toBe('forte')
  })

  it('confidence is modérée when weights are similar', () => {
    // all same gross → equal weights → 1x ratio
    const adjs = [mkAdj('a', 400000), mkAdj('b', 420000)]
    expect(computeReconciledValue(adjs)!.confidence).toBe('modérée')
  })

  it('value is a whole number (Math.round)', () => {
    const adjs = [mkAdj('a', 400001), mkAdj('b', 400002)]
    const result = computeReconciledValue(adjs)!
    expect(Number.isInteger(result.value)).toBe(true)
  })

  it('does not mutate input', () => {
    const adjs = [mkAdj('a', 400000), mkAdj('b', 420000)]
    const copy = adjs.map(a => ({ ...a }))
    computeReconciledValue(adjs)
    expect(adjs[0]).toEqual(copy[0])
  })

  it('ignores adjustments with non-positive sale or adjusted values', () => {
    const adjs = [
      mkAdj('a', 400000),
      { ...mkAdj('b', 420000), salePrice: 0 },
      { ...mkAdj('c', 0), adjusted: 0 },
    ]
    const result = computeReconciledValue(adjs)!
    expect(result.value).toBe(400000)
    expect(Object.keys(result.weights)).toEqual(['a'])
  })

  it('returns null when all adjustments are unusable', () => {
    expect(computeReconciledValue([
      { ...mkAdj('a', 400000), salePrice: 0 },
      { ...mkAdj('b', 0), adjusted: 0 },
    ])).toBeNull()
  })
})
