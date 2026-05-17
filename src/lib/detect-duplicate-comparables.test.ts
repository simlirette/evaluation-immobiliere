import { describe, it, expect } from 'vitest'
import { detectDuplicateComparables } from './detect-duplicate-comparables'
import type { Comparable } from '@/types'

function mkComp(id: string, address: string, salePrice = 400000, saleDate = '2024-01-01'): Comparable {
  return {
    id, rank: '1', address,
    hab_m2: null, terrain_m2: null, year_built: null,
    renovated_year: null, garage_type: null,
    sale_price: salePrice, sale_date: saleDate,
    meta: '', price: '', date: '',
  }
}

describe('detectDuplicateComparables', () => {
  it('empty list → no pairs', () => {
    expect(detectDuplicateComparables([])).toEqual([])
  })

  it('single comp → no pairs', () => {
    expect(detectDuplicateComparables([mkComp('a', '10 rue Laval')])).toEqual([])
  })

  it('distinct comps → no pairs', () => {
    const comps = [
      mkComp('a', '10 rue Laval', 400000, '2024-01-01'),
      mkComp('b', '25 av. Cartier', 420000, '2024-06-01'),
    ]
    expect(detectDuplicateComparables(comps)).toEqual([])
  })

  it('same address (exact) → same-address pair', () => {
    const comps = [
      mkComp('a', '10 rue Laval'),
      mkComp('b', '10 rue Laval'),
    ]
    const pairs = detectDuplicateComparables(comps)
    expect(pairs).toHaveLength(1)
    expect(pairs[0].reason).toBe('same-address')
    expect(pairs[0].idA).toBe('a')
    expect(pairs[0].idB).toBe('b')
  })

  it('same address case-insensitive → same-address pair', () => {
    const comps = [
      mkComp('a', '10 Rue Laval'),
      mkComp('b', '10 rue laval'),
    ]
    const pairs = detectDuplicateComparables(comps)
    expect(pairs).toHaveLength(1)
    expect(pairs[0].reason).toBe('same-address')
  })

  it('same address extra spaces → same-address pair', () => {
    const comps = [
      mkComp('a', '10  rue  Laval'),
      mkComp('b', '10 rue Laval'),
    ]
    expect(detectDuplicateComparables(comps)).toHaveLength(1)
  })

  it('same price + date → same-price-date pair', () => {
    const comps = [
      mkComp('a', '10 rue Laval', 400000, '2024-01-01'),
      mkComp('b', '25 av. Cartier', 400000, '2024-01-01'),
    ]
    const pairs = detectDuplicateComparables(comps)
    expect(pairs).toHaveLength(1)
    expect(pairs[0].reason).toBe('same-price-date')
  })

  it('same price but different date → no pair', () => {
    const comps = [
      mkComp('a', '10 rue Laval', 400000, '2024-01-01'),
      mkComp('b', '25 av. Cartier', 400000, '2024-06-01'),
    ]
    expect(detectDuplicateComparables(comps)).toEqual([])
  })

  it('three comps, two share address → one pair only', () => {
    const comps = [
      mkComp('a', '10 rue Laval', 400000, '2024-01-01'),
      mkComp('b', '25 av. Cartier', 420000, '2024-06-01'),
      mkComp('c', '10 rue laval', 380000, '2023-11-01'),
    ]
    const pairs = detectDuplicateComparables(comps)
    expect(pairs).toHaveLength(1)
    expect(pairs[0].idA).toBe('a')
    expect(pairs[0].idB).toBe('c')
  })
})
