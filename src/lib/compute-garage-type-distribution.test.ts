import { describe, it, expect } from 'vitest'
import { computeGarageTypeDistribution } from './compute-garage-type-distribution'
import type { Comparable } from '@/types'

function mkComp(id: string, garage_type: string | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: null, renovated_year: null, garage_type, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01' }
}

describe('computeGarageTypeDistribution', () => {
  it('returns null for empty array', () => {
    expect(computeGarageTypeDistribution([])).toBeNull()
  })

  it('counts groups correctly', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'simple'), mkComp('c', 'double')]
    const r = computeGarageTypeDistribution(comps)!
    const simple = r.groups.find(g => g.type === 'simple')!
    expect(simple.count).toBe(2)
    expect(simple.pct).toBe(66.7)
  })

  it('groups sorted by count descending', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'double'), mkComp('c', 'double')]
    const r = computeGarageTypeDistribution(comps)!
    expect(r.groups[0].type).toBe('double')
  })

  it('dominantType is the single type when only one exists', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'simple')]
    expect(computeGarageTypeDistribution(comps)!.dominantType).toBe('simple')
  })

  it('dominantType is null when tied', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'double')]
    expect(computeGarageTypeDistribution(comps)!.dominantType).toBeNull()
  })

  it('dominantType is clear winner when one type leads', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'simple'), mkComp('c', 'double')]
    expect(computeGarageTypeDistribution(comps)!.dominantType).toBe('simple')
  })

  it('hasGarageConflict true when multiple non-null types', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'double'), mkComp('c', null)]
    expect(computeGarageTypeDistribution(comps)!.hasGarageConflict).toBe(true)
  })

  it('hasGarageConflict false when all same type', () => {
    const comps = [mkComp('a', 'simple'), mkComp('b', 'simple'), mkComp('c', null)]
    expect(computeGarageTypeDistribution(comps)!.hasGarageConflict).toBe(false)
  })

  it('missingCount counts null garage_type', () => {
    const comps = [mkComp('a', null), mkComp('b', null), mkComp('c', 'simple')]
    expect(computeGarageTypeDistribution(comps)!.missingCount).toBe(2)
  })

  it('all null — groups empty, no conflict', () => {
    const comps = [mkComp('a', null), mkComp('b', null)]
    const r = computeGarageTypeDistribution(comps)!
    expect(r.groups).toHaveLength(0)
    expect(r.hasGarageConflict).toBe(false)
    expect(r.dominantType).toBeNull()
  })
})
