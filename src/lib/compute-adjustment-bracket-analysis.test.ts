import { describe, it, expect } from 'vitest'
import { computeAdjustmentBracketAnalysis } from './compute-adjustment-bracket-analysis'
import type { Adjustment } from '@/types'

function mkAdj(id: string, adjusted: number): Adjustment {
  return { id, comparable_id: id, comparableLabel: `Comp ${id}`, salePrice: 400000, surface_adj: 0, year_adj: 0, condition_adj: 0, garage_adj: 0, adjusted }
}

describe('computeAdjustmentBracketAnalysis', () => {
  it('returns null for empty adjustments', () => {
    expect(computeAdjustmentBracketAnalysis([], 400000)).toBeNull()
  })

  it('returns null for subjectValue <= 0', () => {
    expect(computeAdjustmentBracketAnalysis([mkAdj('a', 400000)], 0)).toBeNull()
    expect(computeAdjustmentBracketAnalysis([mkAdj('a', 400000)], -1)).toBeNull()
  })

  it('isBracketed true when comps above and below subject', () => {
    const adjs = [mkAdj('a', 380000), mkAdj('b', 420000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.isBracketed).toBe(true)
    expect(r.hasBelow).toBe(true)
    expect(r.hasAbove).toBe(true)
  })

  it('isBracketed false when all comps above subject', () => {
    const adjs = [mkAdj('a', 420000), mkAdj('b', 430000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.isBracketed).toBe(false)
    expect(r.hasBelow).toBe(false)
    expect(r.hasAbove).toBe(true)
  })

  it('isBracketed false when all comps below subject', () => {
    const adjs = [mkAdj('a', 360000), mkAdj('b', 390000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.isBracketed).toBe(false)
    expect(r.hasAbove).toBe(false)
  })

  it('classifies equal adjusted price as equal', () => {
    const adjs = [mkAdj('a', 400000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.entries[0].position).toBe('equal')
    expect(r.isBracketed).toBe(false)
  })

  it('nearestBelow is closest comp with adjusted < subject', () => {
    const adjs = [mkAdj('a', 350000), mkAdj('b', 390000), mkAdj('c', 420000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.nearestBelow?.comparableId).toBe('b')
    expect(r.nearestBelow?.adjustedPrice).toBe(390000)
  })

  it('nearestAbove is closest comp with adjusted > subject', () => {
    const adjs = [mkAdj('a', 380000), mkAdj('b', 410000), mkAdj('c', 450000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.nearestAbove?.comparableId).toBe('b')
    expect(r.nearestAbove?.adjustedPrice).toBe(410000)
  })

  it('nearestBelow null when no comp below', () => {
    const r = computeAdjustmentBracketAnalysis([mkAdj('a', 420000)], 400000)!
    expect(r.nearestBelow).toBeNull()
  })

  it('nearestAbove null when no comp above', () => {
    const r = computeAdjustmentBracketAnalysis([mkAdj('a', 380000)], 400000)!
    expect(r.nearestAbove).toBeNull()
  })

  it('entries length matches adjustments count', () => {
    const adjs = [mkAdj('a', 380000), mkAdj('b', 400000), mkAdj('c', 420000)]
    const r = computeAdjustmentBracketAnalysis(adjs, 400000)!
    expect(r.entries).toHaveLength(3)
  })
})
