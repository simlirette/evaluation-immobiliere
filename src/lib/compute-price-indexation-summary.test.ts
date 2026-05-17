import { describe, it, expect } from 'vitest'
import { computePriceIndexationSummary } from './compute-price-indexation-summary'
import type { PriceIndexationEntry } from './compute-price-indexation'

function mkEntry(id: string, originalPrice: number, indexedPrice: number, adjustmentPct: number): PriceIndexationEntry {
  return { comparableId: id, comparableLabel: `Comp ${id}`, originalPrice, indexedPrice, monthsAdjusted: 12, adjustmentPct }
}

describe('computePriceIndexationSummary', () => {
  it('returns null for empty entries', () => {
    expect(computePriceIndexationSummary([])).toBeNull()
  })

  it('count equals entries length', () => {
    expect(computePriceIndexationSummary([mkEntry('a', 400000, 410000, 2.5)])!.count).toBe(1)
  })

  it('totalAdded is sum of (indexed − original)', () => {
    const entries = [mkEntry('a', 400000, 410000, 2.5), mkEntry('b', 500000, 515000, 3.0)]
    expect(computePriceIndexationSummary(entries)!.totalAdded).toBe(25000)
  })

  it('avgAdjPct is mean of adjustmentPcts', () => {
    const entries = [mkEntry('a', 400000, 410000, 2.0), mkEntry('b', 500000, 515000, 4.0)]
    expect(computePriceIndexationSummary(entries)!.avgAdjPct).toBe(3.0)
  })

  it('mostAdjustedId has highest |adjustmentPct|', () => {
    const entries = [mkEntry('a', 400000, 410000, 2.5), mkEntry('b', 500000, 530000, 6.0), mkEntry('c', 300000, 303000, 1.0)]
    expect(computePriceIndexationSummary(entries)!.mostAdjustedId).toBe('b')
  })

  it('leastAdjustedId has lowest |adjustmentPct|', () => {
    const entries = [mkEntry('a', 400000, 410000, 2.5), mkEntry('b', 500000, 530000, 6.0), mkEntry('c', 300000, 303000, 1.0)]
    expect(computePriceIndexationSummary(entries)!.leastAdjustedId).toBe('c')
  })

  it('works with negative adjustments (falling market)', () => {
    const entries = [mkEntry('a', 400000, 390000, -2.5), mkEntry('b', 500000, 485000, -3.0)]
    const r = computePriceIndexationSummary(entries)!
    expect(r.totalAdded).toBe(-25000)
    expect(r.avgAdjPct).toBeCloseTo(-2.75, 1)
  })

  it('mostAdjustedPct uses absolute value (negative adj)', () => {
    const entries = [mkEntry('a', 400000, 390000, -5.0), mkEntry('b', 500000, 502000, 0.4)]
    expect(computePriceIndexationSummary(entries)!.mostAdjustedPct).toBe(5.0)
  })
})
