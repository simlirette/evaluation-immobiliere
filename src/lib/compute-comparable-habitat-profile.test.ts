import { describe, it, expect } from 'vitest'
import { computeComparableHabitatProfile } from './compute-comparable-habitat-profile'
import type { Comparable } from '@/types'

function mkComp(id: string, hab_m2: number | null): Comparable {
  return { id, rank: id, address: '', hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 300000, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeComparableHabitatProfile', () => {
  it('returns null for < 2 valid comps', () => {
    expect(computeComparableHabitatProfile([])).toBeNull()
    expect(computeComparableHabitatProfile([mkComp('a', 100)])).toBeNull()
    expect(computeComparableHabitatProfile([mkComp('a', null), mkComp('b', null)])).toBeNull()
  })

  it('excludes null and zero hab_m2', () => {
    const r = computeComparableHabitatProfile([mkComp('a', null), mkComp('b', 0), mkComp('c', 100), mkComp('d', 200)])!
    expect(r.count).toBe(2)
    expect(r.missingCount).toBe(2)
  })

  it('min and max correct', () => {
    const r = computeComparableHabitatProfile([mkComp('a', 80), mkComp('b', 150), mkComp('c', 200)])!
    expect(r.min).toBe(80)
    expect(r.max).toBe(200)
  })

  it('mean correct', () => {
    const r = computeComparableHabitatProfile([mkComp('a', 100), mkComp('b', 200)])!
    expect(r.mean).toBe(150)
  })

  it('median even count: avg of two middle', () => {
    const r = computeComparableHabitatProfile([mkComp('a', 100), mkComp('b', 200)])!
    expect(r.median).toBe(150)
  })

  it('median odd count: middle value', () => {
    const r = computeComparableHabitatProfile([mkComp('a', 100), mkComp('b', 150), mkComp('c', 200)])!
    expect(r.median).toBe(150)
  })

  it('cv > 0 when values differ', () => {
    const r = computeComparableHabitatProfile([mkComp('a', 100), mkComp('b', 200)])!
    expect(r.cv).toBeGreaterThan(0)
  })

  it('missingCount includes nulls and zeros', () => {
    const r = computeComparableHabitatProfile([mkComp('a', null), mkComp('b', 100), mkComp('c', 200)])!
    expect(r.missingCount).toBe(1)
  })
})
