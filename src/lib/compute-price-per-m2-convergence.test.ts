import { describe, it, expect } from 'vitest'
import { computePricePerM2Convergence } from './compute-price-per-m2-convergence'
import type { Comparable, Adjustment } from '@/types'

function mkComp(id: string, sale_price: number, hab_m2: number | null): Comparable {
  return { id, rank: id, address: '', hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price, sale_date: '2024-01-01', meta: '', price: '', date: '' }
}

function mkAdj(id: string, salePrice: number, adj: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice, surface_adj: adj, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted: salePrice + adj }
}

describe('computePricePerM2Convergence', () => {
  it('returns null when fewer than 2 valid pairs', () => {
    expect(computePricePerM2Convergence([], [])).toBeNull()
    expect(computePricePerM2Convergence([mkComp('a', 300000, null)], [mkAdj('a', 300000, 0)])).toBeNull()
  })

  it('returns null when comps have no hab_m2', () => {
    const comps = [mkComp('a', 300000, null), mkComp('b', 400000, null)]
    const adjs = [mkAdj('a', 300000, 0), mkAdj('b', 400000, 0)]
    expect(computePricePerM2Convergence(comps, adjs)).toBeNull()
  })

  it('converged true when adjustedM2CV < rawM2CV', () => {
    // raw $/m²: 200k/100=2000 and 400k/100=4000 → high spread
    // adj: both to 300k → 3000 each → CV=0 → converged
    const comps = [mkComp('a', 200000, 100), mkComp('b', 400000, 100)]
    const adjs = [mkAdj('a', 200000, 100000), mkAdj('b', 400000, -100000)]
    const r = computePricePerM2Convergence(comps, adjs)!
    expect(r.converged).toBe(true)
    expect(r.adjustedM2CV).toBeLessThan(r.rawM2CV)
  })

  it('converged false when adjustedM2CV >= rawM2CV', () => {
    // adj spreads prices further
    const comps = [mkComp('a', 300000, 100), mkComp('b', 300000, 100)]
    const adjs = [mkAdj('a', 300000, -100000), mkAdj('b', 300000, 100000)]
    const r = computePricePerM2Convergence(comps, adjs)!
    expect(r.converged).toBe(false)
  })

  it('delta = adjustedM2CV - rawM2CV', () => {
    const comps = [mkComp('a', 200000, 100), mkComp('b', 400000, 100)]
    const adjs = [mkAdj('a', 200000, 50000), mkAdj('b', 400000, -50000)]
    const r = computePricePerM2Convergence(comps, adjs)!
    expect(r.delta).toBeCloseTo(r.adjustedM2CV - r.rawM2CV, 5)
  })

  it('skips comps with no matching adjustment', () => {
    const comps = [mkComp('a', 200000, 100), mkComp('b', 400000, 100)]
    const adjs = [mkAdj('a', 200000, 0)]
    // only 1 valid pair → null
    expect(computePricePerM2Convergence(comps, adjs)).toBeNull()
  })

  it('rawM2CV > 0 when prices differ', () => {
    const comps = [mkComp('a', 200000, 100), mkComp('b', 400000, 100)]
    const adjs = [mkAdj('a', 200000, 0), mkAdj('b', 400000, 0)]
    const r = computePricePerM2Convergence(comps, adjs)!
    expect(r.rawM2CV).toBeGreaterThan(0)
  })
})
