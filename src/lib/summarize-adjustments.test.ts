import { describe, it, expect } from 'vitest'
import { summarizeAdjustments } from './summarize-adjustments'
import type { Adjustment } from '@/types'

function mkAdj(adjusted: number): Adjustment {
  return {
    id: String(adjusted),
    comparable_id: 'c1',
    comparableLabel: 'Test',
    salePrice: 400000,
    surface_adj: 0,
    year_adj: 0,
    condition_adj: 0,
    garage_adj: 0,
    adjusted,
  }
}

describe('summarizeAdjustments', () => {
  it('empty array → null', () => {
    expect(summarizeAdjustments([])).toBeNull()
  })

  it('single row — avg/min/max equal adjusted, spread 0', () => {
    const result = summarizeAdjustments([mkAdj(500000)])
    expect(result).toEqual({ avg: 500000, min: 500000, max: 500000, spread: 0 })
  })

  it('two rows — correct avg, min, max, spread', () => {
    const result = summarizeAdjustments([mkAdj(400000), mkAdj(600000)])
    expect(result).toEqual({ avg: 500000, min: 400000, max: 600000, spread: 200000 })
  })

  it('three rows — avg rounds to integer', () => {
    const result = summarizeAdjustments([mkAdj(300000), mkAdj(400000), mkAdj(500000)])
    expect(result?.avg).toBe(400000)
    expect(result?.spread).toBe(200000)
  })

  it('avg rounds correctly for non-divisible totals', () => {
    const result = summarizeAdjustments([mkAdj(100000), mkAdj(200000), mkAdj(300001)])
    // 600001 / 3 = 200000.33... → rounds to 200000
    expect(result?.avg).toBe(200000)
  })

  it('min is the smallest adjusted value', () => {
    const rows = [mkAdj(550000), mkAdj(480000), mkAdj(620000)]
    expect(summarizeAdjustments(rows)?.min).toBe(480000)
  })

  it('max is the largest adjusted value', () => {
    const rows = [mkAdj(550000), mkAdj(480000), mkAdj(620000)]
    expect(summarizeAdjustments(rows)?.max).toBe(620000)
  })
})
