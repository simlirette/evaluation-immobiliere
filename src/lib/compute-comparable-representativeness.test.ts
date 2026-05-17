import { describe, it, expect } from 'vitest'
import { computeComparableRepresentativeness } from './compute-comparable-representativeness'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_price: number): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: String(sale_price), date: '2024-01-01' }
}

describe('computeComparableRepresentativeness', () => {
  it('returns null for fewer than 2 comps', () => {
    expect(computeComparableRepresentativeness([mkComp('a', 400000)], 400000)).toBeNull()
  })

  it('returns null when subjectValue is 0', () => {
    expect(computeComparableRepresentativeness([mkComp('a', 400000), mkComp('b', 500000)], 0)).toBeNull()
  })

  it('withinRange true when subject inside raw price range', () => {
    const r = computeComparableRepresentativeness([mkComp('a', 350000), mkComp('b', 450000)], 400000)!
    expect(r.withinRange).toBe(true)
    expect(r.deviationPct).toBe(0)
    expect(r.compMin).toBe(350000)
    expect(r.compMax).toBe(450000)
  })

  it('withinRange false when subject above raw range', () => {
    const r = computeComparableRepresentativeness([mkComp('a', 300000), mkComp('b', 400000)], 500000)!
    expect(r.withinRange).toBe(false)
    expect(r.deviationPct).toBeGreaterThan(0)
  })

  it('withinRange false when subject below raw range', () => {
    const r = computeComparableRepresentativeness([mkComp('a', 400000), mkComp('b', 500000)], 200000)!
    expect(r.withinRange).toBe(false)
    expect(r.deviationPct).toBeGreaterThan(0)
  })

  it('deviationPct is % from nearest fence above', () => {
    // subject = 600000, compMax = 500000 → (600000-500000)/500000 = 20%
    const r = computeComparableRepresentativeness([mkComp('a', 400000), mkComp('b', 500000)], 600000)!
    expect(r.deviationPct).toBe(20)
  })

  it('withinRange true when subject equals compMin', () => {
    const r = computeComparableRepresentativeness([mkComp('a', 400000), mkComp('b', 500000)], 400000)!
    expect(r.withinRange).toBe(true)
  })
})
