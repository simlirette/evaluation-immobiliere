import type { Comparable } from '@/types'

export interface RenovationProfile {
  /** Comparables with a renovated_year value */
  renovatedCount: number
  /** renovatedCount / total × 100 */
  renovatedPct: number
  /** Average years since renovation (relative to current year) */
  avgRenovationAge: number | null
  /** IDs of comparables renovated within the last 10 years */
  recentlyRenovatedIds: string[]
}

/**
 * Profiles the renovation status of a comparable set.
 * Returns null when no comparables provided.
 */
export function computeRenovationProfile(comps: Comparable[]): RenovationProfile | null {
  if (comps.length === 0) return null

  const currentYear = new Date().getFullYear()
  const renovated = comps.filter(c => c.renovated_year != null)
  const renovatedCount = renovated.length
  const renovatedPct = Math.round((renovatedCount / comps.length) * 1000) / 10

  const renovationAges = renovated.map(c => currentYear - c.renovated_year!)
  const avgRenovationAge = renovationAges.length > 0
    ? Math.round(renovationAges.reduce((s, v) => s + v, 0) / renovationAges.length)
    : null

  const recentlyRenovatedIds = renovated
    .filter(c => currentYear - c.renovated_year! <= 10)
    .map(c => c.id)

  return { renovatedCount, renovatedPct, avgRenovationAge, recentlyRenovatedIds }
}
