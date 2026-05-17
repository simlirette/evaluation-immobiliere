import type { Adjustment } from '@/types'
import { computeMedianIndicatedValue } from './compute-median-indicated-value'
import { summarizeAdjustments } from './summarize-adjustments'

export interface SubjectContext {
  conclusion: number
  median: number
  min: number
  max: number
  withinRange: boolean
  deviationFromMedianPct: number   // positive = above median, negative = below
  direction: 'above' | 'below' | 'at'
}

/**
 * Computes how the proposed conclusion relates to the comparable set's indicated values.
 * Gives evaluators a quick sense of whether the conclusion is well-supported by the comps.
 * Returns null when adjustments are empty or conclusion cannot be compared.
 */
export function computeSubjectContext(
  conclusion: number,
  adjs: Adjustment[],
): SubjectContext | null {
  if (adjs.length === 0) return null
  const summary = summarizeAdjustments(adjs)
  const median = computeMedianIndicatedValue(adjs)
  if (!summary || median == null) return null

  const deviationFromMedianPct = ((conclusion - median) / median) * 100
  const direction: 'above' | 'below' | 'at' =
    Math.abs(deviationFromMedianPct) < 0.01 ? 'at'
    : deviationFromMedianPct > 0 ? 'above'
    : 'below'

  return {
    conclusion,
    median,
    min: summary.min,
    max: summary.max,
    withinRange: conclusion >= summary.min && conclusion <= summary.max,
    deviationFromMedianPct: Math.round(deviationFromMedianPct * 10) / 10,
    direction,
  }
}
