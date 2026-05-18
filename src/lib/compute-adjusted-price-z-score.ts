import type { Adjustment } from '@/types'

export interface AdjustedPriceZScoreEntry {
  id: string
  comparableLabel: string
  adjustedPrice: number
  zScore: number
  outlier: boolean
}

export interface AdjustedPriceZScore {
  entries: AdjustedPriceZScoreEntry[]
  mean: number
  stdDev: number
  outlierIds: string[]
}

const OUTLIER_Z = 2

export function computeAdjustedPriceZScore(adjs: Adjustment[]): AdjustedPriceZScore | null {
  if (adjs.length < 3) return null

  const prices = adjs.map(a => a.adjusted)
  const mean = prices.reduce((s, v) => s + v, 0) / prices.length
  const variance = prices.reduce((s, v) => s + (v - mean) ** 2, 0) / prices.length
  const stdDev = Math.sqrt(variance)

  if (stdDev === 0) {
    const entries = adjs.map(a => ({ id: a.id, comparableLabel: a.comparableLabel, adjustedPrice: a.adjusted, zScore: 0, outlier: false }))
    return { entries, mean, stdDev, outlierIds: [] }
  }

  const entries: AdjustedPriceZScoreEntry[] = adjs.map(a => {
    const zScore = (a.adjusted - mean) / stdDev
    return { id: a.id, comparableLabel: a.comparableLabel, adjustedPrice: a.adjusted, zScore, outlier: Math.abs(zScore) > OUTLIER_Z }
  })

  return { entries, mean, stdDev, outlierIds: entries.filter(e => e.outlier).map(e => e.id) }
}
