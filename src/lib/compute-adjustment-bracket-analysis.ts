import type { Adjustment } from '@/types'

export interface BracketEntry {
  comparableId: string
  comparableLabel: string
  adjustedPrice: number
  /** 'below' adjusted < subject, 'above' adjusted > subject, 'equal' adjusted === subject */
  position: 'below' | 'above' | 'equal'
}

export interface AdjustmentBracketAnalysis {
  /** Whether at least one comp's adjusted price is below the subject */
  hasBelow: boolean
  /** Whether at least one comp's adjusted price is above the subject */
  hasAbove: boolean
  /** True when both hasBelow and hasAbove are true — OEAQ bracketing requirement */
  isBracketed: boolean
  /** All comparables classified relative to the subject */
  entries: BracketEntry[]
  /** Closest comparable below subject (or null) */
  nearestBelow: BracketEntry | null
  /** Closest comparable above subject (or null) */
  nearestAbove: BracketEntry | null
}

/**
 * Classifies each comparable's adjusted price relative to a subject value and
 * determines whether the subject is properly bracketed (comps above AND below).
 *
 * Returns null when adjustments is empty or subjectValue ≤ 0.
 */
export function computeAdjustmentBracketAnalysis(
  adjs: Adjustment[],
  subjectValue: number,
): AdjustmentBracketAnalysis | null {
  if (adjs.length === 0 || subjectValue <= 0) return null

  const entries: BracketEntry[] = adjs.map(a => ({
    comparableId: a.comparable_id,
    comparableLabel: a.comparableLabel,
    adjustedPrice: a.adjusted,
    position: a.adjusted < subjectValue ? 'below' : a.adjusted > subjectValue ? 'above' : 'equal',
  }))

  const below = entries.filter(e => e.position === 'below').sort((a, b) => b.adjustedPrice - a.adjustedPrice)
  const above = entries.filter(e => e.position === 'above').sort((a, b) => a.adjustedPrice - b.adjustedPrice)

  return {
    hasBelow: below.length > 0,
    hasAbove: above.length > 0,
    isBracketed: below.length > 0 && above.length > 0,
    entries,
    nearestBelow: below[0] ?? null,
    nearestAbove: above[0] ?? null,
  }
}
