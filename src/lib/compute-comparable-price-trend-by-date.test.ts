import { describe, it, expect } from 'vitest'
import { computeComparablePriceTrendByDate } from './compute-comparable-price-trend-by-date'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string, sale_price: number): Comparable {
  return { id, rank: id, address: '', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date, meta: '', price: '', date: '' }
}

describe('computeComparablePriceTrendByDate', () => {
  it('returns null for < 2 comps', () => {
    expect(computeComparablePriceTrendByDate([])).toBeNull()
    expect(computeComparablePriceTrendByDate([mkComp('a', '2024-01-01', 300000)])).toBeNull()
  })

  it('returns null when all same date (ssXX = 0)', () => {
    expect(computeComparablePriceTrendByDate([
      mkComp('a', '2024-01-01', 300000),
      mkComp('b', '2024-01-01', 400000),
    ])).toBeNull()
  })

  it('direction = hausse when prices increase over time', () => {
    const r = computeComparablePriceTrendByDate([
      mkComp('a', '2023-01-01', 300000),
      mkComp('b', '2024-01-01', 400000),
    ])!
    expect(r.direction).toBe('hausse')
    expect(r.slope).toBeGreaterThan(0)
  })

  it('direction = baisse when prices decrease over time', () => {
    const r = computeComparablePriceTrendByDate([
      mkComp('a', '2023-01-01', 400000),
      mkComp('b', '2024-01-01', 300000),
    ])!
    expect(r.direction).toBe('baisse')
    expect(r.slope).toBeLessThan(0)
  })

  it('r2 = 1 for perfect linear relationship', () => {
    const r = computeComparablePriceTrendByDate([
      mkComp('a', '2023-01-01', 300000),
      mkComp('b', '2023-07-01', 350000),
      mkComp('c', '2024-01-01', 400000),
    ])!
    expect(r.r2).toBeCloseTo(1, 3)
  })

  it('r2 between 0 and 1 for imperfect fit', () => {
    const r = computeComparablePriceTrendByDate([
      mkComp('a', '2023-01-01', 300000),
      mkComp('b', '2023-06-01', 500000),
      mkComp('c', '2024-01-01', 320000),
    ])!
    expect(r.r2).toBeGreaterThanOrEqual(0)
    expect(r.r2).toBeLessThanOrEqual(1)
  })

  it('count = number of comps', () => {
    const r = computeComparablePriceTrendByDate([
      mkComp('a', '2023-01-01', 300000),
      mkComp('b', '2024-01-01', 400000),
    ])!
    expect(r.count).toBe(2)
  })

  it('sorts comps by date before regression', () => {
    // Reversed input — should still detect hausse
    const r = computeComparablePriceTrendByDate([
      mkComp('b', '2024-01-01', 400000),
      mkComp('a', '2023-01-01', 300000),
    ])!
    expect(r.direction).toBe('hausse')
  })
})
