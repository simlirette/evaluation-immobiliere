import { describe, it, expect } from 'vitest'
import { buildComparablesCsv } from './build-comparables-csv'
import type { Comparable } from '@/types'

function mkComp(overrides: Partial<Comparable> = {}): Comparable {
  return {
    id: 'a', rank: '1', address: '10 rue Laval',
    hab_m2: 120, terrain_m2: 400, year_built: 1990,
    renovated_year: null, garage_type: null,
    sale_price: 420000, sale_date: '2024-03-15',
    meta: '', price: '', date: '',
    ...overrides,
  }
}

describe('buildComparablesCsv', () => {
  it('includes header row', () => {
    const csv = buildComparablesCsv([])
    const firstLine = csv.split('\n')[0]
    expect(firstLine).toContain('Adresse')
    expect(firstLine).toContain('Prix de vente')
    expect(firstLine).toContain('Prix/m²')
  })

  it('empty comps → header only', () => {
    const csv = buildComparablesCsv([])
    expect(csv.split('\n')).toHaveLength(1)
  })

  it('single comp → 2 lines', () => {
    const csv = buildComparablesCsv([mkComp()])
    expect(csv.split('\n')).toHaveLength(2)
  })

  it('data row contains address and price', () => {
    const csv = buildComparablesCsv([mkComp({ address: '25 av. Test', sale_price: 380000 })])
    expect(csv).toContain('25 av. Test')
    expect(csv).toContain('380000')
  })

  it('null fields rendered as empty string', () => {
    const csv = buildComparablesCsv([mkComp({ hab_m2: null, terrain_m2: null, year_built: null })])
    const dataRow = csv.split('\n')[1]
    // hab_m2, terrain_m2, year_built, and price_per_m2 are all empty
    expect(dataRow).toContain(',,,,')
  })

  it('price_per_m2 computed from sale_price / hab_m2', () => {
    const csv = buildComparablesCsv([mkComp({ sale_price: 360000, hab_m2: 120 })])
    expect(csv).toContain('3000')  // 360000/120
  })

  it('price_per_m2 empty when hab_m2 null', () => {
    const csv = buildComparablesCsv([mkComp({ hab_m2: null })])
    const cells = csv.split('\n')[1].split(',')
    expect(cells[cells.length - 1]).toBe('')
  })

  it('address with comma is quoted', () => {
    const csv = buildComparablesCsv([mkComp({ address: 'App. 2, 10 rue Laval' })])
    expect(csv).toContain('"App. 2, 10 rue Laval"')
  })

  it('multiple comps produce correct row count', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp({ id }))
    expect(buildComparablesCsv(comps).split('\n')).toHaveLength(4)
  })
})
