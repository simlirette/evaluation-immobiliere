import { describe, it, expect } from 'vitest'
import { computeComparableStats } from './compute-comparable-stats'
import type { Comparable } from '@/types'

function mkComp(id: string, salePrice: number, saleDate: string, habM2: number | null = null): Comparable {
  return {
    id, rank: '1', address: `${id} Rue Test`,
    hab_m2: habM2, terrain_m2: null, year_built: null,
    renovated_year: null, garage_type: null,
    sale_price: salePrice, sale_date: saleDate,
    meta: '', price: '', date: '',
  }
}

describe('computeComparableStats', () => {
  it('empty → null', () => {
    expect(computeComparableStats([])).toBeNull()
  })

  it('single comp — count = 1', () => {
    const stats = computeComparableStats([mkComp('a', 400000, '2024-01-15')])
    expect(stats?.count).toBe(1)
  })

  it('priceMin and priceMax correct', () => {
    const comps = [
      mkComp('a', 300000, '2023-01-01'),
      mkComp('b', 500000, '2024-01-01'),
      mkComp('c', 400000, '2023-06-01'),
    ]
    const stats = computeComparableStats(comps)!
    expect(stats.priceMin).toBe(300000)
    expect(stats.priceMax).toBe(500000)
  })

  it('dateMin is earliest, dateMax is most recent', () => {
    const comps = [
      mkComp('a', 400000, '2024-03-01'),
      mkComp('b', 400000, '2022-11-15'),
      mkComp('c', 400000, '2023-07-20'),
    ]
    const stats = computeComparableStats(comps)!
    expect(stats.dateMin).toBe('2022-11-15')
    expect(stats.dateMax).toBe('2024-03-01')
  })

  it('priceM2Min/Max computed when all comps have hab_m2', () => {
    const comps = [
      mkComp('a', 400000, '2024-01-01', 100),  // 4000/m²
      mkComp('b', 600000, '2024-01-01', 150),  // 4000/m²
      mkComp('c', 300000, '2024-01-01', 120),  // 2500/m²
    ]
    const stats = computeComparableStats(comps)!
    expect(stats.priceM2Min).toBe(2500)
    expect(stats.priceM2Max).toBe(4000)
  })

  it('priceM2Min/Max null when any comp missing hab_m2', () => {
    const comps = [
      mkComp('a', 400000, '2024-01-01', 100),
      mkComp('b', 400000, '2024-01-01', null),
    ]
    const stats = computeComparableStats(comps)!
    expect(stats.priceM2Min).toBeNull()
    expect(stats.priceM2Max).toBeNull()
  })

  it('all hab_m2 null → priceM2 null', () => {
    const comps = [mkComp('a', 400000, '2024-01-01'), mkComp('b', 500000, '2024-01-01')]
    const stats = computeComparableStats(comps)!
    expect(stats.priceM2Min).toBeNull()
    expect(stats.priceM2Max).toBeNull()
  })

  it('single comp, dateMin === dateMax', () => {
    const stats = computeComparableStats([mkComp('a', 400000, '2023-05-10')])!
    expect(stats.dateMin).toBe('2023-05-10')
    expect(stats.dateMax).toBe('2023-05-10')
  })

  it('count matches input length', () => {
    const comps = ['a','b','c','d','e'].map(id => mkComp(id, 400000, '2024-01-01'))
    expect(computeComparableStats(comps)?.count).toBe(5)
  })
})
