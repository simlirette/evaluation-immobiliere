import type { Comparable, Adjustment } from '@/types'
import { computeGrossAdjustment } from './compute-gross-adjustment'
import { validateComparableDate } from './validate-comparable-date'

export interface ComparableQualityScore {
  comparableId: string
  score: number           // 0–10, higher = better quality
  recencyScore: number    // 0–5 (5 = very recent, 0 = stale)
  adjustmentScore: number // 0–5 (5 = no adjustment needed, 0 = heavy adj)
  label: 'excellent' | 'bon' | 'acceptable' | 'faible'
}

/**
 * Scores each comparable by recency (0–5) and adjustment magnitude (0–5).
 * Comparable must appear in both comps and adjs to receive a score.
 * Returns scores sorted descending by score.
 */
export function computeComparableQualityScore(
  comps: Comparable[],
  adjs: Adjustment[],
): ComparableQualityScore[] {
  const adjMap = new Map(adjs.map(a => [a.comparable_id, a]))
  const today = new Date()

  return comps
    .filter(c => adjMap.has(c.id))
    .map(c => {
      const adj = adjMap.get(c.id)!

      // Recency: 36+ months → 0pt, 0 months → 5pt (linear)
      const { ageMonths } = c.sale_date
        ? validateComparableDate(c.sale_date, today)
        : { ageMonths: null as unknown as number }
      const recencyScore = !c.sale_date || ageMonths == null
        ? 0
        : Math.max(0, Math.round(5 * (1 - Math.min(ageMonths, 36) / 36)))

      // Adjustment: grossPct 0% → 5pt, 40%+ → 0pt (linear)
      const { grossPct } = computeGrossAdjustment(adj)
      const adjustmentScore = Math.max(0, Math.round(5 * (1 - Math.min(grossPct, 40) / 40)))

      const score = recencyScore + adjustmentScore
      const label: ComparableQualityScore['label'] =
        score >= 9 ? 'excellent' : score >= 6 ? 'bon' : score >= 3 ? 'acceptable' : 'faible'

      return { comparableId: c.id, score, recencyScore, adjustmentScore, label }
    })
    .sort((a, b) => b.score - a.score)
}
