import { describe, it, expect } from 'vitest'
import { computeComparableSaleDateGapAnalysis } from './compute-comparable-sale-date-gap-analysis'
import type { Comparable } from '@/types'

function mkComp(id: string, sale_date: string): Comparable {
  return { id, rank: id, address: '', hab_m2: null, terrain_m2: null, year_built: null, renovated_year: null, garage_type: null, sale_price: 300000, sale_date, meta: '', price: '', date: '' }
}

describe('computeComparableSaleDateGapAnalysis', () => {
  it('returns null for < 2 comps', () => {
    expect(computeComparableSaleDateGapAnalysis([])).toBeNull()
    expect(computeComparableSaleDateGapAnalysis([mkComp('a', '2024-01-01')])).toBeNull()
  })

  it('gapCount = comps.length - 1', () => {
    const r = computeComparableSaleDateGapAnalysis([
      mkComp('a', '2023-01-01'),
      mkComp('b', '2023-07-01'),
      mkComp('c', '2024-01-01'),
    ])!
    expect(r.gapCount).toBe(2)
  })

  it('sorts by date before computing gaps', () => {
    // Reversed input
    const r = computeComparableSaleDateGapAnalysis([
      mkComp('b', '2024-01-01'),
      mkComp('a', '2023-01-01'),
    ])!
    expect(r.maxGap).toBeGreaterThan(0)
  })

  it('maxGap is largest consecutive gap in months', () => {
    // gap1: ~6mo, gap2: ~6mo → maxGap ≈ 6
    const r = computeComparableSaleDateGapAnalysis([
      mkComp('a', '2023-01-01'),
      mkComp('b', '2023-07-01'),
      mkComp('c', '2024-01-01'),
    ])!
    expect(r.maxGap).toBeGreaterThan(5)
    expect(r.maxGap).toBeLessThan(7)
  })

  it('largeGapCount = gaps > 12 months', () => {
    // gap: ~24 months → largeGapCount=1
    const r = computeComparableSaleDateGapAnalysis([
      mkComp('a', '2022-01-01'),
      mkComp('b', '2024-01-01'),
    ])!
    expect(r.largeGapCount).toBe(1)
  })

  it('largeGapCount = 0 when all gaps <= 12 months', () => {
    const r = computeComparableSaleDateGapAnalysis([
      mkComp('a', '2023-06-01'),
      mkComp('b', '2024-01-01'),
    ])!
    expect(r.largeGapCount).toBe(0)
  })

  it('meanGap = avg of all consecutive gaps', () => {
    // ~6mo gap × 2 → mean ≈ 6
    const r = computeComparableSaleDateGapAnalysis([
      mkComp('a', '2023-01-01'),
      mkComp('b', '2023-07-01'),
      mkComp('c', '2024-01-01'),
    ])!
    expect(r.meanGap).toBeGreaterThan(5)
    expect(r.meanGap).toBeLessThan(7)
  })
})
