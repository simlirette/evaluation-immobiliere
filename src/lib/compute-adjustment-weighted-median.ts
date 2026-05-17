import type { Adjustment } from '@/types'

export interface AdjustmentWeightedMedian {
  /** Simple (unweighted) median of adjusted prices */
  simpleMedian: number
  /** Weighted median using reconciliation weights (1/(grossPct+1)) */
  weightedMedian: number
  /** Difference between weighted and simple median */
  delta: number
  /** delta / simpleMedian × 100 */
  deltaPct: number
}

function grossPct(a: Adjustment): number {
  const gross = Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)
  return a.salePrice > 0 ? (gross / a.salePrice) * 100 : 0
}

/**
 * Computes both the simple and weighted median of adjusted prices.
 * Weights use the same 1/(grossPct+1) formula as computeReconciledValue,
 * giving higher influence to comps requiring fewer adjustments.
 *
 * Weighted median: sort by adjusted price; accumulate weights; median at the
 * point where cumulative weight ≥ 0.5 of total.
 *
 * Returns null when fewer than 2 adjustments.
 */
export function computeAdjustmentWeightedMedian(adjs: Adjustment[]): AdjustmentWeightedMedian | null {
  if (adjs.length < 2) return null

  const sorted = [...adjs].sort((a, b) => a.adjusted - b.adjusted)
  const n = sorted.length

  // Simple median
  const simpleMedian = n % 2 === 0
    ? Math.round((sorted[n / 2 - 1].adjusted + sorted[n / 2].adjusted) / 2)
    : sorted[Math.floor(n / 2)].adjusted

  // Weights
  const weights = sorted.map(a => 1 / (grossPct(a) / 100 + 1))
  const totalWeight = weights.reduce((s, w) => s + w, 0)
  const normalizedWeights = weights.map(w => w / totalWeight)

  // Weighted median: find value where cumulative weight first reaches 0.5
  let cumulative = 0
  let weightedMedian = sorted[0].adjusted
  for (let i = 0; i < sorted.length; i++) {
    cumulative += normalizedWeights[i]
    if (cumulative >= 0.5) {
      weightedMedian = sorted[i].adjusted
      break
    }
  }

  const delta = weightedMedian - simpleMedian
  const deltaPct = simpleMedian > 0 ? Math.round((delta / simpleMedian) * 10000) / 100 : 0

  return { simpleMedian, weightedMedian, delta, deltaPct }
}
