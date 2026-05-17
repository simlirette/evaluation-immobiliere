import { describe, it, expect } from 'vitest'
import { buildOEAQChecklist } from './build-oeaq-checklist'
import type { Comparable, Adjustment } from '@/types'

function mkComp(id: string, saleDate = '2025-01-01'): Comparable {
  return {
    id, rank: '1', address: '123 Rue Test',
    hab_m2: 100, terrain_m2: null, year_built: null,
    renovated_year: null, garage_type: null,
    sale_price: 400000, sale_date: saleDate,
    meta: '', price: '400 000 $', date: '1 janv. 2025',
  }
}

function mkAdj(id: string, net = 0): Adjustment {
  return {
    id,
    comparable_id: id,
    comparableLabel: id,
    salePrice: 400000,
    surface_adj: net,
    year_adj: 0,
    condition_adj: 0,
    garage_adj: 0,
    adjusted: 400000 + net,
  }
}

const TODAY = new Date('2026-05-17')
const STALE_DATE = '2022-01-01'   // > 36 months from TODAY

describe('buildOEAQChecklist', () => {
  it('all pass when 3+ fresh comps, small adjustments', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp(id))
    const adjs  = ['a', 'b', 'c'].map(id => mkAdj(id, 10000))
    const checks = buildOEAQChecklist(comps, adjs, TODAY)
    expect(checks.every(c => c.pass)).toBe(true)
    expect(checks.every(c => c.message === null)).toBe(true)
  })

  it('min-comparables fails when < 3 comps', () => {
    const checks = buildOEAQChecklist([mkComp('a'), mkComp('b')], [], TODAY)
    const check = checks.find(c => c.id === 'min-comparables')!
    expect(check.pass).toBe(false)
    expect(check.message).toBeTruthy()
  })

  it('stale-dates fails when any comp > 36 months', () => {
    const comps = [mkComp('a'), mkComp('b', STALE_DATE), mkComp('c')]
    const checks = buildOEAQChecklist(comps, [], TODAY)
    const check = checks.find(c => c.id === 'stale-dates')!
    expect(check.pass).toBe(false)
    expect(check.message).toContain('1')
  })

  it('stale-dates message pluralizes for 2 stale', () => {
    const comps = [mkComp('a'), mkComp('b', STALE_DATE), mkComp('c', STALE_DATE)]
    const checks = buildOEAQChecklist(comps, [], TODAY)
    const check = checks.find(c => c.id === 'stale-dates')!
    expect(check.message).toContain('2')
    expect(check.message).toContain('ventes')
  })

  it('stale-dates passes when all comps fresh', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp(id))
    const checks = buildOEAQChecklist(comps, [], TODAY)
    const check = checks.find(c => c.id === 'stale-dates')!
    expect(check.pass).toBe(true)
    expect(check.message).toBeNull()
  })

  it('adjustment-magnitude fails when absPct > 25', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp(id))
    // net = 120000 on 400000 = 30% > 25
    const adjs = [mkAdj('a', 120000), mkAdj('b', 5000), mkAdj('c', 0)]
    const checks = buildOEAQChecklist(comps, adjs, TODAY)
    const check = checks.find(c => c.id === 'adjustment-magnitude')!
    expect(check.pass).toBe(false)
    expect(check.message).toContain('1')
  })

  it('adjustment-magnitude passes when all absPct ≤ 25', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp(id))
    const adjs = [mkAdj('a', 10000), mkAdj('b', 5000), mkAdj('c', 0)]
    const checks = buildOEAQChecklist(comps, adjs, TODAY)
    const check = checks.find(c => c.id === 'adjustment-magnitude')!
    expect(check.pass).toBe(true)
    expect(check.message).toBeNull()
  })

  it('returns exactly 4 checks with correct ids', () => {
    const checks = buildOEAQChecklist([], [], TODAY)
    expect(checks).toHaveLength(4)
    expect(checks.map(c => c.id)).toEqual(['min-comparables', 'stale-dates', 'adjustment-magnitude', 'gross-adjustment'])
  })

  it('gross-adjustment fails when grossPct > 40', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp(id))
    // gross = |160000| + |10000| = 170000 on 400000 = 42.5% > 40
    const adjs = [
      { ...mkAdj('a', 0), surface_adj: 160000, year_adj: 10000 },
      mkAdj('b', 5000),
      mkAdj('c', 0),
    ]
    const checks = buildOEAQChecklist(comps, adjs, TODAY)
    const check = checks.find(c => c.id === 'gross-adjustment')!
    expect(check.pass).toBe(false)
    expect(check.message).toContain('1')
  })

  it('gross-adjustment passes when all grossPct ≤ 40', () => {
    const comps = ['a', 'b', 'c'].map(id => mkComp(id))
    const adjs = ['a', 'b', 'c'].map(id => mkAdj(id, 10000))
    const checks = buildOEAQChecklist(comps, adjs, TODAY)
    const check = checks.find(c => c.id === 'gross-adjustment')!
    expect(check.pass).toBe(true)
    expect(check.message).toBeNull()
  })

  it('today param defaults without error', () => {
    expect(() => buildOEAQChecklist([], [])).not.toThrow()
  })
})
