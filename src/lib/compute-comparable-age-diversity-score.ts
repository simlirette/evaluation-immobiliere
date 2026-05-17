import type { Comparable } from '@/types'

export interface ComparableAgeDiversityScore {
  count: number
  minYear: number
  maxYear: number
  /** maxYear − minYear */
  range: number
  stdDev: number
  /** Number of distinct decades represented (e.g. 1990s, 2000s, 2010s) */
  decadeCount: number
  /**
   * 0–100. Based on range (0–60 pts) and decade spread (0–40 pts).
   * range/100 × 60 + min(decadeCount, 4) × 10 — capped at 100.
   */
  diversityScore: number
  /** 'faible' < 40, 'modérée' < 70, 'élevée' ≥ 70 */
  diversity: 'faible' | 'modérée' | 'élevée'
}

/**
 * Measures how spread the construction years are across the comparable set.
 * A diverse set covers multiple decades; a narrow set may not represent the
 * full range of building vintages in the market.
 *
 * Returns null when fewer than 2 comparables have year_built.
 */
export function computeComparableAgeDiversityScore(
  comps: Comparable[],
): ComparableAgeDiversityScore | null {
  const years = comps.filter(c => c.year_built != null).map(c => c.year_built!)
  if (years.length < 2) return null

  const minYear = Math.min(...years)
  const maxYear = Math.max(...years)
  const range = maxYear - minYear

  const mean = years.reduce((s, y) => s + y, 0) / years.length
  const variance = years.reduce((s, y) => s + (y - mean) ** 2, 0) / years.length
  const stdDev = Math.round(Math.sqrt(variance))

  const decades = new Set(years.map(y => Math.floor(y / 10) * 10))
  const decadeCount = decades.size

  const diversityScore = Math.min(100, Math.round((range / 100) * 60 + Math.min(decadeCount, 4) * 10))
  const diversity: ComparableAgeDiversityScore['diversity'] =
    diversityScore >= 70 ? 'élevée' : diversityScore >= 40 ? 'modérée' : 'faible'

  return { count: years.length, minYear, maxYear, range, stdDev, decadeCount, diversityScore, diversity }
}
