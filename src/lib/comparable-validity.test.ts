import { describe, it, expect } from 'vitest'
import { hasIsoSaleDate, isUsableComparable } from './comparable-validity'
import type { Comparable } from '@/types'

function mkComp(overrides: Partial<Comparable> = {}): Comparable {
  return {
    id: 'c1',
    rank: 'C1',
    address: '123 rue Test',
    hab_m2: null,
    terrain_m2: null,
    year_built: null,
    renovated_year: null,
    garage_type: null,
    sale_price: 400000,
    sale_date: '2025-01-01',
    meta: '',
    price: '400 000 $',
    date: '2025-01-01',
    source_id: 'SRC-1',
    ...overrides,
  }
}

describe('comparable-validity', () => {
  it('accepts comparable with positive price, ISO date and source', () => {
    expect(isUsableComparable(mkComp())).toBe(true)
  })

  it('rejects zero price, missing source or invalid date', () => {
    expect(isUsableComparable(mkComp({ sale_price: 0 }))).toBe(false)
    expect(isUsableComparable(mkComp({ source_id: '' }))).toBe(false)
    expect(isUsableComparable(mkComp({ sale_date: '2025-02-31' }))).toBe(false)
  })

  it('validates ISO calendar dates exactly', () => {
    expect(hasIsoSaleDate(mkComp({ sale_date: '2025-02-28' }))).toBe(true)
    expect(hasIsoSaleDate(mkComp({ sale_date: '2025-2-28' }))).toBe(false)
    expect(hasIsoSaleDate(mkComp({ sale_date: '2025-13-01' }))).toBe(false)
  })
})
