import { describe, it, expect } from 'vitest'
import { sortComparables } from './sort-comparables'
import type { Comparable } from '@/types'

function mkComp(overrides: Partial<Comparable> & { id: string }): Comparable {
  return {
    rank: '1',
    address: '123 Rue Test',
    hab_m2: 100,
    terrain_m2: null,
    year_built: 2000,
    renovated_year: null,
    garage_type: null,
    sale_price: 400000,
    sale_date: '2024-01-01',
    meta: '',
    price: '400 000 $',
    date: '1 janv. 2024',
    ...overrides,
  }
}

const A = mkComp({ id: 'a', rank: '1', sale_price: 300000, sale_date: '2024-03-01', hab_m2: 90 })
const B = mkComp({ id: 'b', rank: '2', sale_price: 500000, sale_date: '2023-06-15', hab_m2: 120 })
const C = mkComp({ id: 'c', rank: '3', sale_price: 400000, sale_date: '2024-01-10', hab_m2: null })

describe('sortComparables', () => {
  it('rank — preserves rank order', () => {
    const result = sortComparables([C, A, B], 'rank')
    expect(result.map(x => x.id)).toEqual(['a', 'b', 'c'])
  })

  it('prix — ascending by sale_price', () => {
    const result = sortComparables([B, C, A], 'prix')
    expect(result.map(x => x.id)).toEqual(['a', 'c', 'b'])
  })

  it('date — most recent first', () => {
    const result = sortComparables([B, A, C], 'date')
    expect(result.map(x => x.id)).toEqual(['a', 'c', 'b'])
  })

  it('surface — largest first', () => {
    const result = sortComparables([A, B, C], 'surface')
    expect(result.map(x => x.id)).toEqual(['b', 'a', 'c'])
  })

  it('prix_m2 — ascending; null hab_m2 goes last', () => {
    const result = sortComparables([A, B, C], 'prix_m2')
    // A: 300000/90 = 3333, B: 500000/120 = 4166, C: null → Infinity
    expect(result.map(x => x.id)).toEqual(['a', 'b', 'c'])
  })

  it('does not mutate input array', () => {
    const input = [B, A, C]
    sortComparables(input, 'prix')
    expect(input.map(x => x.id)).toEqual(['b', 'a', 'c'])
  })

  it('empty array → empty array', () => {
    expect(sortComparables([], 'rank')).toEqual([])
  })
})
