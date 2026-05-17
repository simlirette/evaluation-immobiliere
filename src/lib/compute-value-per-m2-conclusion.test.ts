import { describe, it, expect } from 'vitest'
import { computeValuePerM2Conclusion } from './compute-value-per-m2-conclusion'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: String(sale_price), date: '2024-01-01' }
}

describe('computeValuePerM2Conclusion', () => {
  it('returns null for invalid reconciledValue', () => {
    expect(computeValuePerM2Conclusion(0, 100, [])).toBeNull()
  })

  it('returns null for invalid subjectHabM2', () => {
    expect(computeValuePerM2Conclusion(500000, 0, [])).toBeNull()
    expect(computeValuePerM2Conclusion(500000, -10, [])).toBeNull()
  })

  it('pricePerM2 = reconciledValue / subjectHabM2', () => {
    const r = computeValuePerM2Conclusion(500000, 100, [])!
    expect(r.pricePerM2).toBe(5000)
  })

  it('medianCompM2 and signal null when fewer than 2 comps with hab_m2', () => {
    const r = computeValuePerM2Conclusion(500000, 100, [mkComp('a', 400000, 80)])!
    expect(r.medianCompM2).toBeNull()
    expect(r.signal).toBeNull()
  })

  it('signal is médian when within ±10% of median', () => {
    // comp median: 400000/80 = 5000 $/m²; subject: 500000/100 = 5000 → 0%
    const comps = [mkComp('a', 400000, 80), mkComp('b', 400000, 80), mkComp('c', 400000, 80)]
    const r = computeValuePerM2Conclusion(500000, 100, comps)!
    expect(r.signal).toBe('médian')
    expect(r.vsMedianPct).toBe(0)
  })

  it('signal is haut when >10% above median', () => {
    // subject 6000 $/m², comps 5000 → +20%
    const comps = [mkComp('a', 500000, 100), mkComp('b', 500000, 100), mkComp('c', 500000, 100)]
    const r = computeValuePerM2Conclusion(600000, 100, comps)!
    expect(r.signal).toBe('haut')
  })

  it('signal is bas when >10% below median', () => {
    // subject 4000 $/m², comps 5000 → -20%
    const comps = [mkComp('a', 500000, 100), mkComp('b', 500000, 100), mkComp('c', 500000, 100)]
    const r = computeValuePerM2Conclusion(400000, 100, comps)!
    expect(r.signal).toBe('bas')
  })

  it('medianCompM2 is median of comp $/m²', () => {
    // prices/m²: 3000, 4000, 5000 → median 4000
    const comps = [mkComp('a', 300000, 100), mkComp('b', 400000, 100), mkComp('c', 500000, 100)]
    const r = computeValuePerM2Conclusion(400000, 100, comps)!
    expect(r.medianCompM2).toBe(4000)
  })

  it('skips comps with null hab_m2 for median', () => {
    const comps = [mkComp('a', 500000, 100), mkComp('b', 400000, null), mkComp('c', 500000, 100)]
    const r = computeValuePerM2Conclusion(500000, 100, comps)!
    // only 2 valid comps: both 5000 $/m²
    expect(r.medianCompM2).toBe(5000)
  })
})
