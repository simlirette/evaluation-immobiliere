import { describe, it, expect } from 'vitest'
import { buildAdjustmentsCsv } from './build-adjustments-csv'
import type { Adjustment } from '@/types'

function mkAdj(label: string, overrides: Partial<Adjustment> = {}): Adjustment {
  return {
    id: label, comparable_id: label, comparableLabel: label,
    salePrice: 400000,
    surface_adj: 10000, year_adj: -5000, condition_adj: 0, garage_adj: 0,
    adjusted: 405000,
    ...overrides,
  }
}

describe('buildAdjustmentsCsv', () => {
  it('includes header row', () => {
    const csv = buildAdjustmentsCsv([])
    const header = csv.split('\n')[0]
    expect(header).toContain('Comparable')
    expect(header).toContain('Net adj.')
    expect(header).toContain('Brut adj.')
    expect(header).toContain('Prix ajusté')
  })

  it('empty adjs → header only', () => {
    expect(buildAdjustmentsCsv([]).split('\n')).toHaveLength(1)
  })

  it('single adj → 2 lines', () => {
    expect(buildAdjustmentsCsv([mkAdj('A')]).split('\n')).toHaveLength(2)
  })

  it('includes comparable label and sale price', () => {
    const csv = buildAdjustmentsCsv([mkAdj('10 rue Laval', { salePrice: 420000 })])
    expect(csv).toContain('10 rue Laval')
    expect(csv).toContain('420000')
  })

  it('net and gross percentages included', () => {
    // net = 10000-5000 = 5000 on 400000 = 1.25%; gross = 15000/400000 = 3.75%
    const csv = buildAdjustmentsCsv([mkAdj('A')])
    expect(csv).toContain('1.3')   // net pct rounded
    expect(csv).toContain('3.8')   // gross pct rounded
  })

  it('adjusted price in last column', () => {
    const csv = buildAdjustmentsCsv([mkAdj('A', { adjusted: 415000 })])
    const dataRow = csv.split('\n')[1]
    const cells = dataRow.split(',')
    expect(cells[cells.length - 1]).toBe('415000')
  })

  it('label with comma is quoted', () => {
    const csv = buildAdjustmentsCsv([mkAdj('Apt. 3, 10 rue Test')])
    expect(csv).toContain('"Apt. 3, 10 rue Test"')
  })

  it('multiple adjs produce correct row count', () => {
    const adjs = ['A', 'B', 'C'].map(l => mkAdj(l))
    expect(buildAdjustmentsCsv(adjs).split('\n')).toHaveLength(4)
  })
})
