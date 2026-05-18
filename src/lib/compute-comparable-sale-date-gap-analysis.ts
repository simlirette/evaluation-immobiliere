import type { Comparable } from '@/types'

export interface ComparableSaleDateGapAnalysis {
  gapCount: number
  maxGap: number
  meanGap: number
  largeGapCount: number
}

const MS_PER_MONTH = 1000 * 60 * 60 * 24 * 30.4375

export function computeComparableSaleDateGapAnalysis(comps: Comparable[]): ComparableSaleDateGapAnalysis | null {
  if (comps.length < 2) return null

  const sorted = [...comps]
    .sort((a, b) => a.sale_date.localeCompare(b.sale_date))
    .map(c => new Date(c.sale_date).getTime())

  const gaps: number[] = []
  for (let i = 1; i < sorted.length; i++) {
    gaps.push((sorted[i] - sorted[i - 1]) / MS_PER_MONTH)
  }

  const maxGap = Math.max(...gaps)
  const meanGap = gaps.reduce((s, v) => s + v, 0) / gaps.length
  const largeGapCount = gaps.filter(g => g > 12).length

  return { gapCount: gaps.length, maxGap, meanGap, largeGapCount }
}
