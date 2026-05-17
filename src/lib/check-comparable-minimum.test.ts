import { describe, it, expect } from 'vitest'
import { checkComparableMinimum } from './check-comparable-minimum'
import type { Comparable } from '@/types'

function mkComp(id: string): Comparable {
  return {
    id, rank: '1', address: '123 Rue Test',
    hab_m2: null, terrain_m2: null, year_built: null,
    renovated_year: null, garage_type: null,
    sale_price: 400000, sale_date: '2024-01-01',
    meta: '', price: '400 000 $', date: '1 janv. 2024',
  }
}

describe('checkComparableMinimum', () => {
  it('0 comparables → fails with "Aucun" message', () => {
    const result = checkComparableMinimum([])
    expect(result.pass).toBe(false)
    expect(result.count).toBe(0)
    expect(result.warning).toContain('Aucun')
  })

  it('1 comparable → fails, mentions count and minimum', () => {
    const result = checkComparableMinimum([mkComp('a')])
    expect(result.pass).toBe(false)
    expect(result.count).toBe(1)
    expect(result.warning).toContain('1')
    expect(result.warning).toContain('3')
  })

  it('2 comparables → fails', () => {
    const result = checkComparableMinimum([mkComp('a'), mkComp('b')])
    expect(result.pass).toBe(false)
    expect(result.count).toBe(2)
  })

  it('3 comparables → passes, no warning', () => {
    const result = checkComparableMinimum([mkComp('a'), mkComp('b'), mkComp('c')])
    expect(result.pass).toBe(true)
    expect(result.warning).toBeNull()
    expect(result.count).toBe(3)
  })

  it('5 comparables → passes', () => {
    const comps = ['a','b','c','d','e'].map(mkComp)
    const result = checkComparableMinimum(comps)
    expect(result.pass).toBe(true)
    expect(result.count).toBe(5)
  })

  it('warning mentions OEAQ', () => {
    const result = checkComparableMinimum([mkComp('a')])
    expect(result.warning).toContain('OEAQ')
  })

  it('pass=true → warning is null', () => {
    const comps = ['a','b','c'].map(mkComp)
    expect(checkComparableMinimum(comps).warning).toBeNull()
  })
})
