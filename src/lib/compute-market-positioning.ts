import type { Adjustment } from '@/types'

export interface MarketPositioning {
  /** Proposed conclusion value */
  conclusion: number
  /** Percentile rank in the adjusted price distribution (0–100) */
  percentileRank: number
  /** Number of comparables with adjusted price below conclusion */
  countBelow: number
  /** Number of comparables with adjusted price above conclusion */
  countAbove: number
  /** Total comparables in set */
  total: number
  /** Nearest comparable below conclusion (by adjusted price), or null */
  nearestBelow: { label: string; adjustedPrice: number; delta: number } | null
  /** Nearest comparable above conclusion (by adjusted price), or null */
  nearestAbove: { label: string; adjustedPrice: number; delta: number } | null
  /** 'bas' percentile < 33, 'médian' 33–66, 'haut' > 66 */
  position: 'bas' | 'médian' | 'haut'
}

/**
 * Computes where a proposed conclusion sits within the adjusted price
 * distribution of the comparable set.
 *
 * Returns null when no adjustments or no conclusion provided.
 */
export function computeMarketPositioning(
  conclusion: number,
  adjs: Adjustment[],
): MarketPositioning | null {
  if (adjs.length === 0 || conclusion <= 0) return null

  const sorted = [...adjs].sort((a, b) => a.adjusted - b.adjusted)
  const countBelow = sorted.filter(a => a.adjusted < conclusion).length
  const countAbove = sorted.filter(a => a.adjusted > conclusion).length
  const total = sorted.length

  // Percentile: fraction of values strictly below conclusion
  const percentileRank = Math.round((countBelow / total) * 100)

  const below = sorted.filter(a => a.adjusted < conclusion)
  const above = sorted.filter(a => a.adjusted > conclusion)

  const nearestBelowAdj = below.length > 0 ? below[below.length - 1] : null
  const nearestAboveAdj = above.length > 0 ? above[0] : null

  const nearestBelow = nearestBelowAdj
    ? { label: nearestBelowAdj.comparableLabel, adjustedPrice: nearestBelowAdj.adjusted, delta: conclusion - nearestBelowAdj.adjusted }
    : null
  const nearestAbove = nearestAboveAdj
    ? { label: nearestAboveAdj.comparableLabel, adjustedPrice: nearestAboveAdj.adjusted, delta: nearestAboveAdj.adjusted - conclusion }
    : null

  const position: MarketPositioning['position'] =
    percentileRank < 33 ? 'bas' : percentileRank <= 66 ? 'médian' : 'haut'

  return { conclusion, percentileRank, countBelow, countAbove, total, nearestBelow, nearestAbove, position }
}
