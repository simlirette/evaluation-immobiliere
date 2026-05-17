import type { Comparable, Adjustment } from '@/types'

export interface NeighborhoodComparability {
  /** 0–100 score: higher = more comparable set represents subject neighborhood well */
  score: number
  /** 'forte' ≥ 70, 'modérée' 40–69, 'faible' < 40 */
  strength: 'forte' | 'modérée' | 'faible'
  /** Recency signal: fraction of comps sold within 24 months (0–100) */
  recencyScore: number
  /** Price concentration: inverse of CV of sale prices (tighter range = more representative) */
  concentrationScore: number
  /** Adjustment magnitude: low gross adjustments = comps are already comparable */
  adjustmentScore: number
}

/**
 * Scores how well the comparable set represents the subject's market neighborhood.
 *
 * Three signals (each 0–100, equal weight):
 * 1. Recency: % of comps sold within 24 months of today
 * 2. Price concentration: max(0, 100 - CV%) where CV is stdDev/mean of sale prices
 * 3. Adjustment magnitude: max(0, 100 - avgGrossPct×5) where avgGrossPct is mean gross adj %
 *
 * Returns null when fewer than 2 adjustments or no comparables.
 */
export function computeNeighborhoodComparability(
  comps: Comparable[],
  adjs: Adjustment[],
): NeighborhoodComparability | null {
  if (adjs.length < 2 || comps.length === 0) return null

  const now = new Date()

  // 1. Recency score: comps sold within 24 months
  const compDates = comps.filter(c => c.sale_date).map(c => new Date(c.sale_date))
  const recentCount = compDates.filter(d => {
    const monthsAgo = (now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24 * 30.44)
    return monthsAgo <= 24
  }).length
  const recencyScore = compDates.length > 0 ? Math.round((recentCount / compDates.length) * 100) : 0

  // 2. Price concentration: CV of sale prices
  const prices = comps.filter(c => c.sale_price > 0).map(c => c.sale_price)
  let concentrationScore = 0
  if (prices.length >= 2) {
    const mean = prices.reduce((s, v) => s + v, 0) / prices.length
    const variance = prices.reduce((s, v) => s + (v - mean) ** 2, 0) / prices.length
    const cv = mean > 0 ? (Math.sqrt(variance) / mean) * 100 : 100
    concentrationScore = Math.max(0, Math.round(100 - cv))
  }

  // 3. Adjustment magnitude: average gross adjustment as % of sale price
  const grossPcts = adjs.map(a => {
    const gross = Math.abs(a.surface_adj) + Math.abs(a.year_adj) + Math.abs(a.condition_adj) + Math.abs(a.garage_adj)
    return a.salePrice > 0 ? (gross / a.salePrice) * 100 : 0
  })
  const avgGrossPct = grossPcts.reduce((s, v) => s + v, 0) / grossPcts.length
  const adjustmentScore = Math.max(0, Math.round(100 - avgGrossPct * 5))

  const score = Math.round((recencyScore + concentrationScore + adjustmentScore) / 3)
  const strength: NeighborhoodComparability['strength'] =
    score >= 70 ? 'forte' : score >= 40 ? 'modérée' : 'faible'

  return { score, strength, recencyScore, concentrationScore, adjustmentScore }
}
