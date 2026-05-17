import { describe, it, expect } from 'vitest'
import { computeComparableStreetDiversity } from './compute-comparable-street-diversity'
import type { Comparable } from '@/types'

function mkComp(id: string, address: string): Comparable {
  return { id, rank: id, address, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 300000, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

describe('computeComparableStreetDiversity', () => {
  it('returns null for empty array', () => {
    expect(computeComparableStreetDiversity([])).toBeNull()
  })

  it('concentrated true when all comps on same street', () => {
    const r = computeComparableStreetDiversity([
      mkComp('a', '123 Rue des Érables'),
      mkComp('b', '456 Rue des Érables'),
    ])!
    expect(r.concentrated).toBe(true)
    expect(r.uniqueCount).toBe(1)
  })

  it('concentrated false when multiple streets', () => {
    const r = computeComparableStreetDiversity([
      mkComp('a', '123 Rue des Érables'),
      mkComp('b', '456 Boulevard du Lac'),
    ])!
    expect(r.concentrated).toBe(false)
    expect(r.uniqueCount).toBe(2)
  })

  it('totalCount equals number of comps', () => {
    const r = computeComparableStreetDiversity([mkComp('a', '123 Rue A'), mkComp('b', '456 Rue B'), mkComp('c', '789 Rue A')])!
    expect(r.totalCount).toBe(3)
  })

  it('uniqueCount deduplicates same street different numbers', () => {
    // "123 Rue A" and "789 Rue A" → same street "rue a"
    const r = computeComparableStreetDiversity([mkComp('a', '123 Rue A'), mkComp('b', '789 Rue A'), mkComp('c', '10 Rue B')])!
    expect(r.uniqueCount).toBe(2)
  })

  it('streets array has uniqueCount entries', () => {
    const r = computeComparableStreetDiversity([mkComp('a', '1 Rue A'), mkComp('b', '2 Rue B')])!
    expect(r.streets).toHaveLength(2)
  })

  it('street extraction is case-insensitive', () => {
    const r = computeComparableStreetDiversity([mkComp('a', '1 RUE DES ÉRABLES'), mkComp('b', '2 rue des érables')])!
    expect(r.uniqueCount).toBe(1)
  })
})
