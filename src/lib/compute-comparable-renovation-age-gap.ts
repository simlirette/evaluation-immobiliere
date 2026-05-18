import type { Comparable } from '@/types'

export interface ComparableRenovationAgeGap {
  count: number
  avgGap: number
  minGap: number
  maxGap: number
  recentlyRenovatedCount: number
}

const RECENT_YEARS = 10

export function computeComparableRenovationAgeGap(comps: Comparable[]): ComparableRenovationAgeGap | null {
  const currentYear = new Date().getFullYear()

  const gaps = comps
    .filter(c => c.year_built != null && c.renovated_year != null && c.renovated_year > c.year_built!)
    .map(c => ({
      gap: c.renovated_year! - c.year_built!,
      recentlyRenovated: currentYear - c.renovated_year! <= RECENT_YEARS,
    }))

  if (gaps.length === 0) return null

  const gapValues = gaps.map(g => g.gap)
  const avgGap = gapValues.reduce((s, v) => s + v, 0) / gapValues.length
  const recentlyRenovatedCount = gaps.filter(g => g.recentlyRenovated).length

  return {
    count: gaps.length,
    avgGap,
    minGap: Math.min(...gapValues),
    maxGap: Math.max(...gapValues),
    recentlyRenovatedCount,
  }
}
