import { describe, it, expect } from 'vitest'
import { computeSubjectContext } from './compute-subject-context'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return {
    id, comparable_id: id, comparableLabel: id,
    salePrice: adjusted, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0,
    adjusted,
  }
}

const adjs = [mkAdj('a', 380000), mkAdj('b', 400000), mkAdj('c', 420000)]
// median = 400000, min = 380000, max = 420000

describe('computeSubjectContext', () => {
  it('empty adjustments → null', () => {
    expect(computeSubjectContext(400000, [])).toBeNull()
  })

  it('conclusion at median → direction "at", deviation 0', () => {
    const ctx = computeSubjectContext(400000, adjs)!
    expect(ctx.direction).toBe('at')
    expect(ctx.deviationFromMedianPct).toBe(0)
  })

  it('conclusion above median → direction "above", positive deviation', () => {
    const ctx = computeSubjectContext(410000, adjs)!
    expect(ctx.direction).toBe('above')
    expect(ctx.deviationFromMedianPct).toBeGreaterThan(0)
  })

  it('conclusion below median → direction "below", negative deviation', () => {
    const ctx = computeSubjectContext(390000, adjs)!
    expect(ctx.direction).toBe('below')
    expect(ctx.deviationFromMedianPct).toBeLessThan(0)
  })

  it('within range when between min and max', () => {
    const ctx = computeSubjectContext(400000, adjs)!
    expect(ctx.withinRange).toBe(true)
  })

  it('outside range when above max', () => {
    const ctx = computeSubjectContext(500000, adjs)!
    expect(ctx.withinRange).toBe(false)
  })

  it('outside range when below min', () => {
    const ctx = computeSubjectContext(300000, adjs)!
    expect(ctx.withinRange).toBe(false)
  })

  it('deviationFromMedianPct computed correctly (+2.5%)', () => {
    const ctx = computeSubjectContext(410000, adjs)!
    expect(ctx.deviationFromMedianPct).toBe(2.5)
  })

  it('min and max match adjustment range', () => {
    const ctx = computeSubjectContext(400000, adjs)!
    expect(ctx.min).toBe(380000)
    expect(ctx.max).toBe(420000)
    expect(ctx.median).toBe(400000)
  })
})
