import { describe, it, expect } from 'vitest'
import { computeComparableGarageProfile } from './compute-comparable-garage-profile'
import type { Comparable } from '@/types'

function mkComp(id: string, garage_type: string | null): Comparable {
  return { id, rank: id, address: '', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type, sale_price: 300000, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeComparableGarageProfile', () => {
  it('returns null for empty array', () => {
    expect(computeComparableGarageProfile([])).toBeNull()
  })

  it('total = comps.length', () => {
    const r = computeComparableGarageProfile([mkComp('a', 'attaché'), mkComp('b', null)])!
    expect(r.total).toBe(2)
  })

  it('missingCount = count of null garage_type', () => {
    const r = computeComparableGarageProfile([mkComp('a', 'attaché'), mkComp('b', null), mkComp('c', null)])!
    expect(r.missingCount).toBe(2)
  })

  it('typeCounts groups by garage_type', () => {
    const r = computeComparableGarageProfile([
      mkComp('a', 'attaché'),
      mkComp('b', 'attaché'),
      mkComp('c', 'détaché'),
    ])!
    const attached = r.typeCounts.find(t => t.type === 'attaché')!
    const detached = r.typeCounts.find(t => t.type === 'détaché')!
    expect(attached.count).toBe(2)
    expect(detached.count).toBe(1)
  })

  it('typeCounts sorted descending by count', () => {
    const r = computeComparableGarageProfile([
      mkComp('a', 'attaché'),
      mkComp('b', 'attaché'),
      mkComp('c', 'détaché'),
    ])!
    expect(r.typeCounts[0].type).toBe('attaché')
    expect(r.typeCounts[1].type).toBe('détaché')
  })

  it('typeCounts excludes null garage_type', () => {
    const r = computeComparableGarageProfile([mkComp('a', null), mkComp('b', null)])!
    expect(r.typeCounts).toHaveLength(0)
  })

  it('all missing → missingCount = total', () => {
    const r = computeComparableGarageProfile([mkComp('a', null)])!
    expect(r.missingCount).toBe(1)
    expect(r.total).toBe(1)
  })
})
