import type { Adjustment } from '@/types'

export interface AdjustmentSummary {
  avg: number
  min: number
  max: number
  spread: number
}

/**
 * Computes avg/min/max/spread of adjusted prices from a set of adjustments.
 * Returns null for empty input.
 */
export function summarizeAdjustments(rows: Adjustment[]): AdjustmentSummary | null {
  if (rows.length === 0) return null
  const values = rows.map(r => r.adjusted)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const avg = Math.round(values.reduce((s, v) => s + v, 0) / values.length)
  return { avg, min, max, spread: max - min }
}
