import { describe, it, expect } from 'vitest'
import { computeMarketPositioning } from './compute-market-positioning'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: adjusted, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

const adjs = [mkAdj('a', 380000), mkAdj('b', 400000), mkAdj('c', 420000), mkAdj('d', 440000)]

describe('computeMarketPositioning', () => {
  it('returns null for empty adjustments', () => {
    expect(computeMarketPositioning(410000, [])).toBeNull()
  })

  it('returns null for conclusion <= 0', () => {
    expect(computeMarketPositioning(0, adjs)).toBeNull()
    expect(computeMarketPositioning(-1, adjs)).toBeNull()
  })

  it('countBelow + countAbove ≤ total', () => {
    const r = computeMarketPositioning(410000, adjs)!
    expect(r.countBelow + r.countAbove).toBeLessThanOrEqual(r.total)
    expect(r.total).toBe(4)
  })

  it('percentileRank 0 when conclusion below all comps', () => {
    const r = computeMarketPositioning(300000, adjs)!
    expect(r.percentileRank).toBe(0)
    expect(r.countBelow).toBe(0)
    expect(r.position).toBe('bas')
  })

  it('percentileRank 100 when conclusion above all comps', () => {
    const r = computeMarketPositioning(500000, adjs)!
    expect(r.percentileRank).toBe(100)
    expect(r.countAbove).toBe(0)
    expect(r.position).toBe('haut')
  })

  it('percentileRank 50 when conclusion between 2nd and 3rd of 4', () => {
    // 2 comps below 410000 (380k + 400k) → 2/4 = 50%
    const r = computeMarketPositioning(410000, adjs)!
    expect(r.percentileRank).toBe(50)
    expect(r.position).toBe('médian')
  })

  it('nearestBelow is closest comp with adjusted < conclusion', () => {
    const r = computeMarketPositioning(410000, adjs)!
    expect(r.nearestBelow?.adjustedPrice).toBe(400000)
    expect(r.nearestBelow?.delta).toBe(10000)
  })

  it('nearestAbove is closest comp with adjusted > conclusion', () => {
    const r = computeMarketPositioning(410000, adjs)!
    expect(r.nearestAbove?.adjustedPrice).toBe(420000)
    expect(r.nearestAbove?.delta).toBe(10000)
  })

  it('nearestBelow is null when conclusion below all comps', () => {
    expect(computeMarketPositioning(300000, adjs)!.nearestBelow).toBeNull()
  })

  it('nearestAbove is null when conclusion above all comps', () => {
    expect(computeMarketPositioning(500000, adjs)!.nearestAbove).toBeNull()
  })
})
