import type { ComparableQualityScore } from './compute-comparable-quality-score'
import type { ComparableSimilarityEntry } from './compute-comparable-similarity-score'

export interface ComparableSelectionSummary {
  count: number
  avgQualityScore: number
  /** null when no similarity data is available */
  avgSimilarityScore: number | null
  /** Number of comparables with quality score < 5 */
  lowQualityCount: number
  /** 'forte' when avgQuality ≥ 7 (and avgSimilarity ≥ 70 when available) */
  recommendation: 'forte' | 'acceptable' | 'faible'
}

/**
 * Aggregates quality and (optionally) similarity signals across the comp set
 * to produce a summary recommendation about the selection's representativeness.
 *
 * Returns null when qualityScores is empty.
 */
export function computeComparableSelectionSummary(
  qualityScores: ComparableQualityScore[],
  similarityScores: ComparableSimilarityEntry[] | null,
): ComparableSelectionSummary | null {
  if (qualityScores.length === 0) return null

  const count = qualityScores.length
  const avgQualityScore = Math.round(
    (qualityScores.reduce((s, q) => s + q.score, 0) / count) * 10,
  ) / 10
  const lowQualityCount = qualityScores.filter(q => q.score < 5).length

  let avgSimilarityScore: number | null = null
  if (similarityScores && similarityScores.length > 0) {
    avgSimilarityScore = Math.round(
      similarityScores.reduce((s, e) => s + e.score, 0) / similarityScores.length,
    )
  }

  let recommendation: ComparableSelectionSummary['recommendation']
  if (avgQualityScore >= 7 && (avgSimilarityScore == null || avgSimilarityScore >= 70)) {
    recommendation = 'forte'
  } else if (avgQualityScore < 4 || (avgSimilarityScore != null && avgSimilarityScore < 40)) {
    recommendation = 'faible'
  } else {
    recommendation = 'acceptable'
  }

  return { count, avgQualityScore, avgSimilarityScore, lowQualityCount, recommendation }
}
