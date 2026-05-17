import type { Comparable } from '@/types'

export interface BuildingAgeStats {
  /** Number of comps with valid year_built and sale_date */
  count: number
  min: number
  max: number
  median: number
  avgAge: number
  missingCount: number
}

/**
 * Computes the age of each comparable at time of sale (sale_date year − year_built),
 * then aggregates into statistics across the set.
 *
 * Returns null when fewer than 2 comparables have both year_built and sale_date.
 */
export function computeBuildingAgeStats(comps: Comparable[]): BuildingAgeStats | null {
  const ages = comps
    .filter(c => c.year_built != null && c.sale_date)
    .map(c => parseInt(c.sale_date.slice(0, 4), 10) - c.year_built!)
    .filter(age => age >= 0)

  const missingCount = comps.length - ages.length

  if (ages.length < 2) return null

  const sorted = [...ages].sort((a, b) => a - b)
  const min = sorted[0]
  const max = sorted[sorted.length - 1]
  const mid = Math.floor(sorted.length / 2)
  const median = sorted.length % 2 === 0
    ? Math.round((sorted[mid - 1] + sorted[mid]) / 2)
    : sorted[mid]
  const avgAge = Math.round(ages.reduce((s, v) => s + v, 0) / ages.length)

  return { count: ages.length, min, max, median, avgAge, missingCount }
}
