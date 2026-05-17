import { describe, it, expect } from 'vitest'
import { computeLotSizeAnalysis } from './compute-lot-size-analysis'
import type { Comparable } from '@/types'

function mkComp(id: string, terrain_m2: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2, year_built: null, renovated_year: null, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01' }
}

describe('computeLotSizeAnalysis', () => {
  it('returns null for fewer than 2 comps with terrain_m2', () => {
    expect(computeLotSizeAnalysis([mkComp('a', null)])).toBeNull()
    expect(computeLotSizeAnalysis([mkComp('a', 500)])).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(computeLotSizeAnalysis([])).toBeNull()
  })

  it('computes min and max', () => {
    const comps = [mkComp('a', 300), mkComp('b', 500), mkComp('c', 700)]
    const r = computeLotSizeAnalysis(comps)!
    expect(r.min).toBe(300)
    expect(r.max).toBe(700)
  })

  it('median for odd count', () => {
    const comps = [mkComp('a', 300), mkComp('b', 500), mkComp('c', 700)]
    expect(computeLotSizeAnalysis(comps)!.median).toBe(500)
  })

  it('median for even count', () => {
    const comps = [mkComp('a', 300), mkComp('b', 400), mkComp('c', 500), mkComp('d', 600)]
    expect(computeLotSizeAnalysis(comps)!.median).toBe(450)
  })

  it('count excludes null terrain_m2', () => {
    const comps = [mkComp('a', 500), mkComp('b', null), mkComp('c', 700)]
    const r = computeLotSizeAnalysis(comps)!
    expect(r.count).toBe(2)
    expect(r.missingCount).toBe(1)
  })

  it('cvPct is 0 when all values identical', () => {
    const comps = [mkComp('a', 500), mkComp('b', 500), mkComp('c', 500)]
    expect(computeLotSizeAnalysis(comps)!.cvPct).toBe(0)
  })

  it('cvPct is positive when spread exists', () => {
    const comps = [mkComp('a', 200), mkComp('b', 800), mkComp('c', 1400)]
    expect(computeLotSizeAnalysis(comps)!.cvPct).toBeGreaterThan(0)
  })

  it('excludes terrain_m2 <= 0', () => {
    const comps = [mkComp('a', 0), mkComp('b', 500), mkComp('c', 700)]
    const r = computeLotSizeAnalysis(comps)!
    expect(r.count).toBe(2)
    expect(r.missingCount).toBe(1)
  })
})
