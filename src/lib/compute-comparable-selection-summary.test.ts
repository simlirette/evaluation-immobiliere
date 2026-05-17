import { describe, it, expect } from 'vitest'
import { computeComparableSelectionSummary } from './compute-comparable-selection-summary'
import type { ComparableQualityScore } from './compute-comparable-quality-score'
import type { ComparableSimilarityEntry } from './compute-comparable-similarity-score'

function mkQuality(id: string, score: number): ComparableQualityScore {
  return { comparableId: id, score, recencyScore: Math.floor(score / 2), adjustmentScore: Math.ceil(score / 2), label: score >= 9 ? 'excellent' : score >= 6 ? 'bon' : score >= 3 ? 'acceptable' : 'faible' }
}

function mkSimilarity(id: string, score: number): ComparableSimilarityEntry {
  return { comparableId: id, comparableLabel: `Comp ${id}`, score, sizeDiffPct: null, ageDiff: null }
}

describe('computeComparableSelectionSummary', () => {
  it('returns null for empty quality scores', () => {
    expect(computeComparableSelectionSummary([], null)).toBeNull()
  })

  it('count equals qualityScores length', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 8), mkQuality('b', 6)], null)!
    expect(r.count).toBe(2)
  })

  it('avgQualityScore is mean of scores', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 8), mkQuality('b', 6)], null)!
    expect(r.avgQualityScore).toBe(7)
  })

  it('avgSimilarityScore null when no similarity data', () => {
    expect(computeComparableSelectionSummary([mkQuality('a', 8)], null)!.avgSimilarityScore).toBeNull()
  })

  it('avgSimilarityScore is mean of similarity scores', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 8)], [mkSimilarity('a', 80), mkSimilarity('b', 60)])!
    expect(r.avgSimilarityScore).toBe(70)
  })

  it('lowQualityCount counts scores < 5', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 8), mkQuality('b', 4), mkQuality('c', 3)], null)!
    expect(r.lowQualityCount).toBe(2)
  })

  it('recommendation forte when avgQuality >= 7 and no similarity data', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 7), mkQuality('b', 8)], null)!
    expect(r.recommendation).toBe('forte')
  })

  it('recommendation forte when avgQuality >= 7 and avgSimilarity >= 70', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 8)], [mkSimilarity('a', 80)])!
    expect(r.recommendation).toBe('forte')
  })

  it('recommendation acceptable when avgQuality >= 7 but avgSimilarity < 70', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 8)], [mkSimilarity('a', 50)])!
    expect(r.recommendation).toBe('acceptable')
  })

  it('recommendation faible when avgQuality < 4', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 3), mkQuality('b', 3)], null)!
    expect(r.recommendation).toBe('faible')
  })

  it('recommendation faible when avgSimilarity < 40', () => {
    const r = computeComparableSelectionSummary([mkQuality('a', 7)], [mkSimilarity('a', 30)])!
    expect(r.recommendation).toBe('faible')
  })
})
