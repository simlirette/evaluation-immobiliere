import { describe, it, expect } from 'vitest'
import { computeComparableSaleVelocity } from './compute-comparable-sale-velocity'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string): Comparable {
  return { id, rank: id, address: '', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 300000, sale_date, meta: '', price: '', date: '' }
}

describe('computeComparableSaleVelocity', () => {
  it('returns null for < 2 comps', () => {
    expect(computeComparableSaleVelocity([])).toBeNull()
    expect(computeComparableSaleVelocity([mkComp('a', '2024-01-01')])).toBeNull()
  })

  it('returns null when all same date (spanMonths = 0)', () => {
    expect(computeComparableSaleVelocity([mkComp('a', '2024-01-01'), mkComp('b', '2024-01-01')])).toBeNull()
  })

  it('count equals number of comps', () => {
    const r = computeComparableSaleVelocity([mkComp('a', '2024-01-01'), mkComp('b', '2025-01-01')])!
    expect(r.count).toBe(2)
  })

  it('spanMonths approximately 12 for one year apart', () => {
    const r = computeComparableSaleVelocity([mkComp('a', '2024-01-01'), mkComp('b', '2025-01-01')])!
    expect(r.spanMonths).toBeCloseTo(12, 0)
  })

  it('signal actif when salesPerMonth > 1', () => {
    // 6 comps over ~3 months → ~2/month
    const comps = [
      mkComp('a', '2024-01-01'), mkComp('b', '2024-01-15'),
      mkComp('c', '2024-02-01'), mkComp('d', '2024-02-15'),
      mkComp('e', '2024-03-01'), mkComp('f', '2024-04-01'),
    ]
    const r = computeComparableSaleVelocity(comps)!
    expect(r.signal).toBe('actif')
  })

  it('signal lent when salesPerMonth < 0.5', () => {
    // 2 comps over 6 years → ~0.028/month
    const r = computeComparableSaleVelocity([mkComp('a', '2018-01-01'), mkComp('b', '2024-01-01')])!
    expect(r.signal).toBe('lent')
  })

  it('annualizedRate = salesPerMonth * 12', () => {
    const r = computeComparableSaleVelocity([mkComp('a', '2024-01-01'), mkComp('b', '2025-01-01')])!
    expect(r.annualizedRate).toBeCloseTo(r.salesPerMonth * 12, 5)
  })
})
