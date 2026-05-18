import { describe, it, expect } from 'vitest'
import { computeComparablePriceAnomaly } from './compute-comparable-price-anomaly'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeComparablePriceAnomaly', () => {
  it('returns null for < 2 comps with valid hab_m2', () => {
    expect(computeComparablePriceAnomaly([])).toBeNull()
    expect(computeComparablePriceAnomaly([mkComp('a', 300000, 100)])).toBeNull()
    expect(computeComparablePriceAnomaly([mkComp('a', 300000, null), mkComp('b', 300000, null)])).toBeNull()
  })

  it('panelMedianPricePerM2 computed from valid comps', () => {
    // $/m²: 3000 and 3000 → median = 3000
    const r = computeComparablePriceAnomaly([mkComp('a', 300000, 100), mkComp('b', 300000, 100)])!
    expect(r.panelMedianPricePerM2).toBe(3000)
  })

  it('isAnomaly true when deviationPct > 25%', () => {
    // panel $/m² ≈ 3000; anomaly comp at 300000/50=6000 → 100% deviation
    const r = computeComparablePriceAnomaly([
      mkComp('a', 300000, 100), mkComp('b', 300000, 100), mkComp('c', 300000, 50),
    ])!
    const anomaly = r.entries.find(e => e.id === 'c')!
    expect(anomaly.isAnomaly).toBe(true)
    expect(r.anomalyIds).toContain('c')
  })

  it('isAnomaly false when deviationPct ≤ 25%', () => {
    // all comps at ~3000 $/m² → no anomaly
    const r = computeComparablePriceAnomaly([mkComp('a', 300000, 100), mkComp('b', 310000, 100)])!
    expect(r.anomalyIds).toHaveLength(0)
  })

  it('skips comps with null or zero hab_m2', () => {
    const r = computeComparablePriceAnomaly([
      mkComp('a', 300000, null), mkComp('b', 300000, 100), mkComp('c', 300000, 100),
    ])!
    expect(r.entries).toHaveLength(2)
  })

  it('deviationPct = |actualPpm2 - median| / median × 100', () => {
    // 3 comps: 3000, 3000, 3600 $/m² → median=3000; comp c deviation = 600/3000 = 20%
    const r = computeComparablePriceAnomaly([mkComp('a', 300000, 100), mkComp('b', 300000, 100), mkComp('c', 360000, 100)])!
    const higher = r.entries.find(e => e.id === 'c')!
    expect(higher.deviationPct).toBeCloseTo(20, 1)
  })
})
