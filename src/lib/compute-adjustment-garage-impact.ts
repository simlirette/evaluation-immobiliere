import type { Adjustment } from '@/types'

export type GarageDirection = 'positive' | 'negative' | 'neutral'

export interface AdjustmentGarageImpact {
  countPositive: number
  countNegative: number
  countZero: number
  avgWhenApplied: number | null
  dominantDirection: GarageDirection
}

export function computeAdjustmentGarageImpact(adjs: Adjustment[]): AdjustmentGarageImpact | null {
  if (adjs.length === 0) return null

  let countPositive = 0
  let countNegative = 0
  let countZero = 0
  const applied: number[] = []

  for (const a of adjs) {
    if (a.garage_adj > 0) { countPositive++; applied.push(a.garage_adj) }
    else if (a.garage_adj < 0) { countNegative++; applied.push(a.garage_adj) }
    else countZero++
  }

  const avgWhenApplied = applied.length > 0
    ? applied.reduce((s, v) => s + v, 0) / applied.length
    : null

  let dominantDirection: GarageDirection
  if (countPositive > countNegative && countPositive > countZero) dominantDirection = 'positive'
  else if (countNegative > countZero) dominantDirection = 'negative'
  else dominantDirection = 'neutral'

  return { countPositive, countNegative, countZero, avgWhenApplied, dominantDirection }
}
