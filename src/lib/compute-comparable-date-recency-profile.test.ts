import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { computeComparableDateRecencyProfile } from './compute-comparable-date-recency-profile'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string): Comparable {
  return { id, rank: id, address: `Addr ${id}`, hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 300000, sale_date, meta: '', price: '', date: '' }
}

const NOW = new Date('2026-01-01').getTime()

beforeEach(() => { vi.useFakeTimers(); vi.setSystemTime(NOW) })
afterEach(() => { vi.useRealTimers() })

describe('computeComparableDateRecencyProfile', () => {
  it('returns null for empty array', () => {
    expect(computeComparableDateRecencyProfile([])).toBeNull()
  })

  it('récent when ≤ 12 months ago', () => {
    const r = computeComparableDateRecencyProfile([mkComp('a', '2025-07-01')])!
    expect(r.entries[0].recency).toBe('récent')
  })

  it('modéré when 12–24 months ago', () => {
    const r = computeComparableDateRecencyProfile([mkComp('a', '2024-06-01')])!
    expect(r.entries[0].recency).toBe('modéré')
  })

  it('daté when > 24 months ago', () => {
    const r = computeComparableDateRecencyProfile([mkComp('a', '2023-06-01')])!
    expect(r.entries[0].recency).toBe('daté')
  })

  it('counts per recency category', () => {
    const r = computeComparableDateRecencyProfile([
      mkComp('a', '2025-07-01'), // récent
      mkComp('b', '2024-06-01'), // modéré
      mkComp('c', '2023-06-01'), // daté
    ])!
    expect(r.recentCount).toBe(1)
    expect(r.moderateCount).toBe(1)
    expect(r.staleCount).toBe(1)
  })

  it('stalePct = staleCount/total × 100 rounded', () => {
    const r = computeComparableDateRecencyProfile([
      mkComp('a', '2023-06-01'), // daté
      mkComp('b', '2023-06-01'), // daté
      mkComp('c', '2025-07-01'), // récent
    ])!
    expect(r.stalePct).toBe(67)
  })

  it('entries include monthsAgo > 0', () => {
    const r = computeComparableDateRecencyProfile([mkComp('a', '2025-06-01')])!
    expect(r.entries[0].monthsAgo).toBeGreaterThan(0)
  })

  it('one entry per comp', () => {
    const r = computeComparableDateRecencyProfile([mkComp('a', '2025-01-01'), mkComp('b', '2024-01-01')])!
    expect(r.entries).toHaveLength(2)
  })
})
