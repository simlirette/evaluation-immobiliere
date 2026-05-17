import { describe, it, expect } from 'vitest'
import { computeComparableCompleteness } from './compute-comparable-completeness'
import type { Comparable } from '@/types'

function mkComp(id: string, overrides: Partial<Comparable> = {}): Comparable {
  return {
    id, rank: id, address: `Addr ${id}`,
    hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null,
    garage_type: null, sale_price: 400000, sale_date: '',
    meta: '', price: '', date: '',
    ...overrides,
  }
}

describe('computeComparableCompleteness', () => {
  it('returns empty array for empty input', () => {
    expect(computeComparableCompleteness([])).toEqual([])
  })

  it('returns one entry per comparable', () => {
    const comps = [mkComp('a'), mkComp('b')]
    expect(computeComparableCompleteness(comps)).toHaveLength(2)
  })

  it('grade incomplet when no key fields present', () => {
    const result = computeComparableCompleteness([mkComp('a')])[0]
    expect(result.presentCount).toBe(0)
    expect(result.completenessPct).toBe(0)
    expect(result.grade).toBe('incomplet')
    expect(result.missingFields).toHaveLength(5)
  })

  it('grade complet when all key fields present', () => {
    const full = mkComp('a', { hab_m2: 120, terrain_m2: 400, year_built: 1990, garage_type: 'Détaché', sale_date: '2024-01-01' })
    const result = computeComparableCompleteness([full])[0]
    expect(result.presentCount).toBe(5)
    expect(result.completenessPct).toBe(100)
    expect(result.grade).toBe('complet')
    expect(result.missingFields).toHaveLength(0)
  })

  it('grade partiel when 3 of 5 fields present', () => {
    const partial = mkComp('a', { hab_m2: 120, year_built: 1990, sale_date: '2024-01-01' })
    const result = computeComparableCompleteness([partial])[0]
    expect(result.presentCount).toBe(3)
    expect(result.completenessPct).toBe(60)
    expect(result.grade).toBe('partiel')
  })

  it('missingFields lists absent fields in French', () => {
    const comp = mkComp('a', { hab_m2: 120 }) // only hab_m2 present
    const result = computeComparableCompleteness([comp])[0]
    expect(result.missingFields).toContain('Terrain')
    expect(result.missingFields).toContain('Année constr.')
    expect(result.missingFields).toContain('Garage')
    expect(result.missingFields).toContain('Date de vente')
    expect(result.missingFields).not.toContain('Surface hab.')
  })

  it('comparableId matches input comp id', () => {
    const result = computeComparableCompleteness([mkComp('xyz')])[0]
    expect(result.comparableId).toBe('xyz')
  })

  it('completenessPct boundary: 4/5 = 80% → complet', () => {
    const comp = mkComp('a', { hab_m2: 120, terrain_m2: 400, year_built: 1990, garage_type: 'Détaché' })
    const result = computeComparableCompleteness([comp])[0]
    expect(result.completenessPct).toBe(80)
    expect(result.grade).toBe('complet')
  })

  it('totalFields is 5 for all comparables', () => {
    const result = computeComparableCompleteness([mkComp('a')])[0]
    expect(result.totalFields).toBe(5)
  })
})
