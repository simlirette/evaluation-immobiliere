import type { Comparable } from '@/types'

export interface ComparableSimilarityEntry {
  comparableId: string
  comparableLabel: string
  /** 0–100. Higher = more similar to subject */
  score: number
  /** |comp.hab_m2 - subject.hab_m2| / subject.hab_m2 × 100, null if data missing */
  sizeDiffPct: number | null
  /** |comp.year_built - subject.year_built|, null if data missing */
  ageDiff: number | null
}

export interface SubjectProfile {
  hab_m2?: number | null
  year_built?: number | null
}

/**
 * Scores each comparable's similarity to a subject profile.
 *
 * Size score (0–50): max(0, 50 − |sizeDiffPct| × 2.5) — 0% diff = 50, 20%+ = 0.
 * Age score  (0–50): max(0, 50 − ageDiff × 2.5)        — 0 yr diff = 50, 20+ yr = 0.
 * When only one factor is available, that factor is scaled ×2 to keep range 0–100.
 *
 * Returns null when subject has neither hab_m2 nor year_built.
 */
export function computeComparableSimilarityScore(
  comparables: Comparable[],
  subject: SubjectProfile,
): ComparableSimilarityEntry[] | null {
  const hasSize = subject.hab_m2 != null && subject.hab_m2 > 0
  const hasAge = subject.year_built != null

  if (!hasSize && !hasAge) return null

  return comparables.map(c => {
    let sizeDiffPct: number | null = null
    let ageDiff: number | null = null
    let sizeScore = 0
    let ageScore = 0

    if (hasSize && c.hab_m2 != null && c.hab_m2 > 0) {
      sizeDiffPct = Math.round(Math.abs(c.hab_m2 - subject.hab_m2!) / subject.hab_m2! * 1000) / 10
      sizeScore = Math.max(0, 50 - sizeDiffPct * 2.5)
    }

    if (hasAge && c.year_built != null) {
      ageDiff = Math.abs(c.year_built - subject.year_built!)
      ageScore = Math.max(0, 50 - ageDiff * 2.5)
    }

    // Normalize when only one factor available
    let score: number
    const factorCount = (hasSize ? 1 : 0) + (hasAge ? 1 : 0)
    const earned = sizeScore + ageScore
    score = Math.round(factorCount === 1 ? earned * 2 : earned)

    return {
      comparableId: c.id,
      comparableLabel: c.address,
      score,
      sizeDiffPct,
      ageDiff,
    }
  })
}
