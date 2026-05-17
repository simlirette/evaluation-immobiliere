import { describe, it, expect } from 'vitest'
import { computeComparableSizeRange } from './compute-comparable-size-range'
import type { Comparable } from '@/types'

function mkComp(id: string, hab_m2: number | null): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 400000, sale_date: '2024-01-01', meta: '', price: '400000', date: '2024-01-01' }
}

describe('computeComparableSizeRange', () => {
  it('returns null when subjectHabM2 is null', () => {
    expect(computeComparableSizeRange([mkComp('a', 100), mkComp('b', 120)], null)).toBeNull()
  })

  it('returns null when subjectHabM2 is 0', () => {
    expect(computeComparableSizeRange([mkComp('a', 100), mkComp('b', 120)], 0)).toBeNull()
  })

  it('returns null when fewer than 2 comps have hab_m2', () => {
    expect(computeComparableSizeRange([mkComp('a', 100), mkComp('b', null)], 100)).toBeNull()
  })

  it('bracketed true when subject inside range', () => {
    const r = computeComparableSizeRange([mkComp('a', 80), mkComp('b', 120)], 100)!
    expect(r.bracketed).toBe(true)
    expect(r.min).toBe(80)
    expect(r.max).toBe(120)
  })

  it('bracketed false when subject above range', () => {
    const r = computeComparableSizeRange([mkComp('a', 80), mkComp('b', 90)], 110)!
    expect(r.bracketed).toBe(false)
    expect(r.nearestAbove).toBeNull()
    expect(r.nearestBelow).not.toBeNull()
  })

  it('bracketed false when subject below range', () => {
    const r = computeComparableSizeRange([mkComp('a', 110), mkComp('b', 130)], 90)!
    expect(r.bracketed).toBe(false)
    expect(r.nearestBelow).toBeNull()
    expect(r.nearestAbove).not.toBeNull()
  })

  it('nearestBelow is closest comp smaller than subject', () => {
    const r = computeComparableSizeRange([mkComp('a', 70), mkComp('b', 90), mkComp('c', 120)], 100)!
    expect(r.nearestBelow?.hab_m2).toBe(90)
  })

  it('nearestAbove is closest comp larger than subject', () => {
    const r = computeComparableSizeRange([mkComp('a', 80), mkComp('b', 110), mkComp('c', 130)], 100)!
    expect(r.nearestAbove?.hab_m2).toBe(110)
  })

  it('missingCount counts comps with null hab_m2', () => {
    const r = computeComparableSizeRange([mkComp('a', 80), mkComp('b', null), mkComp('c', 120), mkComp('d', null)], 100)!
    expect(r.missingCount).toBe(2)
  })

  it('bracketed true when subject equals min', () => {
    const r = computeComparableSizeRange([mkComp('a', 100), mkComp('b', 130)], 100)!
    expect(r.bracketed).toBe(true)
  })
})
