import { describe, it, expect } from 'vitest'
import { computeSalePricePerTerrainM2 } from './compute-sale-price-per-terrain-m2'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number, terrain_m2: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: String(sale_price), date: '2024-01-01' }
}

describe('computeSalePricePerTerrainM2', () => {
  it('returns null for fewer than 2 comps with terrain_m2', () => {
    expect(computeSalePricePerTerrainM2([mkComp('a', 400000, 500), mkComp('b', 500000, null)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeSalePricePerTerrainM2([])).toBeNull()
  })

  it('count equals valid comps', () => {
    const comps = [mkComp('a', 400000, 500), mkComp('b', 500000, 400), mkComp('c', 300000, null)]
    expect(computeSalePricePerTerrainM2(comps)!.count).toBe(2)
  })

  it('missingCount counts null terrain_m2', () => {
    const comps = [mkComp('a', 400000, 500), mkComp('b', 500000, null), mkComp('c', 300000, 600)]
    expect(computeSalePricePerTerrainM2(comps)!.missingCount).toBe(1)
  })

  it('min and max are correct', () => {
    const comps = [mkComp('a', 400000, 1000), mkComp('b', 600000, 500), mkComp('c', 300000, 1500)]
    // prices/m²: 400, 1200, 200
    const r = computeSalePricePerTerrainM2(comps)!
    expect(r.min).toBe(200)
    expect(r.max).toBe(1200)
  })

  it('mean is average of $/terrain m²', () => {
    const comps = [mkComp('a', 400000, 1000), mkComp('b', 400000, 1000)]
    // both = 400 $/m²
    expect(computeSalePricePerTerrainM2(comps)!.mean).toBe(400)
  })

  it('cv = 0 for identical values', () => {
    const comps = [mkComp('a', 400000, 1000), mkComp('b', 400000, 1000), mkComp('c', 400000, 1000)]
    expect(computeSalePricePerTerrainM2(comps)!.cv).toBe(0)
  })

  it('median correct for even count', () => {
    const comps = [mkComp('a', 200000, 1000), mkComp('b', 400000, 1000), mkComp('c', 600000, 1000), mkComp('d', 800000, 1000)]
    // values: 200, 400, 600, 800 → median = (400+600)/2 = 500
    expect(computeSalePricePerTerrainM2(comps)!.median).toBe(500)
  })
})
