import { describe, it, expect } from 'vitest'
import { filterComparablesByQuery } from './filter-comparables'
import type { Comparable } from '@/types'

function mkComp(id: string, address: string): Comparable {
  return {
    id, rank: '1', address,
    hab_m2: null, terrain_m2: null, year_built: null,
    renovated_year: null, garage_type: null,
    sale_price: 400000, sale_date: '2024-01-01',
    meta: '', price: '400 000 $', date: '1 janv. 2024',
  }
}

const comps = [
  mkComp('a', '123 Rue de la Paix, Montréal'),
  mkComp('b', '456 Avenue du Mont-Royal'),
  mkComp('c', '789 Boulevard Saint-Laurent'),
]

describe('filterComparablesByQuery', () => {
  it('empty query → all comps returned', () => {
    expect(filterComparablesByQuery(comps, '')).toHaveLength(3)
  })

  it('whitespace-only query → all comps returned', () => {
    expect(filterComparablesByQuery(comps, '   ')).toHaveLength(3)
  })

  it('exact address match (case-insensitive)', () => {
    const result = filterComparablesByQuery(comps, 'mont-royal')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('b')
  })

  it('accent-insensitive match', () => {
    const result = filterComparablesByQuery(comps, 'montreal')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('a')
  })

  it('partial match returns multiple', () => {
    const result = filterComparablesByQuery(comps, 'saint')
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe('c')
  })

  it('no match → empty array', () => {
    expect(filterComparablesByQuery(comps, 'xyz-no-match-zzz')).toHaveLength(0)
  })

  it('empty comps array → empty array', () => {
    expect(filterComparablesByQuery([], 'rue')).toHaveLength(0)
  })

  it('does not mutate input array', () => {
    const input = [...comps]
    filterComparablesByQuery(input, 'rue')
    expect(input).toHaveLength(3)
  })
})
