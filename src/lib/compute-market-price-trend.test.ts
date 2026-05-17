import { describe, it, expect } from 'vitest'
import { computeMarketPriceTrend } from './compute-market-price-trend'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string, sale_price: number): Comparable {
  return {
    id, rank: id, address: `Addr ${id}`,
    hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null,
    garage_type: null, sale_price, sale_date,
    meta: '', price: '', date: '',
  }
}

describe('computeMarketPriceTrend', () => {
  it('returns null for empty array', () => {
    expect(computeMarketPriceTrend([])).toBeNull()
  })

  it('returns null for single comparable', () => {
    expect(computeMarketPriceTrend([mkComp('a', '2024-01-01', 400000)])).toBeNull()
  })

  it('returns null when all dates are identical', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2024-01-01', 420000)]
    expect(computeMarketPriceTrend(comps)).toBeNull()
  })

  it('identifies earliest and latest correctly', () => {
    const comps = [
      mkComp('a', '2024-06-01', 420000),
      mkComp('b', '2024-01-01', 400000),
      mkComp('c', '2025-01-01', 440000),
    ]
    const result = computeMarketPriceTrend(comps)!
    expect(result.earliestDate).toBe('2024-01-01')
    expect(result.latestDate).toBe('2025-01-01')
    expect(result.earliestPrice).toBe(400000)
    expect(result.latestPrice).toBe(440000)
  })

  it('computes variationPct to 1 decimal', () => {
    // 400000 → 420000 = +5%
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 420000)]
    expect(computeMarketPriceTrend(comps)!.variationPct).toBe(5)
  })

  it('direction is hausse when variationPct > 1', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 420000)]
    expect(computeMarketPriceTrend(comps)!.direction).toBe('hausse')
  })

  it('direction is baisse when variationPct < -1', () => {
    const comps = [mkComp('a', '2024-01-01', 420000), mkComp('b', '2025-01-01', 400000)]
    expect(computeMarketPriceTrend(comps)!.direction).toBe('baisse')
  })

  it('direction is stable when variationPct within ±1', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 400000)]
    expect(computeMarketPriceTrend(comps)!.direction).toBe('stable')
  })

  it('periodMonths is approximately 12 for one-year span', () => {
    const comps = [mkComp('a', '2024-01-01', 400000), mkComp('b', '2025-01-01', 420000)]
    expect(computeMarketPriceTrend(comps)!.periodMonths).toBeCloseTo(12, 0)
  })

  it('ignores comps with null sale_date', () => {
    const comps: Comparable[] = [
      { ...mkComp('a', '2024-01-01', 400000) },
      { ...mkComp('b', '2025-01-01', 420000), sale_date: '' },
    ]
    // only 1 valid comp → null
    expect(computeMarketPriceTrend(comps)).toBeNull()
  })
})
