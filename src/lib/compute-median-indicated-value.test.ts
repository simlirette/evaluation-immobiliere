import { describe, it, expect } from 'vitest'
import { computeMedianIndicatedValue } from './compute-median-indicated-value'
import type { Adjustment } from '@/types'

function mkAdj(adjusted: number): Adjustment {
  return {
    id: String(adjusted), comparable_id: String(adjusted),
    comparableLabel: String(adjusted), salePrice: 400000,
    surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0,
    adjusted,
  }
}

describe('computeMedianIndicatedValue', () => {
  it('empty → null', () => {
    expect(computeMedianIndicatedValue([])).toBeNull()
  })

  it('single element → itself', () => {
    expect(computeMedianIndicatedValue([mkAdj(500000)])).toBe(500000)
  })

  it('odd count → middle value', () => {
    const adjs = [300000, 500000, 400000].map(mkAdj)
    expect(computeMedianIndicatedValue(adjs)).toBe(400000)
  })

  it('even count → average of two middle values', () => {
    const adjs = [300000, 400000, 500000, 600000].map(mkAdj)
    expect(computeMedianIndicatedValue(adjs)).toBe(450000)
  })

  it('already sorted', () => {
    const adjs = [100000, 200000, 300000].map(mkAdj)
    expect(computeMedianIndicatedValue(adjs)).toBe(200000)
  })

  it('reverse sorted', () => {
    const adjs = [600000, 400000, 200000].map(mkAdj)
    expect(computeMedianIndicatedValue(adjs)).toBe(400000)
  })

  it('all same value → that value', () => {
    const adjs = [350000, 350000, 350000].map(mkAdj)
    expect(computeMedianIndicatedValue(adjs)).toBe(350000)
  })

  it('does not mutate input array', () => {
    const adjs = [600000, 200000, 400000].map(mkAdj)
    const original = adjs.map(a => a.adjusted)
    computeMedianIndicatedValue(adjs)
    expect(adjs.map(a => a.adjusted)).toEqual(original)
  })
})
