import { describe, it, expect } from 'vitest'
import { computeComparableDataCompleteness } from './compute-comparable-data-completeness'
import type { Comparable } from '@/types'

function mkComp(id: string, overrides: Partial<Comparable> = {}): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 300000, sale_date: '2024-01-01', meta: '', price: '', date: '', ...overrides }
}

describe('computeComparableDataCompleteness', () => {
  it('returns null for empty array', () => {
    expect(computeComparableDataCompleteness([])).toBeNull()
  })

  it('score 0 when all 5 fields missing', () => {
    const r = computeComparableDataCompleteness([mkComp('a')])!
    expect(r.entries[0].score).toBe(0)
  })

  it('score 5 when all fields present', () => {
    const r = computeComparableDataCompleteness([mkComp('a', { hab_m2: 100, terrain_m2: 500, year_built: 1990, renovated_year: 2010, garage_type: 'simple' })])!
    expect(r.entries[0].score).toBe(5)
    expect(r.fullCount).toBe(1)
  })

  it('missingFields lists absent fields', () => {
    const r = computeComparableDataCompleteness([mkComp('a', { hab_m2: 100 })])!
    expect(r.entries[0].missingFields).toHaveLength(4)
    expect(r.entries[0].missingFields).not.toContain('Surface hab.')
  })

  it('sparseCount includes comps with score < 3', () => {
    const r = computeComparableDataCompleteness([
      mkComp('a'),                                              // score 0 → sparse
      mkComp('b', { hab_m2: 100, terrain_m2: 500 }),           // score 2 → sparse
      mkComp('c', { hab_m2: 100, terrain_m2: 500, year_built: 1990 }), // score 3 → not sparse
    ])!
    expect(r.sparseCount).toBe(2)
  })

  it('avgScore is mean of all entry scores', () => {
    const r = computeComparableDataCompleteness([
      mkComp('a'),                              // score 0
      mkComp('b', { hab_m2: 100, terrain_m2: 500, year_built: 1990, renovated_year: 2010, garage_type: 'double' }), // score 5
    ])!
    expect(r.avgScore).toBe(2.5)
  })

  it('one entry per comp', () => {
    const r = computeComparableDataCompleteness([mkComp('a'), mkComp('b')])!
    expect(r.entries).toHaveLength(2)
  })
})
