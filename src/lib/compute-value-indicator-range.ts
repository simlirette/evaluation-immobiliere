import type { Adjustment } from '@/types'

export interface ValueIndicatorRange {
  q1: number
  q3: number
  iqr: number
  midpoint: number
  iqrPct: number
}

export function computeValueIndicatorRange(adjs: Adjustment[]): ValueIndicatorRange | null {
  if (adjs.length < 4) return null

  const sorted = [...adjs.map(a => a.adjusted)].sort((a, b) => a - b)
  const n = sorted.length

  const q1 = n % 4 === 0
    ? (sorted[n / 4 - 1] + sorted[n / 4]) / 2
    : sorted[Math.floor(n / 4)]
  const q3 = n % 4 === 0
    ? (sorted[3 * n / 4 - 1] + sorted[3 * n / 4]) / 2
    : sorted[Math.floor(3 * n / 4)]

  const iqr = q3 - q1
  const midpoint = (q1 + q3) / 2
  const iqrPct = midpoint > 0 ? (iqr / midpoint) * 100 : 0

  return { q1, q3, iqr, midpoint, iqrPct }
}
