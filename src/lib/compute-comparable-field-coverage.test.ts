import { describe, it, expect } from 'vitest'
import { computeComparableFieldCoverage } from './compute-comparable-field-coverage'
import type { Comparable } from '@/types'

function mkComp(id: string, overrides: Partial<Comparable> = {}): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01', ...overrides }
}

describe('computeComparableFieldCoverage', () => {
  it('returns null for empty array', () => {
    expect(computeComparableFieldCoverage([])).toBeNull()
  })

  it('returns 5 field entries', () => {
    expect(computeComparableFieldCoverage([mkComp('a')])!.fields).toHaveLength(5)
  })

  it('coveragePct 100 when all comps have the field', () => {
    const comps = [mkComp('a', { hab_m2: 100 }), mkComp('b', { hab_m2: 120 })]
    const r = computeComparableFieldCoverage(comps)!
    expect(r.fields.find(f => f.field === 'hab_m2')!.coveragePct).toBe(100)
  })

  it('coveragePct 0 when no comps have the field', () => {
    const comps = [mkComp('a'), mkComp('b')]
    const r = computeComparableFieldCoverage(comps)!
    expect(r.fields.find(f => f.field === 'hab_m2')!.coveragePct).toBe(0)
  })

  it('coveragePct 50 when half comps have the field', () => {
    const comps = [mkComp('a', { hab_m2: 100 }), mkComp('b')]
    expect(computeComparableFieldCoverage(comps)!.fields.find(f => f.field === 'hab_m2')!.coveragePct).toBe(50)
  })

  it('overallScore is mean of all field coverages', () => {
    // All fields null → 0%
    expect(computeComparableFieldCoverage([mkComp('a')])!.overallScore).toBe(0)
  })

  it('overallScore 100 when all fields present', () => {
    const comps = [mkComp('a', { hab_m2: 100, terrain_m2: 500, year_built: 2000, renovated_year: 2010, garage_type: 'simple' })]
    expect(computeComparableFieldCoverage(comps)!.overallScore).toBe(100)
  })

  it('sparseFieldCount counts fields with coverage < 50%', () => {
    const comps = [mkComp('a', { hab_m2: 100 }), mkComp('b', { hab_m2: 110 })]
    // hab_m2 = 100%, others = 0% → 4 sparse fields
    expect(computeComparableFieldCoverage(comps)!.sparseFieldCount).toBe(4)
  })
})
