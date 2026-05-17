import { describe, it, expect } from 'vitest'
import { computeComparableDateSpread } from './compute-comparable-date-spread'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: 100, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 400000, sale_date, meta: '', price: '400000', date: sale_date }
}

function monthsAgo(n: number): string {
  const d = new Date()
  d.setMonth(d.getMonth() - n)
  return d.toISOString().slice(0, 10)
}

describe('computeComparableDateSpread', () => {
  it('returns null for fewer than 2 comparables', () => {
    expect(computeComparableDateSpread([mkComp('a', '2024-01-01')])).toBeNull()
    expect(computeComparableDateSpread([])).toBeNull()
  })

  it('minDate and maxDate are correct', () => {
    const comps = [mkComp('a', '2022-01-01'), mkComp('b', '2024-06-01'), mkComp('c', '2023-03-01')]
    const r = computeComparableDateSpread(comps)!
    expect(r.minDate).toBe('2022-01-01')
    expect(r.maxDate).toBe('2024-06-01')
  })

  it('spanMonths is months between earliest and latest', () => {
    const comps = [mkComp('a', '2022-01-01'), mkComp('b', '2024-01-01')]
    expect(computeComparableDateSpread(comps)!.spanMonths).toBe(24)
  })

  it('recent12mCount counts comps within 12 months', () => {
    const comps = [
      mkComp('a', monthsAgo(6)),
      mkComp('b', monthsAgo(10)),
      mkComp('c', monthsAgo(18)),
    ]
    expect(computeComparableDateSpread(comps)!.recent12mCount).toBe(2)
  })

  it('staleCount counts comps older than 24 months', () => {
    const comps = [
      mkComp('a', monthsAgo(6)),
      mkComp('b', monthsAgo(30)),
      mkComp('c', monthsAgo(36)),
    ]
    expect(computeComparableDateSpread(comps)!.staleCount).toBe(2)
  })

  it('recencyScore is récent when >=75% within 12 months', () => {
    const comps = [mkComp('a', monthsAgo(3)), mkComp('b', monthsAgo(6)), mkComp('c', monthsAgo(9)), mkComp('d', monthsAgo(30))]
    // 3/4 = 75%
    expect(computeComparableDateSpread(comps)!.recencyScore).toBe('récent')
  })

  it('recencyScore is daté when >=50% stale', () => {
    const comps = [mkComp('a', monthsAgo(30)), mkComp('b', monthsAgo(36)), mkComp('c', monthsAgo(6))]
    // 2/3 stale
    expect(computeComparableDateSpread(comps)!.recencyScore).toBe('daté')
  })

  it('recencyScore is mixte otherwise', () => {
    const comps = [mkComp('a', monthsAgo(6)), mkComp('b', monthsAgo(18)), mkComp('c', monthsAgo(30))]
    expect(computeComparableDateSpread(comps)!.recencyScore).toBe('mixte')
  })
})
