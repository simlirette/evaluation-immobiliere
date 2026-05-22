import { describe, it, expect } from 'vitest'
import { computeGrossAdjustment } from './compute-gross-adjustment'
import type { Adjustment } from '@/types'

function mkAdj(overrides: Partial<Adjustment> = {}): Adjustment {
  return {
    id: 'a', comparable_id: 'a', comparableLabel: 'A',
    salePrice: 400000,
    surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0,
    adjusted: 400000,
    ...overrides,
  }
}

describe('computeGrossAdjustment', () => {
  it('all zero adjustments → gross 0, grossPct 0', () => {
    const r = computeGrossAdjustment(mkAdj())
    expect(r.gross).toBe(0)
    expect(r.grossPct).toBe(0)
  })

  it('positive adjustments sum correctly', () => {
    const r = computeGrossAdjustment(mkAdj({ surface_adj: 10000, year_adj: 5000, condition_adj: 5000, garage_adj: 0 }))
    expect(r.gross).toBe(20000)
    expect(r.grossPct).toBeCloseTo(5, 5)
  })

  it('negative adjustments treated as absolute', () => {
    const r = computeGrossAdjustment(mkAdj({ surface_adj: -10000, year_adj: -10000 }))
    expect(r.gross).toBe(20000)
  })

  it('mixed signs — gross is sum of absolutes (no cancellation)', () => {
    const r = computeGrossAdjustment(mkAdj({ surface_adj: 20000, year_adj: -20000 }))
    expect(r.gross).toBe(40000)   // 10% each side
    expect(r.grossPct).toBeCloseTo(10, 5)
  })

  it('net can be 0 while gross is non-zero (sign cancellation)', () => {
    const adj = mkAdj({ surface_adj: 40000, year_adj: -40000 })
    expect(adj.surface_adj + adj.year_adj).toBe(0)   // net = 0
    const r = computeGrossAdjustment(adj)
    expect(r.gross).toBe(80000)   // gross = 20%
  })

  it('grossPct > 40 detectable', () => {
    const r = computeGrossAdjustment(mkAdj({ surface_adj: 100000, year_adj: 80000, salePrice: 400000 }))
    expect(r.grossPct).toBeGreaterThan(40)
  })

  it('salePrice 0 → grossPct 0 (no division error)', () => {
    const r = computeGrossAdjustment(mkAdj({ salePrice: 0, surface_adj: 5000 }))
    expect(r.grossPct).toBe(0)
    expect(r.gross).toBe(5000)
  })

  it('negative salePrice has zero grossPct', () => {
    const r = computeGrossAdjustment(mkAdj({ salePrice: -400000, surface_adj: 5000 }))
    expect(r.grossPct).toBe(0)
    expect(r.gross).toBe(5000)
  })
})
