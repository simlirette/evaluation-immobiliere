import type { Adjustment } from '@/types'

export interface MedianAdjustedPrice {
  median: number
  reconciledValue: number
  delta: number
  deltaPct: number
}

export function computeMedianAdjustedPrice(adjs: Adjustment[], reconciledValue: number): MedianAdjustedPrice | null {
  if (adjs.length < 2 || reconciledValue <= 0) return null

  const sorted = [...adjs.map(a => a.adjusted)].sort((a, b) => a - b)
  const n = sorted.length
  const median = n % 2 === 1
    ? sorted[Math.floor(n / 2)]
    : (sorted[n / 2 - 1] + sorted[n / 2]) / 2

  const delta = reconciledValue - median
  const deltaPct = (delta / median) * 100

  return { median, reconciledValue, delta, deltaPct }
}
