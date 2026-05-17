import type { Adjustment } from '@/types'

export type ConditionDirection = 'positive' | 'negative' | 'neutral'

export interface AdjustmentConditionBias {
  countPositive: number
  countNegative: number
  countZero: number
  avgWhenApplied: number | null
  dominantDirection: ConditionDirection
}

export function computeAdjustmentConditionBias(adjs: Adjustment[]): AdjustmentConditionBias | null {
  if (adjs.length === 0) return null

  let countPositive = 0
  let countNegative = 0
  let countZero = 0
  const applied: number[] = []

  for (const a of adjs) {
    if (a.condition_adj > 0) { countPositive++; applied.push(a.condition_adj) }
    else if (a.condition_adj < 0) { countNegative++; applied.push(a.condition_adj) }
    else countZero++
  }

  const avgWhenApplied = applied.length > 0
    ? applied.reduce((s, v) => s + v, 0) / applied.length
    : null

  let dominantDirection: ConditionDirection
  if (countPositive > countNegative && countPositive > countZero) dominantDirection = 'positive'
  else if (countNegative > countZero) dominantDirection = 'negative'
  else dominantDirection = 'neutral'

  return { countPositive, countNegative, countZero, avgWhenApplied, dominantDirection }
}
